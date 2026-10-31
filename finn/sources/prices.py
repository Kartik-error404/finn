"""End-of-day price & volume. Yahoo Finance chart API directly (same data yfinance wraps)."""
from .. import sample
from ..config import MODE
from ..net import fetch_json

YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}.NS?range=3mo&interval=1d"


def history(symbol):
    """Return {"source", "rows": [{"date", "close", "volume"}...]} oldest->newest."""
    if MODE != "demo":
        try:
            j = fetch_json(YAHOO.format(sym=symbol), ttl=6 * 3600)
            r = j["chart"]["result"][0]
            q = r["indicators"]["quote"][0]
            rows = [
                {"date": ts, "close": c, "volume": v}
                for ts, c, v in zip(r["timestamp"], q["close"], q["volume"])
                if c is not None and v is not None
            ]
            if len(rows) > 5:
                return {"source": "live", "rows": rows}
        except Exception as e:
            if MODE == "live":
                raise
            print(f"[prices] {symbol}: live failed ({e.__class__.__name__}), using demo")
    return {"source": "demo", "rows": sample.prices(symbol)}


def eod_stats(symbol, lookback=20):
    h = history(symbol)
    rows = h["rows"]
    last, prev = rows[-1], rows[-2]
    window = rows[-lookback - 1:-1]
    avg_vol = sum(r["volume"] for r in window) / max(len(window), 1)
    return {
        "symbol": symbol,
        "source": h["source"],
        "close": round(last["close"], 2),
        "change_pct": round((last["close"] / prev["close"] - 1) * 100, 2),
        "volume": int(last["volume"]),
        "avg_volume": int(avg_vol),
        "volume_multiple": round(last["volume"] / avg_vol, 2) if avg_vol else 0,
        "spark": [round(r["close"], 2) for r in rows[-30:]],
        "date": last["date"],
    }
