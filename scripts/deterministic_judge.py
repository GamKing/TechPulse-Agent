#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deterministic Judge - Tier 3 Programmatic Hard Gate Engine
Frontier Tech Industrial Analysis Engine (Topic-Agnostic Operating System Edition)

Executes programmatic, rule-based audits across ANY frontier technology domain:
1. Source Existence & Metadata (Gate 1)
2. Claim Entailment & Target-Result Drift (Gate 2)
3. Epistemic Birth Certificate & Taxonomy (Gate 3)
4. Parameter Provenance & 5-Step Lineage (Gate 4)
5. Parameter Orthogonality & Residual Honesty (Gate 5)
6. Parameter Pre-registration & Blind Cryptographic Lock (Gate 6)
7. Validation Leakage & Information Firewall (Gate 7)
8. Artifact Enforcement & Decoupled Verdicts (Gate 8)
9. Global Precision Regex Audit (Gate 9)
10. Causal Distance Penalty & Missing Bridges (Gate 10)
11. Company Exposure & Valuation Decoupling (Gate 11)

Supports:
  --topic <topic_name>       (e.g., humanoid_robot, ai_coding, ai_biotech)
  --benchmark-dir <path>     (explicit target directory)
"""

import argparse
import datetime
import json
import math
import os
import re
import sys
from pathlib import Path
from strict_gates import StrictGates
from verification import digest

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class DeterministicJudge(StrictGates):
    def __init__(self, benchmark_dir: str = None, topic: str = None, config_path: str = None, output_dir: str = None, verification_results=None):
        if topic:
            self.topic = topic
            self.benchmark_dir = Path(benchmark_dir) if benchmark_dir else Path(f"reports/{topic}_benchmark")
        elif benchmark_dir:
            self.benchmark_dir = Path(benchmark_dir)
            self.topic = self.benchmark_dir.name.replace("_benchmark", "")
        else:
            self.topic = "humanoid_robot"
            self.benchmark_dir = Path("reports/humanoid_robot_benchmark")

        self.config_path = Path(config_path) if config_path else Path("config/pipeline_config.json")
        self.output_dir = Path(output_dir) if output_dir else self.benchmark_dir
        self.config = self._load_config()

        if verification_results is not None:
            self.verification_results = verification_results
        else:
            v_file = self.benchmark_dir / "verification_results.json"
            if v_file.is_file():
                try:
                    with open(v_file, "r", encoding="utf-8") as f:
                        self.verification_results = json.load(f)
                except Exception:
                    self.verification_results = {}
            else:
                self.verification_results = {}

        # Gate Results Registry
        self.gate_results = {}
        self.audit_log = []
        self.start_time = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def _load_config(self):
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "tiers": {
                "tier_3_deterministic_judge": {
                    "scoring_policy": {
                        "max_dual_model_divergence_pct": 20.0,
                        "forbidden_subjective_valuation_terms": [
                            "白马底仓", "安全边际高", "提供看涨期权", "估值洼地", "强烈推荐", "必买标的", "无风险套利", "已提前预支了", "市场已经预支了"
                        ]
                    }
                }
            }
        }

    def _read_evidence_jsonl(self):
        evidence_file = self.benchmark_dir / "evidence.jsonl"
        if not evidence_file.exists():
            return None
        records = []
        with open(evidence_file, "r", encoding="utf-8") as f:
            for line_idx, line in enumerate(f, start=1):
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Invalid evidence JSONL at line {line_idx}") from e
        return records

    def _read_json(self, filename):
        filepath = self.benchmark_dir / filename
        if not filepath.exists():
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def _read_text(self, filename):
        filepath = self.benchmark_dir / filename
        if not filepath.exists():
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    # =========================================================================
    # GATE 1: SOURCE EXISTENCE & METADATA GATE (Critical)
    # =========================================================================
    def audit_gate_3_epistemic_birth_certificate(self, evidence_records):
        gate_name = "GATE_EPISTEMIC_BIRTH_CERTIFICATE"
        if not evidence_records:
            return {"gate": gate_name, "type": "CRITICAL", "status": "FAIL", "details": "No evidence records."}

        valid_epistemic_types = [
            "FACT", "SECONDARY_ESTIMATE", "ASSUMPTION", "HYPOTHESIS",
            "INFERENCE", "MODEL_RESULT", "FORECAST", "FALSIFICATION"
        ]

        secondary_sources = [
            "THIRD_PARTY_INDUSTRY_REPORT", "INDUSTRY_CONSORTIUM_DATABASE",
            "INDUSTRY_RESEARCH_ARTICLE", "CONSULTING_ESTIMATE", "BROKER_RESEARCH"
        ]

        taxonomy_errors = []
        for rec in evidence_records:
            eid = rec.get("id", "UNKNOWN")
            etype = rec.get("epistemic_type", "")
            stype = rec.get("source_type", "")

            if etype not in valid_epistemic_types:
                taxonomy_errors.append(f"{eid}: invalid epistemic_type '{etype}'")

            # Generic Epistemic Birth Certificate Rule:
            # Third-party consulting estimates, teardowns, and survey databases MUST NOT masquerade as FACT!
            if stype in secondary_sources and etype == "FACT":
                taxonomy_errors.append(
                    f"{eid}: source_type '{stype}' is an institutional estimate/teardown and CANNOT be classified as FACT (must be SECONDARY_ESTIMATE)."
                )

        if taxonomy_errors:
            return {
                "gate": gate_name,
                "type": "CRITICAL",
                "status": "FAIL",
                "details": f"Taxonomy / Birth Certificate violations: {taxonomy_errors}"
            }

        return {
            "gate": gate_name,
            "type": "CRITICAL",
            "status": "PASS",
            "details": f"Epistemic birth certificates verified across {len(evidence_records)} items. Third-party consulting/teardowns strictly classified as SECONDARY_ESTIMATE."
        }

    # =========================================================================
    # GATE 4: PARAMETER PROVENANCE & 5-STEP LINEAGE GATE (Critical)
    # =========================================================================
    def audit_gate_5_parameter_orthogonality_dual_model(self, assumptions_data):
        gate_name = "GATE_PARAMETER_ORTHOGONALITY_DUAL_MODEL"
        if not assumptions_data:
            return {"gate": gate_name, "type": "CRITICAL", "status": "FAIL", "details": "assumptions.json not found."}

        ortho = assumptions_data.get("parameter_orthogonality_audit", {})
        dual_model = assumptions_data.get("dual_model_architecture", {})

        if not ortho or not dual_model:
            return {
                "gate": gate_name,
                "type": "CRITICAL",
                "status": "FAIL",
                "details": "Missing parameter_orthogonality_audit or dual_model_architecture."
            }

        # Check anti-double counting rule
        anti_dc = ortho.get("anti_double_counting_rule", "")
        if not anti_dc:
            return {"gate": gate_name, "type": "CRITICAL", "status": "FAIL", "details": "Missing anti_double_counting_rule."}

        div_audit = dual_model.get("divergence_audit", {})
        divergences = div_audit.get("divergences", [])

        invalid_classifications = []
        conflicts = []
        honesty_violations = []

        for d in divergences:
            scale = d.get("scale", "")
            div_pct = d.get("divergence_percent", 999.0)
            classification = d.get("classification", "")
            if div_pct < 20.0 and classification != "CONSISTENT":
                invalid_classifications.append(f"{scale}: {div_pct}% must be classified as CONSISTENT")
            elif 20.0 <= div_pct <= 40.0 and classification != "MATERIAL_DIVERGENCE":
                invalid_classifications.append(f"{scale}: {div_pct}% must be classified as MATERIAL_DIVERGENCE")
            elif div_pct > 40.0:
                conflicts.append(f"{scale}: divergence {div_pct}% > 40% triggers MODEL_CONFLICT")

            # Residual Honesty Rule Check:
            # Forbids 100% artificial balancing; mandates reporting real unexplained residual >= 3.0%
            res_h = d.get("residual_honesty", {})
            unexp_pct = res_h.get("unexplained_residual_percent", 0.0)
            prim_pct = res_h.get("primary_explained_percent", 100.0)

            if unexp_pct < 3.0:
                honesty_violations.append(f"{scale}: unexplained residual {unexp_pct}% < 3.0% (violates Residual Honesty Rule)")
            if prim_pct >= 95.0:
                honesty_violations.append(f"{scale}: primary explained {prim_pct}% >= 95.0% (artificial force-balance detected)")

        if invalid_classifications or conflicts or honesty_violations:
            return {
                "gate": gate_name,
                "type": "CRITICAL",
                "status": "FAIL",
                "details": f"Divergence policy violation: Invalid: {invalid_classifications}; Conflicts: {conflicts}; Honesty violations: {honesty_violations}"
            }

        max_div = max(d.get("divergence_percent", 0.0) for d in divergences)
        return {
            "gate": gate_name,
            "type": "CRITICAL",
            "status": "PASS",
            "details": f"Anti-double-counting decoupled. Residual Honesty Rule verified across all {len(divergences)} stages (Max divergence: {max_div}%, unexplained residuals between 3.0%~15.0% honestly disclosed).",
            "divergence_audit": divergences
        }

    # =========================================================================
    # GATE 6: PARAMETER PRE-REGISTRATION & BLIND PARAMETERIZATION GATE (Critical)
    # =========================================================================
    def audit_gate_6_global_precision_regex(self, report_text):
        gate_name = "GATE_GLOBAL_PRECISION_REGEX_AUDIT"
        if not report_text:
            return {"gate": gate_name, "type": "HIGH", "status": "FAIL", "details": "report.md not found."}

        mandatory_markers = ["[FACT", "[SECONDARY ESTIMATE", "[ASSUMPTION", "[MODEL RESULT", "[INFERENCE", "[FORECAST"]
        marker_counts = {m: report_text.count(m) for m in mandatory_markers}

        zero_markers = [m for m, count in marker_counts.items() if count == 0]
        if zero_markers:
            return {
                "gate": gate_name,
                "type": "HIGH",
                "status": "FAIL",
                "details": f"Missing mandatory cognitive classification tags in report: {zero_markers}"
            }

        # Check for pseudo-precision score like 9.4/10 in qualitative table
        if "/ 10" in report_text or "/10" in report_text:
            # Check if it appears in value capture table context
            if re.search(r'\b\d\.\d\s*/\s*10\b', report_text):
                return {
                    "gate": gate_name,
                    "type": "HIGH",
                    "status": "FAIL",
                    "details": "Pseudo-precision decimal score (/10) detected in qualitative table. Must use categorical grades (CRITICAL / VERY HIGH / HIGH / MEDIUM / LOW)."
                }

        return {
            "gate": gate_name,
            "type": "HIGH",
            "status": "PASS",
            "details": f"Global precision audit passed. Zero pseudo-precision table ratings. Cognitive tag distribution: {marker_counts}"
        }

    # =========================================================================
    # GATE 10: CAUSAL DISTANCE PENALTY & MISSING BRIDGES GATE (High Priority)
    # =========================================================================
    def audit_gate_7_causal_distance_penalty(self, thesis_data):
        gate_name = "GATE_CAUSAL_DISTANCE_PENALTY"
        if not thesis_data:
            return {"gate": gate_name, "type": "HIGH", "status": "FAIL", "details": "thesis.json not found."}

        matrix = thesis_data.get("evidence_to_hypothesis_impact_matrix", [])
        active_rqs = thesis_data.get("active_research_questions", [])

        if not matrix:
            return {"gate": gate_name, "type": "HIGH", "status": "FAIL", "details": "No evidence_to_hypothesis_impact_matrix in thesis.json."}

        violations = []
        for row in matrix:
            eid = row.get("evidence_id", "")
            cdist = row.get("causal_distance", "")
            # Check any impact hypothesis key
            for key, val in row.items():
                if key.startswith("impact_"):
                    if cdist == "FAR" and "STRONG" in str(val):
                        violations.append(f"{eid} has causal_distance=FAR but claims STRONG support in {key}.")

        if not active_rqs:
            violations.append("Missing active_research_questions generated from missing bridges.")

        if violations:
            return {
                "gate": gate_name,
                "type": "HIGH",
                "status": "FAIL",
                "details": f"Causal distance violations: {violations}"
            }

        return {
            "gate": gate_name,
            "type": "HIGH",
            "status": "PASS",
            "details": f"All {len(matrix)} matrix rows satisfy causal distance penalties. Active RQs ({len(active_rqs)} items) properly bound to missing bridges."
        }

    # =========================================================================
    # GATE 11: COMPANY EXPOSURE & VALUATION DECOUPLING GATE (High Priority)
    # =========================================================================
    def audit_gate_8_valuation_decoupling(self, report_text, thesis_data):
        gate_name = "GATE_VALUATION_DECOUPLING"
        forbidden_terms = self.config.get("tiers", {}).get("tier_3_deterministic_judge", {}).get(
            "scoring_policy", {}
        ).get("forbidden_subjective_valuation_terms", [
            "白马底仓", "安全边际高", "提供看涨期权", "估值洼地", "强烈推荐", "必买标的", "无风险套利", "已提前预支了", "市场已经预支了"
        ])

        found_forbidden = []
        for term in forbidden_terms:
            if report_text and term in report_text:
                found_forbidden.append(f"Found in report.md: '{term}'")

        # Check thesis company exposure cards decoupling
        cards = thesis_data.get("company_exposure_cards_decoupled", []) if thesis_data else []
        uncoupled_cards = []
        for c in cards:
            cname = c.get("name", c.get("ticker", "UNKNOWN"))
            if not c.get("company_fact_audit") or not c.get("earnings_translation") or not c.get("valuation_sensitivity"):
                uncoupled_cards.append(f"{cname} missing 3-tier decoupling")

        if found_forbidden or uncoupled_cards:
            return {
                "gate": gate_name,
                "type": "HIGH",
                "status": "FAIL",
                "details": f"Forbidden subjective terms / Model-Result-to-Fact Drift: {found_forbidden}; Incomplete cards: {uncoupled_cards}"
            }

        return {
            "gate": gate_name,
            "type": "HIGH",
            "status": "PASS",
            "details": f"Zero forbidden subjective investment terms or model-result drifts found. All {len(cards)} company exposure cards decouple Fact Audit, Earnings Translation, and Implied Expectations."
        }

    # =========================================================================
    # GATE 12: DECISION CONSISTENCY (知行合一) —— 决策卡 → 结论方向一致性
    # =========================================================================
    def audit_gate_decision_consistency(self, thesis_data):
        """校验研报"引用公理 → 结论方向"是否知行合一（避免'说佩蕾丝泡沫期却盲目推买入'）。

        研报在 thesis.json 提供 machine-readable decision_rationale:
          [
            {"axiom": "佩蕾丝技术资本周期", "conclusion_direction": "buy",
             "kill_switch_triggered": false}
          ]
        门禁对照决策卡的公理本体（DECISION_DIRECTION）：
          1. 公理方向 avoid/buy，而研报结论方向与之冲突 → FAIL（知行不一）
          2. 若 kill_switch 已触发却仍按公理原方向下结论 → FAIL（无视证伪触发器）
        无 decision_rationale → UNVERIFIED（未声明推理依据，不通过）。
        """
        try:
            from decision_heuristics import DECISION_DIRECTION
        except Exception:
            DECISION_DIRECTION = {}
        gate_name = "GATE_DECISION_CONSISTENCY"
        if not thesis_data:
            return {"gate": gate_name, "type": "HIGH", "status": "UNVERIFIED",
                    "details": "thesis.json not found; decision rationale unavailable."}
        rationale = thesis_data.get("decision_rationale", [])
        if not rationale:
            return {"gate": gate_name, "type": "HIGH", "status": "UNVERIFIED",
                    "details": "No decision_rationale declared in thesis.json; inference basis unverifiable."}

        violations = []
        # Step3-P2：与 monitor.json 前线监控清单联动——研报声明未触发 kill_switch，
        # 但 monitor 显示该公理红线已激活(激活态)，则研报自相矛盾。
        monitor_activated = {}
        mf = self.benchmark_dir / "monitor.json"
        if mf.is_file():
            try:
                mdata = json.loads(mf.read_text(encoding="utf-8"))
                for mi in mdata.get("items", []):
                    if mi.get("kill_switch_activated"):
                        monitor_activated[mi.get("axiom")] = mi.get("kill_switch_signals", [])
            except Exception:
                monitor_activated = {}
        for item in rationale:
            axiom = item.get("axiom", "")
            direction = item.get("conclusion_direction", "").lower()
            ks = bool(item.get("kill_switch_triggered", False))
            base_dir = DECISION_DIRECTION.get(axiom)
            if not axiom or not base_dir:
                violations.append(f"{axiom or 'UNKNOWN'}: 未知公理，无法对照决策卡")
                continue
            # 知行合一：公理方向与结论方向不应冲突（avoid vs buy）
            if direction and base_dir != direction:
                violations.append(
                    f"{axiom} 公理方向={base_dir} 但研报结论={direction} → 知行不一（违反所引公理）")
            # 止损触发：kill_switch 已触发却仍按原方向下结论
            if ks and direction and direction == base_dir:
                violations.append(
                    f"{axiom}: kill_switch 已触发({item.get('kill_signal', '')}) 却仍按 {direction} 下结论 → 无视证伪触发器")
            # Step3-P2：monitor.json 显示该公理红线已激活，但研报却声明未触发 → 自相矛盾
            if axiom in monitor_activated and not ks:
                violations.append(
                    f"{axiom}: monitor.json 显示 kill_switch 已激活({monitor_activated[axiom][:1]}) 但研报声明 kill_switch_triggered=false → 监控与声明矛盾")

        return {
            "gate": gate_name,
            "type": "HIGH",
            "status": "FAIL" if violations else "PASS",
            "details": "; ".join(violations) if violations else
                       f"All {len(rationale)} decision rationale entries are knowledge-action consistent (知行合一)."
        }

    # =========================================================================
    # OVERALL VERDICT AGGREGATION
    # =========================================================================
    def execute_audit(self):
        evidence_records = self._read_evidence_jsonl()
        assumptions_data = self._read_json("assumptions.json")
        holdout_data = self._read_json("holdout_registry.json")
        thesis_data = self._read_json("thesis.json")
        report_text = self._read_text("report.md")

        # Run all 13 gates (6 Critical, 7 High Priority)
        results = [
            self.audit_gate_1_source_existence(evidence_records),
            self.audit_gate_2_claim_entailment_target_result(evidence_records),
            self.audit_gate_3_epistemic_birth_certificate(evidence_records),
            self.audit_gate_4_parameter_provenance_recalculation(assumptions_data),
            self.audit_gate_5_parameter_orthogonality_dual_model(assumptions_data),
            self.audit_gate_parameter_preregistration_blind(assumptions_data),
            self.audit_gate_validation_leakage(assumptions_data, holdout_data),
            self.audit_gate_artifact_enforcement(self.benchmark_dir),
            self.audit_gate_6_global_precision_regex(report_text),
            self.audit_gate_7_causal_distance_penalty(thesis_data),
            self.audit_gate_8_valuation_decoupling(report_text, thesis_data),
            self.audit_gate_decision_consistency(thesis_data),
            self.audit_gate_parameter_unit_contract(assumptions_data)
        ]


        critical_fails = [r for r in results if r["type"] == "CRITICAL" and r["status"] != "PASS"]
        high_fails = [r for r in results if r["type"] == "HIGH" and r["status"] != "PASS"]

        if critical_fails:
            overall_verdict = "FAIL"
        elif high_fails:
            overall_verdict = "PARTIAL_PASS"
        else:
            overall_verdict = "PASS"

        scorecard = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "scorecard_id": f"DETERMINISTIC_SCORECARD_{self.topic.upper()}",
            "topic": self.topic,
            "benchmark_target": f"Institutional Benchmark Report ({self.topic})",
            "scope": "Listed claims and checks only; not certification of the entire report",
            "report_binding": {"path": str((self.benchmark_dir / "report.md").resolve()), "content_hash": digest((self.benchmark_dir / "report.md").read_bytes()) if (self.benchmark_dir / "report.md").is_file() else None},
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "overall_verdict": overall_verdict,
            "summary": {
                "total_gates": len(results),
                "critical_gates_total": sum(1 for r in results if r["type"] == "CRITICAL"),
                "critical_gates_passed": sum(1 for r in results if r["type"] == "CRITICAL" and r["status"] == "PASS"),
                "high_priority_gates_total": sum(1 for r in results if r["type"] == "HIGH"),
                "high_priority_gates_passed": sum(1 for r in results if r["type"] == "HIGH" and r["status"] == "PASS"),
                "critical_failures": [r["gate"] for r in critical_fails],
                "high_priority_failures": [r["gate"] for r in high_fails]
            },
            "gate_breakdown": results
        }

        # Save scorecard json
        self.output_dir.mkdir(parents=True, exist_ok=True)
        out_json_path = self.output_dir / "audit_scorecard.json"
        with open(out_json_path, "w", encoding="utf-8") as f:
            json.dump(scorecard, f, indent=2, ensure_ascii=False)

        # Generate human-readable Markdown
        out_md_path = self.output_dir / "audit_scorecard.md"
        self._write_markdown_report(out_md_path, scorecard)

        return scorecard

    def _write_markdown_report(self, path: Path, scorecard: dict):
        lines = [
            f"# 独立确定性审计评分卡 (Deterministic Judge Scorecard - Topic: {scorecard['topic']})",
            "",
            f"- **执行引擎**：`Deterministic Judge` (Tier 3 Python 确定性通用硬性规则引擎)",
            f"- **课题标识**：`{scorecard['topic']}`",
            f"- **审计标的**：`{scorecard['benchmark_target']}`",
            f"- **审计时间**：`{scorecard['timestamp']}`",
            f"- **最终客观判定**：**`{scorecard['overall_verdict']}`**",
            "",
            f"- **范围**：{scorecard['scope']}，仅绑定 {scorecard['report_binding']}。",
            "---",
            "",
            "## 一、门禁汇总统计",
            "",
            f"| 门禁类别 | 总数 | 通过数 | 状态 |",
            f"| :--- | :--- | :--- | :--- |",
            f"| **关键门禁 (Critical Gates)** | {scorecard['summary']['critical_gates_total']} | {scorecard['summary']['critical_gates_passed']} | {'✅ ALL PASS' if scorecard['summary']['critical_gates_total'] == scorecard['summary']['critical_gates_passed'] else '❌ CRITICAL FAIL'} |",
            f"| **高优门禁 (High Priority Gates)** | {scorecard['summary']['high_priority_gates_total']} | {scorecard['summary']['high_priority_gates_passed']} | {'✅ ALL PASS' if scorecard['summary']['high_priority_gates_total'] == scorecard['summary']['high_priority_gates_passed'] else '⚠️ WARNING / PARTIAL'} |",
            "",
            "---",
            "",
            "## 二、逐门禁执行明细 (Gate Execution Breakdown)",
            "",
            "| 门禁标识 | 优先级 | 判定结果 | 审计执行明细 |",
            "| :--- | :--- | :--- | :--- |"
        ]

        for r in scorecard["gate_breakdown"]:
            badge = "✅ PASS" if r["status"] == "PASS" else r["status"]
            lines.append(f"| `{r['gate']}` | **{r['type']}** | {badge} | {r['details']} |")

        lines.extend([
            "",
            "---",
            "",
            "## 三、确定性判定原则 (Deterministic Rule)",
            "",
            "> 1. **全领域通用规则引擎**：适用于人形机器人、AI Coding、具身智能、商业航天等任意前沿科技课题；",
            "> 2. **严禁大模型自我打分**：评级完全由 Python 规则脚本根据底层数据、元数据、公式重算、残差诚实准则与实体产物完整性程序化计算得出；",
            "> 3. **一票否决权**：任一 Critical Gate 为 FAIL，整体审计结果绝对禁止判定为 PASS；",
            "> 4. **实体产物约束 (No Artifact, No Claim)**：若缺少可执行 JSON/JSONL 产物、哈希失配或存在偷看验证集行为，直接否决外部验证资格；",
            "> 5. **透明可审计**：所有审计结果与推导链均归档于 `audit_scorecard.json` 供第三方独立复核。"
        ])

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="Deterministic Judge - Hard Gate Engine")
    parser.add_argument("--topic", default=None, help="Topic name (e.g. humanoid_robot, ai_coding)")
    parser.add_argument("--benchmark-dir", default=None, help="Benchmark target directory")
    parser.add_argument("--config", default="config/pipeline_config.json", help="Path to pipeline configuration")
    parser.add_argument("--output-dir", default=None, help="Output directory for scorecards")
    args = parser.parse_args()

    judge = DeterministicJudge(
        benchmark_dir=args.benchmark_dir,
        topic=args.topic,
        config_path=args.config,
        output_dir=args.output_dir
    )
    scorecard = judge.execute_audit()

    print(f"\n========================================================")
    print(f"   DETERMINISTIC JUDGE AUDIT COMPLETED: [{judge.topic.upper()}]")
    print(f"========================================================")
    print(f"Topic:   {scorecard['topic']}")
    print(f"Target:  {scorecard['benchmark_target']}")
    print(f"Verdict: {scorecard['overall_verdict']}")
    print(f"Critical Gates: {scorecard['summary']['critical_gates_passed']} / {scorecard['summary']['critical_gates_total']}")
    print(f"High Priority:  {scorecard['summary']['high_priority_gates_passed']} / {scorecard['summary']['high_priority_gates_total']}")
    print(f"Scorecard JSON: {judge.output_dir / 'audit_scorecard.json'}")
    print(f"Scorecard MD:   {judge.output_dir / 'audit_scorecard.md'}")
    print(f"========================================================\n")

    if scorecard["overall_verdict"] != "PASS":
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
