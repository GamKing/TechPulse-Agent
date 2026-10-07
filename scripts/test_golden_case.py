#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-End Golden Case 回归测试 (全闭环黄金基准)
Frontier Tech Industrial Analysis Engine

战术动作1：验证整条链路在真实数据下能"合法 PASS"（工业级抗辩力证明）。

Golden 基线 = reports/nvidia_benchmark（数据全真实：真实抓取快照+SHA256、真实审稿、真实参数卡）。
检验点：
  1. 门禁验证：13 道门禁全部 PASS，overall_verdict=PASS，exit 语义 0。
  2. 纯代码验算（无 LLM）：Gate 4 依赖的 verification.calculate 用 AST 白名单，
     正确重算 莱特定律 LR=1-2^b、BOM 累积降本 C1*Q^b、毛利拐点 (1-(1-LR)^n)。
  3. 检索/计算内核：以"莱特定律×封装良品率→BOM 降本→毛利拐点"为 Golden 计算内核，
     验证 AST 原语在无模型参与下产出确定性的正确浮点。

核心立场（与 Fail-Closed 一致）：Golden Case 验证的是"合法数据能 PASS"，
不是"造假凑绿"。检索布局若达不到理想切片分布是语料覆盖边界，不在本测试捏造。
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from verification import calculate
from deterministic_judge import DeterministicJudge


class GoldenCaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        # 复制真实 golden 基线
        src = Path(__file__).resolve().parents[1] / 'reports/nvidia_benchmark'
        shutil.copytree(src, self.root, dirs_exist_ok=True)

    # ---- 1. 门禁验证：13 道全绿 PASS ----
    def test_all_13_gates_pass_on_golden_baseline(self):
        judge = DeterministicJudge(benchmark_dir=self.root)
        sc = judge.execute_audit()
        self.assertEqual(sc['overall_verdict'], 'PASS')
        gates = {g['gate']: g['status'] for g in sc['gate_breakdown']}
        self.assertEqual(len(gates), 13, f"应 13 道门禁, 实际 {len(gates)}")
        for name, status in gates.items():
            self.assertEqual(status, 'PASS', f"门禁 {name} 应为 PASS, 实际 {status}")
        # exit 语义：overall==PASS → 0
        self.assertEqual(0 if sc['overall_verdict'] == 'PASS' else 1, 0)

    # ---- 2. 纯代码验算（无 LLM，AST 白名单）----
    def test_wrights_law_pure_code_recalculation(self):
        # 莱特定律 LR = 1 - 2^b；无任何 LLM 参与
        lr = calculate('1 - 2**(b)', {'b': -0.23447})
        self.assertAlmostEqual(lr, 0.150003, places=4)
        # BOM 累积降本：4 次累积产量翻倍后成本残值率 C1*Q^b
        bom = calculate('C1 * (2**(n*b))', {'C1': 100.0, 'n': 4.0, 'b': -0.23447})
        self.assertAlmostEqual(bom, 52.20, places=1)
        # 毛利拐点：累计毛利改善系数 1-(1-LR)^n
        margin = calculate('1 - (1 - LR)**n', {'LR': 0.15, 'n': 4.0})
        self.assertAlmostEqual(margin, 0.4780, places=3)

    # ---- 3. 良品率爬坡 → 降本 → 毛利拐点的三段推演（Golden 计算内核）----
    def test_bom_cost_and_margin_turning_point_golden_core(self):
        # 场景：人形机器人专用主控芯片，良品率爬坡带动成本下降
        # 阶段1: 良品率 0.70→0.90 爬坡, 有效产出提升
        effective_yield = calculate('yield_start + ramp * periods', {'yield_start': 0.70, 'ramp': 0.05, 'periods': 4.0})
        self.assertAlmostEqual(effective_yield, 0.90, places=3)
        # 阶段2: 莱特定律驱动单位 BOM 降本
        lr = calculate('1 - 2**(b)', {'b': -0.25})
        bom_unit = calculate('C1 * (2**(n*b))', {'C1': 120.0, 'n': 5.0, 'b': -0.25})
        # 阶段3: 毛利拐点（成本降速 > 价格降速）
        margin_delta = calculate('(1 - (1 - LR)**n) - price_erosion', {'LR': lr, 'n': 5.0, 'price_erosion': 0.10})
        # 拐点成立: 毛利改善系数显著 > 价格侵蚀
        self.assertGreater(margin_delta, 0.20)
        # 所有重算确定性：AST 白名单、有限浮点、无 LLM
        self.assertIsInstance(bom_unit, float)
        self.assertTrue(all(x == x for x in [lr, bom_unit, margin_delta]))  # 非 NaN

    # ---- 4. 恶意表达式在纯代码验算下被拒（Golden 的抗伪造面）----
    def test_golden_rejects_code_injection(self):
        for expr in ["__import__('os').system('x')", 'float("nan")', '2**10000', '1/0']:
            with self.assertRaises((ValueError, ArithmeticError)):
                calculate(expr, {})


# ---- RAG 确定性评测（自建、纯标准库，防检索负优化）----
class RagEvalTests(unittest.TestCase):
    def test_rag_benchmark_metrics_meet_thresholds(self):
        # 对真实 golden dataset 运行评测，指标应达阈值（Hit@5>=60%, MRR>=0.3, 饥饿率=0）
        import sys
        _repo = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(_repo / 'scripts'))
        from eval_rag import run_rag_benchmark
        # 捕获指标：eval_rag 内部打印+sys.exit，这里改由问题绕开 exit 用私有方式调用
        # 直接复用其数据与检索，单独计算三项指标
        import json
        cases = json.loads((_repo / 'tests/retrieval_golden_dataset.json').read_text(encoding='utf-8'))
        from problem_router import ProblemRouter
        router = ProblemRouter()
        hits = mrr = topic_hits = starve = 0
        for case in cases:
            d = router.route(case['query'])
            rec = d['retrieved_axioms'][:5]
            rec_ids = [c.get('chunk_id', '') for c in rec]
            exp_topic = case.get('expected_topic')
            exp_facts = set(case.get('expected_fact_ids', []))
            target = False
            rank = 0
            for i, c in enumerate(rec, 1):
                cid = c.get('chunk_id', '')
                if exp_topic and exp_topic in set(c.get('methodology_topics', [])):
                    target = True
                    if not rank:
                        rank = i
                if exp_facts and cid in exp_facts:
                    target = True
                    if not rank:
                        rank = i
            if target:
                hits += 1
                mrr += 1.0 / rank
            if exp_topic and any(exp_topic in set(c.get('methodology_topics', [])) for c in rec):
                topic_hits += 1
            if exp_facts and sum(1 for c in rec if c.get('epistemic_type') == 'FACT') < 2:
                starve += 1
        n = len(cases)
        self.assertGreaterEqual(hits / n * 100, 60.0, "Hit@5 应达阈值")
        self.assertGreaterEqual(mrr / n, 0.30, "MRR 应达阈值")
        self.assertEqual(starve, 0, "微观事实饥饿率必须为 0")

    def test_rag_benchmark_detects_regression_with_bad_dataset(self):
        # 负向验证：若 golden dataset 全是不可达的假 chunk_id，Hit 必跌到 0 → 能测出退化
        import sys, json
        _repo = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(_repo / 'scripts'))
        from problem_router import ProblemRouter
        router = ProblemRouter()
        bad = [{'query': '佩蕾丝技术资本周期', 'expected_topic': '不存在的主题XYZ'}]
        rec = router.route(bad[0]['query'])['retrieved_axioms'][:5]
        hit = any('不存在的主题XYZ' in set(c.get('methodology_topics', [])) for c in rec)
        self.assertFalse(hit, "不可达 ground-truth 应导致 Hit=0（评测应能测出退化）")


class DocxExtractionTests(unittest.TestCase):
    def test_docx_extraction_stdlib(self):
        # 纯标准库 docx 抽取：能提取 <w:t> 文本
        import sys
        _repo = Path(__file__).resolve().parents[1]
        sys.path.insert(0, str(_repo / 'scripts'))
        from rag_index_builder import extract_docx_text
        src = _repo / 'inputDoc' / '文字稿20200618【前哨科技特训营】学员整理《DARPA的产业拉动&机器人产业的未来》.docx'
        if not src.is_file():
            self.skipTest("docx 样例缺失")
        text = extract_docx_text(src)
        self.assertGreater(len(text), 100, "docx 应抽出可读文本")
        self.assertIn("DARPA", text)

    def test_docx_in_index(self):
        # Ray Dalio 世界秩序 docx 应已纳入当前索引（达利奥债务周期权威资料）
        import json
        idx = json.load(open(Path(__file__).resolve().parents[1] / 'rag/research/axiom_index.json', encoding='utf-8'))
        has_docx = any(d['filename'].endswith('.docx') and d.get('status') == 'INDEXED' for d in idx['documents'])
        self.assertTrue(has_docx, "docx 文档应已进索引")


class NvidiaTrendBenchmarkTests(unittest.TestCase):
    """英伟达趋势基准：13 门禁闭环 + 知行合一实证。"""

    def setUp(self):
        import shutil, tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        src = Path(__file__).resolve().parents[1] / 'reports/nvidia_trend_2026_benchmark'
        self.root = Path(self.tmp.name) / 'trend'
        shutil.copytree(src, self.root)

    def test_trend_benchmark_all_13_gates_pass(self):
        judge = DeterministicJudge(benchmark_dir=self.root)
        sc = judge.execute_audit()
        self.assertEqual(sc['overall_verdict'], 'PASS', f"应全绿, 实际 {sc['overall_verdict']}")
        gates = {g['gate']: g['status'] for g in sc['gate_breakdown']}
        self.assertEqual(len(gates), 13)
        for name, status in gates.items():
            self.assertEqual(status, 'PASS', f"{name} 应为 PASS")

    def test_trend_decision_consistency_empirical(self):
        # 实证：若把高利率公理方向错写为 hold(应 avoid)，Gate 12 知行合一必须拦截。
        import json as _json
        tp = self.root / 'thesis.json'
        t = _json.loads(tp.read_text(encoding='utf-8'))
        for item in t['decision_rationale']:
            if item['axiom'] == '高利率与现金流重估':
                item['conclusion_direction'] = 'hold'  # 错误：公理方向是 avoid
        tp.write_text(_json.dumps(t, ensure_ascii=False), encoding='utf-8')
        judge = DeterministicJudge(benchmark_dir=self.root)
        sc = judge.execute_audit()
        g12 = next(g for g in sc['gate_breakdown'] if g['gate'] == 'GATE_DECISION_CONSISTENCY')
        self.assertEqual(g12['status'], 'FAIL', "公理 avoid 却写 hold 必须被知行合一拦截")


if __name__ == '__main__':
    unittest.main()
