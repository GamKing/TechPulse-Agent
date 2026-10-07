import json
import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from deterministic_judge import DeterministicJudge
from evidence_auditor_harness import EvidenceAuditorHarness
from verification import digest, calculate


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.record = {'id': 'C1', 'claim': 'Revenue is 999 billion.',
                       'source_url': 'https://example.invalid/source',
                       'http_status': 200, 'content_hash': 'sha256:not-a-hash',
                       'extracted_text': 'Revenue is 1 billion.'}
        self.judge = DeterministicJudge(benchmark_dir=self.root)

    def test_fake_source_rejected(self):
        self.assertEqual(self.judge.audit_gate_1_source_existence([self.record])['status'], 'FAIL')

    def test_author_verdict_is_not_verification(self):
        self.record.update(claim_support='FULL', verdict='VERIFIED')
        self.assertEqual(self.judge.audit_gate_2_claim_entailment_target_result([self.record])['status'], 'UNVERIFIED')

    def test_explicit_contradiction_rejected(self):
        self.record['claim_support'] = 'CONTRADICT'
        self.assertEqual(self.judge.audit_gate_2_claim_entailment_target_result([self.record])['status'], 'FAIL')

    def test_math_requires_execution(self):
        data = {'parameter_provenance_cards': [{'param_id': 'X', 'formula': '2+2=5',
                'derivation_steps': ['2+2=5'], 'recomputable': True}]}
        self.assertEqual(self.judge.audit_gate_4_parameter_provenance_recalculation(data)['status'], 'UNVERIFIED')
        data['parameter_provenance_cards'][0].update(base_value=5,
            calculation={'expression': '2+2', 'inputs': {}})
        self.assertEqual(self.judge.audit_gate_4_parameter_provenance_recalculation(data)['status'], 'FAIL')
        data['parameter_provenance_cards'][0]['base_value'] = 4
        self.assertEqual(self.judge.audit_gate_4_parameter_provenance_recalculation(data)['status'], 'PASS')

    def test_arithmetic_safety(self):
        for expression in ["__import__('os')", 'float("nan")', '2**10000', '1/0']:
            with self.assertRaises((ValueError, ArithmeticError)):
                calculate(expression, {})

    def harness(self):
        return EvidenceAuditorHarness(self.root, config_path=str(self.root / 'missing.json'), force_override=True)

    def assessment(self, entailment='FULL'):
        return json.dumps({'entailment': entailment, 'target_to_result_drift': False,
                           'epistemic_type_valid': True, 'confidence': 'HIGH',
                           'evidence_quote': 'Revenue is 1 billion.'})

    @patch('evidence_auditor_harness.fetch_source')
    def test_live_receipt_and_tampering(self, fetch):
        fetch.return_value = (b'raw source', 'Revenue is 1 billion.', 200, self.record['source_url'])
        harness = self.harness()
        with patch.object(harness, 'call_external_llm', return_value=self.assessment('CONTRADICT')):
            receipt = harness.run_adversarial_claim_audit(self.record)
        self.judge.verification_results = {'C1': receipt}
        self.assertEqual(self.judge.audit_gate_1_source_existence([self.record])['status'], 'PASS')
        self.assertEqual(self.judge.audit_gate_2_claim_entailment_target_result([self.record])['status'], 'FAIL')
        (self.root / receipt['snapshot_path']).write_bytes(b'tampered')
        self.assertEqual(self.judge.audit_gate_1_source_existence([self.record])['status'], 'FAIL')

    @patch('evidence_auditor_harness.fetch_source')
    def test_reviewer_failure_and_malformed_output(self, fetch):
        fetch.return_value = (b'raw', 'Revenue is 1 billion.', 200, self.record['source_url'])
        harness = self.harness()
        for response in [None, 'not json', '{}', '[]']:
            with patch.object(harness, 'call_external_llm', return_value=response):
                receipt = harness.run_adversarial_claim_audit(self.record)
            self.assertEqual(receipt['audit_status'], 'ERROR')
            self.judge.verification_results = {'C1': receipt}
            self.assertNotEqual(self.judge.audit_gate_2_claim_entailment_target_result([self.record])['status'], 'PASS')

    def test_default_does_not_claim_model_execution(self):
        harness = EvidenceAuditorHarness(self.root, config_path=str(self.root / 'missing.json'))
        with patch('evidence_auditor_harness.fetch_source') as fetch:
            receipt = harness.run_adversarial_claim_audit(self.record)
        fetch.assert_not_called()
        self.assertEqual(receipt['audit_status'], 'NOT_RUN')
        self.assertFalse(receipt['external_llm_used'])

    def test_broken_jsonl_is_not_silently_skipped(self):
        (self.root / 'evidence.jsonl').write_text(json.dumps(self.record) + '\n{broken', encoding='utf-8')
        with self.assertRaises(ValueError):
            self.judge._read_evidence_jsonl()

    def test_claim_change_invalidates_receipt(self):
        self.judge.verification_results = {'C1': {'claim_hash': digest(b'old claim'),
            'audit_status': 'COMPLETED', 'assessment': json.loads(self.assessment())}}
        self.assertEqual(self.judge.audit_gate_2_claim_entailment_target_result([self.record])['status'], 'UNVERIFIED')

    def test_end_to_end_reviewer_result_reaches_judge(self):
        source = Path(__file__).resolve().parents[1] / 'reports/nvidia_benchmark'
        shutil.copytree(source, self.root, dirs_exist_ok=True)
        (self.root / 'evidence.jsonl').write_text(json.dumps(self.record) + '\n', encoding='utf-8')
        harness = self.harness()
        with patch('evidence_auditor_harness.fetch_source', return_value=(
                b'raw', 'Revenue is 1 billion.', 200, self.record['source_url'])), \
                patch.object(harness, 'call_external_llm', return_value=self.assessment('CONTRADICT')), \
                contextlib.redirect_stdout(io.StringIO()):
            scorecard = harness.execute_pipeline()
        gate = next(g for g in scorecard['gate_breakdown'] if g['gate'] == 'GATE_CLAIM_ENTAILMENT_TARGET_RESULT')
        self.assertEqual(gate['status'], 'FAIL')
        self.assertEqual(scorecard['overall_verdict'], 'FAIL')
        self.assertEqual(scorecard['report_binding']['content_hash'], digest((self.root / 'report.md').read_bytes()))
        self.assertTrue((self.root / 'verification_results.json').exists())

    def test_persisted_receipts_not_trusted_on_new_run(self):
        (self.root / 'verification_results.json').write_text('{"C1":{"audit_status":"COMPLETED"}}')
        self.assertEqual(self.judge.verification_results, {})

    def test_plaintext_api_key_is_rejected(self):
        config = {'tiers': {'tier_2_evidence_auditor': {'model_config': {'custom_override': {
            'enabled': True, 'provider': 'deepseek', 'api_base': 'https://api.deepseek.com/v1',
            'api_key': 'sk-TESTKEY-not-real-0000'}}}}}
        config_path = self.root / 'cfg.json'
        config_path.write_text(json.dumps(config), encoding='utf-8')
        harness = EvidenceAuditorHarness(self.root, config_path=str(config_path), force_override=True)
        with self.assertRaises(ValueError):
            harness.call_external_llm('prompt')

    def test_plaintext_token_forbidden_for_remote_provider(self):
        config = {'tiers': {'tier_2_evidence_auditor': {'model_config': {'custom_override': {
            'enabled': True, 'provider': 'deepseek', 'api_base': 'https://api.deepseek.com/v1',
            'api_key': 'my-secret-token'}}}}}
        config_path = self.root / 'cfg.json'
        config_path.write_text(json.dumps(config), encoding='utf-8')
        harness = EvidenceAuditorHarness(self.root, config_path=str(config_path), force_override=True)
        with self.assertRaises(ValueError):
            harness.call_external_llm('prompt')

    def test_missing_env_key_fails_closed(self):
        config = {'tiers': {'tier_2_evidence_auditor': {'model_config': {'custom_override': {
            'enabled': True, 'provider': 'deepseek', 'api_base': 'https://api.deepseek.com/v1',
            'api_key': 'env:DEEPSEEK_API_KEY'}}}}}
        config_path = self.root / 'cfg.json'
        config_path.write_text(json.dumps(config), encoding='utf-8')
        harness = EvidenceAuditorHarness(self.root, config_path=str(config_path), force_override=True)
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(ValueError):
                harness.call_external_llm('prompt')

    # ---- 抓手三：知行合一门禁 GATE_DECISION_CONSISTENCY ----
    def test_decision_consistency_pass_when_aligned(self):
        thesis = {'decision_rationale': [
            {'axiom': '佩蕾丝技术资本周期', 'conclusion_direction': 'avoid',
             'kill_switch_triggered': False}]}
        gate = self.judge.audit_gate_decision_consistency(thesis)
        self.assertEqual(gate['status'], 'PASS')
        self.assertEqual(gate['type'], 'HIGH')

    def test_decision_consistency_fails_when_action_diverges(self):
        # 引用佩蕾丝(avoid) 却结论 buy → 知行不一 FAIL
        thesis = {'decision_rationale': [
            {'axiom': '佩蕾丝技术资本周期', 'conclusion_direction': 'buy',
             'kill_switch_triggered': False}]}
        gate = self.judge.audit_gate_decision_consistency(thesis)
        self.assertEqual(gate['status'], 'FAIL')

    def test_decision_consistency_fails_when_kill_switch_ignored(self):
        # kill_switch 已触发却仍按原方向下结论 → FAIL
        thesis = {'decision_rationale': [
            {'axiom': '莱特定律与学习曲线', 'conclusion_direction': 'buy',
             'kill_switch_triggered': True, 'kill_signal': '良率不升反降'}]}
        gate = self.judge.audit_gate_decision_consistency(thesis)
        self.assertEqual(gate['status'], 'FAIL')

    def test_decision_consistency_unverified_without_rationale(self):
        gate = self.judge.audit_gate_decision_consistency({})
        self.assertEqual(gate['status'], 'UNVERIFIED')

    def test_decision_consistency_registered_in_scorecard(self):
        # 知行合一门禁应出现在 execute_audit 的结果里（第 12 道）
        source = Path(__file__).resolve().parents[1] / 'reports/nvidia_benchmark'
        shutil.copytree(source, self.root, dirs_exist_ok=True)
        scorecard = self.judge.execute_audit()
        gates = [g['gate'] for g in scorecard['gate_breakdown']]
        self.assertIn('GATE_DECISION_CONSISTENCY', gates)
        self.assertGreater(scorecard['summary']['total_gates'], 11)

    # ---- Step1-P0b：Unit Contract（单位契约，防跨量纲胡算）----
    def test_unit_contract_missing_unit_fails(self):
        data = {'parameter_provenance_cards': [
            {'param_id': 'P-1', 'calculation': {'expression': '2+2', 'inputs': {}}}]}
        gate = self.judge.audit_gate_parameter_unit_contract(data)
        self.assertEqual(gate['status'], 'FAIL')

    def test_unit_contract_cross_dimension_add_fails(self):
        data = {'parameter_provenance_cards': [
            {'param_id': 'P-1', 'unit': 'USD',
             'calculation': {'expression': 'a + b', 'unit_map': {'a': 'USD', 'b': 'count'}}}]}
        gate = self.judge.audit_gate_parameter_unit_contract(data)
        self.assertEqual(gate['status'], 'FAIL')

    def test_unit_contract_same_dimension_passes(self):
        data = {'parameter_provenance_cards': [
            {'param_id': 'P-2', 'unit': 'USD',
             'calculation': {'expression': 'a + b', 'unit_map': {'a': 'USD', 'b': 'USD'}}}]}
        gate = self.judge.audit_gate_parameter_unit_contract(data)
        self.assertEqual(gate['status'], 'PASS')

    def test_unit_contract_unverified_without_cards(self):
        gate = self.judge.audit_gate_parameter_unit_contract({})
        self.assertEqual(gate['status'], 'UNVERIFIED')

    def test_unit_dims_parsing(self):
        from strict_gates import StrictGates
        self.assertEqual(StrictGates._unit_dims('USD/unit'), {'USD': 1, 'unit': -1})
        self.assertEqual(StrictGates._unit_dims('k_units/month'), {'k_units': 1, 'month': -1})
        self.assertEqual(StrictGates._unit_dims(None), None)

    # ---- Step2-P1：离线证据导入协议（Air-gapped Evidence Ingestion）----
    def test_offline_import_and_offline_first_read(self):
        from verification import import_offline_snapshot, fetch_source_offline
        src = self.root / 'manual_src.html'
        src.write_text('<html>Revenue is 1 billion [FACT]</html>', encoding='utf-8')
        entry = import_offline_snapshot(self.root, 'https://offline.example.com/rpt', src)
        self.assertIn('content_hash', entry)
        # 未知 URL → None（回退在线）
        self.assertIsNone(fetch_source_offline('https://unknown.example.com/x', self.root))
        # 命中 → 返回本地快照
        body, text, status, url = fetch_source_offline('https://offline.example.com/rpt', self.root)
        self.assertEqual(status, 200)
        self.assertIn('Revenue is 1 billion', text)
        self.assertEqual(url, 'https://offline.example.com/rpt')

    def test_offline_snapshot_tamper_rejected(self):
        # 离线快照被篡改 → 哈希不符 → 拒绝使用（回退在线）
        from verification import import_offline_snapshot, fetch_source_offline
        src = self.root / 's.html'
        src.write_text('authentic body', encoding='utf-8')
        entry = import_offline_snapshot(self.root, 'https://tamper.example.com/a', src)
        snap = self.root / entry['path']
        snap.write_bytes(b'tampered!!')
        self.assertIsNone(fetch_source_offline('https://tamper.example.com/a', self.root))

    # ---- Step3-P2：方法论强类型模板 + monitor.json 前线监控清单 ----
    def test_monitor_builder_three_slots(self):
        from pathlib import Path
        _repo = Path(__file__).resolve().parents[1]
        from monitor_builder import load_templates
        tpl = load_templates(str(_repo / 'scripts/methodology_templates.json'))
        self.assertTrue(len(tpl) >= 15)
        for canon, card in tpl.items():
            for slot in ('applicable_phase', 'ast_formula_template', 'falsification_redlines'):
                self.assertTrue(card.get(slot), f"{canon} 缺槽位 {slot}")

    def test_monitor_builder_generates_monitor_json(self):
        from monitor_builder import build_monitor
        data = build_monitor(self.root, "佩蕾丝技术资本周期",
                             phase="INSTALLATION",
                             observation={"utilization": 0.55, "revenue_diverge": 0.3},
                             rationale_note="test")
        item = data["items"][0]
        self.assertEqual(item["axiom"], "佩蕾丝技术资本周期")
        self.assertEqual(item["recommended_direction"], "avoid")
        self.assertIn("utilization", item["monitored_variables"])
        self.assertTrue(item["falsification_redlines"])
        self.assertTrue((self.root / "monitor.json").is_file())

    def test_monitor_builder_unknown_axiom_raises(self):
        from monitor_builder import build_monitor
        with self.assertRaises(ValueError):
            build_monitor(self.root, "不存在的公理")

    def test_decision_consistency_detects_monitor_kill_switch_contradiction(self):
        # Step3-P2：monitor.json 显示某公理 kill_switch 已激活，但研报声明未触发 → 矛盾 FAIL
        from monitor_builder import build_monitor
        # 生成一个 kill_switch 激活的 monitor 条目（莱特定律，良率红线触发）
        build_monitor(self.root, "莱特定律与学习曲线", phase="SCALING",
                      observation={"b": 0.05})  # 任意观测，构造条目
        # 手工把该条目标记为 kill_switch 已激活
        import json as _json
        mf = self.root / "monitor.json"
        md = _json.loads(mf.read_text(encoding="utf-8"))
        md["items"][0]["kill_switch_activated"] = True
        md["items"][0]["kill_switch_signals"] = ["良率不升反降(观测到)"]
        mf.write_text(_json.dumps(md, ensure_ascii=False), encoding="utf-8")
        # 研报声明：引用莱特定律，结论 buy，但 kill_switch_triggered=false（与 monitor 矛盾）
        thesis = {'decision_rationale': [
            {'axiom': '莱特定律与学习曲线', 'conclusion_direction': 'buy',
             'kill_switch_triggered': False}]}
        gate = self.judge.audit_gate_decision_consistency(thesis)
        self.assertEqual(gate['status'], 'FAIL')
        self.assertIn("监控与声明矛盾", gate['details'])

    # ---- 演进动作3：Kill-Switch Monitor CLI（check_monitors）----
    def test_check_monitors_redline_triggers(self):
        from check_monitors import check_redline, run
        # 数值红线：良品率 < 0.8 触发
        chk = check_redline("良品率爬坡低于阈值 yield < 0.8 时降本失效", {"yield": 0.72})
        self.assertTrue(chk["triggered"])
        self.assertEqual(chk["matched_var"], "yield")
        # 健康值不触发
        chk2 = check_redline("yield < 0.8", {"yield": 0.90})
        self.assertFalse(chk2["triggered"])
        # 无法解析（汉字阈值）不误报
        chk3 = check_redline("连续两季度利用率环比下降>10%", {})
        self.assertFalse(chk3["triggered"])

    def test_check_monitors_cli_end_to_end(self):
        import json as _json
        from check_monitors import run
        bdir = self.root / "mbench"
        bdir.mkdir(parents=True, exist_ok=True)
        monitor = {"items": [{
            "axiom": "莱特定律与学习曲线", "recommended_direction": "buy",
            "applicable_phase": "SCALING",
            "falsification_redlines": ["yield < 0.8 时降本失效"],
            "kill_switch_activated": False, "kill_switch_signals": []}]}
        (bdir / "monitor.json").write_text(_json.dumps(monitor, ensure_ascii=False), encoding="utf-8")
        # 触发值 → 告警
        rep = run([str(bdir)], {"yield": 0.72})
        self.assertTrue(rep["alerted"])
        # 安全值 → 不告警
        rep2 = run([str(bdir)], {"yield": 0.90})
        self.assertFalse(rep2["alerted"])
        # 无 monitor → 不误报
        rep3 = run([str(self.root / "no_monitor")], {"yield": 0.5})
        self.assertFalse(rep3["alerted"])

    def test_judge_autoloads_verification_results_from_disk(self):
        v_results = {'C1': {'fetch_status': 'FETCHED', 'http_status': 200}}
        (self.root / 'verification_results.json').write_text(json.dumps(v_results), encoding='utf-8')
        judge = DeterministicJudge(benchmark_dir=self.root)
        self.assertEqual(judge.verification_results, v_results)


if __name__ == '__main__':
    unittest.main()
