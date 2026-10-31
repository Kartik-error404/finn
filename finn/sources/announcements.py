"""Corporate announcements from NSE's public JSON endpoint (cookie-warmed)."""
import time
from datetime import datetime

from .. import sample
from ..config import MODE
from ..net import fetch_json, warm_cookies

NSE_HOME = "https://www.nseindia.com/companies-listing/corporate-filings-announcements"
NSE_API = ("https://www.nseindia.com/api/corporate-announcements"
           "?index=equities&symbol={sym}&from_date={frm}&to_date={to}")
_warmed = False


def _parse_nse_time(s):
    for fmt in ("%d-%b-%Y %H:%M:%S", "%d-%b-%Y %H:%M"):
        try:
            return datetime.strptime(s, fmt).timestamp()
        except (ValueError, TypeError):
            pass
    return time.time()


def for_symbol(symbol, hours):
    """Return (source, [ {symbol, subject, text, url, ts} ])."""
    global _warmed
    if MODE != "demo":
        try:
            if not _warmed:
                warm_cookies(NSE_HOME)
                _warmed = True
            now = datetime.now()
            frm = datetime.fromtimestamp(time.time() - hours * 3600)
            url = NSE_API.format(sym=symbol, frm=frm.strftime("%d-%m-%Y"), to=now.strftime("%d-%m-%Y"))
            data = fetch_json(url, ttl=900, headers={"Referer": NSE_HOME, "Accept": "application/json"})
            items = data if isinstance(data, list) else data.get("data", [])
            out = [{
                "symbol": symbol,
                "subject": it.get("desc", ""),
                "text": it.get("attchmntText", "") or "",
                "url": it.get("attchmntFile", ""),
                "ts": _parse_nse_time(it.get("an_dt") or it.get("sort_date")),
            } for it in items]
            return "live", [a for a in out if a["ts"] >= time.time() - hours * 3600]
        except Exception as e:
            if MODE == "live":
                raise
            print(f"[nse] {symbol}: live failed ({e.__class__.__name__}), using demo")
    return "demo", [a for a in sample.announcements() if a["symbol"] == symbol
                    and a["ts"] >= time.time() - hours * 3600]
