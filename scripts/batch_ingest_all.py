#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
batch_ingest_all.py —— 全量 RAG 语料批处理流水线
Frontier Tech Industrial Analysis Engine

遵循"全量批处理四安全规范"，把 raw 文档脱水入库为 axiom_index.json，且不破坏 golden 评测。

三步推进法：
  阶段1 Canary Run ：--limit 5   （挑 5-10 份不同风格文档试探跑，检查异常/编码）
  阶段2 Full Batch  ：--limit 0   （全量 246 文档批处理）
  阶段3 Regression  ：自动跑 eval_rag.py 确认 12 个金标用例依旧满分

四安全规范：
  1. Immutable Backup —— 覆盖前把当前索引备份为 axiom_index_backup_<ts>.json；chunk_id 基于
     文档序号+切片序号确定性生成（同文档同切片→同 ID），避免重复跑批 ID 抖动。
  2. Encoding Guardrails —— 每份文档抽取强制 errors="replace"，捕获 UnicodeDecodeError/异常，
     单份损坏绝不让整个批次崩溃（返回空串跳过并计数）。
  3. Density & Noise Filter —— 批处理激活信噪比门禁：noise_ratio>阈值的切片被拦截，不污染知识库。
  4. Regression Check —— 批处理末尾自动调用 eval_rag.py，Hit@5/饥饿率不达标即 sys.exit(1)。

纯 Python 标准库 + PyMuPDF(已豁免)；零 pip 新增。
用法:
  python scripts/batch_ingest_all.py --limit 5      # Canary
  python scripts/batch_ingest_all.py                # Full batch (全量)
  python scripts/batch_ingest_all.py --noise-filter 0.55   # 自定义噪声门禁
"""

import argparse
import datetime
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "scripts"))

from rag_index_builder import (  # noqa: E402
    extract_doc_text, slot_chunks, load_skill_keywords, tag_methodology_topics,
    noisiness, _MICRO_FACT_TERMS,
)


def _backup_index(index_path: Path):
    """规范1：覆盖前强制备份当前索引。"""
    if not index_path.is_file():
        return None
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = index_path.parent / f"axiom_index_backup_{ts}.json"
    shutil.copyfile(index_path, backup)
    return backup


def _chunk_for_batch(text, min_hit_chars, skill_kw, all_kws, source, topic,
                     noise_gate, chunk_chars=600, valid_from=None, doc_idx=0, chunk_idx=0):
    """复用 builder 的切片逻辑 + 信噪比门禁 + 确定性 chunk_id。"""
    hits = [k for k in all_kws if k and k in text]
    if not hits or len(text) < min_hit_chars:
        return None
    fact_hits = [t for t in _MICRO_FACT_TERMS if t and t in text]
    if fact_hits:
        hits = list(dict.fromkeys(hits + fact_hits))
    # 规范3：信噪比脱水门禁——低信噪切片拦截在门外
    noise = noisiness(text)
    if noise > noise_gate:
        return None
    match_detail = {}
    for skill, kws in skill_kw.items():
        matched = [k for k in kws if k in text]
        if matched:
            match_detail[skill] = matched[:5]
    m_topics = tag_methodology_topics(text)
    return {
        "text": text,
        "source": source,
        "topic": topic,
        "chunk_id": f"D{doc_idx:04d}_C{chunk_idx:04d}",   # 确定性：同文档同切片→同ID
        "epistemic_type": "INFERENCE",
        "skills": {"matched_skills": list(match_detail.keys()),
                   "match_detail": match_detail},
        "methodology_topics": m_topics["canonical_topics"],
        "methodology_terms": m_topics["hit_terms"],
        "keywords": hits[:20],
        "noise_ratio": noise,
        "valid_from": valid_from,
        "valid_to": None,
    }


def build_full_index(input_dir, manifest_path, config_path, out_path,
                     min_hit_chars, noise_gate, max_chunks_per_doc, limit=0):
    """全量遍历 manifest 文档（limit=0 表示全部），遵循编码防御 + 信噪比门禁。"""
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    all_docs = manifest.get("all_scanned", [])
    # 按浓度降序（高价值文档优先），便于 Canary 取前 N 试探
    all_docs = sorted(all_docs, key=lambda d: -d.get("methodology_hits", 0))
    selected = all_docs if limit <= 0 else all_docs[:limit]

    # 补充非 PDF 语料（xlsx / docx）：扫描 inputDoc 目录，把 manifest 没覆盖的可抽取文件也纳入。
    # 使 xlsx(企业分析框架)、docx(Ray Dalio / DARPA 机器人) 也能进索引。
    if limit <= 0:  # 仅全量批处理时纳入非 PDF；Canary 仍按浓度取 PDF 试探
        _extra = []
        for p in sorted(Path(input_dir).iterdir()):
            if not p.is_file():
                continue
            if p.suffix.lower() in (".xlsx", ".docx") and p.name not in {d.get("file") for d in all_docs}:
                _extra.append({"file": p.name, "methodology_hits": 0, "chars": 0, "hit_terms": {}})
        selected = selected + _extra

    skill_kw = load_skill_keywords(Path(config_path))
    all_kws = sorted({k for kws in skill_kw.values() for k in kws})

    documents, errors, skipped_noise = [], 0, 0
    for di, doc in enumerate(selected):
        fname = doc.get("file", "")
        pdf = Path(input_dir) / fname
        v_from = None
        m = re.search(r"(20\d{2})(\d{2})(\d{2})", fname)
        if m:
            v_from = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        # 规范2：编码防御——单份损坏返回空串继续，不崩溃
        try:
            raw, engine = extract_doc_text(pdf)
        except UnicodeDecodeError:
            raw, engine = "", "ENCODING_ERR"
        except Exception as exc:
            errors += 1
            raw, engine = "", f"ERR:{type(exc).__name__}"
        chunks = []
        if raw:
            for ci, ch in enumerate(slot_chunks(raw, 600)[:max_chunks_per_doc]):
                snip = _chunk_for_batch(ch["text"], min_hit_chars, skill_kw, all_kws,
                                        fname, "全量批处理语料", noise_gate,
                                        valid_from=v_from, doc_idx=di, chunk_idx=ci)
                if snip:
                    chunks.append(snip)
                else:
                    skipped_noise += 1
        documents.append({
            "filename": fname, "topic": "全量批处理", "layer": "batch",
            "extracted": bool(raw), "engine": engine, "chars": len(raw),
            "chunks": chunks,
            "status": "INDEXED" if chunks else ("EXTRACT_FAILED" if not raw else "NO_KEYWORD_HITS"),
        })

    index = {
        "schema_version": "1.0",
        "kind": "keyword-axiom-index",
        "description": "全量批处理语料索引（batch_ingest_all.py 生成，含信噪比门禁）",
        "built_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "batch": {"docs_selected": len(selected), "docs_encoding_errors": errors,
                  "chunks_noise_skipped": skipped_noise, "noise_gate": noise_gate},
        "documents": documents,
    }
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    total_chunks = sum(len(d["chunks"]) for d in documents)
    return index, errors, skipped_noise, total_chunks


def _run_eval(dataset_path):
    """规范4：批处理后立即跑 golden 评测回归。"""
    import eval_rag
    eval_rag.run_rag_benchmark(Path(dataset_path), top_k=5, hit_threshold=60.0, mrr_threshold=0.30)


def main():
    ap = argparse.ArgumentParser(description="全量 RAG 语料批处理流水线")
    ap.add_argument("--input-dir", default="inputDoc")
    ap.add_argument("--manifest", default="rag/research/source_manifest.json")
    ap.add_argument("--config", default="config/pipeline_config.json")
    ap.add_argument("--output", default="rag/research/axiom_index.json")
    ap.add_argument("--limit", type=int, default=0, help="0=全量；>0=仅前 N 份(Canary)")
    ap.add_argument("--min-hit-chars", type=int, default=40)
    ap.add_argument("--noise-filter", type=float, default=0.55, help="信噪比门禁，>此值拦截")
    ap.add_argument("--max-chunks", type=int, default=60)
    ap.add_argument("--dataset", default="tests/retrieval_golden_dataset.json")
    ap.add_argument("--no-eval", action="store_true", help="跳过阶段3回归")
    args = ap.parse_args()
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    out = Path(args.output)
    # 规范1：备份
    backup = _backup_index(out)
    print(f"[规范1] 已备份当前索引 → {backup.name if backup else '(无原索引)'}")

    print(f"[阶段] {'Canary(前'+str(args.limit)+'份)' if args.limit>0 else 'Full Batch(全量)'} 开始…")
    t0 = time.time()
    index, errors, skipped, total_chunks = build_full_index(
        args.input_dir, args.manifest, args.config, str(out),
        args.min_hit_chars, args.noise_filter, args.max_chunks, args.limit)
    dt = time.time() - t0
    print(f"[完成] {dt:.1f}s | 文档={len(index['documents'])} 切片={total_chunks} "
          f"编码错误={errors} 低信噪拦截={skipped}")

    # 规范3：信噪比门禁统计
    noisy_in = sum(1 for d in index["documents"] for c in d["chunks"] if c["noise_ratio"] > args.noise_filter)
    print(f"[规范3] 入库切片中仍含噪声({args.noise_filter}以上)={noisy_in}（门禁应已拦截）")

    # 规范4：回归评测
    if not args.no_eval:
        print("\n[规范4] 回归护栏：运行 eval_rag.py…")
        _run_eval(args.dataset)
    else:
        print("\n[规范4] 已跳过(--no-eval)")


if __name__ == "__main__":
    main()