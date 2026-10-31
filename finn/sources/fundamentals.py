"""Company fundamentals from screener.in: multi-year tables + links to annual reports and
concall transcripts (primary documents). Parsed with stdlib regex, no bs4 needed."""
import html
import re

from .. import sample
from ..config import MODE
from ..net import fetch

SCREENER = "https://www.screener.in/company/{sym}/{variant}"


def _clean(s):
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s).replace("\xa0", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s.rstrip("+").strip()


def _num(s):
    s = s.replace(",", "").replace("%", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def _section(page, sid):
    m = re.search(rf'<section[^>]+id="{sid}".*?</section>', page, re.S)
    return m.group(0) if m else ""


def _table(section_html):
    """-> {"headers": [...periods], "rows": {label: [floats]}}"""
    t = re.search(r"<table.*?</table>", section_html, re.S)
    if not t:
        return {"headers": [], "rows": {}}
    trs = re.findall(r"<tr.*?</tr>", t.group(0), re.S)
    headers, rows = [], {}
    for i, tr in enumerate(trs):
        cells = [_clean(c) for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", tr, re.S)]
        if not cells:
            continue
        if i == 0:
            headers = cells[1:]
        else:
            rows[cells[0]] = [_num(c) for c in cells[1:]]
    return {"headers": headers, "rows": rows}


def _parse(page, symbol):
    name = _clean((re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S) or [None, symbol])[1])
    about_m = re.search(r'class="[^"]*about[^"]*"[^>]*>(.*?)</div>', page, re.S)
    ratios = {}
    for li in re.findall(r"<li[^>]*>(.*?)</li>", (re.search(r'id="top-ratios".*?</ul>', page, re.S) or [""])[0], re.S):
        n = re.search(r'class="name"[^>]*>(.*?)</span>', li, re.S)
        v = re.search(r'class="[^"]*value[^"]*"[^>]*>(.*?)</span>\s*$', li, re.S)
        if n:
            ratios[_clean(n.group(1))] = _clean(v.group(1) if v else li.split(n.group(0))[-1])

    def links(cls):
        block = re.search(rf'class="documents {cls}.*?</ul>', page, re.S)
        out = []
        if block:
            if cls == "concalls":
                for li in re.findall(r"<li.*?</li>", block.group(0), re.S):
                    period = _clean((re.search(r"<div[^>]*>(.*?)</div>", li, re.S) or [None, ""])[1])
                    tr = re.search(r'href="([^"]+)"[^>]*>\s*Transcript', li)
                    if tr:
                        out.append({"title": period, "url": html.unescape(tr.group(1))})
            else:
                for href, txt in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', block.group(0), re.S):
                    out.append({"title": _clean(txt), "url": html.unescape(href)})
        return out[:8]

    return {
        "symbol": symbol, "name": name,
        "about": _clean(about_m.group(1)) if about_m else "",
        "top_ratios": ratios,
        "quarters": _table(_section(page, "quarters")),
        "annual": _table(_section(page, "profit-loss")),
        "balance": _table(_section(page, "balance-sheet")),
        "cashflow": _table(_section(page, "cash-flow")),
        "ratios": _table(_section(page, "ratios")),
        "docs": {"annual_reports": links("annual-reports"), "concalls": links("concalls")},
    }


def get(symbol):
    symbol = symbol.upper().strip()
    if MODE != "demo":
        for variant in ("consolidated/", ""):
            try:
                page = fetch(SCREENER.format(sym=symbol, variant=variant), ttl=24 * 3600).decode("utf-8", "replace")
                d = _parse(page, symbol)
                if d["annual"]["rows"]:
                    d["source"] = "live"
                    d["source_url"] = SCREENER.format(sym=symbol, variant=variant)
                    return d
            except Exception as e:
                if MODE == "live":
                    raise
                print(f"[screener] {symbol}{variant}: {e.__class__.__name__}")
    d = sample.fundamentals(symbol)
    d["source"] = "demo"
    return d
