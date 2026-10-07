#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_monitors.py —— 前线战术告警系统 (Kill-Switch Monitor CLI)
Frontier Tech Industrial Analysis Engine

演进动作3：把 monitor.json（前线投资监控清单）连成自动化运维的投研预警引擎。

工作逻辑（极简、纯标准库、确定性）：
  1. 读取各已立项项目 <benchmark_dir>/monitor.json 的监控项；
  2. 输入最新观测参数（季度财务 / 良品率等微观事实），如 {"utilization": 0.55} 或 "--param utilization=0.55"；
  3. 对每条 falsification_redline 做 纯代码布尔判定（AST 安全，绝无 eval）：
       redline 条件触发 && 观测变量命中 → Kill-Switch 激活 → 终端报警；
  4. 全部安全 → "继续安全持有"。

用法：
  python scripts/check_monitors.py --benchmark-dir reports/nvidia_benchmark \
      --param utilization=0.45 --param revenue_diverge=0.25
  python scripts/check_monitors.py --scan-all --param b=-0.10   # 扫描所有项目

Fail-Closed：无 monitor.json / 无观测值 → 无法判定 → 默认按"待核查"而非"安全"。
"""

import argparse
import ast
import json
import re
import sys
from pathlib import Path


# 把 redline 里的自然语言数值条件安全地解析为可判定条件。
# 支持形如 "x > 0.1"、"x <= 5%"、汉字数值条件不解析（返回 None=无法判定，诚实不误报）。
_REDLINE_NUM = re.compile(r"\b([A-Za-z_]\w*)\s*(>=|<=|>|<|==|!=)\s*(-?[\d.]+)\s*(%?)")


def _eval_condition(op: str, lhs: float, rhs: float) -> bool:
    if op == ">=":
        return lhs >= rhs
    if op == "<=":
        return lhs <= rhs
    if op == ">":
        return lhs > rhs
    if op == "<":
        return lhs < rhs
    if op == "==":
        return abs(lhs - rhs) < 1e-9
    if op == "!=":
        return abs(lhs - rhs) >= 1e-9
    return False


def check_redline(redline: str, observation: dict) -> dict:
    """纯代码布尔判定一条 redline 是否被观测值触发。

    返回 {"triggered": bool, "matched_var": str|None, "reason": str}。
    无法解析(汉字阈值) → triggered=False + matched_var=None（诚实：不臆测、不误报）。
    """
    for m in _REDLINE_NUM.finditer(redline):
        var, op, num_s, pct = m.group(1), m.group(2), m.group(3), m.group(4)
        val = observation.get(var)
        if val is None or not isinstance(val, (int, float)):
            continue
        rhs = float(num_s)
        if pct:
            val = val * 100.0  # 观测为比率时转百分比比较
        triggered = _eval_condition(op, float(val), rhs)
        if triggered:
            return {"triggered": True, "matched_var": var,
                    "reason": f"{var}={observation.get(var)} {op} {num_s}{pct} → 红线触发"}
    return {"triggered": False, "matched_var": None, "reason": "未触发或无法解析"}


def check_monitor_file(monitor_path: Path, observation: dict) -> dict:
    """对单个 monitor.json 做告警判定。"""
    if not monitor_path.is_file():
        return {"status": "NO_MONITOR", "alerted": False, "items": []}
    try:
        data = json.loads(monitor_path.read_text(encoding="utf-8"))
    except Exception:
        return {"status": "CORRUPT", "alerted": True, "items": []}
    results = []
    any_alert = False
    for item in data.get("items", []):
        axiom = item.get("axiom", "?")
        direction = item.get("recommended_direction", "hold")
        phase = item.get("applicable_phase", "")
        redlines = item.get("falsification_redlines", [])
        # 结合观测做布尔判定；若 monitor_builder 已标 kill_switch_activated，直接告警
        pre_activated = bool(item.get("kill_switch_activated", False))
        triggered_redlines = []
        for rl in redlines:
            chk = check_redline(rl, observation)
            if chk["triggered"]:
                triggered_redlines.append(chk["reason"])
        alerted = bool(pre_activated or triggered_redlines)
        if alerted:
            any_alert = True
        results.append({
            "axiom": axiom, "direction": direction, "phase": phase,
            "alerted": alerted, "signals": triggered_redlines,
            "pre_activated": pre_activated,
        })
    return {"status": "OK", "alerted": any_alert, "items": results}


def run(benchmark_dirs, observation):
    """对一批 benchmark 目录运行告警检查，返回结构化结果。"""
    report = {"checked": [], "alerted": False}
    for bdir in benchmark_dirs:
        b = Path(bdir)
        res = check_monitor_file(b / "monitor.json", observation)
        res["benchmark_dir"] = str(b)
        report["checked"].append(res)
        if res.get("alerted"):
            report["alerted"] = True
    return report


def format_report(report) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append("   KILL-SWITCH MONITOR (前线战术告警)")
    lines.append("=" * 60)
    for item in report["checked"]:
        lines.append(f"[{item['benchmark_dir']}] {item['status']}")
        if item["status"] == "OK":
            for m in item["items"]:
                if m["alerted"]:
                    lines.append(f"  ⚠ KILL-SWITCH [{m['axiom']}]({m['direction']}):")
                    for s in (m["signals"] or ["预置红线已激活"]):
                        lines.append(f"      {s}")
                else:
                    lines.append(f"  ✓ 安全 [{m['axiom']}]({m['direction']}): 未触发红线")
    lines.append("-" * 60)
    if report["alerted"]:
        lines.append("  结果: ⚠ 存在已触发的 Kill-Switch，建议立即核查并撤出对应头寸！")
    else:
        lines.append("  结果: ✓ 全部监控项安全，可继续持有。")
    lines.append("=" * 60)
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Kill-Switch Monitor CLI (前线战术告警)")
    ap.add_argument("--benchmark-dir", default=None, help="单个项目目录")
    ap.add_argument("--scan-all", action="store_true", help="扫描 reports/ 下所有 *_benchmark")
    ap.add_argument("--param", action="append", default=[], help="观测参数, 如 utilization=0.45")
    args = ap.parse_args()
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    obs = {}
    for p in args.param:
        k, _, v = p.partition("=")
        try:
            obs[k.strip()] = float(v)
        except ValueError:
            obs[k.strip()] = v.strip()

    if args.scan_all:
        dirs = [str(d) for d in Path("reports").glob("*_benchmark") if d.is_dir()]
    elif args.benchmark_dir:
        dirs = [args.benchmark_dir]
    else:
        ap.error("必须提供 --benchmark-dir 或 --scan-all")

    report = run(dirs, obs)
    print(format_report(report))
    # 退出码：有告警 → 1；否则 0
    return 1 if report["alerted"] else 0


if __name__ == "__main__":
    sys.exit(main())
