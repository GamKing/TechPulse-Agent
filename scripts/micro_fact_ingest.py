#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
micro_fact_ingest.py —— 微观事实数据源注入器
Frontier Tech Industrial Analysis Engine

边界2修复：语料(inputDoc 方法论文本)只有方法论、缺乏"封装/良品率/产能/ASP"等微观事实。
本工具允许分析师/数据管道把真实行业数据（TSMC 财报、SEMI 报告、IDC 追踪等）落盘为结构化 JSON，
转成带时间戳的微观事实切片，并入独立补充索引 rag/research/micro_facts.json，
使"009 台积电封装良品率"这类真实数据可被检索（而非凭空从讲义里找）。

数据槽位 schema（每个事实一条）:
{
  "fact_id": "TSMC-2027-COWOS-YIELD",
  "source": "TSMC 2026 Investor Conference / SEMI report",
  "source_url": "https://...",
  "valid_from": "2026-Q3",          # 时间戳优先(Time Superseding)用
  "claim": "2027 年 CoWoS 封装良品率预期 85%",
  "value": 0.85, "unit": "ratio",   # Unit Contract 用
  "keywords": ["封装", "良品率", "cowos", "台积电", "coverage"],
  "metrics": {"n_doublings": 4, "learning_rate": 0.15}   # 供莱特定律等模板公式引用
}
纯标准库；可被 rag builder / router 以"补充事实切片"方式并入检索。
"""

import argparse
import datetime
import json
import sys
from pathlib import Path

DEFAULT_OUT = "rag/research/micro_facts.json"


def load_input(path: Path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise ValueError(f"无法解析输入 {path}: {e}")
    return data if isinstance(data, list) else data.get("facts", [])


def normalize_fact(f: dict) -> dict:
    """校验并规范化一条微观事实。返回补齐默认字段的 dict。"""
    required = ("fact_id", "source", "claim")
    for r in required:
        if not f.get(r):
            raise ValueError(f"事实缺字段 {r}: {f.get('fact_id', '<unknown>')}")
    kws = list(f.get("keywords", []))
    for t in ("良品率", "良率", "产能", "封装", "成本", "bom", "降本"):
        if t in f.get("claim", ""):
            kws.append(t)
    return {
        "fact_id": f["fact_id"],
        "source": f["source"],
        "source_url": f.get("source_url", ""),
        "valid_from": f.get("valid_from", "2026-Q1"),
        "valid_to": f.get("valid_to"),
        "claim": f["claim"],
        "value": f.get("value"),
        "unit": f.get("unit", "dimensionless"),
        "keywords": sorted(set(kws)),
        "metrics": f.get("metrics", {}),
        # 供 router 合并检索时识别为"微观事实切片"
        "is_micro_fact": True,
        "ingested_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


def ingest(input_path: str, output: str = DEFAULT_OUT) -> dict:
    facts = [normalize_fact(f) for f in load_input(Path(input_path))]
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    # 与既有 micro_facts 合并（fact_id 去重，新覆盖旧）
    merged = {}
    if out.is_file():
        try:
            existing = json.loads(out.read_text(encoding="utf-8"))
            for f in existing.get("facts", []):
                merged[f["fact_id"]] = f
        except Exception:
            merged = {}
    for f in facts:
        merged[f["fact_id"]] = f
    doc = {
        "schema_version": "1.0",
        "kind": "micro-fact-index",
        "description": "微观事实数据源补充索引（行业数据，非方法论文本）；与 axiom_index.json 合并召回",
        "built_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "facts": [merged[k] for k in sorted(merged)],
    }
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    return doc


def main():
    ap = argparse.ArgumentParser(description="微观事实数据源注入器")
    ap.add_argument("--input", required=True, help="行业数据 JSON 文件路径")
    ap.add_argument("--output", default=DEFAULT_OUT)
    args = ap.parse_args()
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    doc = ingest(args.input, args.output)
    print(f"微观事实索引已更新: {args.output} ({len(doc['facts'])} 条)")


if __name__ == "__main__":
    main()