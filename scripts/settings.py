# -*- coding: utf-8 -*-
"""
统一配置中心 (settings) —— config/pipeline_config.json 的单一访问入口
Frontier Tech Industrial Analysis Engine

P1-2: 把散落在 problem_router 里的检索权重/端点/开关硬编码收敛为 config 持久化配置，
统一从 config/pipeline_config.json 读取。任何脚本要读检索增强参数都走此入口，
避免改代码才能调参（为消融实验 / A/B 提供配置化地基）。

config 结构（config/pipeline_config.json → problem_router.retrieval）:
  "retrieval": {
     "semantic": bool,            # 语义向量召回（默认 false）
     "llm_normalize": bool,       # LLM 规范化（默认 false）
     "weights": {topic_overlap, keyword_hit, keyword_broad, skill_overlap, micro_fact, topic_suppress_micro},
     "endpoints": {embed_api, llm_api_base, embed_model, llm_model}
  }
缺失/损坏时提供保守默认（Fail-Closed：全部默认关、保守权重）。
"""

import json
from pathlib import Path

_CONFIG_PATH = Path("config/pipeline_config.json")

# 保守默认（与旧硬编码一致，保证无 config 段时行为不回退）
_DEFAULTS = {
    "semantic": False,
    "llm_normalize": False,
    "weights": {
        "topic_overlap": 3.0,
        "keyword_hit": 1.5,
        "keyword_broad": 0.5,
        "skill_overlap": 1.2,
        "micro_fact": 2.0,
        "topic_suppress_micro": 0.4,
    },
    "endpoints": {
        "embed_api": "http://127.0.0.1:22434/api/embed",
        "llm_api_base": "http://127.0.0.1:22434/v1",
        "embed_model": "nomic-embed-text",
        "llm_model": "qwen2.5-benchmark",
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """递归合并：override 的键覆盖 base，保留 base 中 override 未提及的键。"""
    out = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_retrieval_config() -> dict:
    """读取 problem_router.retrieval 配置段，与默认深度合并。损坏时回退默认。"""
    try:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            cfg = json.load(f)
        retrieval = cfg.get("problem_router", {}).get("retrieval", {})
    except Exception:
        retrieval = {}
    return _deep_merge(_DEFAULTS, retrieval)


def save_retrieval_config(retrieval: dict) -> None:
    """把 retrieval 配置段写回 config/pipeline_config.json（供工具/CLI 持久化调参）。"""
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        cfg = json.load(f)
    cfg.setdefault("problem_router", {})
    # 合并而非整体覆盖：保留 problem_router 其他段
    cfg["problem_router"]["retrieval"] = _deep_merge(_DEFAULTS, retrieval)
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    return