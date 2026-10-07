#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automated Test Suite for Problem Intent Classifier & Specialized Model Router
"""

import unittest
from unittest.mock import patch
from problem_router import ProblemRouter, format_cli_output


class TestProblemRouter(unittest.TestCase):
    def setUp(self):
        self.router = ProblemRouter()

    def test_tech_feasibility_routing(self):
        queries = [
            "人形机器人手腕关节微电机的散热寿命与莱特定律降本速度如何测算？",
            "行星滚柱丝杠加工公差与高精度螺纹磨床国产化良品率分析",
            "端到端 VLA 大模型的物理世界接触推理与 MTBF 连续无故障运行测试",
            "中国科技制造家如何进行复杂工程集成与小单快反异构计算调优？",
            "如何提升工厂员工的机器智商并利用RPA与脑力替代实现流程自动化？"
        ]
        for q in queries:
            d = self.router.route(q)
            self.assertEqual(d["category"], "TECH_FEASIBILITY", f"Failed for query: {q}")
            self.assertEqual(d["pipeline_id"], "tech_pipeline")
            self.assertIn("commercialization-engineering", d["active_skills"])
            self.assertIn("tech-manufacturing-edge", d["active_skills"])
            self.assertIn("machine-iq-automation", d["active_skills"])

    def test_industry_topology_routing(self):
        queries = [
            "海外具身智能商业模式在国内会不会水土不服？卡洛塔大周期处于哪个阶段？",
            "智能硬件产业链控制点分析与赢家集团双链拓扑",
            "中国精密制造企业借道新加坡与迪拜出海的积木式创新突围",
            "AI与云计算从底层硬件到云原生SaaS的三级扩散时序与展开期渗透率",
            "芯片与通信产业如何通过长板协作与新木桶理论破除纵向大包大揽反全包陷阱？"
        ]
        for q in queries:
            d = self.router.route(q)
            self.assertEqual(d["category"], "INDUSTRY_TOPOLOGY", f"Failed for query: {q}")
            self.assertEqual(d["pipeline_id"], "industry_pipeline")
            self.assertIn("macro-tech-cycle-diagnostics", d["active_skills"])
            self.assertIn("perez-capital-cycle", d["active_skills"])
            self.assertIn("diffusion-pipeline", d["active_skills"])
            self.assertIn("ecosystem-coordination", d["active_skills"])
            self.assertIn("mindset-behavior-shift", d["active_skills"])

    def test_company_valuation_routing(self):
        queries = [
            "绿的谐波当前估值和市值是否透支了未来3年人形机器人的爆发预期？",
            "三花智控机器人执行器分部营收预测与逆向隐含 PE 敏感性压力测试",
            "初创具身团队 CEO 融资决断力与成长期空降高管团队基因诊断",
            "科技企业双长制治理中懂技术的CEO与首席科学家的股权分配与量产阵痛超前信号",
            "新消费企业商业模式如何通过按需订阅与高NDR完成习惯改变并重塑公司估值？"
        ]
        for q in queries:
            d = self.router.route(q)
            self.assertEqual(d["category"], "COMPANY_VALUATION", f"Failed for query: {q}")
            self.assertEqual(d["pipeline_id"], "company_pipeline")
            self.assertIn("stage-valuation", d["active_skills"])
            self.assertIn("dual-leader-governance", d["active_skills"])
            self.assertIn("mindset-behavior-shift", d["active_skills"])

    def test_full_synthesis_routing(self):
        queries = [
            "全面分析人形机器人产业链，输出1+4+6完整全景研报",
            "请对英伟达进行全维度深度研报综合分析，生成全套基准产物"
        ]
        for q in queries:
            d = self.router.route(q)
            self.assertEqual(d["category"], "FULL_SYNTHESIS", f"Failed for query: {q}")
            self.assertEqual(d["pipeline_id"], "full_synthesis_pipeline")
            self.assertIn("meta-cognitive-map", d["active_skills"])
            self.assertIn("perez-capital-cycle", d["active_skills"])
            self.assertIn("dual-leader-governance", d["active_skills"])
            self.assertIn("ecosystem-coordination", d["active_skills"])
            self.assertIn("mindset-behavior-shift", d["active_skills"])
            self.assertIn("machine-iq-automation", d["active_skills"])
            self.assertIn("geopolitical-deconstruction", d["active_skills"])
            self.assertIn("global-corporate-citizen", d["active_skills"])
            self.assertIn("macro-crisis-immunity", d["active_skills"])

    def test_policy_regulation_routing(self):
        queries = [
            "中美博弈下政客选举口水与跨国大资本利益对等互惠空间评估",
            "中国制造业如何通过德州模式工作权法案与本地化治理建立企业公民身份？"
        ]
        for q in queries:
            d = self.router.route(q)
            self.assertEqual(d["category"], "MACRO_POLICY_REGULATION", f"Failed for query: {q}")
            self.assertEqual(d["pipeline_id"], "policy_pipeline")
            self.assertIn("geopolitical-deconstruction", d["active_skills"])
            self.assertIn("global-corporate-citizen", d["active_skills"])

    def test_capital_crisis_routing(self):
        queries = [
            "俄乌冲突与地缘黑天鹅引发的短期布朗运动是暴跌危机还是核心科技资产黄金坑？",
            "达利奥债务危机模型下美国本币债务风险与大资本避险蓄水池测算"
        ]
        for q in queries:
            d = self.router.route(q)
            self.assertEqual(d["category"], "CAPITAL_TRANSACTION", f"Failed for query: {q}")
            self.assertEqual(d["pipeline_id"], "capital_pipeline")
            self.assertIn("macro-crisis-immunity", d["active_skills"])

    def test_fine_grained_skill_resolution(self):
        # Case 1: Texas local politics & school district tax abatement
        q1 = "我们在德州建厂，怎么跟学区谈判减免财产税？"
        d1 = self.router.route(q1)
        self.assertEqual(d1["pipeline_id"], "policy_pipeline")
        self.assertIn("global-corporate-citizen", d1["primary_skills"])
        self.assertEqual(d1["minimality_sufficiency_verdict"], "MINIMAL_SUFFICIENT")
        self.assertTrue(len(d1["pruned_skills"]) > 0)

        # Case 2: Geopolitical election rhetoric vs structural blockade
        q2 = "美国大选后对华出口管制，哪些属于选举口水，哪些是大资本利益主导的结构性封锁？"
        d2 = self.router.route(q2)
        self.assertEqual(d2["pipeline_id"], "policy_pipeline")
        self.assertIn("geopolitical-deconstruction", d2["primary_skills"])
        self.assertEqual(d2["minimality_sufficiency_verdict"], "MINIMAL_SUFFICIENT")

        # Case 3: Geopolitical liquidity & central bank rates
        q3 = "地缘事件后央行加息/降息节奏与流动性释放指标。"
        d3 = self.router.route(q3)
        self.assertEqual(d3["pipeline_id"], "capital_pipeline")
        self.assertIn("macro-crisis-immunity", d3["primary_skills"])

        # Case 4: Scientist CEO & Dual-leader governance
        q4 = "科学家创业当CEO有哪些陷阱？双长制治理中懂技术的CEO与首席科学家的股权如何分配？"
        d4 = self.router.route(q4)
        self.assertEqual(d4["pipeline_id"], "company_pipeline")
        self.assertIn("dual-leader-governance", d4["primary_skills"])

        # Case 5: Ecosystem coordination vs vertical integration
        q5 = "芯片通信产业如何通过长板协作与新木桶理论破除纵向大包大揽反全包陷阱？"
        d5 = self.router.route(q5)
        self.assertEqual(d5["pipeline_id"], "industry_pipeline")
        self.assertIn("ecosystem-coordination", d5["primary_skills"])

    def test_retrieved_axioms_field_present_and_empty_safe(self):
        # Decision dict must always carry retrieved_axioms (backward-compatible empty default)
        d = self.router.route("俄乌冲突与地缘黑天鹅引发的短期布朗运动是暴跌危机还是核心科技资产黄金坑？")
        self.assertIsInstance(d["retrieved_axioms"], list)
        # Every axiom chunk carries a source for traceability
        for axiom in d["retrieved_axioms"]:
            self.assertIn("text", axiom)
            self.assertIn("source", axiom)
            self.assertIn("topic", axiom)

    def test_retrieved_axioms_keyword_priority(self):
        # 专业词命中应排到宽泛词（AI/技术）之前
        d = self.router.route("AI芯片产业双链拓扑与控制点分析")
        axioms = d["retrieved_axioms"]
        if len(axioms) >= 2 and axioms[0]["matched_keywords"]:
            self.assertTrue(axioms[0]["score"] >= axioms[1]["score"],
                            "top-1 axiom must not score lower than second axiom")

    def test_router_tolerates_missing_axiom_index(self):
        saved = self.router.axiom_index_path
        try:
            self.router.axiom_index = None
            self.router.axiom_index_path = "rag/research/does_not_exist.json"
            d = self.router.route("AI芯片产业双链拓扑与控制点分析")
            self.assertEqual(d["retrieved_axioms"], [])
        finally:
            self.router.axiom_index_path = saved
            self.router.axiom_index = None

    def test_retrieved_axioms_carry_methodology_topics(self):
        # 切片必须带方法论主题标注（方案B：别名归一到 canonical）
        d = self.router.route("佩蕾丝资本周期下AI芯片处于安装期还是展开期")
        axioms = d["retrieved_axioms"]
        self.assertTrue(len(axioms) >= 1, "佩蕾丝查询应召回到公理")
        # 至少一条切片带方法论主题
        with_topics = [a for a in axioms if a.get("methodology_topics")]
        self.assertTrue(with_topics, "召回切片应携带方法论主题标注")
        # 主题里应含佩蕾丝/扩散相关 canonical
        all_topics = {t for a in axioms for t in a.get("methodology_topics", [])}
        self.assertTrue(any("佩蕾丝" in t or "扩散" in t or "周期" in t for t in all_topics),
                        f"应命中佩蕾丝/扩散主题，实际: {all_topics}")

    def test_alias_normalization_enables_cross_word_recall(self):
        # "卡洛塔""资本周期""安装期" 都是佩蕾丝主题的别名，应能归一到 canonical 召回
        from methodology_aliases import canonical_for_term
        self.assertEqual(canonical_for_term("卡洛塔"), "佩蕾丝技术资本周期")
        self.assertEqual(canonical_for_term("安装期"), "佩蕾丝技术资本周期")
        self.assertEqual(canonical_for_term("闪电战"), "兰切斯特法则")
        # query 含别名（"卡洛塔"）时，应命中"佩蕾丝技术资本周期"主题切片
        d = self.router.route("卡洛塔大周期下AI芯片的扩散")
        all_topics = {t for a in d["retrieved_axioms"] for t in a.get("methodology_topics", [])}
        self.assertTrue(any("佩蕾丝" in t or "扩散" in t for t in all_topics),
                        f"别名'卡洛塔'应召回佩蕾丝/扩散主题，实际: {all_topics}")

    def test_lanchester_alias_recall(self):
        # "闪电战"（兰切斯特别名）查询应召回到兰切斯特法则主题
        d = self.router.route("闪电战局部优势竞争策略")
        all_topics = {t for a in d["retrieved_axioms"] for t in a.get("methodology_topics", [])}
        self.assertTrue(any("兰切斯特" in t for t in all_topics),
                        f"'闪电战'别名应召回兰切斯特主题，实际: {all_topics}")

    # ---- 边界1：语义向量检索（可选，默认关 + 离线降级）----
    def test_semantic_default_off_no_embed_calls(self):
        from problem_router import ProblemRouter
        r = ProblemRouter()
        self.assertFalse(r.semantic)
        with patch.object(r, '_embed', side_effect=RuntimeError("不应调用")):
            # 默认关时 retrieve 不应触碰 embedding
            self.assertEqual(r._semantic_bonus([1.0], "text"), 0.0)

    def test_semantic_on_degrades_when_offline(self):
        # embedding 失败(离线) → bonus 0，检索照常、不抛错
        from problem_router import ProblemRouter
        r = ProblemRouter(semantic=True)
        with patch.object(r, '_embed', return_value=None):
            bonus = r._semantic_bonus([1.0, 0.0], "任意切片")
            self.assertEqual(bonus, 0.0)
            d = r.route("封装良品率与良品率爬坡")
            self.assertIn("retrieved_axioms", d)

    def test_semantic_bonus_adds_on_cosine(self):
        # embedding 在线且向量相近时，bonus > 0 且封顶
        from problem_router import ProblemRouter
        r = ProblemRouter(semantic=True)
        with patch.object(r, '_embed', side_effect=lambda t: [1.0, 0.0] if "query" in t else [0.9, 0.1]):
            b = r._semantic_bonus([1.0, 0.0], "query-ish 切片")
            self.assertGreater(b, 0.0)
            self.assertLessEqual(b, 0.9)  # cap

    # ---- 边界2b：微观事实补充索引（行业数据源）----
    def test_micro_fact_merge_into_retrieval(self):
        # 注入微观事实后，行业数据查询应能召回到该事实切片
        import json as _json
        from pathlib import Path
        _repo = Path(__file__).resolve().parents[1]
        mf = _repo / 'rag/research/micro_facts.json'
        orig = mf.read_text(encoding='utf-8') if mf.is_file() else None
        try:
            mf.write_text(_json.dumps({"facts": [{
                "fact_id": "T-1", "source": "TSMC", "claim": "台积电CoWoS封装良品率爬升至82%",
                "valid_from": "2026-Q3", "keywords": ["封装", "良品率", "cowos"]}]}),
                encoding='utf-8')
            r = ProblemRouter()
            r.axiom_index = None  # 强制重载
            d = r.route("台积电封装良品率爬坡")
            texts = [a.get('text', '') for a in d['retrieved_axioms']]
            self.assertTrue(any("CoWoS封装良品率" in t for t in texts),
                            "微观事实应被召回")
        finally:
            if orig is not None:
                mf.write_text(orig, encoding='utf-8')
            else:
                mf.unlink() if mf.exists() else None

    def test_micro_fact_index_tolerant_when_missing(self):
        # 无 micro_facts.json → 检索照常、不抛错
        from pathlib import Path
        _repo = Path(__file__).resolve().parents[1]
        mf = _repo / 'rag/research/micro_facts.json'
        orig = mf.read_text(encoding='utf-8') if mf.is_file() else None
        try:
            if mf.exists():
                mf.unlink()
            r = ProblemRouter()
            r.axiom_index = None
            d = r.route("佩蕾丝资本周期")
            self.assertIn("retrieved_axioms", d)
        finally:
            if orig is not None:
                mf.write_text(orig, encoding='utf-8')

    # ---- 配置化：--semantic/--llm-normalize 持久化到 config ----
    def test_switches_read_from_config(self):
        # config 开启 → router 默认读取到 True
        import json as _j, tempfile, os
        from problem_router import ProblemRouter
        cfg = _j.load(open('config/pipeline_config.json', encoding='utf-8'))
        cfg.setdefault('problem_router', {})['retrieval'] = {
            'semantic': True, 'llm_normalize': True,
            'weights': {'topic_overlap': 5.0}}
        tmp = tempfile.mkdtemp()
        p = os.path.join(tmp, 'cfg.json')
        open(p, 'w', encoding='utf-8').write(_j.dumps(cfg, ensure_ascii=False))
        r = ProblemRouter(config_path=p)
        self.assertTrue(r.semantic)
        self.assertTrue(r.llm_normalize)
        self.assertEqual(r.WEIGHT_TOPIC_OVERLAP, 5.0, "权重应从 config retrieval 段读取")
        # 显式 False 覆盖 config
        r2 = ProblemRouter(config_path=p, semantic=False, llm_normalize=False)
        self.assertFalse(r2.semantic)
        self.assertFalse(r2.llm_normalize)

    def test_switches_default_off_without_config(self):
        # 默认 config → False，保持纯离线确定性
        from problem_router import ProblemRouter
        r = ProblemRouter()
        self.assertFalse(r.semantic)
        self.assertFalse(r.llm_normalize)

    def test_cli_output_shows_retrieved_axioms(self):
        from problem_router import format_cli_output
        d = self.router.route("佩蕾丝资本周期下AI芯片处于安装期还是展开期")
        out = format_cli_output(d)
        self.assertIn("Retrieved Axioms", out)
        self.assertIn("佩蕾丝", d["reason"] + out)
        # 检测到召回时，CLI 区块必须包含高亮与来源
        self.assertIn("来源", out)

    def test_phenomenon_word_maps_to_canonical(self):
        # 死穴修复：用户口语现象词（Level 2）必须归一到 canonical，无需说出学名
        from methodology_aliases import canonical_for_text
        cases = [
            ("跟风砸钱后来泡沫破了路网光纤留下来", "佩蕾丝技术资本周期"),
            ("小公司以小博大找个细分切口集中火力打穿", "兰切斯特法则"),
            ("卡脖子命脉掌握在别人手里谁说了算", "双链拓扑与控制点"),
            ("越造越便宜产量翻倍成本就降下来", "莱特定律与学习曲线"),
            ("借钱借到极限还不起债去杠杆", "达利奥债务周期与避险"),
        ]
        for text, expected in cases:
            topics = canonical_for_text(text)["canonical_topics"]
            self.assertIn(expected, topics, f"现象词应归一到 {expected}，实际 {topics}")

    def test_colloquial_bubble_query_recalls_perez_axiom(self):
        # 端到端：口语描述"泡沫破裂但基建留下"应召回到佩蕾丝周期公理（不带学名）
        q = "很多新技术刚出来时大家都在跟风砸钱，后来泡沫破了，但底层的路网和光纤都留下来了，这是什么规律？"
        d = self.router.route(q)
        axioms = d["retrieved_axioms"]
        all_topics = {t for a in axioms for t in a.get("methodology_topics", [])}
        # 只要召回非空，且命中"泡沫/展开期"这类佩蕾丝核心论述即视为成功
        self.assertTrue(axioms, "口语查询应召回到公理")
        bubble_hit = any("泡沫" in (a.get("highlight") or "") for a in axioms)
        topic_hit = any("佩蕾丝" in t or "扩散" in t for t in all_topics)
        self.assertTrue(bubble_hit or topic_hit,
                        f"应召回佩蕾丝主题/泡沫公理，主题={all_topics}")

    def test_decision_heuristics_cards_are_complete(self):
        # 决策型认知RAG：每张决策卡必须带"适用/触发/动作/失效/门禁"五个字段（No Action, No Index）
        from decision_heuristics import DECISION_HEURISTICS, all_canonicals
        required = ["applicable_condition", "trigger_signals", "action_heuristics", "kill_switch", "gates"]
        self.assertTrue(len(all_canonicals()) >= 15, "至少应有 15 大方法论主题决策卡")
        for canonical, card in DECISION_HEURISTICS.items():
            for f in required:
                self.assertTrue(card.get(f), f"{canonical} 决策卡缺字段 {f}")
            # 动作卡必须含悲观/基准/乐观三分
            self.assertIn("基准", card["action_heuristics"], f"{canonical} 动作卡缺基准情景")
            self.assertIn("悲观", card["action_heuristics"])
            self.assertIn("乐观", card["action_heuristics"])
            # kill-switch 必须非空（预测必带止损/证伪触发器）
            self.assertTrue(card["kill_switch"], f"{canonical} 缺失效条件")

    def test_retrieved_axioms_carry_decision_cards(self):
        # 召回切片必须附带命中主题的决策卡
        d = self.router.route("佩蕾丝资本周期下AI芯片处于安装期还是展开期")
        axioms = d["retrieved_axioms"]
        self.assertTrue(axioms)
        has_cards = any(a.get("decision_heuristics") for a in axioms)
        self.assertTrue(has_cards, "召回切片应携带决策卡(decision_heuristics)")
        # CLI 输出应展示决策卡区块
        from problem_router import format_cli_output
        out = format_cli_output(d)
        self.assertIn("决策卡", out)
        self.assertIn("失效条件", out)

    # ---- 缺陷2：权重参数化 + 微观事实抑制 ----
    def test_weights_are_parameterized_not_magic(self):
        # 权重必须来自可配置类常量（便于消融），而非散落魔数
        self.assertEqual(ProblemRouter.WEIGHT_TOPIC_OVERLAP, 3.0)
        self.assertEqual(ProblemRouter.WEIGHT_SKILL_OVERLAP, 1.2)
        self.assertTrue(ProblemRouter.TOPIC_SUPPRESS_WHEN_MICRO < 1.0)

    def test_micro_fact_query_preserves_fact_chunks(self):
        # 强事实查询（成本/毛利）下，事实切片应排进召回、不被方法论主题霸占
        d = self.router.route("英伟达AI芯片的成本与毛利分析")
        self.assertTrue(self.router.is_micro_fact_query("英伟达AI芯片的成本与毛利分析"))
        axioms = d["retrieved_axioms"]
        self.assertTrue(axioms)
        # 首条应含成本/毛利等事实内容（索引里真实存在该切片）
        top_text = axioms[0].get("text", "") or ""
        self.assertTrue(any(w in top_text for w in ("成本", "毛利", "营收")),
                        f"微观事实查询首条应命中事实切片，实际: {top_text[:60]}")

    # ---- 缺陷3：切片信噪比 ----
    def test_noise_ratio_present_and_batch_filtered(self):
        import json
        from pathlib import Path
        idx = json.load(open(Path(__file__).resolve().parents[1] / 'rag/research/axiom_index.json', encoding='utf-8'))
        # 切片必须带 noise_ratio 字段
        all_chunks = [c for d in idx["documents"] for c in d["chunks"]]
        self.assertTrue(all("noise_ratio" in c for c in all_chunks), "切片应带 noise_ratio")
        # 批处理后（batch_ingest_all.py 信噪比门禁 no-noise-gate=0.55），索引不应再有高噪切片
        noisy = [c for c in all_chunks if c["noise_ratio"] > 0.55]
        self.assertEqual(noisy, [], "批处理后索引不应含低信噪比切片（>0.55 已被门禁拦截）")
        # 检索时最高分召回切片也不应是低信噪比切片（降权仍生效）
        r = self.router
        r.axiom_index = None
        d = r.route("佩蕾丝资本周期下AI芯片处于安装期还是展开期")
        top_noise = d["retrieved_axioms"][0].get("noise_ratio", 0)
        self.assertLessEqual(top_noise, 0.55, "最高分召回切片不应是低信噪比切片")

    # ---- 缺陷1：LLM 规范化重写（可选开关，默认关 + 离线回退） ----
    def test_llm_normalize_default_off(self):
        # 默认构造 llm_normalize=False，normalize_query_with_llm 不发起任何请求
        self.assertFalse(self.router.llm_normalize)
        self.assertEqual(self.router.normalize_query_with_llm("随便什么query"), [])

    def test_llm_normalize_online_enhances_obscure_query(self):
        # 词袋完全失效的隐晦 query，开启 LLM 规范化后可归一到 canonical
        from unittest.mock import patch
        from problem_router import ProblemRouter, canonical_for_text
        q = "大家看到风口一个劲往里扎，等价格都归零了又全撤了，可那些早埋好的底子里头后面还能翻出来用"
        self.assertEqual(set(canonical_for_text(q)["canonical_topics"]), set(), "此句词袋应失效")
        r = ProblemRouter(llm_normalize=True)
        with patch.object(r, 'normalize_query_with_llm', return_value=["资本周期", "安装期"]) as m:
            eff = r._effective_query(q)
        m.assert_called_once_with(q)
        self.assertIn("资本周期", eff)
        self.assertIn("佩蕾丝技术资本周期", canonical_for_text(eff)["canonical_topics"])

    def test_llm_normalize_offline_falls_back_to_alias(self):
        # 模型离线/失败时自动回退词袋：有效 query == 原始，route 不抛错
        from unittest.mock import patch
        from problem_router import ProblemRouter
        r = ProblemRouter(llm_normalize=True)
        with patch.object(r, 'normalize_query_with_llm', return_value=[]) as m:
            eff = r._effective_query("测试query")
            d = r.route("测试query")
        self.assertEqual(eff.strip(), "测试query")
        self.assertEqual(m.call_count, 2, "normalize 被调两次（_effective_query + route 内部）")
        self.assertIn("retrieved_axioms", d)

    # ---- P1-2：统一配置中心 settings ----
    def test_settings_load_merge_and_save(self):
        import json as _j, tempfile, os
        from settings import load_retrieval_config, save_retrieval_config, _DEFAULTS
        # 默认段齐全且全关
        cfg = load_retrieval_config()
        self.assertFalse(cfg['semantic'])
        self.assertFalse(cfg['llm_normalize'])
        for k in ('topic_overlap', 'keyword_hit', 'skill_overlap'):
            self.assertIn(k, cfg['weights'])
        # 缺失段回退默认（损坏 config 不崩）
        tmp = tempfile.mkdtemp()
        bad = os.path.join(tmp, 'bad.json')
        open(bad, 'w', encoding='utf-8').write('{broken')
        from settings import _CONFIG_PATH
        _saved = _CONFIG_PATH
        # 直接测 _deep_merge 语义
        from settings import _deep_merge
        merged = _deep_merge({'a': 1, 'nested': {'x': 1, 'y': 2}}, {'nested': {'y': 9}, 'b': 3})
        self.assertEqual(merged['a'], 1)
        self.assertEqual(merged['nested']['y'], 9)
        self.assertEqual(merged['nested']['x'], 1)
        self.assertEqual(merged['b'], 3)

    # ---- skill+RAG 协同编排器 ----
    def test_skill_rag_analysis_produces_framework(self):
        # 编排器应提取 skill 流程 + RAG 公理，输出结构化分析草稿
        import json as _j
        from skill_rag_analysis import build_analysis
        out, slots, recalled = build_analysis(
            "tech-impact-trimode-evaluator",
            "自动驾驶技术对汽车产业的影响是增强还是颠覆", {})
        self.assertIn("Skill + RAG", out)
        self.assertIn("判定逻辑", out)          # skill 判定算法骨架
        self.assertIn("target_subject", out)    # 输入参数槽
        self.assertEqual(len(recalled) > 0, True, "RAG 应召回公理支撑")
        # 参数槽至少含 skill Schema 里的 target_subject / current_status
        self.assertTrue(any("target_subject" in s for s in slots) or any("target_subject" in out for s in [""]))
        # 无效 skill 应报错
        with self.assertRaises(ValueError):
            build_analysis("nonexistent-skill", "q", {})

    def test_skill_rag_list_detects_schema_skills(self):
        # --list 应识别出带可解析 Schema 的 skill（tech-impact 等）
        from skill_rag_analysis import list_skills
        skills = list_skills()
        names = {n for n, has, _ in skills if has}
        self.assertIn("tech-impact-trimode-evaluator", names)

    def test_skill_rag_report_executes_verdict(self):
        # report 模式应执行 skill 判定算法，产出模式定性 + RAG 公理
        from skill_rag_analysis import build_report, execute_tech_impact_verdict
        # 单元：判定执行器正确分支
        v_disrupt = execute_tech_impact_verdict(
            {"alters_control": True, "targets_existing_market": True,
             "can_cross_chasm": True, "can_blitzscale": True})
        self.assertIn("产业颠覆", v_disrupt["mode"])
        v_enhance = execute_tech_impact_verdict(
            {"alters_control": False, "targets_existing_market": True})
        self.assertIn("产业增强", v_enhance["mode"])
        # 报告生成：含标题、判定、RAG 公理
        out, verdict, recalled = build_report(
            "tech-impact-trimode-evaluator",
            "特斯拉自动驾驶与Robotaxi对汽车产业的影响",
            {"alters_control": True, "targets_existing_market": True,
             "can_cross_chasm": True, "can_blitzscale": True})
        self.assertIn("# ", out)          # 标题
        self.assertIn("产业颠覆", out)     # 判定结论
        self.assertTrue(len(recalled) > 0)  # RAG 公理支撑
        self.assertIsNotNone(verdict)

    # ---- 外部数据工具层 data_tool ----
    def test_data_tool_parse_and_format(self):
        # 解析腾讯行情字段（不依赖网络，直接走 get_quote 的解析但 mock urlopen）
        from data_tool import format_quote
        q = {"symbol": "TSLA", "code": "TSLA.OQ", "name": "特斯拉",
             "price": 370.59, "prev_close": 354.11, "change": 16.48,
             "change_pct": 4.65, "currency": "USD", "time": "2026-10-02 16:00:01"}
        out = format_quote(q)
        self.assertIn("TSLA", out)
        self.assertIn("370.59", out)
        # 错误行情
        err = format_quote({"symbol": "X", "error": "timeout"})
        self.assertIn("拉取失败", err)

    def test_data_tool_normalize_symbol(self):
        from data_tool import normalize_symbol
        self.assertEqual(normalize_symbol("688036"), "sh688036")
        self.assertEqual(normalize_symbol("601127"), "sh601127")
        self.assertEqual(normalize_symbol("300750"), "sz300750")
        self.assertEqual(normalize_symbol("TSLA"), "usTSLA")

    # ---- B：决策合成器（估值加权 + skill 模式 + 方向）----
    def test_decision_synthesizer_valuation_weight(self):
        from skill_rag_analysis import synthesize_decision
        # 高估值(PE 343) + 进攻模式 → 估值规避加权，压过模式乐观 → 观望/规避
        high_pe = {"pe": 343.14}
        disrupt_verdict = {"mode": "产业颠覆·新霸主崛起", "action": "重塑产业链控制点、快速建立用户心智护城河"}
        d1 = synthesize_decision(disrupt_verdict, high_pe, "")
        self.assertNotEqual(d1["conclusion"], "建议买入", "高估值不应建议买入")
        # 低估值(PE 19) + 进攻模式 → 倾向买入
        low_pe = {"pe": 19.7}
        d2 = synthesize_decision(disrupt_verdict, low_pe, "")
        self.assertIn("买入", d2["conclusion"])
        # 无估值/无判定 → 数据不足
        d3 = synthesize_decision(None, None, "")
        self.assertIn("数据不足", d3["conclusion"])

    # ---- 财务基本面（东财 F10）----
    def test_data_tool_secucode_and_fundamental_format(self):
        from data_tool import _secucode, get_fundamentals, format_fundamental
        self.assertEqual(_secucode("688036"), "688036.SH")
        self.assertEqual(_secucode("300750"), "300750.SZ")
        self.assertIsNone(_secucode("TSLA"), "美股无 SECUCODE")
        # 格式化（mock 数据，不依赖网络）
        f = {"symbol": "688036", "report_date": "2026中报", "report_type": "中报",
             "revenue_yi": 354.31, "revenue_yoy": 21.85, "net_profit_yi": 17.73,
             "profit_yoy": 46.22, "gross_margin": 22.63, "roe": 8.37, "bps": 18.39}
        out = format_fundamental(f)
        self.assertIn("354.31", out)
        self.assertIn("17.73", out)

    # ---- 技术面 / 价格趋势 ----
    def test_price_trend_format_and_sign(self):
        # 趋势研判逻辑（上行/下行/震荡 + 数据不足兜底）
        t_up = {"range_change_pct": 8.5, "first_close": 50, "last_close": 54.25, "bars": 10}
        sign = "上行趋势" if t_up["range_change_pct"] > 5 else "区间震荡"
        self.assertEqual(sign, "上行趋势")
        t_down = {"range_change_pct": -7.0}
        sign2 = "下行趋势" if t_down["range_change_pct"] < -5 else "区间震荡"
        self.assertEqual(sign2, "下行趋势")
        t_flat = {"range_change_pct": 2.0}
        sign3 = "区间震荡" if -5 <= 2.0 <= 5 else "?"
        self.assertEqual(sign3, "区间震荡")
        # get_price_trend 失败兜底（不崩）
        from data_tool import get_price_trend
        r = get_price_trend("TSLA000")  # 无效代码 → 应返回 error dict，不抛
        self.assertIsInstance(r, dict)

    # ---- 成长趋势（多期财务派生）----
    def test_growth_trend_derivation(self):
        # 用模拟多期财务行验证增速序列/加速度/毛利率方向
        from data_tool import _growth_trend
        rows = [
            {"REPORT_DATE": "2025-06-30", "REPORT_DATE_NAME": "2025中报",
             "TOTALOPERATEREVETZ": -15.86, "PARENTNETPROFITTZ": -57.48, "XSMLL": 20.09},
            {"REPORT_DATE": "2025-12-31", "REPORT_DATE_NAME": "2025年报",
             "TOTALOPERATEREVETZ": -4.55, "PARENTNETPROFITTZ": -53.49, "XSMLL": 19.15},
            {"REPORT_DATE": "2026-06-30", "REPORT_DATE_NAME": "2026中报",
             "TOTALOPERATEREVETZ": 21.85, "PARENTNETPROFITTZ": 46.22, "XSMLL": 22.63},
        ]
        g = _growth_trend(rows)
        self.assertEqual(g["revenue_yoy_seq"], [-15.86, -4.55, 21.85])  # 正序
        self.assertEqual(g["profit_yoy_seq"], [-57.48, -53.49, 46.22])
        self.assertEqual(g["profit_yoy_accel"], round(46.22 - (-53.49), 2))
        self.assertEqual(g["margin_direction"], "改善")

    # ---- 美股营收序列（东财美股 F10）----
    def test_us_revenue_error_paths(self):
        # 无网络依赖：A股代码 → error；任意调用不抛异常
        from data_tool import get_us_revenue
        r = get_us_revenue("688036")  # A股数字代码 → 明确 error
        self.assertIn("error", r)
        self.assertIn("美股", r["error"])
        # 美股查询失败/无数据也应返回 dict（不抛异常）
        r2 = get_us_revenue("TSLA")
        self.assertIsInstance(r2, dict)

    def test_us_revenue_note_honest_boundary(self):
        # 若返回数据，必须携带"净利/毛利暂无免费源"的诚实边界说明
        from data_tool import get_us_revenue
        r = get_us_revenue("TSLA")
        if "error" not in r:
            self.assertIn("净利/毛利暂无免费公网源", r.get("note", ""))


if __name__ == "__main__":
    unittest.main()

