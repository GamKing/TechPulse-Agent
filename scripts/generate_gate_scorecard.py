#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_gate_scorecard.py —— 自动生成统一黄金评分卡 GATE_SCORECARD.md
Frontier Tech Industrial Analysis Engine

P1-4: 把手写静态文档升级为"自动生成交付件"。
从一个基准(默认 nvidia_benchmark，黄金基线)触发 deterministic_judge，
从 scorecard.gate_breakdown 提取 13 道门禁的规范名/类型/实时状态，自动生成 GATE_SCORECARD.md。

优点:
  - 门禁清单与代码/实际执行同步（不会手写遗漏）；
  - 每次跑都刷新各门禁在黄金基线上的真实状态；
  - 作为交付件，可供审计/汇报/Tier 1 对齐使用。

用法: python scripts/generate_gate_scorecard.py [--benchmark-dir ...] [--output GATE_SCORECARD.md]
"""

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "scripts"))


# 每道门禁的一句话说明（人工维护描述，与门禁清单分离；清单来自引擎而非手写）
GATE_DESCRIPTIONS = {
    "GATE_SOURCE_EXISTENCE": "来源物理存在性：快照重算 SHA-256 与凭证一致",
    "GATE_CLAIM_ENTAILMENT_TARGET_RESULT": "语义蕴含 × 目标漂移：独立审稿 FULL",
    "GATE_EPISTEMIC_BIRTH_CERTIFICATE": "认识论出生证：禁止二手估算冒充 FACT",
    "GATE_PARAMETER_PROVENANCE_RECALCULATION": "参数溯源 AST 重算（无大模型，纯代码）",
    "GATE_PARAMETER_ORTHOGONALITY_DUAL_MODEL": "双模型参数正交 + 诚实残差规则",
    "GATE_PARAMETER_PREREGISTRATION_BLIND": "预登记盲审：参数先固化、哈希锁定、防事后挑拣",
    "GATE_VALIDATION_LEAKAGE": "验证泄漏防火墙：holdout 隔离+独立审计+时序",
    "GATE_ARTIFACT_ENFORCEMENT": "产物完整性：9 件必需产物俱在",
    "GATE_GLOBAL_PRECISION_REGEX_AUDIT": "全局精度正则：认知标签齐全 + 无伪精度",
    "GATE_CAUSAL_DISTANCE_PENALTY": "因果距离惩罚：远距离证据不得声称强支持",
    "GATE_VALUATION_DECOUPLING": "估值脱钩：禁煽动词 + 三级脱钩",
    "GATE_DECISION_CONSISTENCY": "知行合一：公理方向与研报结论方向一致",
    "GATE_PARAMETER_UNIT_CONTRACT": "单位契约：参数卡声明 unit + AST 跨量纲检查",
}


def generate_scorecard(benchmark_dir, output_path):
    from deterministic_judge import DeterministicJudge
    judge = DeterministicJudge(benchmark_dir=benchmark_dir)
    sc = judge.execute_audit()

    gates = sc["gate_breakdown"]
    summary = sc["summary"]
    verdict = sc["overall_verdict"]

    critical = [g for g in gates if g["type"] == "CRITICAL"]
    high = [g for g in gates if g["type"] == "HIGH"]

    lines = []
    lines.append("# agent-rag 统一黄金评分卡 (GATE_SCORECARD · 自动生成)")
    lines.append("")
    lines.append(f"> 本文件由 `scripts/generate_gate_scorecard.py` 自动生成于 `{sc.get('timestamp')}`。")
    lines.append(f"> 门禁清单来自 `deterministic_judge.execute_audit()` 实际执行（非手写），确保与代码同步。")
    lines.append(f"> 基准: `{benchmark_dir}` | 主题: `{sc.get('topic')}`")
    lines.append("")
    lines.append(f"## 总判定: **{verdict}** (exit {'0' if verdict=='PASS' else '1'})")
    lines.append("")
    lines.append(f"| 类别 | 通过 | 总数 |")
    lines.append(f"| :--- | :--- | :--- |")
    lines.append(f"| CRITICAL | {summary.get('critical_gates_passed')} / {summary.get('critical_gates_total')} |")
    lines.append(f"| HIGH | {summary.get('high_priority_gates_passed')} / {summary.get('high_priority_gates_total')} |")
    lines.append("")
    lines.append("## 门禁明细")
    lines.append("")
    lines.append("| 门禁 | 优先级 | 状态 | 说明 |")
    lines.append("| :--- | :---: | :---: | :--- |")

    for g in critical + high:
        name = g["gate"]
        desc = GATE_DESCRIPTIONS.get(name, g.get("details", "")[:50])
        lines.append(f"| `{name}` | {g['type']} | {g['status']} | {desc} |")

    lines.append("")
    lines.append("## Fail-Closed 语义")
    lines.append("")
    lines.append("- **PASS**: 在物理数据/纯代码下被证明通过")
    lines.append("- **FAIL**: 拒绝（数据伪造/缺失/篡改）")
    lines.append("- **UNVERIFIED**: 证据不足——聚合中视为未过关，绝不当作通过")
    lines.append("")
    lines.append("> 聚合规则: 任一 CRITICAL 非 PASS → FAIL；无 critical 失败但 HIGH 非 PASS → PARTIAL_PASS；全 PASS → PASS。")
    lines.append("> 生成命令: `python scripts/generate_gate_scorecard.py --benchmark-dir {benchmark_dir}`")

    Path(output_path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] 黄金评分卡已生成 → {output_path}")
    print(f"     基准={benchmark_dir} 门禁={len(gates)} 判定={verdict}")
    return sc


def main():
    ap = argparse.ArgumentParser(description="自动生成统一黄金评分卡")
    ap.add_argument("--benchmark-dir", default="reports/nvidia_benchmark")
    ap.add_argument("--output", default=str(_REPO / "GATE_SCORECARD.md"))
    args = ap.parse_args()
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    # 允许相对路径基准
    bdir = args.benchmark_dir
    if not Path(bdir).exists() and (Path(_REPO) / bdir).exists():
        bdir = str(Path(_REPO) / bdir)
    generate_scorecard(bdir, args.output)


if __name__ == "__main__":
    main()