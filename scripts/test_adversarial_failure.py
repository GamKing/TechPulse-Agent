#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对抗攻防测试套件 (Adversarial Failure Testing)
Frontier Tech Industrial Analysis Engine

战术动作2：故意搞破坏的逆向测试，证明 Fail-Closed（非证伪即拒绝）不是纸老虎。

三大攻击场景（均以 nvidia 全绿 Golden 基线为基底，注入破坏后断言对应门禁 FAIL）：
  A. 伪造算术攻击 —— 篡改 parameter_registry 预期结果 → Gate 4 AST 重算 FAIL
  B. 篡改快照攻击 —— 改 source_snapshots 一个字节 → Gate 1 SHA-256 哈希不符 FAIL
  C. 空洞口号攻击 —— 塞无事实支撑的空泛断言 → Gate 10 因果距离 / Gate 11 估值脱钩拦截

核心立场：合法数据 PASS、伪造数据 FAIL——双向证明系统既有"抗辩力"又有"熔断力"。
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from deterministic_judge import DeterministicJudge


def _copy_golden(tmp: Path) -> Path:
    src = Path(__file__).resolve().parents[1] / 'reports/nvidia_benchmark'
    dest = tmp / 'golden'
    shutil.copytree(src, dest)
    return dest


class AdversarialFailureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    # ---- A. 伪造算术攻击：篡改参数卡预期值 → Gate 4 FAIL ----
    def test_forged_arithmetic_expectation_fails_gate4(self):
        bench = _copy_golden(self.root)
        # 读取当前 assumptions 的参数卡，把 base_value 篡改成错误值
        ap = bench / 'assumptions.json'
        a = json.loads(ap.read_text(encoding='utf-8'))
        for card in a.get('parameter_provenance_cards', []):
            if card.get('param_id') == 'P-T01' and card.get('calculation'):
                card['base_value'] = 0.999  # 伪造：真实重算是 0.150003
        ap.write_text(json.dumps(a, ensure_ascii=False, indent=2), encoding='utf-8')

        judge = DeterministicJudge(benchmark_dir=bench)
        sc = judge.execute_audit()
        gate = next(g for g in sc['gate_breakdown'] if g['gate'] == 'GATE_PARAMETER_PROVENANCE_RECALCULATION')
        self.assertEqual(gate['status'], 'FAIL', "伪造算术预期必须被 Gate 4 一票否决")
        self.assertEqual(sc['overall_verdict'], 'FAIL', "整体 verdict 必须 FAIL")

    # ---- A2. 恶意表达式注入 → Gate 4 拒绝 ----
    def test_forged_expression_rejected(self):
        from verification import calculate
        with self.assertRaises((ValueError, ArithmeticError)):
            calculate("__import__('os').system('x')", {})

    # ---- B. 篡改快照攻击：改一个字节 → Gate 1 哈希不符 FAIL ----
    def test_tampered_snapshot_byte_fails_gate1(self):
        bench = _copy_golden(self.root)
        # 找一个真实快照，翻转一个字节
        snap_dir = bench / 'source_snapshots'
        snaps = list(snap_dir.glob('*.bin'))
        self.assertTrue(snaps, "Golden 应有 source_snapshots")
        target = snaps[0]
        data = bytearray(target.read_bytes())
        data[0] ^= 0x01  # 翻转第一个字节
        target.write_bytes(bytes(data))

        judge = DeterministicJudge(benchmark_dir=bench)
        sc = judge.execute_audit()
        gate = next(g for g in sc['gate_breakdown'] if g['gate'] == 'GATE_SOURCE_EXISTENCE')
        self.assertEqual(gate['status'], 'FAIL', "篡改快照必须被 Gate 1 哈希比对拒绝")
        self.assertIn('hash mismatch', gate['details'].lower())

    # ---- C. 空洞口号攻击：无事实支撑的空泛断言 → Gate 10/11 拦截 ----
    def test_vague_slogan_attacks_gate10_gate11(self):
        bench = _copy_golden(self.root)
        # 篡改 report.md：塞入煽动词（Gate 11 拦截）
        rp = bench / 'report.md'
        original = rp.read_text(encoding='utf-8')
        # 追加无事实支撑的空泛断言 + 禁止煽动词
        rp.write_text(original + "\n该公司未来必将垄断具身智能市场，属于强烈推荐、安全边际高的白马底仓。\n", encoding='utf-8')
        # 篡改 thesis：一条 FAR 因果距离却配 STRONG（Gate 10 拦截）
        tp = bench / 'thesis.json'
        t = json.loads(tp.read_text(encoding='utf-8'))
        t.setdefault('evidence_to_hypothesis_impact_matrix', [])
        t['evidence_to_hypothesis_impact_matrix'].append({
            "evidence_id": "FAKE-E01", "causal_distance": "FAR",
            "impact_HA": "STRONG_SUPPORT"
        })
        tp.write_text(json.dumps(t, ensure_ascii=False, indent=2), encoding='utf-8')

        judge = DeterministicJudge(benchmark_dir=bench)
        sc = judge.execute_audit()
        g10 = next(g for g in sc['gate_breakdown'] if g['gate'] == 'GATE_CAUSAL_DISTANCE_PENALTY')
        g11 = next(g for g in sc['gate_breakdown'] if g['gate'] == 'GATE_VALUATION_DECOUPLING')
        # Gate 11 应拦截煽动词；Gate 10 应拦截 FAR+STRONG。
        # 二者均为 HIGH 门禁——红灯(FAIL)使整体降级为 PARTIAL_PASS（critical 一票否决才会 FAIL）。
        self.assertEqual(g11['status'], 'FAIL', "煽动词必须被 Gate 11 拦截")
        self.assertEqual(g10['status'], 'FAIL', "FAR+STRONG 因果距离违规必须被 Gate 10 拦截")
        self.assertNotEqual(sc['overall_verdict'], 'PASS', "HIGH 门禁红灯后整体不得 PASS")

    # ---- C2. 空泛断言在正则门禁被拦（Gate 9 精度审计）----
    def test_vague_claim_fails_precision_gate(self):
        bench = _copy_golden(self.root)
        rp = bench / 'report.md'
        # 删掉所有认知分类标签 → Gate 9 缺失必需标签 FAIL
        import re
        text = rp.read_text(encoding='utf-8')
        text = re.sub(r'\[(FACT|SECONDARY ESTIMATE|ASSUMPTION|MODEL RESULT|INFERENCE|FORECAST)[^\]]*\]', '', text)
        rp.write_text(text, encoding='utf-8')
        judge = DeterministicJudge(benchmark_dir=bench)
        sc = judge.execute_audit()
        g9 = next(g for g in sc['gate_breakdown'] if g['gate'] == 'GATE_GLOBAL_PRECISION_REGEX_AUDIT')
        self.assertEqual(g9['status'], 'FAIL', "缺失认知分类标签必须被 Gate 9 拦截")


if __name__ == '__main__':
    unittest.main()
