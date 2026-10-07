#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG Axiom Index Builder (特训营讲义 → 知识底册索引)
Frontier Tech Industrial Analysis Engine

依赖约束：
- 核心索引逻辑仅使用 Python 3.12+ 标准库；
- PDF 文本抽取优先用本地已装的 PyMuPDF (fitz) —— 这是唯一被豁免的第三方库，
  仅用于"RAG 摄入（knowledge ingestion）"，绝不进入验证/门禁路径（VERIFIED 原语仍为 stdlib-only）。
  理由：inputDoc 讲义为 CID 编码中文 PDF，poppler pdftotext 无 ToUnicode 映射取不出中文；
  PyMuPDF 能正确解码文字层。此豁免已在 AGENTS.md 变更记录中声明。
- 若 fitz 不可用则回退外部命令 pdftotext（poppler）。

职责：
1. 抽取 inputDoc/ 下 6 份方法论 PDF 的文字层；
2. 以 config/pipeline_config.json 的 skill_signatures（35 技能关键词）为锚分块，
   建立 切片 → 命中的技能 / 关键词 / 主题来源 的交叉引用；
3. 产出 rag/research/axiom_index.json，供 problem_router 做第二级关键词召回。

不做（诚实边界）：
- .xlsx/.jpg/.png 等非 PDF 语料标记 SKIP_NEEDS_OCR，不在本脚本内 OCR；
- 不做向量嵌入；召回为关键词 + 规则加权（保持验证路径 stdlib-only 铁律）。
"""

import argparse
import datetime
import json
import shutil
import subprocess
import sys
from pathlib import Path

from methodology_aliases import METHODOLOGY_ALIASES, canonical_for_text

# 目标方法论 PDF（相对 inputDoc/）；每份配一个主题标签用于切片溯源
METHODOLOGY_DOCS = [
    {"filename": "1-王煜全方法论_笔记整合.pdf", "topic": "王煜全科技产业分析方法论总纲"},
    {"filename": "文字版20240104创新地图核心理念V2（24年1月）.pdf", "topic": "创新地图核心方法论"},
    {"filename": "前哨科技特训营课程体系思维导图20240619 林丽碧.pdf", "topic": "特训营课程体系与方法论图谱"},
    {"filename": "文字稿 20230601【科技特训营】英伟达&AI芯片企业分析.pdf", "topic": "英伟达与AI芯片产业分析案例"},
    {"filename": "文字稿 20230608【科技特训营】苹果与MR产业未来.pdf", "topic": "苹果与MR产业未来案例"},
    {"filename": "1-内部资料【科技特训营】科技创业企业尽职调查清单pdf.pdf", "topic": "科技创业企业尽调清单"},
    {"filename": "1-内部资料【科技特训营】企业分析框架-整理人： Paul.xlsx", "topic": "企业分析框架阶梯(技术→产品→企业)"},
]

# 非 PDF 方法论文档：仅登记来源与跳过原因（需 OCR）
SKIPPED_DOCS = [
    {"filename": "技术革命与金融资本.jpg",
     "reason": "图片需 OCR（不在本脚本范围）"},
]

DEFAULT_CHUNK_CHARS = 600
DEFAULT_MIN_HIT_CHARS = 40
DEFAULT_MAX_CHUNKS_PER_DOC = 60


def extract_with_pymupdf(pdf_path: Path) -> str:
    """PyMuPDF 抽取文字层（能解 CID 中文）。失败返回空串。"""
    try:
        import fitz  # noqa: F401
    except Exception:
        return ""
    try:
        doc = fitz.open(str(pdf_path))
        return "".join(page.get_text() for page in doc)
    except Exception:
        return ""


def extract_with_pdftotext(pdf_path: Path) -> str:
    """回退：外部命令 pdftotext -layout。失败返回空串。"""
    exe = shutil.which("pdftotext")
    if not exe:
        return ""
    try:
        proc = subprocess.run([exe, "-layout", str(pdf_path), "-"],
                              capture_output=True, timeout=120)
        if proc.returncode != 0:
            return ""
        return proc.stdout.decode("utf-8", errors="replace")
    except (subprocess.TimeoutExpired, OSError):
        return ""


def extract_xlsx_text(xlsx_path: Path) -> str:
    """stdlib zip+XML 抽取 xlsx 共享字符串（企业分析框架类表格）。无第三方依赖。"""
    import zipfile
    import re
    try:
        z = zipfile.ZipFile(str(xlsx_path))
        names = z.namelist()
        if "xl/sharedStrings.xml" not in names:
            return ""
        ss = z.read("xl/sharedStrings.xml").decode("utf-8", "replace")
        strings = re.findall(r"<t[^>]*>(.*?)</t>", ss, re.S)
        # 简单去重保序
        seen, out = set(), []
        for s in strings:
            s = s.strip()
            if s and s not in seen:
                seen.add(s)
                out.append(s)
        return " ".join(out)
    except Exception:
        return ""


def extract_docx_text(docx_path: Path) -> str:
    """stdlib zip 读 docx 的 word/document.xml，提取全部 <w:t> 文本。无第三方依赖。"""
    import zipfile
    import re
    try:
        z = zipfile.ZipFile(str(docx_path))
        if "word/document.xml" not in z.namelist():
            return ""
        xml = z.read("word/document.xml").decode("utf-8", "replace")
        # 提取段落文本：<w:t ...>text</w:t>，段落间加换行分隔
        paras = []
        for para in re.findall(r"<w:p\b.*?</w:p>", xml, re.S):
            texts = re.findall(r"<w:t\b[^>]*>(.*?)</w:t>", para, re.S)
            if texts:
                paras.append("".join(texts))
        # 兜底：若段落结构缺失，退化为全文档所有 w:t 拼接
        if not paras:
            return " ".join(re.findall(r"<w:t\b[^>]*>(.*?)</w:t>", xml, re.S))
        return "\n".join(paras)
    except Exception:
        return ""


def extract_doc_text(path: Path) -> tuple:
    """按扩展名分派抽取器，返回 (text, engine)。"""
    if path.suffix.lower() == ".pdf":
        return extract_pdf_text(path)
    if path.suffix.lower() == ".xlsx":
        return extract_xlsx_text(path), "xlsx-stdlib"
    if path.suffix.lower() == ".docx":
        return extract_docx_text(path), "docx-stdlib"
    return "", "none"


def extract_pdf_text(pdf_path: Path) -> tuple:
    """返回 (text, engine)。engine 用于在索引中留下溯源（pymupdf / pdftotext / none）。"""
    text = extract_with_pymupdf(pdf_path)
    if len(text.strip()) > 200:
        return text, "pymupdf"
    text = extract_with_pdftotext(pdf_path)
    if len(text.strip()) > 200:
        return text, "pdftotext"
    return "", "none"


def load_skill_keywords(config_path: Path) -> dict:
    try:
        with open(config_path, encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        return {}
    sig = cfg.get("skill_signatures", {})
    out = {}
    for name, meta in sig.items():
        kws = []
        if isinstance(meta, dict):
            kws = list(meta.get("keywords", [])) + list(meta.get("name_zh", "").split())
        elif isinstance(meta, str):
            kws = meta.split()
        out[name] = [k for k in kws if k]
    return out


def slot_chunks(text: str, chunk_chars: int) -> list:
    text = " ".join(text.split())
    if not text:
        return []
    chunks, start, n = [], 0, len(text)
    while start < n:
        end = min(start + chunk_chars, n)
        if end < n:
            for sep in ("。", "；", "；", ". ", "！", "？"):
                idx = text.rfind(sep, start + chunk_chars // 2, end)
                if idx != -1:
                    end = idx + len(sep)
                    break
        seg = text[start:end].strip()
        if seg:
            chunks.append({"offset": start, "text": seg})
        start = end
    return chunks


# 口语填充/客套词：出现密度过高说明该切片低信噪比（来自演讲/文字稿的口水话）
_FILLER_WORDS = ("这个", "然后", "就是", "就是说", "对吧", "所以说", "那我们就",
                 "其实我觉得", "我觉得", "大家知道", "你会发现", "为什么呢", "就是说",
                 "对不对", "是不是", "嗯", "哎呀", "反正", "说到底", "说白了")
# 实质性信号词（方法论文本应承载的内容线索）：用于对比信噪
_SIGNAL_WORDS = ("因为", "所以", "取决于", "假设", "如果", "则", "意味着", "等于",
                 "比例", "率", "抛出", "买入", "规避", "风险", "下降", "上升", "成本",
                 "模型", "公理", "阶段", "周期", "控制点", "创新")


# 微观事实词：与 problem_router._MICRO_FACT_KEYWORDS 保持同源，用于索引时把微观事实词
# 也纳入切片 keywords，使"良品率/封装/交付"这类事实切片可被检索到（缺陷2完整闭环）。
_MICRO_FACT_TERMS = (
    "良品率", "良率", "产能", "交付", "交期", "价格", "成本", "毛利", "营收", "出货量",
    "占比", "库存", "wafer", "封装", "cowos", "hbm", "制程", "带宽", "算力", "单颗",
    "单位", "汇率", "asp", "spec", "公差", "丝杠", "减速器", "电机", "bom", "物料",
    "产能爬坡", "良率爬坡", "封装", "良品",
)


# 日期解析：从讲义/文字稿文件名提取 8 位日期（如 20230601 / 20240104 / 20240619）。
# 用于切片 valid_from 推断，支撑"时间戳优先(Time Superseding)"——微观事实按时间倒序，
# 旧数据自动降权，杜绝"拿明朝的剑斩清朝的官"。
def extract_valid_from(filename: str):
    """从文件名提取 YYYYMMDD 日期（或其子串 YYYYMM）。无法解析返回 None。

    匹配 8 位纯数字日期（如 20230601）或 6 位年月（如 202306）。
    """
    import re
    for pat in (r"(20\d{2})(\d{2})(\d{2})", r"(20\d{2})(\d{2})"):
        m = re.search(pat, filename)
        if m:
            y, mo = m.group(1), m.group(2)
            d = m.group(3) if len(m.groups()) == 3 else "01"
            return f"{y}-{mo}-{d}"
    return None


def noisiness(text: str) -> float:
    """返回切片噪声率 ∈ [0, 1]。填充词密度相对实质信号词密度的占比。

    >0.55 视为低信噪比切片（口语口水话为主，可能稀释 Tier 1 上下文）。
    """
    len_chars = max(1, len(text))
    filler = sum(text.count(w) for w in _FILLER_WORDS)
    signal = sum(text.count(w) for w in _SIGNAL_WORDS)
    return round(filler / (filler + signal + 1), 3)


def tag_methodology_topics(text: str) -> dict:
    """用别名表(学名 + 现象词)把切片命中的方法论归一到 canonical 主题。

    返回 {"canonical_topics": [...], "hit_terms": {...}}，供切片溯源与下游召回。
    同时命中学名（佩蕾丝/安装期）与口语现象词（泡沫破裂/路网铺设），解决专有名词断裂。
    """
    result = canonical_for_text(text)
    return {"canonical_topics": result["canonical_topics"],
            "hit_terms": result["hit_terms"]}


def _chunk_for(text, chunk_chars, min_hit_chars, skill_kw, all_kws, source, topic, valid_from=None):
    hits = [k for k in all_kws if k and k in text]
    if not hits or len(text) < min_hit_chars:
        return None
    # 缺陷2完整闭环：微观事实词也纳入索引 keywords，使事实切片可被检索到
    fact_hits = [t for t in _MICRO_FACT_TERMS if t and t in text]
    if fact_hits:
        hits = list(dict.fromkeys(hits + fact_hits))  # 去重保序
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
        "skills": {"matched_skills": list(match_detail.keys()),
                   "match_detail": match_detail},
        "methodology_topics": m_topics["canonical_topics"],
        "methodology_terms": m_topics["hit_terms"],
        "keywords": hits[:20],
        # 缺陷3修复：切片信噪比（口语填充密度）。>0.55 视为低信噪，下游检索应降权。
        "noise_ratio": noisiness(text),
        # Step1-P0：时间戳优先(Time Superseding)。valid_to=None 表示当前仍有效。
        "valid_from": valid_from,
        "valid_to": None,
    }


def build_index(input_dir, config_path, out_path, chunk_chars, min_hit_chars, max_chunks_per_doc,
                manifest_path="rag/research/source_manifest.json", expand_top=40):
    skill_kw = load_skill_keywords(config_path)
    all_kws = sorted({k for kws in skill_kw.values() for k in kws})

    # 分层语料：核心层（固定方法论讲义）+ 扩充层（manifest 浓度 TOP-N）
    doc_specs = [dict(d) for d in METHODOLOGY_DOCS]
    core_names = {d["filename"] for d in doc_specs}
    manifest_exists = Path(manifest_path).exists()
    if manifest_exists:
        manifest = json.load(open(manifest_path, encoding="utf-8"))
        ranked = sorted([r for r in manifest.get("all_scanned", [])
                         if r.get("methodology_hits", 0) >= 20 and r["file"] not in core_names],
                        key=lambda r: -r.get("methodology_hits", 0))
        for r in ranked[:expand_top]:
            doc_specs.append({"filename": r["file"], "topic": "扩充语料·方法论浓度TOP",
                              "methodology_hits": r.get("methodology_hits", 0), "layer": "expansion"})
    for d in doc_specs:
        d.setdefault("layer", "core")

    documents = []
    for doc in doc_specs:
        pdf = Path(input_dir) / doc["filename"]
        if not pdf.exists():
            documents.append({**doc, "extracted": False, "engine": "missing", "chars": 0,
                              "chunks": [], "status": "FILE_MISSING"})
            continue
        raw, engine = extract_doc_text(pdf)
        snippets = []
        v_from = extract_valid_from(doc["filename"])
        if raw:
            hit_count = 0
            for ch in slot_chunks(raw, chunk_chars)[:max_chunks_per_doc]:
                snip = _chunk_for(ch["text"], chunk_chars, min_hit_chars, skill_kw, all_kws,
                                  doc["filename"], doc.get("topic", ""), valid_from=v_from)
                if snip:
                    hit_count += 1
                    snippets.append(snip)
            status = "INDEXED" if snippets else ("EXTRACTED_NO_HITS" if raw else "EXTRACT_FAILED")
        else:
            status = "EXTRACT_FAILED"
        documents.append({**doc, "extracted": bool(raw), "engine": engine, "chars": len(raw),
                          "chunks": snippets, "status": status})

    skipped = [{"filename": d["filename"], "reason": d["reason"]} for d in SKIPPED_DOCS]
    index = {
        "schema_version": "1.0",
        "kind": "keyword-axiom-index",
        "description": "特训营方法论讲义(核心层)+全集浓度TOP扩充层 → 35 技能关键词 + 方法论主题交叉引用的公理索引",
        "built_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "layer_policy": {"core_docs": len(METHODOLOGY_DOCS), "expansion_top": expand_top,
                         "manifest_used": manifest_exists},
        "documents": documents,
        "skipped": skipped,
    }
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    return index


def main():
    ap = argparse.ArgumentParser(description="Build RAG axiom index from methodology PDFs")
    ap.add_argument("--input-dir", default="inputDoc")
    ap.add_argument("--config", default="config/pipeline_config.json")
    ap.add_argument("--output", default="rag/research/axiom_index.json")
    ap.add_argument("--chunk-chars", type=int, default=DEFAULT_CHUNK_CHARS)
    ap.add_argument("--min-hit-chars", type=int, default=DEFAULT_MIN_HIT_CHARS)
    ap.add_argument("--max-chunks", type=int, default=DEFAULT_MAX_CHUNKS_PER_DOC)
    ap.add_argument("--manifest", default="rag/research/source_manifest.json")
    ap.add_argument("--expand-top", type=int, default=40, help="从 manifest 浓度 TOP-N 扩充语料；0=只用核心层")
    args = ap.parse_args()
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    index = build_index(args.input_dir, args.config, args.output,
                        args.chunk_chars, args.min_hit_chars, args.max_chunks,
                        args.manifest, args.expand_top)
    total_chunks = sum(len(d["chunks"]) for d in index["documents"])
    print(f"已索引文档: {sum(1 for d in index['documents'] if d['chunks'])}/{len(index['documents'])} (引擎: {sorted(set(d['engine'] for d in index['documents']))})")
    print(f"总切片数:   {total_chunks}")
    for d in index["documents"]:
        print(f"  [{d['engine']:9s}] {d['status']:18s} {d['filename'][:42]:44s} chunks={len(d['chunks']):3d} chars={d['chars']}")
    print(f"写入: {args.input_dir}/../{args.output}" if False else f"写入: {args.output}")


if __name__ == "__main__":
    main()
