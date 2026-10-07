#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Problem Intent Classifier & Specialized Model Router (问题分类与两级模型/技能路由分发引擎)
Frontier Tech Industrial Analysis Engine (v4.5.0)

Two-Tier Dispatch Architecture:
Tier 1: Macro Domain & Model Pipeline Routing (TECH / INDUSTRY / COMPANY / POLICY / INTEL / CAPITAL / SYNTHESIS)
Tier 2: Fine-Grained Skill Selection & Occam's Razor Pruning (Minimal Sufficient Skill Set vs Extraneous Pruned Skills)
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

from methodology_aliases import METHODOLOGY_ALIASES, canonical_for_text, TERM_TO_CANONICAL
from decision_heuristics import heuristics_for_topics

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class ProblemRouter:
    def __init__(self, config_path: str = None, llm_normalize=None, semantic=None):
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = Path("config/pipeline_config.json")

        # 缺陷1可选增强：LLM 规范化重写开关（默认关，保持纯离线确定性）
        # 开启时把口语 query 转成标准方法论词串再叠加召回；模型离线/失败自动回退词袋。
        self.llm_normalize = llm_normalize
        self._normalized_cache = {}
        # 边界1：语义向量检索开关（默认关）。embedding 由本地 Ollama nomic-embed-text 提供
        # （允许的外部命令依赖），向量计算纯 Python 标准库，不引入第三方库。离线时自动跳过该维度。
        self.semantic = semantic
        self._embed_cache = {}

        self.config = self._load_config()
        self.router_config = self.config.get("problem_router", {})
        # P1-2 统一配置：检索增强开关/权重/端点从 config/problem_router/retrieval 读取，
        # 用 settings 默认值做深度合并兜底（支持自定义 config_path，不回退全局路径）。
        from settings import load_retrieval_config, _DEFAULTS
        _re_enh = self.router_config.get("retrieval")
        if not isinstance(_re_enh, dict):
            _re_enh = load_retrieval_config()  # 兜底：默认段
        # 深度合并：只读 config 里显式给的键，其余用默认
        def _merge(base, over):
            out = dict(base)
            for k, v in (over or {}).items():
                if isinstance(v, dict) and isinstance(out.get(k), dict):
                    out[k] = _merge(out[k], v)
                else:
                    out[k] = v
            return out
        _re_enh = _merge(_DEFAULTS, _re_enh)
        if self.llm_normalize is None:
            self.llm_normalize = bool(_re_enh.get("llm_normalize", False))
        if self.semantic is None:
            self.semantic = bool(_re_enh.get("semantic", False))
        # 权重 / 端点从配置加载（覆盖类常量默认，供消融实验配置化）
        w = _re_enh.get("weights", {})
        self.WEIGHT_TOPIC_OVERLAP = float(w.get("topic_overlap", self.WEIGHT_TOPIC_OVERLAP))
        self.WEIGHT_KEYWORD_HIT = float(w.get("keyword_hit", self.WEIGHT_KEYWORD_HIT))
        self.WEIGHT_KEYWORD_BROAD = float(w.get("keyword_broad", self.WEIGHT_KEYWORD_BROAD))
        self.WEIGHT_SKILL_OVERLAP = float(w.get("skill_overlap", self.WEIGHT_SKILL_OVERLAP))
        self.WEIGHT_MICRO_FACT = float(w.get("micro_fact", self.WEIGHT_MICRO_FACT))
        self.TOPIC_SUPPRESS_WHEN_MICRO = float(w.get("topic_suppress_micro", self.TOPIC_SUPPRESS_WHEN_MICRO))
        ep = _re_enh.get("endpoints", {})
        self.EMBED_API = ep.get("embed_api", self.EMBED_API)
        self.EMBED_MODEL = ep.get("embed_model", self.EMBED_MODEL)
        self.LLM_API_BASE = ep.get("llm_api_base", self.LLM_API_BASE)
        self.LLM_MODEL = ep.get("llm_model", self.LLM_MODEL)
        self.categories = self.router_config.get("classification_categories", [])
        self.pipelines = self.config.get("specialized_pipelines", {})
        self.skill_signatures = self.config.get("skill_signatures", {})

        # Fallback skill signatures if config doesn't supply them
        if not self.skill_signatures:
            self.skill_signatures = self._default_skill_signatures()

        # RAG 第二级召回：特训营公理索引（惰性加载；缺失/损坏 → 空，路由保持容错）
        self.axiom_index_path = Path("rag/research/axiom_index.json")
        self.axiom_index = None

        # Keyword weights & patterns
        self.tech_keywords = [
            "技术", "原理", "算法", "良品率", "良率", "公差", "工程调优", "量产", "实验室", 
            "学术树", "硬指标", "临界点", "mtbf", "莱特定律", "学习率", "bom", "执行器", 
            "丝杠", "减速器", "电机", "散热", "芯片", "参数", "公式", "物理", "寿命", "机械",
            "自由度", "线束", "感知", "扭矩", "力控", "端到端", "vla", "驱动", "材料",
            "坦克", "单点技术", "第一性原理",
            "科技制造", "科技制造家", "工程集成", "小单快反", "柔性制造", "量产阵痛", "爬坡", "交付排队", "产线节拍", "异构计算", "软硬解耦",
            "机器智商", "脑力替代", "流程自动化", "rpa", "人效倍增", "长板协作", "系统总包", "集成商调通"
        ]
        self.industry_keywords = [
            "产业", "大周期", "渗透率", "产业链", "拓扑", "控制点", "赢家集团", "制度转换", 
            "出海", "全球化", "积木式创新", "卡洛塔", "中立节点", "双链", "地缘政治", "spac", 
            "趋势", "格局", "宏观", "行业", "普及", "爆发点", "拐点", "替代", "生态", "壁垒",
            "安装期", "展开期", "时间锥", "本土化", "跨国", "准入",
            "三方双向选择", "生产规模化", "创意规模化", "历史押韵",
            "三级扩散", "硬件-平台-应用", "扩散时序", "云原生", "敏捷供应链", "科技制造家", "高利率重估", "现金流重估", "高利率", "流动性收紧", "佩蕾丝",
            "生态繁荣", "长板协作", "新木桶理论", "总包控制点", "反全包", "大包大揽", "行为改变", "习惯改变", "观念改变", "文化出海", "长湿雪道", "长雪道"
        ]
        self.company_keywords = [
            "估值", "企业", "公司", "财报", "营收", "毛利", "pe", "ps", "股票", "团队", 
            "ceo", "空降高管", "瓦特", "伯顿", "商业模式", "订阅", "raas", "aigs", "服务化", 
            "隐含预期", "标的", "投资", "市值", "股价", "管理", "合伙人", "创始人", "净利",
            "现金流", "出货量", "市占率", "分部", "溢价", "折价", "白马", "透支",
            "数字移民", "数字原住民", "闪电战", "能力圈层", "演绎法", "归纳法失效",
            "双长制", "首席科学家", "超前信号", "超前量", "量产阵痛", "股权分配", "高利率重估", "现金流重估", "低pe陷阱", "价值陷阱", "按需付费",
            "机器智商", "脑力替代", "1人带多机", "高端服务平民化", "习惯改变", "观念改变", "长板协作", "总包控制力", "任务拆解"
        ]
        self.policy_keywords = [
            "政策", "法规", "监管", "管制", "出口管制", "关税", "地缘政治", "合规", "准入", "牌照",
            "红旗法案", "文化滞后", "长臂管辖", "反垄断", "数据跨境", "安全审查", "外国投资审查", "制裁",
            "产缘政治", "大资本利益", "大国博弈", "中美博弈", "聪明的互惠", "选举口水", "企业公民", "全球制造",
            "德州", "德克萨斯", "德州模式", "工作权", "学区", "学区减免", "财产税", "阿肯色", "本土制造", "海外建厂", "海外选址", "选址", "谈判", "选民"
        ]
        self.intelligence_keywords = [
            "学术树", "师承", "导师", "论文溯源", "科学家", "八卦", "反常信号", "狗没有叫", 
            "知乎", "吐槽", "离职", "寻与伺", "真实线索", "实验室真伪", "学术源流", "离群值", "异常信号", "归因诊断", "三步校准"
        ]
        self.capital_keywords = [
            "资本运作", "spac", "并购", "收购", "制造即投资", "二股东", "股权", "天使占位", 
            "退出机制", "pipe", "资本工具", "上市催熟", "市值管理", "战略投资三部曲", "定增", "对赌",
            "高利率", "加息", "降息", "央行加息", "央行降息", "加息节奏", "流动性释放", "双周期", "现金流重估", "价值陷阱", "低pe陷阱", "流动性收紧",
            "地缘冲突", "地缘事件", "布朗运动", "危机避险", "避险资产", "本币债务", "债务危机", "达利奥", "黄金坑", "大资本蓄水池", "黑天鹅"
        ]
        self.synthesis_keywords = [
            "全景", "全面分析", "深度研报", "1+4+6", "综合分析", "完整报告", "全套产物", 
            "基准报告", "系统分析", "全维度", "全面评估", "master", "演化模型", "母模型"
        ]

    def _load_config(self) -> dict:
        if not self.config_path.exists():
            return {}
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Failed to load config from {self.config_path}: {e}", file=sys.stderr)
            return {}

    def _default_skill_signatures(self) -> dict:
        return {
            "geopolitical-deconstruction": {
                "name_zh": "大国政治与政党更迭理性穿透框架",
                "keywords": ["大选", "选举", "口水", "选举口水", "大资本利益", "聪明的互惠", "smart reciprocity", "对等性", "reciprocity", "单边关税", "出口管制", "实体清单", "中美博弈", "产缘政治", "结构性封锁", "法案豁免", "商业豁免", "脱钩"]
            },
            "global-corporate-citizen": {
                "name_zh": "西方地方政治与政商博弈落地框架",
                "keywords": ["德州", "德克萨斯", "学区", "isd", "财产税", "税收减免", "312", "313", "工作权", "企业公民", "海外建厂", "海外选址", "选民交差", "made in america by china", "made by chinese", "工会", "地方政治", "阿肯色", "本土雇佣", "社区赞助"]
            },
            "macro-crisis-immunity": {
                "name_zh": "地缘冲突与主权政治避险框架",
                "keywords": ["地缘冲突", "俄乌", "战争", "黑天鹅", "布朗运动", "避险", "避险资产", "本币债务", "债务危机", "达利奥", "黄金坑", "大资本蓄水池", "央行加息", "央行降息", "加息节奏", "流动性释放", "金融制裁", "资产冻结", "抗审查", "数字资产", "btc"]
            }
        }

    def _resolve_fine_grained_skills(self, query: str, pipeline_id: str, pipeline_skills: list) -> dict:
        """
        Tier 2: Fine-grained Skill Scoring, Ranking & Occam's Razor Pruning
        """
        q_lower = query.lower()
        skill_scores = {}
        skill_hits = {}

        for skill_id, meta in self.skill_signatures.items():
            kws = meta.get("keywords", [])
            hits = [kw for kw in kws if kw in q_lower]
            if hits:
                # Score based on hit count and specificity (longer keywords carry higher diagnostic value)
                score = sum(1.0 + 0.25 * len(kw) for kw in hits)
                # Boost if skill belongs to the designated pipeline
                if skill_id in pipeline_skills:
                    score *= 1.2
                skill_scores[skill_id] = round(score, 2)
                skill_hits[skill_id] = hits

        # Rank all matched skills
        ranked = sorted(skill_scores.items(), key=lambda x: x[1], reverse=True)

        primary = []
        secondary = []

        if ranked:
            # Top-1 is always primary
            primary.append(ranked[0][0])
            for sid, s in ranked[1:]:
                # Strong additional hits qualify as primary (up to 3)
                if s >= 2.0 and len(primary) < 3:
                    primary.append(sid)
                elif len(secondary) < 2:
                    secondary.append(sid)

            # Ensure we have at least 1 secondary skill if pipeline offers good complement
            if not secondary:
                for ps in pipeline_skills:
                    if ps not in primary and ps not in secondary:
                        secondary.append(ps)
                        if len(secondary) >= 2:
                            break
        else:
            # Generic fallback: pick top 2 pipeline default skills as primary
            primary = pipeline_skills[:2] if len(pipeline_skills) >= 2 else pipeline_skills
            secondary = pipeline_skills[2:4] if len(pipeline_skills) >= 4 else []

        # Occam's Razor Pruning: Skills defined in the pipeline template that were NOT triggered
        pruned = [s for s in pipeline_skills if s not in primary and s not in secondary]

        # Formulate rationale
        hit_summaries = []
        for s in primary:
            name_zh = self.skill_signatures.get(s, {}).get("name_zh", s)
            hits = skill_hits.get(s, [])
            if hits:
                hit_summaries.append(f"{s} (匹配关键词: {', '.join(hits)})")
            else:
                hit_summaries.append(f"{s} (基准管线主导技能)")

        if hit_summaries:
            rationale = f"核心因果驱动技能: {'; '.join(hit_summaries)}。基于奥卡姆剃刀剪枝排除 {len(pruned)} 个弱因果关联管线预设技能。"
        else:
            rationale = f"未检测到强单一技能指纹，默认激活管线核心基准技能。剪枝排除 {len(pruned)} 个冗余技能。"

        verdict = "FULL_PANORAMA" if pipeline_id == "full_synthesis_pipeline" else "MINIMAL_SUFFICIENT"

        return {
            "targeted_skills": primary + secondary,
            "primary_skills": primary,
            "secondary_skills": secondary,
            "pruned_skills": pruned,
            "skill_match_scores": skill_scores,
            "skill_hits": skill_hits,
            "skill_selection_rationale": rationale,
            "minimality_sufficiency_verdict": verdict
        }

    def route(self, query: str) -> dict:
        """
        Classifies query into one of:
        - TECH_FEASIBILITY
        - INDUSTRY_TOPOLOGY
        - COMPANY_VALUATION
        - MACRO_POLICY_REGULATION
        - INTELLIGENCE_SCOUTING
        - CAPITAL_TRANSACTION
        - FULL_SYNTHESIS
        """
        q_lower = query.lower()

        # Check for explicit FULL_SYNTHESIS triggers first
        synthesis_hits = [kw for kw in self.synthesis_keywords if kw in q_lower]
        if len(synthesis_hits) >= 1:
            return self._build_decision(
                query=query,
                category="FULL_SYNTHESIS",
                confidence=0.95,
                scores={"FULL_SYNTHESIS": 3.0},
                matched_keywords={"FULL_SYNTHESIS": synthesis_hits},
                reason="Query explicitly requested full panoramic / comprehensive 1+4+6 analysis"
            )

        # Count keyword hits with weighting
        tech_hits = [kw for kw in self.tech_keywords if kw in q_lower]
        ind_hits = [kw for kw in self.industry_keywords if kw in q_lower]
        comp_hits = [kw for kw in self.company_keywords if kw in q_lower]
        pol_hits = [kw for kw in self.policy_keywords if kw in q_lower]
        intel_hits = [kw for kw in self.intelligence_keywords if kw in q_lower]
        cap_hits = [kw for kw in self.capital_keywords if kw in q_lower]

        score_tech = float(len(tech_hits))
        score_ind = float(len(ind_hits))
        score_comp = float(len(comp_hits))
        score_pol = float(len(pol_hits))
        score_intel = float(len(intel_hits))
        score_cap = float(len(cap_hits))

        # Boost specific high-confidence indicator phrases
        if any(w in q_lower for w in ["丝杠", "减速器", "mtbf", "莱特定律", "学习率", "良率", "散热", "公差", "科技制造家", "小单快反", "异构计算", "机器智商", "脑力替代", "rpa"]):
            score_tech += 2.5
        if any(w in q_lower for w in ["大周期", "双链", "控制点", "卡洛塔", "制度转换", "出海", "三级扩散", "展开期", "敏捷供应链", "佩蕾丝", "长板协作", "新木桶理论", "反全包", "观念改变", "文化出海"]):
            score_ind += 2.5
        if any(w in q_lower for w in ["估值", "财报", "pe", "隐含预期", "ceo", "股票", "团队", "营收", "毛利", "双长制", "首席科学家", "超前信号", "1人带多机", "高端服务平民化", "习惯改变"]):
            score_comp += 2.5
        if any(w in q_lower for w in ["出口管制", "关税", "合规", "红旗法案", "文化滞后", "长臂管辖", "产缘政治", "大资本利益", "企业公民", "德州", "德州模式", "聪明的互惠", "大国博弈", "中美博弈", "学区", "学区减免", "财产税", "本土制造", "海外建厂"]):
            score_pol += 2.5
        if any(w in q_lower for w in ["学术树", "师承", "狗没有叫", "反常信号", "知乎", "吐槽", "离职"]):
            score_intel += 2.5
        if any(w in q_lower for w in ["制造即投资", "spac", "并购", "二股东", "战略投资三部曲", "高利率", "双周期", "低pe陷阱", "布朗运动", "危机避险", "避险资产", "本币债务", "债务危机", "达利奥", "黄金坑", "地缘冲突", "地缘事件", "央行加息", "央行降息", "加息节奏", "流动性释放"]):
            score_cap += 2.5

        scores = {
            "TECH_FEASIBILITY": round(score_tech, 2),
            "INDUSTRY_TOPOLOGY": round(score_ind, 2),
            "COMPANY_VALUATION": round(score_comp, 2),
            "MACRO_POLICY_REGULATION": round(score_pol, 2),
            "INTELLIGENCE_SCOUTING": round(score_intel, 2),
            "CAPITAL_TRANSACTION": round(score_cap, 2)
        }

        total_score = sum(scores.values())

        # If multiple domains have strong signals, consider FULL_SYNTHESIS
        active_domains = [cat for cat, s in scores.items() if s >= 2.0]
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top1_cat, top1_score = sorted_scores[0]
        top2_cat, top2_score = sorted_scores[1]

        is_balanced_multi_domain = False
        if len(active_domains) >= 3:
            is_balanced_multi_domain = True
        elif len(active_domains) == 2 and total_score >= 6.5:
            if top2_score > 0 and (top1_score / (top1_score + top2_score)) <= 0.65:
                is_balanced_multi_domain = True

        if is_balanced_multi_domain:
            return self._build_decision(
                query=query,
                category="FULL_SYNTHESIS",
                confidence=0.90,
                scores=scores,
                matched_keywords={"TECH": tech_hits, "INDUSTRY": ind_hits, "COMPANY": comp_hits, "POLICY": pol_hits, "INTEL": intel_hits, "CAPITAL": cap_hits},
                reason="Query spans across multiple analytical domains with high balanced intensity"
            )

        # Determine winner
        if total_score == 0:
            winner = "INDUSTRY_TOPOLOGY"
            confidence = 0.50
            reason = "No dominant domain keywords found; defaulted to industry baseline"
        else:
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            winner = sorted_scores[0][0]
            confidence = round(sorted_scores[0][1] / total_score, 2)
            reason = f"Dominant signal in {winner} (score: {sorted_scores[0][1]}/{total_score})"

        return self._build_decision(
            query=query,
            category=winner,
            confidence=confidence,
            scores=scores,
            matched_keywords={"TECH": tech_hits, "INDUSTRY": ind_hits, "COMPANY": comp_hits, "POLICY": pol_hits, "INTEL": intel_hits, "CAPITAL": cap_hits},
            reason=reason
        )

    def _load_axiom_index(self) -> None:
        """Lazy-load axiom index + 微观事实补充索引。Tolerant of missing/corrupt: must never crash."""
        if self.axiom_index is not None:
            return
        base = {"documents": [], "skipped": []}
        try:
            with open(self.axiom_index_path, encoding="utf-8") as f:
                base = json.load(f)
        except Exception:
            pass
        # 边界2 + 评测地基：给每个切片注入稳定 chunk_id 与认识论类型 epistemic_type。
        # 方法论切片 = ASSUMPTION/方法论；微观事实切片(合并时)用 fact_id 作 chunk_id 标 FACT。
        # chunk_id 用于 RAG 评测 golden dataset 的 ground-truth 定位、溯源与 MRR 计算。
        for di, doc in enumerate(base.get("documents", [])):
            for ci, chunk in enumerate(doc.get("chunks", [])):
                chunk["chunk_id"] = f"D{di:03d}_C{ci:03d}"
                chunk.setdefault("epistemic_type", chunk.get("epistemic_type") or "INFERENCE")
        # 边界2：合并微观事实补充索引（行业数据，如 TSMC 封装良品率）为可检索切片
        try:
            mf = Path("rag/research/micro_facts.json")
            if mf.is_file():
                mdata = json.loads(mf.read_text(encoding="utf-8"))
                mchunks = []
                for fct in mdata.get("facts", []):
                    mchunks.append({
                        "text": fct.get("claim", ""),
                        "source": fct.get("source", "micro-fact"),
                        "topic": "微观事实(行业数据)",
                        "chunk_id": fct.get("fact_id", "FACT-UNKNOWN"),
                        "epistemic_type": "FACT",
                        "keywords": list(fct.get("keywords", [])),
                        "methodology_topics": [],
                        "skills": {"matched_skills": [], "match_detail": {}},
                        "noise_ratio": 0.0,
                        "valid_from": fct.get("valid_from"),
                        "is_micro_fact": True,
                    })
                base.setdefault("documents", []).append({
                    "filename": "micro_facts.json", "topic": "微观事实补充", "layer": "micro_fact",
                    "extracted": True, "engine": "micro_fact_ingest", "chars": 0,
                    "chunks": mchunks, "status": "INDEXED"})
        except Exception:
            pass
        self.axiom_index = base

    # 高频宽泛词：字面命中时降权，避免稀释专业术语的召回排位
    _BROAD_KEYWORDS = frozenset(["ai", "技术", "企业", "产业", "市场", "公司", "行业", "分析", "产品", "科技"])
    # 微观事实词：query 含这些词时判定为"强事实/微观问题"，应抑制方法论主题权重、保全微观事实切片
    # （修复缺陷2：避免"泛理论凌驾于微观事实之上"的召回偏置）
    _MICRO_FACT_KEYWORDS = frozenset([
        "良品率", "良率", "产能", "交付周期", "交期", "价格", "成本", "毛利", "营收", "出货量",
        "占比", "库存", "wafer", "封装", "cowos", "hbm", "nm", "制程", "带宽", "算力", "topps",
        "单颗", "单位", "汇率", "asp", "spec", "良率", "良品", "公差", "丝杠", "减速器", "电机",
        "bom", "物料", "产能爬坡", "良率爬坡",
    ])

    @classmethod
    def _keyword_weight(cls, kw: str) -> float:
        return 0.5 if kw.lower() in cls._BROAD_KEYWORDS else 1.5

    # 边界1：语义向量检索（可选，默认关）。embedding 走本地 Ollama nomic-embed-text，
    # 向量计算纯 Python 标准库。离线/失败自动返回空 bonus（退化回纯关键词）。
    EMBED_API = "http://127.0.0.1:22434/api/embed"
    EMBED_MODEL = "nomic-embed-text"

    def _embed(self, text: str):
        if text in self._embed_cache:
            return self._embed_cache[text]
        try:
            payload = json.dumps({"model": self.EMBED_MODEL, "input": text}).encode("utf-8")
            req = urllib.request.Request(self.EMBED_API, data=payload,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                v = json.loads(resp.read().decode("utf-8"))["embeddings"][0]
            self._embed_cache[text] = v
            return v
        except Exception:
            self._embed_cache[text] = None
            return None

    @staticmethod
    def _cosine(a, b):
        import math
        if not a or not b:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        return dot / (na * nb) if na > 0 and nb > 0 else 0.0

    def _semantic_bonus(self, query_emb, chunk_text: str, cap: float = 0.9) -> float:
        """返回 query 与切片的语义相似度（0~cap），作为叠加分。query_emb 或切片无向量时返回 0。"""
        if not self.semantic or query_emb is None:
            return 0.0
        chunk_emb = self._embed(chunk_text)
        if chunk_emb is None:
            return 0.0
        return min(self._cosine(query_emb, chunk_emb), cap)

    # 缺陷1可选增强：LLM 规范化重写 —— 把用户口语 query 提取为 3-5 个标准方法论词串，
    # 叠加到召回（默认关闭，开启时模型离线/失败自动回退词袋，绝不影响纯离线确定性）。
    LLM_API_BASE = "http://127.0.0.1:22434/v1"
    LLM_MODEL = "qwen2.5-benchmark"
    LLM_GATHER_CANONICALS = sorted(TERM_TO_CANONICAL.keys())

    def normalize_query_with_llm(self, query: str) -> list:
        """尝试用本地 LLM 把 query 转成方法论标准词串；失败/离线返回 []（调用方回退词袋）。

        结果与原始 query 叠加（扩展而非替换），故即使模型输出不准也不会丢失原始匹配。
        Prompt 要求穷举匹配本系统已知方法论词表，输出为纯词串（简化解析）。
        """
        if not self.llm_normalize:
            return []
        if query in self._normalized_cache:
            return self._normalized_cache[query]
        # 采样系统词表（避免 prompt 过长，取每主题代表词）
        vocab = list(TERM_TO_CANONICAL.keys())[:80]
        system = (
            "你是产业投研术语标准化助手。请阅读用户对产业现象/方法的口语化描述，"
            "从中提取它最可能对应的 3-5 个标准方法论关键词。只从下面词表中挑选，"
            "不要造词、不要解释，用空格分隔输出，不要换行、不要引号:\n" + " ".join(vocab)
        )
        try:
            payload = {
                "model": self.LLM_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": query},
                ],
                "temperature": 0.0,
            }
            req = urllib.request.Request(
                self.LLM_API_BASE + "/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "Authorization": "Bearer ollama"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                content = result["choices"][0]["message"]["content"]
            tokens = [t for t in re.split(r"[\s,，、;；]+", content) if t]
            normalized = tokens[:6]
            self._normalized_cache[query] = normalized
            return normalized
        except Exception:
            # 模型离线/超时/解析失败：自动回退词袋（不改动原始 query）
            self._normalized_cache[query] = []
            return []

    def _effective_query(self, query: str) -> str:
        """返回实际用于召回的 query：原始 query 可叠加 LLM 规范化词串（增强而非替换）。"""
        norm = self.normalize_query_with_llm(query)
        return (query + " " + " ".join(norm)).strip() if norm else query

    # 缺陷2修复：权重参数化（魔数 → 可配置常量，便于消融实验与调参）
    WEIGHT_TOPIC_OVERLAP = 3.0      # 切片命中 query 的方法论主题
    WEIGHT_KEYWORD_HIT = 1.5        # query 与切片技能关键词字面重合
    WEIGHT_KEYWORD_BROAD = 0.5      # 宽泛词命中
    WEIGHT_SKILL_OVERLAP = 1.2      # 切片命中技能与路由技能重合
    WEIGHT_MICRO_FACT = 2.0         # 微观事实型 query 时，事实词命中额外加权
    TOPIC_SUPPRESS_WHEN_MICRO = 0.4  # 微观事实型 query 时，方法论主题权重的抑制系数

    @classmethod
    def is_micro_fact_query(cls, query: str) -> bool:
        """判断 query 是否为"强事实/微观"型问题（涉及具体技术指标/经营数据）。"""
        q = query.lower()
        return any(w in q for w in cls._MICRO_FACT_KEYWORDS)

    # Step1-P0：时间戳优先(Time Superseding)。微观事实切片按 valid_from 新度倾斜，
    # 旧数据自动降权（不淘汰），杜绝"拿明朝的剑斩清朝的官"。
    TIME_SCALE_YEAR = 8.0        # 距今每早一年，微观事实切片减这么多分（上限被 TRUNC 约束）
    TIME_MAX_PENALTY = 2.5       # 时间衰减最大惩罚（避免老旧但唯一的事实被彻底压掉）

    @staticmethod
    def _time_penalty(valid_from: str) -> float:
        """按 valid_from 距今多少年给惩罚分（0=时鲜，越大越旧）。解析失败→最大惩罚。"""
        if not valid_from:
            return ProblemRouter.TIME_MAX_PENALTY
        y = ""
        for ch in valid_from:
            if ch.isdigit() or ch == "-":
                y += ch
        try:
            year = int(y[:4])
        except Exception:
            return ProblemRouter.TIME_MAX_PENALTY
        now = 2026  # 当前基准年（项目运行日期）
        age = max(0, now - year)
        return min(age * (ProblemRouter.TIME_SCALE_YEAR / 2), ProblemRouter.TIME_MAX_PENALTY)

    def retrieve_axioms(self, query: str, skill_hits: list, limit: int = 3) -> list:
        """第二级召回：从特训营公理索引召回 top-N 切片，三重打分维度：

        1. 方法论主题/别名召回（跨字面）：query 命中某方法论主题的别名（如"佩蕾丝/卡洛塔/资本周期/安装期"
           → canonical"佩蕾丝技术资本周期"），则切片带该主题时显著加权 ×3.0。这是方案B的核心，让
           "佩蕾丝"与字面不同的同类表述互相命中。
        2. 技能关键词命中（原逻辑）：query 与切片技能关键词字面重合 ×1.5（宽泛词 ×0.5 降权）。
        3. 技能重合：切片命中技能与路由技能交集 ×1.2。

        纯关键词 + 规则加权（验证路径 stdlib-only 铁律；无向量嵌入）。
        返回 {text, highlight, source, topic, matched_skills, matched_keywords, methodology_topics, score}。
        """
        self._load_axiom_index()
        docs = (self.axiom_index or {}).get("documents", [])
        if not docs:
            return []
        # 缺陷1可选增强：q_eff = 原始 query 叠加 LLM 规范化词串（默认/离线时 == query）
        q_eff = self._effective_query(query)
        q_lower = q_eff.lower()
        # 边界1：语义向量检索（可选开关）。仅当开启且 embedding 可用时才计算一次 query 向量。
        q_emb = self._embed(q_eff) if self.semantic else None
        skill_hit_set = set(skill_hits or [])
        # 归一 q_eff 到方法论 canonical 主题：同时命中学名(Level1)与现象词(Level2)+LLM 规范词。
        # 解决"专有名词断裂"——用户描述现象(泡沫破裂/路网留下)也能归一到佩蕾丝周期。
        q_topics = set(canonical_for_text(q_eff)["canonical_topics"])
        # 缺陷2修复：若为"强事实/微观"型 query，抑制方法论主题权重，保全微观事实切片
        is_micro = self.is_micro_fact_query(query)
        scored = []
        for doc in docs:
            for chunk in doc.get("chunks", []):
                text = chunk.get("text", "")
                kws = chunk.get("keywords", [])
                # (2) 技能关键词字面命中（参数化）
                score = 0.0
                hit_kws = []
                for kw in kws:
                    if kw and kw.lower() in q_lower:
                        w = self._keyword_weight(kw)
                        # 微观事实 query 时，事实类词命中额外加权（保护微观事实不被主题挤出）
                        if is_micro and any(f in kw.lower() for f in self._MICRO_FACT_KEYWORDS):
                            w += self.WEIGHT_MICRO_FACT
                        score += w
                        hit_kws.append(kw)
                # (1) 方法论主题/别名：切片带 query 命中的 canonical 主题 → 强加权（参数化 + 微观抑制）
                chunk_topics = set(chunk.get("methodology_topics", []))
                topic_overlap = q_topics & chunk_topics
                if topic_overlap:
                    topic_w = self.WEIGHT_TOPIC_OVERLAP
                    if is_micro:
                        topic_w *= self.TOPIC_SUPPRESS_WHEN_MICRO
                    score += topic_w * len(topic_overlap)
                # (3) 技能重合（跨字面回退，保证产业类查询仍有主题相关结果）
                matched_skills = chunk.get("skills", {}).get("matched_skills", [])
                overlap = set(matched_skills) & skill_hit_set
                if overlap:
                    score += self.WEIGHT_SKILL_OVERLAP * len(overlap)
                # 缺陷3修复：低信噪比切片降权（口语口水话稀释 Tier 1 上下文）
                noise = chunk.get("noise_ratio", 0.0)
                if noise > 0.55:
                    score *= 0.5
                # 边界1：语义向量召回加分（可选开关）。仅对未被主题强命中的切片追加，
                # 避免重复叠加；中文同义(封装良品率↔良品率爬坡)效果好，跨语言弱由词袋兜底。
                if self.semantic and not topic_overlap:
                    score += self._semantic_bonus(q_emb, text)
                # Step1-P0：时间戳优先。仅对微观事实切片生效——旧数据降权(不淘汰)，
                # 但若该切片事实词命中了 query，仍保持其可召回性。
                vf = chunk.get("valid_from")
                if is_micro and vf:
                    score -= self._time_penalty(vf)
                if score <= 0 and not hit_kws and not topic_overlap:
                    continue
                # 高亮定位：优先命中 query 别名，其次命中关键词/技能词
                highlight = text
                radius = 120
                focus = None
                for t_op in topic_overlap:  # chunk 的 canonical 主题词
                    focus = t_op
                    break
                search_terms = hit_kws or list(overlap) or ([focus] if focus else [])
                for kw in search_terms:
                    idx = text.lower().find(kw.lower())
                    if idx != -1:
                        start = max(0, idx - radius)
                        end = min(len(text), idx + len(kw) + radius)
                        highlight = text[start:end]
                        break
                scored.append({
                    "text": text,
                    "highlight": highlight,
                    "source": chunk.get("source", ""),
                    "topic": chunk.get("topic", ""),
                    "methodology_topics": sorted(chunk_topics),
                    "matched_skills": matched_skills[:3],
                    "matched_keywords": hit_kws[:5],
                    "valid_from": chunk.get("valid_from"),
                    # 评测地基：透传稳定 chunk_id 与认识论类型（供 RAG golden 评测 MRR/Hit 定位）
                    "chunk_id": chunk.get("chunk_id", ""),
                    "epistemic_type": chunk.get("epistemic_type", "INFERENCE"),
                    # 决策型认知RAG：该切片命中的方法论主题对应的战术决策卡（No Action, No Index）
                    "decision_heuristics": heuristics_for_topics(sorted(chunk_topics)),
                    "score": round(score, 2),
                })
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]

    def _build_decision(self, query: str, category: str, confidence: float, scores: dict, matched_keywords: dict, reason: str,
                        retrieved_axioms: list = None) -> dict:
        pipeline_map = {
            "TECH_FEASIBILITY": "tech_pipeline",
            "INDUSTRY_TOPOLOGY": "industry_pipeline",
            "COMPANY_VALUATION": "company_pipeline",
            "MACRO_POLICY_REGULATION": "policy_pipeline",
            "INTELLIGENCE_SCOUTING": "intelligence_pipeline",
            "CAPITAL_TRANSACTION": "capital_pipeline",
            "FULL_SYNTHESIS": "full_synthesis_pipeline"
        }
        pipeline_id = pipeline_map.get(category, "industry_pipeline")
        pipeline_spec = self.pipelines.get(pipeline_id, {})
        pipeline_default_skills = pipeline_spec.get("active_skills", [])

        # Execute Tier 2 Fine-Grained Skill Resolution
        skill_res = self._resolve_fine_grained_skills(query, pipeline_id, pipeline_default_skills)

        # Tier 2 RAG 召回：以路由命中的技能为锚，从特训营公理索引召回切片。
        # 显式传入的 retrieved_axioms（如外部契约）优先；否则基于技能交集计算。
        if retrieved_axioms is None:
            retrieved_axioms = self.retrieve_axioms(query, skill_res["targeted_skills"])

        cat_meta = next((c for c in self.categories if c.get("category") == category), {})

        return {
            "query": query,
            "category": category,
            "category_name_zh": cat_meta.get("name_zh", category),
            "confidence": confidence,
            "scores": scores,
            "reason": reason,
            "pipeline_id": pipeline_id,
            "pipeline_name_zh": pipeline_spec.get("name_zh", pipeline_id),
            "target_domain": pipeline_spec.get("target_domain", category),
            "recommended_model_profile": pipeline_spec.get("recommended_model_profile", {}),
            # Keep active_skills populated with pipeline default skills for backward compatibility
            "active_skills": pipeline_default_skills,
            "pipeline_skills": pipeline_default_skills,
            # Tier 2 Fine-Grained Resolution deliverables
            "targeted_skills": skill_res["targeted_skills"],
            "primary_skills": skill_res["primary_skills"],
            "secondary_skills": skill_res["secondary_skills"],
            "pruned_skills": skill_res["pruned_skills"],
            "skill_match_scores": skill_res["skill_match_scores"],
            "skill_selection_rationale": skill_res["skill_selection_rationale"],
            "minimality_sufficiency_verdict": skill_res["minimality_sufficiency_verdict"],
            "mandatory_gates": pipeline_spec.get("mandatory_gates", []),
            "primary_deliverable": pipeline_spec.get("primary_deliverable", "report.md"),
            "core_metrics": pipeline_spec.get("core_metrics", []),
            "matched_keywords": matched_keywords,
            # Tier 2 RAG 召回：特训营讲义公理片段（无则空列表，向后兼容）
            "retrieved_axioms": retrieved_axioms or []
        }


def format_cli_output(decision: dict) -> str:
    lines = []
    lines.append("=" * 68)
    lines.append("   PROBLEM INTENT CLASSIFIER & TWO-TIER DISPATCH DECISION")
    lines.append("=" * 68)
    lines.append(f"Query:               \"{decision['query']}\"")
    lines.append(f"Selected Category:   [{decision['category']}] ({decision['category_name_zh']})")
    lines.append(f"Routing Confidence:  {int(decision['confidence'] * 100)}%")
    lines.append(f"Decision Reason:     {decision['reason']}")
    lines.append("-" * 68)
    lines.append(f"Designated Pipeline: {decision['pipeline_id']} ({decision['pipeline_name_zh']})")
    
    prof = decision.get("recommended_model_profile", {})
    lines.append(f"Model Role:          {prof.get('model_role', 'N/A')}")
    lines.append(f"Model Traits:        {prof.get('model_characteristics', 'N/A')}")
    lines.append(f"Example Models:      {', '.join(prof.get('example_models', []))}")
    lines.append("-" * 68)
    lines.append(f"Targeted Skills ({decision['minimality_sufficiency_verdict']}):")
    lines.append(f"  ★ Primary Skills ({len(decision['primary_skills'])}):")
    for s in decision["primary_skills"]:
        lines.append(f"      - {s}")
    lines.append(f"  ☆ Secondary Skills ({len(decision['secondary_skills'])}):")
    for s in decision["secondary_skills"]:
        lines.append(f"      - {s}")
    if decision["pruned_skills"]:
        lines.append(f"  ✗ Pruned Pipeline Skills ({len(decision['pruned_skills'])}):")
        lines.append(f"      - {', '.join(decision['pruned_skills'])}")
    lines.append(f"Selection Rationale: {decision['skill_selection_rationale']}")
    lines.append("-" * 68)
    lines.append(f"Mandatory Gates:     {', '.join(decision['mandatory_gates'])}")
    lines.append(f"Primary Deliverable: {decision['primary_deliverable']}")
    lines.append(f"Core Metrics:        {', '.join(decision['core_metrics'])}")
    # Tier 2 RAG 召回：特训营讲义公理片段（方法论主题 + 关键词 + 来源 + 高亮）
    axioms = decision.get("retrieved_axioms") or []
    if axioms:
        lines.append("-" * 68)
        lines.append(f"Retrieved Axioms (RAG / 特训营讲义公理召回, {len(axioms)}):")
        for i, a in enumerate(axioms, 1):
            mt = "、".join(a.get("methodology_topics") or []) or "-"
            hs = a.get("highlight") or a.get("text") or ""
            hs = hs if len(hs) <= 150 else hs[:147].rstrip() + "..."
            lines.append(f"  [{i}] (score={a.get('score', '?')}) 主题:{mt}")
            lines.append(f"      {hs.replace(chr(10), ' ')}")
            src = a.get("source", "")
            if src:
                src_short = Path(src).name if src else src
                lines.append(f"       ↳ 来源: {src_short}")
            # 决策型认知RAG：附上命中主题的战术决策卡（适用/动作/失效/门禁）
            for card in (a.get("decision_heuristics") or [])[:2]:
                lines.append(f"      ▸ 决策卡[{card.get('canonical','')}]:")
                ah = card.get("action_heuristics", {}).get("基准", "")
                if ah:
                    lines.append(f"          建议动作(基准): {ah[:90]}")
                ks = (card.get("kill_switch") or [""])[0]
                if ks:
                    lines.append(f"          失效条件(Kill-Switch): {ks[:90]}")
                gs = card.get("gates") or []
                if gs:
                    lines.append(f"          对应门禁: {', '.join(gs)}")
        lines.append("-" * 68)
    lines.append("=" * 68)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Problem Intent Classifier & Two-Tier Model/Skill Router")
    parser.add_argument("--query", "-q", type=str, required=True, help="User input question or research topic")
    parser.add_argument("--config", "-c", type=str, default=None, help="Path to pipeline_config.json")
    parser.add_argument("--json", action="store_true", help="Output raw JSON decision")
    parser.add_argument("--output", "-o", type=str, default=None, help="Save JSON decision to file")
    parser.add_argument("--llm-normalize", action="store_true", default=None,
                        help="Use local LLM to normalize colloquial query into methodology terms. "
                             "Default reads config/problem_router/retrieval_enhancements; falls back to alias bag if model offline")
    parser.add_argument("--semantic", action="store_true", default=None,
                        help="Enable semantic vector recall via local Ollama embedding. "
                             "Default reads config/problem_router/retrieval_enhancements; degrades to keyword recall if model offline")

    args = parser.parse_args()

    router = ProblemRouter(config_path=args.config, llm_normalize=args.llm_normalize,
                           semantic=args.semantic)
    decision = router.route(args.query)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(decision, f, ensure_ascii=False, indent=2)
        print(f"[SUCCESS] Saved routing decision to {out_path}")

    if args.json:
        print(json.dumps(decision, ensure_ascii=False, indent=2))
    else:
        print(format_cli_output(decision))


if __name__ == "__main__":
    main()
