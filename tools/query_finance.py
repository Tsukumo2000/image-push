# -*- coding: utf-8 -*-
"""
query_finance.py — A股财务数据查询与指标计算工具（离线版）

所有数字来自同目录下的 stock.db（SQLite），不联网、不编造。
用法（JSON 输出到 stdout）：

  python query_finance.py list                       # 列出库里所有股票
  python query_finance.py quote <code> <start> <end> # 日线行情（YYYY-MM-DD 或 YYYYMMDD）
  python query_finance.py report <code> <period>     # 某期三表全部科目
  python query_finance.py item <code> <period> <科目>  # 单科目值（支持模糊匹配名称）
  python query_finance.py ratio <code> <period>      # 核心财务指标
  python query_finance.py trend <code> <科目> [n]     # 某科目最近 n 期走势（默认8）
"""
import sys, json, sqlite3, os, re

_HERE = os.path.dirname(os.path.abspath(__file__))
# 依次尝试：包根/data/stock.db（标准布局）→ 脚本同目录/stock.db → 上级/data/stock.db
_CANDIDATES = [
    os.path.join(_HERE, "..", "data", "stock.db"),
    os.path.join(_HERE, "stock.db"),
    os.path.join(_HERE, "data", "stock.db"),
]
DB = next((os.path.normpath(p) for p in _CANDIDATES if os.path.exists(p)), None)
if DB is None:
    DB = os.path.normpath(_CANDIDATES[0])


def conn():
    if not os.path.exists(DB):
        die(f"数据库不存在: {DB}")
    return sqlite3.connect(DB)


def die(msg):
    print(json.dumps({"error": msg}, ensure_ascii=False))
    sys.exit(0)


def norm_period(p):
    """2024 / 2024年报 / 20241231 -> 20241231；也接受 20240930 等"""
    p = str(p).strip()
    if re.fullmatch(r"\d{4}", p):
        return p + "1231"
    p = p.replace("-", "").replace("/", "")
    if re.fullmatch(r"\d{8}", p):
        return p
    die(f"无法识别的报告期: {p}（用 2024 或 20241231）")


def get_val(cur, code, period, item):
    """按科目名精确取；取不到则模糊匹配，返回 (item_name, value)"""
    def _f(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    r = cur.execute(
        "SELECT item, value FROM financial_report WHERE code=? AND report_date=? AND item=?",
        (code, period, item)).fetchone()
    if r:
        return r[0], _f(r[1])
    r = cur.execute(
        """SELECT item, value FROM financial_report WHERE code=? AND report_date=? AND item LIKE ?
           ORDER BY LENGTH(item) LIMIT 1""", (code, period, f"%{item}%")).fetchone()
    return (r[0], _f(r[1])) if r else (None, None)


def ok(**kw):
    kw["source"] = "data/stock.db"
    print(json.dumps(kw, ensure_ascii=False, indent=2))


def main():
    if len(sys.argv) < 2:
        die("用法: query_finance.py {list|quote|report|item|ratio|trend} ...")
    cmd = sys.argv[1].lower()
    cur = conn().cursor()

    if cmd == "list":
        rows = cur.execute("SELECT code, name, industry FROM stocks").fetchall()
        ok(stocks=[{"code": c, "name": n, "industry": i} for c, n, i in rows])

    elif cmd == "quote":
        if len(sys.argv) < 5:
            die("用法: quote <code> <start> <end>")
        code, s, e = sys.argv[2], norm_period(sys.argv[3]), norm_period(sys.argv[4])
        s, e = s.replace("1231", "-12-31"), e.replace("1231", "-12-31")
        rows = cur.execute(
            """SELECT date, open, high, low, close, volume FROM daily_quote
               WHERE code=? AND date BETWEEN ? AND ? ORDER BY date""",
            (code, s, e)).fetchall()
        if not rows:
            die(f"{code} 在 {s}~{e} 无行情")
        closes = [r[4] for r in rows if r[4] is not None]
        ret = round((closes[-1] / closes[0] - 1) * 100, 2) if len(closes) > 1 else None
        ok(code=code, rows=len(rows), first=rows[0][0], last=rows[-1][0],
           period_start_close=closes[0], period_end_close=closes[-1],
           period_return_pct=ret,
           max_close=max(closes), min_close=min(closes))

    elif cmd == "report":
        if len(sys.argv) < 4:
            die("用法: report <code> <period>")
        code, period = sys.argv[2], norm_period(sys.argv[3])
        rows = cur.execute(
            """SELECT statement, item, value FROM financial_report
               WHERE code=? AND report_date=? ORDER BY statement, value DESC""",
            (code, period)).fetchall()
        if not rows:
            avail = [r[0] for r in cur.execute(
                "SELECT DISTINCT report_date FROM financial_report WHERE code=? ORDER BY report_date DESC LIMIT 10",
                (code,))]
            die(f"{code} 无 {period} 数据。最近可用报告期: {avail}")
        out = {}
        for st, it, v in rows:
            out.setdefault(st, {})[it] = v
        ok(code=code, period=period, statements=out)

    elif cmd == "item":
        if len(sys.argv) < 5:
            die("用法: item <code> <period> <科目>")
        code, period, it = sys.argv[2], norm_period(sys.argv[3]), sys.argv[4]
        if not cur.execute("SELECT 1 FROM stocks WHERE code=?", (code,)).fetchone():
            die(f"本库无股票 {code} 的数据。库内仅有: {[r[0] for r in cur.execute('SELECT code FROM stocks')]}")
        name, v = get_val(cur, code, period, it)
        if name is None:
            die(f"{code} {period} 找不到科目「{it}」")
        ok(code=code, period=period, item=name, value=v)

    elif cmd == "ratio":
        if len(sys.argv) < 4:
            die("用法: ratio <code> <period>")
        code, period = sys.argv[2], norm_period(sys.argv[3])
        known = cur.execute("SELECT name FROM stocks WHERE code=?", (code,)).fetchone()
        if not known:
            codes = [r[0] for r in cur.execute("SELECT code FROM stocks")]
            die(f"本库无股票 {code} 的数据。库内仅有: {codes}")
        out = {"code": code, "name": known[0], "period": period}
        def V(item):
            """只取值，不要科目名"""
            return get_val(cur, code, period, item)[1]
        ca  = V("流动资产合计")
        cl  = V("流动负债合计")
        inv = V("存货")
        ta  = V("资产总计")
        tl  = V("负债合计")
        rev = V("营业收入")
        np_ = V("净利润")
        ocf = V("经营活动产生的现金流量净额")

        def r2(a, b):
            return round(a / b, 4) if (a is not None and b not in (None, 0)) else None
        out["current_ratio"] = r2(ca, cl)                    # 流动比率
        out["quick_ratio"] = r2((ca - inv) if (ca is not None and inv is not None) else None, cl)  # 速动比率
        out["debt_ratio"] = r2(tl, ta)                       # 资产负债率
        out["net_margin"] = r2(np_, rev)                     # 净利率
        out["ocf_to_revenue"] = r2(ocf, rev)                 # 经营现金流/收入
        out["raw"] = {"流动资产合计": ca, "流动负债合计": cl, "存货": inv,
                      "资产总计": ta, "负债合计": tl, "营业收入": rev,
                      "净利润": np_, "经营活动产生的现金流量净额": ocf}
        missing = [k for k, v in out["raw"].items() if v is None]
        if missing:
            out["missing_items"] = missing
        ok(**out)

    elif cmd == "trend":
        if len(sys.argv) < 4:
            die("用法: trend <code> <科目> [期数]")
        code, it = sys.argv[2], sys.argv[3]
        n = int(sys.argv[4]) if len(sys.argv) > 4 else 8
        rows = cur.execute(
            """SELECT report_date, item, value FROM financial_report
               WHERE code=? AND item LIKE ? AND report_date LIKE '%1231'
               ORDER BY report_date DESC LIMIT ?""", (code, f"%{it}%", n)).fetchall()
        if not rows:
            die(f"{code} 找不到科目「{it}」的年度数据")
        ok(code=code, item=rows[0][1],
           series=[{"period": r[0], "value": r[2]} for r in reversed(rows)])

    else:
        die(f"未知命令: {cmd}")


if __name__ == "__main__":
    main()
