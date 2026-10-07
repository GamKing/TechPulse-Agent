#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
monitor.json 生成器 (前线投资监控清单构建)
Frontier Tech Industrial Analysis Engine

Step3-P2：15 核心方法论强类型卡片化的落地出口。

Tier 1 在研报中引用某方法论公理时，填充三个槽位后调用本生成器：
  1. applicable_phase    —— 当前适用阶段判断
  2. ast_formula_template —— 该公理的 AST 可计算公式原语（对应 parameter_registry.json）
  3. falsification_redlines —— 预设证伪红线（Kill-Switch）

输出 monitor.json —— 一张"前线投资监控清单"，每条监控项：
  - 引用的公理 canonical + 决策卡方向
  - 适用阶段
  - 待观测的核心变量（从公式模板解析）
  - 证伪红线（Kill-Switch）：观测到即推翻预测
  - kill_switch 激活状态（若观测变量已触发红线 → activated）

纯 Python 标准库；模板在 methodology_templates.json（静态、可版本化）。
用法:
  python scripts/monitor_builder.py --benchmark-dir reports/nvidia_benchmark \
      --axiom '佩蕾丝技术资本周期' --phase 'INSTALLATION' \
      --observation '{"utilization": 0.55, "revenue_diverge": 0.3}'
"""

import argparse
import json
import re
import sys
from pathlib import Path


def load_templates(path="scripts/methodology_templates.json"):
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("templates", {})


def load_heuristics(path="scripts/decision_heuristics.py"):
    """动态导入决策卡方向映射（避免硬编码重复）。"""
    sys.path.insert(0, "scripts")
    from decision_heuristics import DECISION_DIRECTION
    return DECISION_DIRECTION


def extract_variables(formula_template: str):
    """从公式模板中提取真实变量名（排除 Python 关键字/数字/内置名/字符串字面量）。"""
    if not formula_template:
        return []
    # 去掉单双引号包裹的字符串字面量（枚举常量等），避免把 'EXPANSION' 误当变量
    without_str = re.sub(r"'[^']*'|\"[^\"]*\"", " ", formula_template)
    tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", without_str)
    stop = {"if", "else", "max", "min", "abs", "and", "or", "not", "True", "False", "None",
            "round", "len", "int", "float", "b", "phase"}
    return sorted({t for t in tokens if t not in stop})


def build_monitor(benchmark_dir, axiom, phase=None, observation=None, rationale_note=""):
    """生成 monitor.json 前线监控清单条目，追加到 <benchmark_dir>/monitor.json。

    axiom            —— 引用的方法论 canonical（必须在模板与决策卡中存在）
    phase            —— Tier1 判定的适用阶段（optional，默认模板 applicable_phase 描述）
    observation      —— 研报观测到的当前变量值 dict，用于判定 kill_switch 是否激活
    """
    templates = load_templates()
    directions = load_heuristics()
    if axiom not in templates:
        raise ValueError(f"Unknown axiom template: {axiom}. Available: {list(templates.keys())}")

    tpl = templates[axiom]
    applicable = phase or tpl.get("applicable_phase", "")
    formula = tpl.get("ast_formula_template", "")
    redlines = tpl.get("falsification_redlines", [])
    direction = directions.get(axiom, "hold")
    variables = extract_variables(formula)

    # Kill-Switch 激活判定（启发式）：若观测值里有任一变量触发"低于/高于"红线阈值
    obs = observation or {}
    activation_signals = []
    for var in variables:
        val = obs.get(var)
        if val is None or not isinstance(val, (int, float)):
            continue
        for redline in redlines:
            m = re.search(rf"{var}\s*(>=|<=|>|<|==)\s*([\d.]+)", redline)
            if m:
                op, thr = m.group(1), float(m.group(2))
                triggered = (op == ">=" and val >= thr) or (op == "<=" and val <= thr) or \
                            (op == ">" and val > thr) or (op == "<" and val < thr) or \
                            (op == "==" and abs(val - thr) < 1e-9)
                if triggered:
                    activation_signals.append(f"{var}={val} 触发了红线: {redline.strip()[:60]}")

    item = {
        "axiom": axiom,
        "recommended_direction": direction,
        "applicable_phase": applicable,
        "monitored_variables": variables,
        "ast_formula_template": formula,
        "falsification_redlines": redlines,
        "kill_switch_activated": bool(activation_signals),
        "kill_switch_signals": activation_signals,
        "rationale_note": rationale_note,
    }

    bdir = Path(benchmark_dir)
    bdir.mkdir(parents=True, exist_ok=True)
    mf = bdir / "monitor.json"
    data = {"items": []}
    if mf.is_file():
        try:
            data = json.loads(mf.read_text(encoding="utf-8"))
            data.setdefault("items", [])
        except Exception:
            data = {"items": []}
    # 去重（同 axiom 覆盖更新）
    data["items"] = [x for x in data["items"] if x.get("axiom") != axiom]
    data["items"].append(item)
    mf.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return data


def main():
    ap = argparse.ArgumentParser(description="Build monitor.json frontline monitoring checklist")
    ap.add_argument("--benchmark-dir", default="reports/nvidia_benchmark")
    ap.add_argument("--axiom", required=True, help="Methodology canonical, e.g. 佩蕾丝技术资本周期")
    ap.add_argument("--phase", default=None, help="Applicable phase判定")
    ap.add_argument("--observation", default=None, help='JSON dict of observed variables, e.g. {"utilization": 0.55}')
    ap.add_argument("--note", default="", help="Rationale note")
    args = ap.parse_args()

    obs = json.loads(args.observation) if args.observation else None
    data = build_monitor(args.benchmark_dir, args.axiom, args.phase, obs, args.note)
    item = data["items"][-1]
    print(f"monitor.json 已更新: {args.benchmark_dir}/monitor.json")
    print(f"  公理: {item['axiom']} | 方向: {item['recommended_direction']} | 阶段: {item['applicable_phase']}")
    print(f"  监控变量: {item['monitored_variables']}")
    print(f"  kill_switch_activated: {item['kill_switch_activated']}")
    if item["kill_switch_signals"]:
        for s in item["kill_switch_signals"]:
            print(f"    ⚠ {s}")


if __name__ == "__main__":
    main()
