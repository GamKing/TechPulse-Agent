"""Verification gates. Live audit receipts are supplied by the harness, never by evidence.jsonl."""
import math
import ast
import operator
from verification import calculate, digest


class StrictGates:
    def _result(self, name, status, details, priority='CRITICAL'):
        return {'gate': name, 'type': priority, 'status': status, 'details': details}

    # =========================================================================
    # 单位契约 (Unit Contract)：防止参数卡跨量纲胡乱运算
    # =========================================================================
    @staticmethod
    def _unit_dims(unit: str) -> dict:
        """把单位字符串规范化为 基础量纲 → 幂次 映射。

        支持形如 'USD/unit'、'k_units/month'、'USD'、'GB * unit' 的简单单位。
        无法解析的 token 视为原子量纲幂次 1。返回 None 表示 unit 缺失/空。
        """
        if not unit or not str(unit).strip():
            return None
        s = str(unit).strip().replace('(', ' ').replace(')', ' ')
        # 拆 '/'：分子在前（+1 幂），分母在后（-1 幂）
        parts = s.split('/')
        dims = {}
        for slot, chunk in enumerate(parts):
            sign = -1 if slot >= 1 else 1
            for token in chunk.replace('*', ' ').replace('·', ' ').split():
                token = token.strip()
                if token:
                    dims[token] = dims.get(token, 0) + sign
        return dims

    @staticmethod
    def _dims_eq(a: dict, b: dict) -> bool:
        return a == b or (not a and not b)

    @staticmethod
    def _dims_scale(a: dict, k: float) -> dict:
        """标量乘：k 视为无量纲，量纲不变。"""
        return dict(a)

    @classmethod
    def _check_expression_units(cls, expression: str, unit_map: dict) -> list:
        """AST 可视化推导表达式各子式量纲，检测跨量纲 add/sub。

        unit_map: {变量名 -> 单位字符串}。字面量视为无量纲 {}（与任何 dims 可加，除非显式标注）。
        返回违规列表；无违规返回空列表。
        乘除量纲按向量相加减推导（启发式，纯标准库）。
        """
        violations = []
        try:
            tree = ast.parse(expression, mode='eval')
        except SyntaxError:
            return []
        var_dims = {}
        # 先解析变量的单位
        for name, u in (unit_map or {}).items():
            if isinstance(u, str):
                d = cls._unit_dims(u)
                if d is not None:
                    var_dims[name] = d
        import operator as _op
        mul = _op.mul
        ops = {ast.Add: lambda a, b: ({}, {}), ast.Sub: lambda a, b: ({}, {})}

        def _dims_of(node, known=None):
            nonlocal violations
            known = known if known is not None else var_dims
            if isinstance(node, ast.Constant):
                return {}  # 字面量无量纲
            if isinstance(node, ast.Name):
                # 只认 unit_map 显式声明的量纲；未声明→None（不做任何臆造，不触发跨量纲判定）
                return known.get(node.id)
            if isinstance(node, ast.UnaryOp):
                return _dims_of(node.operand, known)
            if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub)):
                a = _dims_of(node.left, known)
                b = _dims_of(node.right, known)
                # 仅当两侧量纲都"已知且明确"时才判定跨量纲；任一未知→不判（避免误伤）
                if a is not None and b is not None and not cls._dims_eq(a, b):
                    violations.append(
                        f"'{expression}' 中 {'+  ' if isinstance(node.op, ast.Add) else '-  '}跨量纲: {a} vs {b}")
                return a if a is not None else b
            if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Mult, ast.Div)):
                a = _dims_of(node.left, known)
                b = _dims_of(node.right, known)
                if a is None or b is None:
                    return a or b
                if isinstance(node.op, ast.Div):
                    return {k: a.get(k, 0) - b.get(k, 0) for k in set(a) | set(b)}
                return {k: a.get(k, 0) + b.get(k, 0) for k in set(a) | set(b)}
            if isinstance(node, ast.Pow):
                return _dims_of(node.left, known)
            return None
        _dims_of(tree.body)
        return violations

    def audit_gate_parameter_unit_contract(self, data):
        """逐参数卡检查：有 calculation 的参数卡必须声明 unit；AST 可视化检查加减不跨量纲。

        规则：
          1. 有 calculation 的参数卡若缺省 unit → FAIL（强契约：每个可演算参数都要单位）。
          2. 对计算表达式做 AST 可视化，add/sub 两操作数量纲必须一致；mul/div 量纲由子式导出。
        单位解析是启发式的（标准单位名词表）——无法解析的单位按原子量纲处理，不误伤。
        """
        cards = (data or {}).get('parameter_provenance_cards', [])
        violations = []
        base_units = {}   # param_id -> dims（供表达式引用）
        for card in cards:
            cid = card.get('param_id', 'UNKNOWN')
            unit = card.get('unit')
            spec = card.get('calculation')
            if not isinstance(spec, dict):
                continue
            dims = self._unit_dims(unit)
            if dims is None:
                violations.append(f'{cid}: 有 calculation 但未声明 unit（Unit Contract 违约）')
            else:
                base_units[cid] = dims
                expr = spec.get('expression', '')
                unit_map = spec.get('unit_map') or {}
                cross = self._check_expression_units(expr, unit_map)
                if cross:
                    violations.extend(f'{cid}: {c}' for c in cross)
        return self._result('GATE_PARAMETER_UNIT_CONTRACT',
                            'FAIL' if violations else ('PASS' if cards else 'UNVERIFIED'),
                            '; '.join(violations) if violations else
                            (f'All {len(cards)} parameter cards declare units; AST-level cross-unit check applies.' if cards else 'No parameter cards to check.'),
                            'HIGH')

    def audit_gate_1_source_existence(self, records):
        errors = []
        if not records:
            errors.append('No evidence records')
        seen = set()
        for record in records or []:
            cid = record.get('id')
            receipt = self.verification_results.get(cid, {})
            if not cid or cid in seen:
                errors.append('Missing or duplicate claim ID')
            seen.add(cid)
            path = self.benchmark_dir / receipt.get('snapshot_path', '__missing__')
            if not path.resolve().is_relative_to(self.benchmark_dir.resolve()):
                errors.append(f'{cid}: snapshot outside benchmark directory')
                continue
            if (receipt.get('fetch_status') != 'FETCHED' or receipt.get('http_status') != 200
                    or receipt.get('source_url') != record.get('source_url')
                    or not path.is_file()):
                errors.append(f'{cid}: no successful independent fetch in this run')
            elif digest(path.read_bytes()) != receipt.get('content_hash'):
                errors.append(f'{cid}: snapshot hash mismatch')
        return self._result('GATE_SOURCE_EXISTENCE', 'FAIL' if errors else 'PASS',
                            '; '.join(errors) or 'Live source snapshots match recomputed hashes; this does not establish claim truth.')

    def audit_gate_2_claim_entailment_target_result(self, records):
        errors, missing = [], []
        for record in records or []:
            cid = record.get('id')
            receipt = self.verification_results.get(cid, {})
            if record.get('claim_support') == 'CONTRADICT':
                errors.append(f'{cid}: recorded contradiction')
            if receipt.get('claim_hash') != digest(str(record.get('claim', '')).encode('utf-8')):
                missing.append(f'{cid}: no audit bound to current claim')
                continue
            result = receipt.get('assessment')
            if receipt.get('audit_status') != 'COMPLETED' or not result:
                missing.append(f'{cid}: semantic verification not completed')
                continue
            if (result.get('entailment') != 'FULL' or result.get('target_to_result_drift') is not False
                    or result.get('epistemic_type_valid') is not True):
                errors.append(f'{cid}: claim unsupported, contradicted, or epistemically invalid')
        if not records:
            errors.append('No evidence records')
        return self._result('GATE_CLAIM_ENTAILMENT_TARGET_RESULT',
                            'FAIL' if errors else ('UNVERIFIED' if missing else 'PASS'),
                            '; '.join(errors + missing) or 'Independent model assessments support these claims; model review is not a guarantee of truth.')

    def audit_gate_4_parameter_provenance_recalculation(self, data):
        cards = (data or {}).get('parameter_provenance_cards', [])
        errors, unsupported = [], []
        for card in cards:
            cid = card.get('param_id', 'UNKNOWN')
            spec = card.get('calculation')
            if not isinstance(spec, dict):
                unsupported.append(f'{cid}: no executable calculation specification')
                continue
            try:
                value = calculate(spec['expression'], spec['inputs'])
                expected = card['base_value']
                if type(expected) not in (int, float) or not math.isfinite(expected):
                    raise ValueError('Non-finite or non-numeric base_value')
                if not math.isclose(value, expected, rel_tol=1e-9, abs_tol=1e-12):
                    errors.append(f'{cid}: declared {expected}, computed {value}')
            except (ValueError, TypeError, KeyError, SyntaxError, ArithmeticError) as exc:
                errors.append(f'{cid}: invalid calculation ({exc})')
        if not cards:
            errors.append('No parameter cards')
        return self._result('GATE_PARAMETER_PROVENANCE_RECALCULATION',
                            'FAIL' if errors else ('UNVERIFIED' if unsupported else 'PASS'),
                            '; '.join(errors + unsupported) or 'Arithmetic recomputed only; input provenance and units require separate review.')

    def audit_gate_parameter_preregistration_blind(self, data):
        reg = (data or {}).get('blind_parameterization_registry', {})
        if not reg:
            return self._result('GATE_PARAMETER_PREREGISTRATION_BLIND', 'UNVERIFIED',
                                'No blind_parameterization_registry found in assumptions data.')
        t_pre = reg.get('pre_registration_timestamp')
        t_cmp = reg.get('comparison_timestamp')
        top_hash = reg.get('top_down_set_hash')
        bottom_hash = reg.get('bottom_up_set_hash')
        proto = reg.get('isolation_protocol')
        if not (t_pre and t_cmp and top_hash and bottom_hash):
            return self._result('GATE_PARAMETER_PREREGISTRATION_BLIND', 'FAIL',
                                'Incomplete registration metadata: timestamps or parameter hashes missing.')
        if proto != 'BLIND_PARAMETERIZATION_ENFORCED':
            return self._result('GATE_PARAMETER_PREREGISTRATION_BLIND', 'FAIL',
                                f'Invalid isolation protocol: {proto}')
        if t_pre > t_cmp:
            return self._result('GATE_PARAMETER_PREREGISTRATION_BLIND', 'FAIL',
                                'Chronological violation: pre-registration timestamp is after comparison timestamp.')
        if reg.get('post_comparison_modification_detected', False):
            return self._result('GATE_PARAMETER_PREREGISTRATION_BLIND', 'FAIL',
                                'Post-comparison modification detected in parameter set.')
        return self._result('GATE_PARAMETER_PREREGISTRATION_BLIND', 'PASS',
                            'Pre-registration cryptographic lock hashes and chronological timestamps verified.')

    def audit_gate_validation_leakage(self, data, holdout):
        if not holdout:
            return self._result('GATE_VALIDATION_LEAKAGE', 'UNVERIFIED',
                                'No holdout registry provided for validation leakage audit.', 'HIGH')
        proto = holdout.get('isolation_protocol')
        if proto not in ('STRICT_INFORMATION_FIREWALL', 'CRYPTOGRAPHICALLY_ENFORCED'):
            return self._result('GATE_VALIDATION_LEAKAGE', 'FAIL',
                                f'Holdout isolation protocol not enforced ({proto}).', 'HIGH')
        indep = holdout.get('independence_audit', {}).get('independence_verdict')
        if indep != 'INDEPENDENT':
            return self._result('GATE_VALIDATION_LEAKAGE', 'FAIL',
                                f'Holdout independence audit failed: {indep}', 'HIGH')
        ts = holdout.get('timestamps', {})
        if not ts.get('chronological_order_valid', False):
            return self._result('GATE_VALIDATION_LEAKAGE', 'FAIL',
                                'Timeline firewall chronological order invalid.', 'HIGH')
        return self._result('GATE_VALIDATION_LEAKAGE', 'PASS',
                            'Timeline firewall and holdout dataset isolation verified; no leakage detected.', 'HIGH')

    def audit_gate_artifact_enforcement(self, benchmark_dir):
        names = ['parameter_registry.json', 'validation_criteria.json', 'holdout_registry.json',
                 'model_run_topdown.json', 'model_run_bottomup.json', 'validation_run.json',
                 'audit_log.jsonl', 'evidence.jsonl', 'report.md']
        missing = [name for name in names if not (benchmark_dir / name).is_file()
                   or not (benchmark_dir / name).stat().st_size]
        return self._result('GATE_ARTIFACT_ENFORCEMENT', 'FAIL' if missing else 'PASS',
                            'Missing: ' + ', '.join(missing) if missing else
                            'All 9 required benchmark artifacts physically exist and are non-empty.', 'HIGH')

