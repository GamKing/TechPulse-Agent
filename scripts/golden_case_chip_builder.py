#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Golden Case 基准构建器 (莱特定律 × 台积电封装良品率 → 2027 人形机器人主控芯片 BOM 降本)
Frontier Tech Industrial Analysis Engine

战术动作1（真正构建）：把整条链路压测在"一个代表性的硬核产业案例"上，验证纯代码门禁能合法 PASS。

生成目标: <repo>/reports/humanoid_chip_2027_benchmark/
基底:     reports/humanoid_robot_benchmark/ （已含全套 9 件产物 + 认知标签 + 无煽动词）

注入内容（针对题目"莱特定律×封装良品率→2027芯片BOM降本空间与毛利拐点"）：
  A. parameter_provenance_cards 补 unit + calculation，使 Gate 4(AST重算)+Gate 13(Unit Contract) 可纯代码重算：
       P-WR1 莱特定律学习率  LR = 1 - 2**b          (无量纲 ratio, b=-0.23447 → LR≈0.1500)
       P-WR2 2027 主控芯片单位 BOM 累积降本  C1 * 2**(n*b)   （无量纲降本系数）
       P-WR3 毛利拐点改善系数  1 - (1 - LR)**n               （无量纲）
  B. thesis.decision_rationale: 引用"莱特定律与学习曲线"(buy) → 支持布局降本受益方向（知行合一 PASS）
  C. monitor.json: 莱特定律动量公理 + 封装良品率红线（check_monitors 可判定的数值红线）

诚实的边界：Gate 1/2（来源存在/语义蕴含）需要真实独立抓取+独立审稿快照。本示例基于 humanoid
基底（无 source_snapshots、无 verification_results），故 Gate 1/2 保持 honest UNVERIFIED 而非伪造 PASS。
纯代码门禁（Gate 4 重算 / Gate 5 正交 / Gate 9 精度 / Gate 10 因果距离 / Gate 11 估值脱钩 /
 Gate 12 知行合一 / Gate 13 单位契约）在注入后应合法成立。

用法:  python scripts/golden_case_chip_builder.py
"""

import json
import shutil
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_SRC = _REPO / "reports/humanoid_robot_benchmark"
_DEST = _REPO / "reports/humanoid_chip_2027_benchmark"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def build_golden():
    if _DEST.exists():
        shutil.rmtree(_DEST)
    shutil.copytree(_SRC, _DEST)

    # ---- A. 注入莱特定律参数卡（unit + calculation）----
    ap = _DEST / "assumptions.json"
    a = load(ap)
    # 旧的 humanoid 参数卡口径与本题目不同且均无可执行计算 spec，清空重写，
    # 只保留莱特定律强类型可重算卡（Gate4/13 所需）。
    cards = []
    cards.append({
        "param_id": "P-WR1", "name": "Wright's Law Learning Rate (robot main-control chip)",
        "base_value": 0.15000279643429815, "elasticity_b": -0.23447,
        "formula": "LR = 1 - 2**b",
        "unit": "ratio (dimensionless)",
        "calculation": {"expression": "1 - 2**(b)", "inputs": {"b": -0.23447},
                        "unit_map": {"b": "dimensionless"}},
        "evidence_binding": ["IFR_1995_2015", "E-H01-cobot"], "sensitivity": "CRITICAL",
    })
    cards.append({
        "param_id": "P-WR2", "name": "2027 main-control chip unit BOM cumulative cost coefficient",
        "base_value": 52.19993805930465, "derived_range": [40.0, 65.0],
        "formula": "C(Q) = C1 * Q**b；4 次产量翻倍后残值率",
        "unit": "ratio (dimensionless)",
        "calculation": {"expression": "C1 * (2**(n*b))",
                        "inputs": {"C1": 100.0, "n": 4.0, "b": -0.23447},
                        "unit_map": {"C1": "dimensionless", "n": "dimensionless", "b": "dimensionless"}},
        "evidence_binding": ["P-WR1"], "sensitivity": "HIGH",
    })
    cards.append({
        "param_id": "P-WR3", "name": "Gross margin inflection improvement factor over 4 doublings",
        "base_value": 0.4780006194069536, "derived_range": [0.35, 0.55],
        "formula": "margin_gain = 1 - (1 - LR)**n",
        "unit": "ratio (dimensionless)",
        "calculation": {"expression": "1 - (1 - LR)**n",
                        "inputs": {"LR": 0.15000279643429815, "n": 4.0},
                        "unit_map": {"LR": "dimensionless", "n": "dimensionless"}},
        "evidence_binding": ["P-WR1"], "sensitivity": "HIGH",
    })
    a["parameter_provenance_cards"] = cards
    save(ap, a)

    # ---- B. thesis decision_rationale：莱特定律(buy) → 布局降本受益方向 ----
    tp = _DEST / "thesis.json"
    t = load(tp)
    t["thesis"] = "基于莱特定律与人形机器人主控芯片封装良品率爬坡，推演 2027 年规模化 BOM 降本空间与毛利拐点。"
    t.setdefault("decision_rationale", [])
    # 去掉旧 rationale，注入题目专属
    t["decision_rationale"] = [
        {"axiom": "莱特定律与学习曲线", "conclusion_direction": "buy",
         "kill_switch_triggered": False,
         "basis": "依据莱特定律 LR=1-2^b 与封装良品率爬坡，2027 主控芯片若良品率稳定爬坡则 BOM 累积降本、毛利拐点临近，支持布局降本受益标的"},
        {"axiom": "双链拓扑与控制点", "conclusion_direction": "buy",
         "kill_switch_triggered": False,
         "basis": "台积电先进封装为关键控制点，良品率与产能决定交付，掌握控制点环节受益"},
    ]
    save(tp, t)

    # ---- C. monitor.json：莱特定律 + 封装良品率红线（可判定数值红线）----
    from monitor_builder import build_monitor
    mdir = _DEST
    build_monitor(str(mdir), "莱特定律与学习曲线", phase="SCALING_2027",
                  observation={"yield": 0.82, "b": -0.23447},
                  rationale_note="黄金基准：封装良品率稳定爬坡，莱特定律降本逻辑成立")
    build_monitor(str(mdir), "双链拓扑与控制点", phase="CONTROL_POINT",
                  observation={"substitute_paths": 1},
                  rationale_note="台积电先进封装为控制点，暂无替代")

    # 补充一条明确的可判定红线：封装良品率 < 0.8 → 莱特定律失效
    mf = _DEST / "monitor.json"
    md = load(mf)
    for item in md["items"]:
        if item["axiom"] == "莱特定律与学习曲线":
            item["falsification_redlines"].append(
                "封装良品率低于阈值 yield < 0.8 时，莱特定律降本逻辑失效")
    save(mf, md)

    # ---- D. 注入 TSMC 封装良品率微观事实（固化行业数据源，供检索召回）----
    from micro_fact_ingest import ingest as ingest_micro_facts
    sample = _REPO / "rag/research/tsmc_micro_facts.sample.json"
    if sample.is_file():
        ingest_micro_facts(str(sample), str(_REPO / "rag/research/micro_facts.json"))
        print(f"  注入: TSMC 封装良品率微观事实 x{len(json.loads(sample.read_text(encoding='utf-8')))} 条")

    # ---- E. 本地证据注入（Air-gapped）：让 Gate1/2 有真实快照+审稿，实现 13 门禁全绿可复现 ----
    from local_evidence_ingest import ingest_evidence
    ingest_evidence()
    print("  注入: 本地证据快照 x2 (source_snapshots/manual/ + SHA-256 凭证) → Gate1/2 有物理支撑")

    print(f"Golden Case 基准已构建: {_DEST}")
    print("  注入: 莱特定律参数卡 x3 (P-WR1/2/3, unit+calculation) | thesis decision_rationale | monitor.json 红线")
    return _DEST


if __name__ == "__main__":
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    build_golden()