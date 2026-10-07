#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
skill_rag_analysis.py —— Skill + RAG 协同分析编排器
Frontier Tech Industrial Analysis Engine

把 .agents/skills/ 的"分析作业流程"(Skill) 与 rag 的公理知识(RAG) 组合成交互式分析：
  ① 读指定 skill 的 SKILL.md → 提取触发条件 / 输入参数槽 / 判定逻辑骨架 / 输出 Schema
  ② 调 problem_router.retrieve_axioms(query) → 用方法论公理给 skill 的判定提供知识定性
  ③ 把"待填参数"作为槽位呈现，输出「分析框架 + RAG 公理支撑 + 参数槽」的结构化草稿

这是 skill(骨架) + RAG(血肉) + 外部数据(燃料，参数槽待填) 三件套的脚本侧驱动。
Skill = 作业流程（怎么分析），RAG = 方法论知识（分析依据），外部参数 = 用户/工具后填。

用法:
  python scripts/skill_rag_analysis.py --skill tech-impact-trimode-evaluator \
      --query "自动驾驶技术对汽车产业的影响" [--params '{"alters_control":true,"targets_existing_market":true}']
  python scripts/skill_rag_analysis.py --list       # 列出可用 skill
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

_REPO = Path(__file__).resolve().parents[1]
_SKILLS_DIR = _REPO / ".agents/skills"


def list_skills():
    """列出带可解析 Schema 的 skill 及其一句话描述。"""
    out = []
    for d in sorted(_SKILLS_DIR.iterdir()):
        md = d / "SKILL.md"
        if not md.is_file():
            continue
        text = md.read_text(encoding="utf-8")
        # 提取 frontmatter description
        m = re.search(r"description:\s*>\s*\n(.*?)\n---", text, re.S)
        desc = (m.group(1).strip().replace("\n", " ") if m else "")[:120]
        has_schema = "Input Schema" in text or "输入参数" in text or "Schema" in text
        out.append((d.name, has_schema, desc))
    return out


def extract_input_schema(text):
    """启发式提取 skill 的输入参数槽（从 Input Schema YAML 或 '输入参数' 段）。"""
    slots = []
    # 尝试 YAML ```yaml ... ``` 块（含 Input/输入参数）
    for block in re.findall(r"```ya?ml\n(.*?)```", text, re.S):
        if "输入" in block or "input" in block.lower() or "target_subject" in block:
            for line in block.splitlines():
                s = line.strip()
                if re.match(r"^[a-z_]+:", s) and not s.startswith("#"):
                    slots.append(s.split(":")[0].strip())
    # 兼容 '输入参数 (Input Schema)' 段落里 'xxx: "string (...)"' 形式
    seg = re.search(r"输入参数.{0,20}Input Schema\s*\n(.*?)(?:\n###|\n##|\Z)", text, re.S)
    if seg:
        for line in seg.group(1).splitlines():
            s = line.strip()
            if re.match(r"^[a-z_]+:", s):
                slots.append(s.split(":")[0].strip())
    return sorted(set(slots))


def extract_trigger_conditions(text):
    """提取触发条件（Trigger Conditions）。兼容 '## 2. 触发条件 (Trigger Conditions)' 等标题。"""
    triggers = []
    # 匹配含"触发条件"的标题行，捕获其后到下一个 ##/### 标题前的列表项
    m = re.search(r"^#{2,4}[^\n]*触发条件[^\n]*\n(.*?)(?=^#{2,4}[^\n]*\n|\Z)", text, re.M | re.S)
    if not m:
        m = re.search(r"Trigger Conditions\s*\n(.*?)(?=^#{2,4}[^\n]*\n|\Z)", text, re.M | re.S)
    if m:
        for t in m.group(1).splitlines():
            s = t.strip()
            if s.startswith(("-", "*", "\u2022")):
                triggers.append(s.lstrip("-*\u2022 ").strip())
    if not triggers:
        m2 = re.search(r"Use this skill (?:when|to)\s*(.*?)\.", text)
        triggers = [m2.group(1).strip()] if m2 else []
    return [t for t in triggers if t][:6]


def extract_decision_logic(text):
    """提取 skill 的判定算法（text 代码块内的 IF/ELSE 骨架）。"""
    # 找 ```text 或普通代码块内容，精确定位含 '判断是否改变产业核心' 或 IF 的审判段
    for block in re.findall(r"```text\n(.*?)```", text, re.S):
        if "IF" in block and ("END IF" in block or "RETURN" in block):
            lines = block.splitlines()
            show = []
            for ln in lines:
                s = ln.strip()
                if not s:
                    continue
                if s.startswith("//") or s == "END IF" or s.startswith("ELSE IF"):
                    continue
                show.append(s[:90])
                if len(show) >= 10:
                    show.append("... (完整判定算法见 SKILL.md)")
                    break
            return show
    return []


def build_analysis(skill_name, query, params, top_k=3):
    """核心：skill 流程 + RAG 公理 + 参数槽 → 结构化分析草稿。"""
    md = _SKILLS_DIR / skill_name / "SKILL.md"
    if not md.is_file():
        raise ValueError(f"Skill 不存在: {skill_name}. 用 --list 查看可用项")
    text = md.read_text(encoding="utf-8")

    # ① skill 流程结构
    skill_title = (skill_name.replace("-", " ").title())
    title_m = re.search(r"^#\s*(.+)", text, re.M)
    if title_m:
        skill_title = title_m.group(1).strip()
    input_slots = extract_input_schema(text)
    triggers = extract_trigger_conditions(text)
    decision_logic = extract_decision_logic(text)

    # ② RAG 公理支撑
    from problem_router import ProblemRouter
    router = ProblemRouter()
    decision = router.route(query)
    recalled = decision.get("retrieved_axioms", [])[:top_k]

    # ③ 组装草稿
    lines = []
    lines.append("=" * 66)
    lines.append("  Skill + RAG 协同分析草稿 (Skill-Driven)")
    lines.append("=" * 66)
    lines.append(f"Skill  : {skill_title}  ({skill_name})")
    lines.append(f"Query  : {query}")
    lines.append(f"路由   : {decision['category']} → {decision['pipeline_id']}")
    lines.append("")
    lines.append("## 1. 触发条件 (何时启用本流程)")
    for t in triggers:
        lines.append(f"   - {t}")
    lines.append("")
    if decision_logic:
        lines.append("## 1b. Skill 判定逻辑骨架 (据此产出模式判定)")
        for ln in decision_logic:
            lines.append(f"   {ln}")
        lines.append("")
    lines.append("## 2. Skill 需要的输入参数槽 (待外部数据/用户填充)")
    if input_slots:
        for s in input_slots:
            val = params.get(s, "<待填>")
            lines.append(f"   - {s} = {val}")
    else:
        lines.append("   (未识别到结构化参数槽，需人工阅读 SKILL.md 正文)")
    lines.append("")
    lines.append("## 3. RAG 方法论公理支撑 (供 skill 判定参考)")
    for a in recalled:
        mt = a.get("methodology_topics", [])
        lines.append(f"   [{a['score']}] 主题={mt[:1]} 来源={a['source'][:30]}")
        lines.append(f"       {a.get('highlight', '')[:120].replace(chr(10), ' ')}")
    lines.append("")
    lines.append("## 4. 输出结构 (参考 skill 输出 Schema)")
    lines.append("   按 SKILL.md 的 Output Schema / 判定算法产出: 模式定性、关键瓶颈、因果判定、观测指标。")
    lines.append("=" * 66)
    return "\n".join(lines), input_slots, recalled


def execute_tech_impact_verdict(params):
    """把 tech-impact-trimode-evaluator 的 IF/ELSE 判定翻译为可执行规则，返回模式定性结论。

    依据 SKILL.md 判定算法：
      1. alters_control=F & targets_existing_market=T → 产业增强
      2. alters_control=T & targets_existing_market=T → 产业颠覆（看跨裂谷+闪电扩张→霸主 or 死局）
      3. targets_existing_market=F → 产业新增（看需求显性化→黄金蓝海 or 伪需求陷阱）
    """
    alters_control = bool(params.get("alters_control"))
    targets_existing_market = bool(params.get("targets_existing_market"))

    if not alters_control and targets_existing_market:
        return {
            "mode": "产业增强 (Industry Enhancement)",
            "beneficiary": "既有龙头巨头（微软/英伟达/苹果/主流车企）",
            "risk": "低风险、可预期收益",
            "action": "做'送水人'与'赋能者'，与巨头深度合作或被整合；单打独斗做通用平台注定被碾压",
            "key_bottleneck": "无（强者恒强、锦上添花路径）",
        }
    if alters_control and targets_existing_market:
        can_cross = bool(params.get("can_cross_chasm"))
        can_blitz = bool(params.get("can_blitzscale"))
        if can_cross and can_blitz:
            return {
                "mode": "产业颠覆·新霸主崛起 (Disruption)",
                "beneficiary": "具备全栈工程化 + 闪电扩张能力的进攻型新进入者",
                "risk": "极高风险、极高回报",
                "action": "重塑产业链控制点、快速建立用户心智护城河、不对称击穿巨头组织惯性",
                "key_bottleneck": "裂谷跨越 + 巨头反扑承受力",
            }
        return {
            "mode": "产业颠覆·能力断层死局 (Disruption-Failure)",
            "beneficiary": "无（创业者成'先烈'，为巨头教育市场）",
            "risk": "极度致命",
            "action": "立即停止正面硬碰，收缩至垂直极端细分，补齐量产与交付短板",
            "key_bottleneck": "工程良率/资本决战不足",
        }
    if not targets_existing_market:
        explicit = bool(params.get("is_explicit_demand", True))
        if explicit:
            return {
                "mode": "产业新增·黄金蓝海 (Creation)",
                "beneficiary": "率先把复杂技术包装为极简标准化爆品的领航者",
                "risk": "中等风险（开拓者）",
                "action": "全力打磨杀手级单点体验、建用户习惯与开发者生态、制定新市场标准",
                "key_bottleneck": "显性化需求转化",
            }
        return {
            "mode": "产业新增·自嗨伪需求陷阱 (Creation-Failure)",
            "beneficiary": "无（技术超前于时代、长期教育市场无收入）",
            "risk": "死亡泥潭",
            "action": "停止自嗨式科研推销、重构用户场景、把隐性需求转化为显性刚需",
            "key_bottleneck": "需求付费意愿缺失",
        }
    return {"mode": "参数不足 (alters_control & targets_existing_market 均为 False，无法判定)", "beneficiary": "-", "risk": "-", "action": "需重新取值", "key_bottleneck": "-"}


VERDICT_EXECUTORS = {
    "tech-impact-trimode-evaluator": execute_tech_impact_verdict,
}


def synthesize_decision(verdict, quote, skill_dir_hint):
    """B 部分：决策合成器——用行情估值(PE) + skill 判定模式 + 方向，合成最终可下注结论。

    规则（纯代码，Fail-Closed：数据不足不臆断）：
      - 估值维度：PE > 100 视为高估(规避倾向)；PE 20~100 中性；PE < 20 低估(买入倾向)
      - 模式维度：skill 判定 "产业颠覆·新霸主"/"产业新增·黄金蓝海" → 进攻(buy 倾向)
                   "产业增强" → 中性(hold)；"死局/伪需求" → 规避
      - 方向维度：RAG 公理 recommended_direction（buy/hold/avoid）
    最终合成：三信号投票，多数决定 buy/hold/avoid。任一维度不可得则该维度弃权。
    """
    if not verdict or not quote:
        return {"conclusion": "数据不足，无法合成决策", "signals": []}

    pe = quote.get("pe")
    signals = []

    # 1) 估值信号（Fail-Closed：估值是高风险的硬约束，异常时加权）
    pe = quote.get("pe")
    if pe is not None:
        if pe > 100:
            # 高估值是硬性规避信号：权重×2，压过"产业模式乐观"
            signals.extend(["估值-规避(PE高企)", "估值-规避(PE>100硬约束)"])
        elif pe < 10:
            # 极低 PE 可能失真(周期顶/一次性)，不给买入票，只观望
            signals.append("估值-观望(PE异常低，可能失真)")
        elif pe < 20:
            signals.append("估值-买入(PE低估)")
        else:
            signals.append("估值-观望(PE中性)")

    # 2) 模式信号（skill 判定）
    mode = verdict.get("mode", "")
    if any(k in mode for k in ("新霸主", "黄金蓝海")):
        signals.append("模式-买入(产业进攻型)")
    elif any(k in mode for k in ("死局", "伪需求")):
        signals.append("模式-规避(陷阱)")
    elif "产业增强" in mode:
        signals.append("模式-观望(增强但非主角)")

    # 3) 方向信号（skill 判定里带的方向，若有）
    act = verdict.get("action", "")
    if any(k in act for k in ("护城河", "闪电", "击穿")):
        signals.append("战术-买入(进攻型)")
    elif any(k in act for k in ("停止", "收缩", "规避")):
        signals.append("战术-规避(防守)")

    # 投票（估值异常信号已多算一票）
    buy = sum(1 for s in signals if "买入" in s)
    avoid = sum(1 for s in signals if "规避" in s)
    if buy > avoid:
        conclusion = "建议买入"
    elif avoid > buy:
        conclusion = "建议规避"
    else:
        conclusion = "建议观望"

    return {"conclusion": conclusion, "signals": signals}


def build_report(skill_name, query, params):
    """生成一份正式 Markdown 分析报告（skill 判定执行结论 + RAG 公理支撑 + 监控清单）。"""
    md = _SKILLS_DIR / skill_name / "SKILL.md"
    if not md.is_file():
        raise ValueError(f"Skill 不存在: {skill_name}")
    text = md.read_text(encoding="utf-8")
    title_m = re.search(r"^#\s*(.+)", text, re.M)
    title = title_m.group(1).strip() if title_m else skill_name
    input_slots = extract_input_schema(text)
    decision_logic = extract_decision_logic(text)

    from problem_router import ProblemRouter
    router = ProblemRouter()
    decision = router.route(query)
    recalled = decision.get("retrieved_axioms", [])[:3]

    # 执行 skill 判定（若该 skill 有可执行器）
    verdict = None
    executor = VERDICT_EXECUTORS.get(skill_name)
    if executor:
        verdict = executor(params)

    # 实时行情：从 params 的 symbol 或 query 中识别标的代码，用 data_tool 拉真实数据
    quote = None
    fundamentals = None
    trend = None
    us_revenue = None
    sym = params.get("symbol")
    if not sym:
        m = re.search(r"(?:688\d{3}|60\d{4}|30\d{4}|TSLA|NVDA|AAPL|MSFT|GOOG|AMZN|AMD|BABA|NIO|XPEV|LI|ON|BYDDY)", query, re.IGNORECASE)
        if m:
            sym = m.group(0)
    if sym:
        try:
            from data_tool import get_quote, get_fundamentals, get_price_trend, get_us_revenue
            quote = get_quote(str(sym))
            fundamentals = get_fundamentals(str(sym))  # 仅 A股有数据；美股返回 error
            trend = get_price_trend(str(sym))          # 技术面：近 3 月区间涨跌
            us_revenue = get_us_revenue(str(sym))      # 美股营收序列（A股返回 error）
        except Exception:
            quote = None
            fundamentals = None
            trend = None
            us_revenue = None

    # B 部分：合成最终决策（估值 PE + skill 模式 + 方向）
    final_decision = synthesize_decision(verdict, quote, skill_name) if (quote or verdict) else None

    L = []
    L.append(f"# {title}")
    L.append("")
    L.append(f"**分析标的 / 主题**：{query}")
    L.append(f"**路由**：`{decision['category']}` → `{decision['pipeline_id']}`")
    L.append(f"**调用方法框架**：`{skill_name}`（.agents/skills）")
    L.append("")
    L.append("---")
    L.append("")
    if quote and "error" not in quote:
        L.append("## 〇、标的实时行情（外部数据工具层）")
        L.append("")
        L.append(f"| 指标 | 数值 |")
        L.append(f"| :--- | :--- |")
        L.append(f"| **标的** | {quote.get('name')} ({quote.get('code')}) |")
        L.append(f"| **现价** | {quote.get('price')} {quote.get('currency')} |")
        L.append(f"| **涨跌** | {quote.get('change')} ({quote.get('change_pct')}%) |")
        L.append(f"| **昨收** | {quote.get('prev_close')} |")
        L.append(f"| **市盈率 PE** | {quote.get('pe') if quote.get('pe') else 'N/A'} |")
        L.append(f"| **总市值** | {quote.get('market_cap')} 亿 |")
        L.append(f"| **行情时间** | {quote.get('time')} |")
        L.append("")
        L.append("> 数据来源：腾讯行情接口（stdlib urllib 实时拉取）。")
        L.append("")
        L.append("---")
        L.append("")
    # 财务基本面段（仅 A股，东财 F10）
    if fundamentals and "error" not in fundamentals:
        L.append("## 〇b、财务基本面（东财 F10）")
        L.append("")
        L.append(f"**报告期**：{fundamentals.get('report_date')}（{fundamentals.get('report_type')}）")
        L.append("")
        L.append("| 指标 | 数值 |")
        L.append("| :--- | :--- |")
        L.append(f"| **营业收入** | {fundamentals.get('revenue_yi')} 亿元（同比 {fundamentals.get('revenue_yoy')}%） |")
        L.append(f"| **归母净利润** | {fundamentals.get('net_profit_yi')} 亿元（同比 {fundamentals.get('profit_yoy')}%） |")
        L.append(f"| **销售毛利率** | {fundamentals.get('gross_margin')}% |")
        L.append(f"| **ROE(加权)** | {fundamentals.get('roe')}% |")
        L.append(f"| **每股净资产 BPS** | {fundamentals.get('bps')} |")
        L.append("")
        g = fundamentals.get("growth_trend", {})
        if g.get("revenue_yoy_seq") or g.get("gross_margin_seq"):
            L.append("**成长趋势（近 5-6 期）**")
            L.append("")
            rv = g.get("revenue_yoy_seq") or []
            pf = g.get("profit_yoy_seq") or []
            gm = g.get("gross_margin_seq") or []
            if rv:
                rv_str = " → ".join(str(x) for x in rv)
                L.append(f"- 营收同比：`{rv_str}`（加速度 {g.get('revenue_yoy_accel')}）")
            if pf:
                pf_str = " → ".join(str(x) for x in pf)
                L.append(f"- 净利同比：`{pf_str}`（加速度 {g.get('profit_yoy_accel')}）")
            if gm:
                gm_str = " → ".join(str(x) for x in gm)
                L.append(f"- 毛利率：`{gm_str}`（{g.get('margin_direction')}）")
            L.append("")
        L.append("> 数据来源：东财 F10（stdlib urllib 实时拉取）。")
        L.append("")
        L.append("---")
        L.append("")
    # 美股营收成长趋势段（东财美股 F10，近 6 期；美股专用，A股此段为空）
    if us_revenue and "error" not in us_revenue:
        rseq = us_revenue.get("revenue_seq", [])[-6:]
        if rseq:
            L.append("## 〇b2、美股营收成长趋势（东财美股 F10）")
            L.append("")
            L.append(f"**最新累计期**：{us_revenue.get('report_date')} 营收 {us_revenue.get('revenue_latest_yi')} 亿美元（同比 {us_revenue.get('revenue_yoy')}%，加速度 {us_revenue.get('revenue_yoy_accel')}）")
            L.append("")
            L.append("| 报告期 | 营收(亿美元) | 同比% |")
            L.append("| :--- | :--- | :--- |")
            for x in rseq:
                yoy = x.get("yoy")
                L.append(f"| {x['period']} | {x['revenue_usd_yi']} | {yoy if yoy is not None else '-'} |")
            L.append("")
            L.append(f"> {us_revenue.get('note', '')}")
            L.append("")
            L.append("---")
            L.append("")
    # 技术面段（腾讯 K 线近 3 月区间涨跌）
    if trend and "error" not in trend:
        L.append("## 〇c、技术面 / 价格趋势（腾讯 K 线）")
        L.append("")
        L.append("| 指标 | 数值 |")
        L.append("| :--- | :--- |")
        L.append(f"| **近 3 月区间涨幅** | {trend.get('range_change_pct')}% |")
        L.append(f"| **区间价格** | {trend.get('first_close')} → {trend.get('last_close')} |")
        L.append(f"| **K 线样本** | {trend.get('bars')} 根 |")
        L.append("")
        sign = "上行趋势" if trend.get("range_change_pct", 0) > 5 else ("下行趋势" if trend.get("range_change_pct", 0) < -5 else "区间震荡")
        L.append(f"> 研判：{sign}（近 3 月 {trend.get('range_change_pct')}%）。")
        L.append("")
        L.append("---")
        L.append("")
    L.append("## 一、分析方法与触发条件")
    L.append("本报告由 Skill（作业流程）+ RAG（方法论公理）协同生成。")
    L.append("触发本方法框架的条件（skill 定义）：")
    L.append("")
    for t in extract_trigger_conditions(text):
        L.append(f"- {t}")
    L.append("")
    L.append("## 二、判定结论（skill 算法执行结果）")
    L.append("")
    if verdict:
        L.append(f"### 模式定性：**{verdict['mode']}**")
        L.append("")
        L.append("| 维度 | 判定 |")
        L.append("| :--- | :--- |")
        L.append(f"| **核心受益方** | {verdict['beneficiary']} |")
        L.append(f"| **风险等级** | {verdict['risk']} |")
        L.append(f"| **关键瓶颈** | {verdict['key_bottleneck']} |")
        L.append(f"| **战术建议** | {verdict['action']} |")
    else:
        L.append("> 该 skill 无可执行判定器，以下仅为方法论框架——判定需人工/外部执行。")
    L.append("")
    L.append("## 三、方法论公理支撑（RAG 召回）")
    L.append("")
    for a in recalled:
        L.append(f"- **{a.get('methodology_topics',[''])[0]}**：{a.get('highlight','')[:140].replace(chr(10),' ')}")
    L.append("")
    L.append("## 四、参数槽（外部数据待填，用于补强判定）")
    L.append("")
    for s in input_slots:
        L.append(f"- `{s}`：{params.get(s, '<待填>')}")
    L.append("")
    L.append("## 五、投后监控建议（Kill-Switch 方向）")
    L.append("- 若判定为**产业颠覆**：监控『工程良率爬坡 / 资本决战期限』，跌破即撤")
    L.append("- 若判定为**产业新增**：监控『显性需求付费转化率』，" "长期无付费转化即证伪")
    L.append("- 若判定为**产业增强**：监控『巨头采纳/吸收速度』，合作受阻即重估")
    L.append("")
    if final_decision:
        L.append("## 六、最终决策结论（决策合成器）")
        L.append("")
        L.append(f"### **{final_decision['conclusion']}**")
        L.append("")
        L.append("| 合成信号 | 判定 |")
        L.append("| :--- | :--- |")
        for s in final_decision["signals"]:
            L.append(f"| {s.split('-')[0]} | {s.split('-',1)[1]} |")
        L.append("")
        L.append("> 由估值(PE) + 产业模式 + 战术方向 三信号投票合成；数据不足则不出结论（Fail-Closed）。")
        L.append("")
    L.append("---")
    L.append("")
    L.append("> 由 agent-rag Skill+RAG 协同编排器生成 · 供投研决策参考，非投资建议。")

    return "\n".join(L), verdict, recalled


def main():
    ap = argparse.ArgumentParser(description="Skill + RAG 协同分析编排器")
    ap.add_argument("--skill", help="skill 名称，如 tech-impact-trimode-evaluator")
    ap.add_argument("--query", help="分析问题")
    ap.add_argument("--params", default="{}", help='输入参数槽 JSON, 如 {"alters_control":true}')
    ap.add_argument("--list", action="store_true", help="列出可用 skill")
    ap.add_argument("--report", action="store_true",
                    help="输出完整分析报告（需含可执行 skill 判定的参数）")
    ap.add_argument("--out", default=None, help="报告写入文件路径（可选）")
    args = ap.parse_args()
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    if args.list:
        for name, has_schema, desc in list_skills():
            mark = "✓schema" if has_schema else "       "
            print(f"  [{mark}] {name:40s} {desc}")
        return

    if not args.skill or not args.query:
        ap.error("需提供 --skill 与 --query")
    try:
        params = json.loads(args.params)
    except Exception:
        params = {}
    if args.report:
        out, verdict, _ = build_report(args.skill, args.query, params)
        if verdict:
            print(f"[判定] {verdict['mode']}")
    else:
        out, _, _ = build_analysis(args.skill, args.query, params)
    if args.out:
        Path(args.out).write_text(out, encoding="utf-8")
        print(f"[已写入报告] {args.out}")
    else:
        print(out)


if __name__ == "__main__":
    main()