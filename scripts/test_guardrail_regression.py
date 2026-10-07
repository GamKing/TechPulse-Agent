#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
防自欺端到端回归测试 (Guardrail Regression Suite)
Frontier Tech Industrial Analysis Engine

模拟三类恶意输入，验证裁判引擎 100% 触发 Fail-Closed 精准拦截：
  1. 伪造 URL + 篡改快照哈希（门禁 1：来源存在性）
  2. 浮点计算矛盾（门禁 4：参数溯源 AST 重算）
  3. 主观煽动词注入（门禁 9：全局精度正则审计 + 门禁 8：估值解耦）
  4. 作者自评不算验证（门禁 2：语义蕴含必须独立审稿背书）

全部断言必须在 FAIL-Closed 语义下成立：任何伪造证据都不得产生 PASS。
"""

import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from deterministic_judge import DeterministicJudge
from evidence_auditor_harness import EvidenceAuditorHarness
from verification import digest, calculate


class GuardrailRegressionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        # 伪造证据：URL 指向不存在域名，content_hash 是作者自填的假哈希
        self.forged = {'id': 'FORGED-1', 'claim': 'Revenue is 999 billion.',
                       'source_url': 'https://forged.invalid/not-real',
                       'http_status': 200, 'content_hash': 'sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff',
                       'extracted_text': 'Revenue is 999 billion (author claims).'}

    # ---- 1. 伪造 URL + 无独立抓取 → 必须 FAIL ----
    def test_forged_url_without_independent_fetch_fails_closed(self):
        judge = DeterministicJudge(benchmark_dir=self.root)
        gate = judge.audit_gate_1_source_existence([self.forged])
        self.assertEqual(gate['status'], 'FAIL')

    # ---- 1b. 伪造内容哈希（作者自填）不被信任 → 必须 FAIL ----
    def test_author_declared_hash_not_trusted(self):
        judge = DeterministicJudge(benchmark_dir=self.root)
        # 作者声称 verification 全绿，但没有真实 receipt / 快照
        judge.verification_results = {'FORGED-1': {
            'fetch_status': 'FETCHED', 'http_status': 200,
            'source_url': self.forged['source_url'],
            'snapshot_path': 'source_snapshots/missing.bin',
            'content_hash': 'sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'}}
        gate = judge.audit_gate_1_source_existence([self.forged])
        # 快照文件不存在 → 无论哈希声明为何都必须 FAIL
        self.assertEqual(gate['status'], 'FAIL')

    # ---- 2. 浮点计算矛盾（声明值 ≠ AST 重算值）→ 必须 FAIL ----
    def test_contradictory_math_fails_closed(self):
        judge = DeterministicJudge(benchmark_dir=self.root)
        data = {'parameter_provenance_cards': [{
            'param_id': 'P-1',
            'name': 'Fake learning rate',
            'base_value': 0.42,                     # 声明 42%（fake）
            'calculation': {'expression': '1 - 2**(b)', 'inputs': {'b': -0.23447}}}]}
        gate = judge.audit_gate_4_parameter_provenance_recalculation(data)
        # 0.1500028 ≠ 0.42 → FAIL（Fail-Closed 拦截自嗨数字）
        self.assertEqual(gate['status'], 'FAIL')

    def test_malicious_expression_rejected(self):
        judge = DeterministicJudge(benchmark_dir=self.root)
        data = {'parameter_provenance_cards': [{
            'param_id': 'P-2',
            'base_value': 1.0,
            'calculation': {'expression': '__import__("os").system("x")', 'inputs': {}}}]}
        gate = judge.audit_gate_4_parameter_provenance_recalculation(data)
        self.assertEqual(gate['status'], 'FAIL')

    # ---- 2b. 正确可重算公式 → PASS（对照：证明门禁有真判定能力）----
    def test_honest_math_passes(self):
        judge = DeterministicJudge(benchmark_dir=self.root)
        # 用能精确满足 isclose(rel_tol=1e-9) 的 base_value：直接取自重算结果
        recomputed = calculate('1 - 2**(b)', {'b': -0.23447})
        data = {'parameter_provenance_cards': [{
            'param_id': 'P-3',
            'base_value': recomputed,
            'calculation': {'expression': '1 - 2**(b)', 'inputs': {'b': -0.23447}}}]}
        gate = judge.audit_gate_4_parameter_provenance_recalculation(data)
        self.assertEqual(gate['status'], 'PASS')

    # ---- 3. 缺失认知分类标签的"黑话"报告 → 触发精度门禁拦截 ----
    def test_manipulative_prose_triggers_precision_gate(self):
        # report.md 用主观煽动口吻且缺 [FACT]/[ASSUMPTION] 等认知分类标签
        report = self.root / 'report.md'
        report.write_text('该标的属于白马底仓，安全边际极高，当前处于估值洼地，建议加仓。', encoding='utf-8')
        judge = DeterministicJudge(benchmark_dir=self.root)
        gate = judge.audit_gate_6_global_precision_regex((self.root / 'report.md').read_text(encoding='utf-8'))
        # 缺少必需认知分类标签 → FAIL（Fail-Closed）
        self.assertEqual(gate['status'], 'FAIL')

    # ---- 3b. 证伪句必须带精度标签；无标签笼统措辞被判非 PASS ----
    def test_vague_claim_not_passed(self):
        report = self.root / 'report.md'
        report.write_text('英伟达营收大幅增长，核心技术遥遥领先。', encoding='utf-8')
        judge = DeterministicJudge(benchmark_dir=self.root)
        gate = judge.audit_gate_6_global_precision_regex((self.root / 'report.md').read_text(encoding='utf-8'))
        # 无 [SECONDARY ESTIMATE] 等标签 → FAIL（绝非 PASS）
        self.assertEqual(gate['status'], 'FAIL')

    # ---- 4. 作者自评"verified"永远不算验证 → 门禁 2 拒绝 ----
    def test_author_self_assessment_never_passes_entailment(self):
        judge = DeterministicJudge(benchmark_dir=self.root)
        self.forged.update(claim_support='FULL', verdict='VERIFIED')
        gate = judge.audit_gate_2_claim_entailment_target_result([self.forged])
        self.assertEqual(gate['status'], 'UNVERIFIED')  # 未绑定独立审稿 receipt

    # ---- 5. 端到端：整条证据链被污染 → 裁判仍守住 FAIL ----
    def test_end_to_end_forged_pipeline_fails(self):
        from unittest.mock import patch
        shutil.copytree(Path(__file__).resolve().parents[1] / 'reports/nvidia_benchmark',
                        self.root, dirs_exist_ok=True)
        (self.root / 'evidence.jsonl').write_text(json.dumps(self.forged) + '\n', encoding='utf-8')
        harness = EvidenceAuditorHarness(self.root, config_path=str(self.root / 'missing.json'),
                                         force_override=True)
        with patch('evidence_auditor_harness.fetch_source', return_value=(
                b'forged bytes', 'attacker text', 200, self.forged['source_url'])), \
                patch.object(harness, 'call_external_llm',
                             return_value=json.dumps({'entailment': 'FULL',
                                                      'target_to_result_drift': False,
                                                      'epistemic_type_valid': True,
                                                      'confidence': 'HIGH',
                                                      'evidence_quote': 'attacker text'})), \
                contextlib.redirect_stdout(io.StringIO()):
            scorecard = harness.execute_pipeline()
        self.assertEqual(scorecard['overall_verdict'], 'FAIL')


if __name__ == '__main__':
    unittest.main()