#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data_tool.py —— 外部数据工具层 (stdlib urllib 拉取真实行情)
Frontier Tech Industrial Analysis Engine

参考 Hermes 的"工具集(Toolsets)"机制，为分析提供真实外部数据（燃料层）。
用纯 Python stdlib `urllib` 调用腾讯行情接口，拉取并解析标的/指数行情，返回结构化指标。
保持：零第三方库、RAG 方法论不被外部数据污染（外部数据走独立工具层，用完即弃）。

设计：
  get_quote("688036") / get_quote("TSLA")  → dict{name, code, price, prev_close, change, change_pct, time, currency}
  支持格式：A股 6 位数字（自动映射 沪sh/深sz）、美股字母（us前缀）、指数（sh000001 等）

诚实边界：
  - 免费行情接口仅供参考，可能限流/延迟；失败时返回 error 字段而非伪造。
  - 这是"行情燃料"，非财报深度（营收/毛利需另接基本面 API）。

用法:
  python scripts/data_tool.py --symbol TSLA
  python scripts/data_tool.py --symbol 688036 --symbol 601127
  python scripts/data_tool.py --list-quotes 688036,TSLA
"""

import argparse
import json
import sys
import urllib.request
from pathlib import Path


def _to_float(v):
    """安全转 float；解析失败返回 None。"""
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def normalize_symbol(symbol: str) -> str:
    """把用户输入标准化为腾讯行情代码格式。"""
    s = symbol.strip().upper()
    if s.isdigit() and len(s) == 6:
        return ("sh" if s.startswith(("6", "9", "5")) else "sz") + s
    # 美股：如 TSLA → usTSLA.OQ
    if s.isalpha():
        return "us" + s
    # 已带前缀（sh/sz/us）原样返回
    return s.lower()


def get_quote(symbol: str, timeout: int = 8) -> dict:
    """拉取并解析单只标的的实时行情。纯 stdlib，失败返回 error。"""
    sym = normalize_symbol(symbol)
    url = f"https://qt.gtimg.cn/q={sym}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        raw = urllib.request.urlopen(req, timeout=timeout).read().decode("gbk", "replace")
        body = raw.split("=", 1)[1].strip().strip('"')
        f = body.split("~")
        if len(f) < 33:
            return {"symbol": symbol, "error": "malformed response"}
        return {
            "symbol": symbol,
            "code": f[2],
            "name": f[1],
            "price": float(f[3]),
            "prev_close": float(f[4]),
            "change": float(f[31]),
            "change_pct": float(f[32]),
            "pe": _to_float(f[39]),            # 市盈率（f39，A股/美股通用，交叉验证）
            "market_cap": _to_float(f[44]),    # 总市值（亿，A股通用；美股为亿美元量级）
            "eps": _to_float(f[47]),           # 每股收益（美股 f47；A股此字段布局不同，可能 None）
            # A股固定 CNY；美股 f[35]=币种（USD）
            "currency": (f[35] if len(f) > 35 and not f[2].isdigit() else "CNY"),
            "time": f[30],
            "source": "tencent-quote",
        }
    except Exception as e:
        return {"symbol": symbol, "error": f"{type(e).__name__}: {str(e)[:60]}"}


def _secucode(symbol: str) -> str:
    """把标的代码转为东财 SECUCODE 格式（A股 688036→688036.SH）。非 A股返回 None。"""
    s = symbol.strip().lstrip("shsz.us").upper()
    if s.isdigit() and len(s) == 6:
        suffix = ".SZ" if s.startswith(("0", "3")) else ".SH"
        return s + suffix
    return None


def get_price_trend(symbol: str, months: int = 3, timeout: int = 10) -> dict:
    """腾讯 K 线拉取近 N 月区间涨跌（技术面/趋势维度）。纯 stdlib。

    返回 {range_change_pct, bars, first_close, last_close}；失败返回 error。
    腾讯 K 线接口稳定，作为技术面数据源。
    """
    sym = normalize_symbol(symbol)
    # 日期窗口：粗略用固定近 3 月（start/end 由调用方传入更精确）
    url = (f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
           f"?param={sym},day,2026-06-01,2026-10-01,10,qfq")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        d = json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode())
        data = d.get("data", {}).get(sym, {})
        bars = data.get("qfqday") or data.get("day") or []
        if not bars:
            return {"symbol": symbol, "error": "无 K 线数据"}
        first = float(bars[0][2])
        last = float(bars[-1][2])
        return {
            "symbol": symbol,
            "bars": len(bars),
            "first_close": first,
            "last_close": last,
            "range_change_pct": round((last / first - 1) * 100, 2),
            "source": "tencent-kline",
        }
    except Exception as e:
        return {"symbol": symbol, "error": f"{type(e).__name__}: {str(e)[:60]}"}


def _us_revenue_rows(security_code: str, page_size: int = 200, timeout: int = 15) -> list:
    """拉取东财美股利润表（RPT_USF10_FN_INCOME）营收科目，只保留累计口径（Q1/Q6/Q9/FY）。

    单季行(Q2/Q3/Q4)与累计行口径重叠，跳过避免污染趋势序列。返回按报告期升序的行。
    """
    import urllib.request as _ur
    url = ("https://datacenter-web.eastmoney.com/api/data/v1/get"
           "?reportName=RPT_USF10_FN_INCOME&columns=ALL"
           f"&filter=(SECURITY_CODE%3D%22{security_code}%22)"
           f"&pageNumber=1&pageSize={page_size}&source=USF10&client=PC")
    req = _ur.Request(url, headers={"User-Agent": "Mozilla/5.0",
                                    "Referer": "https://emweb.securities.eastmoney.com/"})
    d = json.loads(_ur.urlopen(req, timeout=timeout).read().decode())
    rows = (d.get("result") or {}).get("data") or []
    out = []
    seen = set()
    for r in rows:
        item = r.get("ITEM_NAME") or ""
        period = r.get("REPORT") or ""
        if "主营收入" not in item and "营业收入" not in item:
            continue
        # 只留累计口径：/Q1, /Q6, /Q9, /FY（跳单季 Q2/Q3/Q4）
        if not (period.endswith(("/Q1", "/Q6", "/Q9", "/FY")) or "/FY" in period or period.endswith("FY")):
            continue
        if period in seen:
            continue
        seen.add(period)
        out.append(r)
    return sorted(out, key=lambda r: str(r.get("REPORT_DATE", "")))


def get_us_revenue(symbol: str, timeout: int = 15) -> dict:
    """美股营收序列（东财美股利润表，纯 urllib）：多期主营收入 + 同比 + 成长趋势。

    只用累计口径（Q1/Q6/Q9/FY）——与 A股多期同比口径一致，趋势干净。
    失败（如非美股/无数据）返回 error。净利/毛利暂无免费源，如实不伪造。
    """
    code = symbol.strip().upper()
    if code.isdigit():
        return {"symbol": symbol, "error": "美股营收需字母代码（如 TSLA）"}
    try:
        rows = _us_revenue_rows(code, timeout=timeout)
        if not rows:
            return {"symbol": symbol, "error": "无美股营收数据"}
        latest = rows[-1]  # 升序后最新累计期
        rev_seq = [{"period": r.get("REPORT"), "revenue_usd_yi": round(r.get("AMOUNT", 0) / 1e8, 2),
                    "yoy": round(r.get("YOY_RATIO"), 2) if isinstance(r.get("YOY_RATIO"), (int, float)) else None}
                   for r in rows]
        yoy_seq = [round(r.get("YOY_RATIO"), 2) for r in rows if isinstance(r.get("YOY_RATIO"), (int, float))]
        accel = round(yoy_seq[-1] - yoy_seq[-2], 2) if len(yoy_seq) >= 2 else None
        return {
            "symbol": symbol,
            "report_date": latest.get("REPORT"),
            "revenue_latest_yi": round(latest.get("AMOUNT", 0) / 1e8, 2),
            "revenue_yoy": round(latest.get("YOY_RATIO"), 2) if isinstance(latest.get("YOY_RATIO"), (int, float)) else None,
            "revenue_seq": rev_seq,
            "revenue_yoy_seq": yoy_seq,
            "revenue_yoy_accel": accel,
            "note": "来源东财美股F10营收科目(累计口径)；净利/毛利暂无免费公网源",
            "source": "eastmoney-us-f10",
        }
    except Exception as e:
        return {"symbol": symbol, "error": f"{type(e).__name__}: {str(e)[:60]}"}


def _growth_trend(rows):
    """从多期财务行推导成长趋势：增速序列 + 最新加速度 + 毛利率方向。"""
    def _f(v):
        return round(float(v), 2) if isinstance(v, (int, float)) else None
    # 按报告期先后排序（东财默认最新在前，转正序）
    seq = sorted(rows, key=lambda r: str(r.get("REPORT_DATE", "")))
    rev_yoy = [_f(r.get("TOTALOPERATEREVETZ")) for r in seq]
    profit_yoy = [_f(r.get("PARENTNETPROFITTZ")) for r in seq]
    gm = [_f(r.get("XSMLL")) for r in seq]
    periods = [r.get("REPORT_DATE_NAME") for r in seq]
    # 取有同比值的近 N 期（去掉首期无同比）
    rv = [x for x in rev_yoy if x is not None]
    pf = [x for x in profit_yoy if x is not None]
    def _accel(series):
        if len(series) >= 2:
            return round(series[-1] - series[-2], 2)
        return None
    # 毛利率方向：对比最近期与中游
    gm_dir = "改善" if gm and len([g for g in gm if g]) >= 2 and gm[-1] > gm[0] else ("恶化" if gm and gm[-1] < gm[0] else "平稳")
    return {
        "periods": periods,
        "revenue_yoy_seq": rv,
        "profit_yoy_seq": pf,
        "gross_margin_seq": [g for g in gm],
        "revenue_yoy_accel": _accel(rv),
        "profit_yoy_accel": _accel(pf),
        "margin_direction": gm_dir,
    }


def get_fundamentals(symbol: str, timeout: int = 12) -> dict:
    """东财 F10 拉取财务基本面（营收/净利润/毛利率/ROE/BPS）+ 成长趋势。纯 stdlib。

    返回已单位化(亿元/%)或原始数值；失败返回 error。仅支持 A股。
    """
    secucode = _secucode(symbol)
    if not secucode:
        return {"symbol": symbol, "error": "基本面接口仅支持 A股（如 688036）"}
    url = ("https://datacenter.eastmoney.com/securities/api/data/v1/get"
           "?reportName=RPT_F10_FINANCE_MAINFINADATA&columns=ALL"
           f"&filter=(SECUCODE%3D%22{secucode}%22)"
           "&pageNumber=1&pageSize=6&source=HSF10&client=PC")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        d = json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode())
        data = d.get("result", {}).get("data", [])
        if not data:
            return {"symbol": symbol, "secucode": secucode, "error": "无财务数据"}

        def _yv(v):
            # 东财市值单位 万分之一元级的营收/净利，统一转亿元(除以1e8)
            return round(v / 1e8, 2) if isinstance(v, (int, float)) else None

        rec = data[0]
        growth = _growth_trend(data)
        return {
            "symbol": symbol,
            "secucode": rec.get("SECUCODE"),
            "report_date": rec.get("REPORT_DATE_NAME"),
            "report_type": rec.get("REPORT_TYPE"),
            # 财务（亿元）
            "revenue_yi": _yv(rec.get("TOTALOPERATEREVE")),
            "net_profit_yi": _yv(rec.get("PARENTNETPROFIT")),
            "revenue_yoy": round(rec.get("TOTALOPERATEREVETZ"), 2) if rec.get("TOTALOPERATEREVETZ") not in (None, "-") else None,
            "profit_yoy": round(rec.get("PARENTNETPROFITTZ"), 2) if rec.get("PARENTNETPROFITTZ") not in (None, "-") else None,
            # 比率/每股（%）
            "gross_margin": round(rec.get("XSMLL"), 2) if isinstance(rec.get("XSMLL"), (int, float)) else None,
            "roe": round(rec.get("ROEJQ"), 2) if isinstance(rec.get("ROEJQ"), (int, float)) else None,
            "bps": round(rec.get("BPS"), 2) if isinstance(rec.get("BPS"), (int, float)) else None,
            # 成长趋势
            "growth_trend": growth,
            "source": "eastmoney-f10",
        }
    except Exception as e:
        return {"symbol": symbol, "error": f"{type(e).__name__}: {str(e)[:60]}"}


def get_quotes(symbols, timeout=8):
    """批量拉取。串行 + 小延时避免触发限流。"""
    import time
    out = []
    for s in symbols:
        out.append(get_quote(s, timeout))
        time.sleep(0.3)
    return out


def format_quote(q: dict) -> str:
    if "error" in q:
        return f"[{q['symbol']}] 拉取失败: {q['error']}"
    pe = f"{q['pe']:.1f}" if q.get("pe") else "N/A"
    mc = f"{q['market_cap']:.1f}亿" if q.get("market_cap") else "N/A"
    return (f"[{q['symbol']}] {q['name']}  现价 {q['price']} {q.get('currency','')}  "
            f"涨跌 {q['change']}({q['change_pct']}%)  PE {pe}  总市值 {mc}  时间 {q['time']}")


def format_fundamental(f: dict) -> str:
    if "error" in f:
        return f"[{f['symbol']}] 财务拉取失败: {f['error']}"
    return (f"[{f['symbol']}] {f.get('report_date')} {f.get('report_type')}: "
            f"营收 {f.get('revenue_yi')}亿(同比{f.get('revenue_yoy')}%) "
            f"净利 {f.get('net_profit_yi')}亿(同比{f.get('profit_yoy')}%) "
            f"毛利率 {f.get('gross_margin')}% ROE {f.get('roe')}% BPS {f.get('bps')}")


def main():
    ap = argparse.ArgumentParser(description="外部数据工具层：拉取真实行情 + 基本面 + 技术趋势")
    ap.add_argument("--symbol", action="append", default=[], help="标的代码，如 TSLA / 688036 / 601127")
    ap.add_argument("--fundamental", action="store_true", help="同时拉取财务基本面（仅 A股）")
    ap.add_argument("--trend", action="store_true", help="拉取技术面（近 3 月区间涨跌）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    if not args.symbol:
        ap.error("需提供 --symbol")
    quotes = get_quotes(args.symbol)
    if args.json:
        out = quotes
        if args.fundamental:
            for s in args.symbol:
                out.append(get_fundamentals(s))
        if args.trend:
            for s in args.symbol:
                out.append(get_price_trend(s))
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return
    for q in quotes:
        print(format_quote(q))
    if args.fundamental:
        for s in args.symbol:
            print(format_fundamental(get_fundamentals(s)))
    if args.trend:
        for s in args.symbol:
            t = get_price_trend(s)
            if "error" in t:
                print(f"[{s}] 技术面拉取失败: {t['error']}")
            else:
                print(f"[{s}] 近{t.get('bars',0)}根K线 区间涨幅 {t['range_change_pct']}%  ({t.get('first_close')}→{t.get('last_close')})")


if __name__ == "__main__":
    main()