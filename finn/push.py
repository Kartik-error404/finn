"""PUSH: windowed digest + threshold alerts, with type-specific enrichment."""
import re
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

from . import classify as C
from . import llm, sample
from .config import load_portfolio, load_settings
from .sources import announcements, fundamentals, prices


def _names_map():
    m = {k: {"symbol": k, "name": v["name"], "sector": v["sector"]} for k, v in sample.COMPANY_PROFILES.items()}
    for p in load_portfolio():
        m[p["symbol"]] = p
    return m


def _pmap(fn, items):
    with ThreadPoolExecutor(max_workers=8) as ex:
        return list(ex.map(fn, items))


def _row(table, *labels):
    for lab in labels:
        for k, v in table["rows"].items():
            if k.lower().startswith(lab.lower()):
                return v
    return None


def _pct(a, b):
    if a is None or b in (None, 0):
        return None
    return round((a / b - 1) * 100, 1)


# ---------- enrichment ----------

def results_card(symbol):
    """Headline Revenue / EBITDA / PBT / PAT, QoQ and YoY, from the quarterly results table."""
    f = fundamentals.get(symbol)
    q = f["quarters"]
    hdr = q["headers"]
    if len(hdr) < 2:
        return None
    metrics = [("Revenue", ("Sales", "Revenue")),
               ("EBITDA", ("Operating Profit", "Financing Profit")),
               ("PBT", ("Profit before tax",)),
               ("PAT", ("Net Profit",))]
    rows = []
    for label, keys in metrics:
        s = _row(q, *keys)
        if not s:
            continue
        cur = s[-1]
        rows.append({"metric": label, "value": cur,
                     "qoq": _pct(cur, s[-2]) if len(s) > 1 else None,
                     "yoy": _pct(cur, s[-5]) if len(s) > 4 else None})
    opm = _row(q, "OPM")
    return {"period": hdr[-1], "vs_qoq": hdr[-2], "vs_yoy": hdr[-5] if len(hdr) > 4 else None,
            "unit": "₹ Cr", "rows": rows, "margin": opm[-1] if opm else None,
            "margin_prev_yoy": opm[-5] if opm and len(opm) > 4 else None, "source": f["source"]}


NAME_RX = re.compile(r"\b(Mr|Ms|Mrs|Dr|Shri|Smt)\.?\s+([A-Z][a-zA-Z]+(?:\s+[A-Z]\.)?(?:\s+[A-Z][a-zA-Z]+){0,3})")
ROLE_RX = re.compile(r"(Chief [A-Z][a-z]+ Officer|CFO|CEO|COO|Managing Director|Whole[- ]time Director|"
                     r"Independent Director|Company Secretary|Chairman|Director)", re.I)


def person_card(symbol, subject, text):
    """Who is the incoming/outgoing person? SEBI LODR requires a 'brief profile' in appointment
    filings, so the filing itself is the first (primary) source; LinkedIn is a one-tap deep link."""
    names = _names_map()
    blob = f"{subject}. {text}"
    m = NAME_RX.search(blob)
    name = m.group(2).replace("(DEMO PERSON)", "").strip() if m else None
    role = (ROLE_RX.search(blob) or [None])[0]
    direction = "outgoing" if re.search(r"resign|cessation|superannuat|retire|stepped down", subject + " " + text, re.I) else "incoming"
    prof = re.search(r"(brief profile[:\-]?\s*)(.+)", text, re.I | re.S)
    bio = prof.group(2).strip() if prof else None
    if not bio and text and llm.enabled():
        bio = llm.complete(f"From this filing, write a 2-line professional background of the person "
                           f"being appointed. If none is given, reply 'Not disclosed.'\n\n{text[:2500]}",
                           tier="cheap", max_tokens=120)
    company = names.get(symbol, {}).get("name", symbol)
    return {"name": name, "role": role, "direction": direction, "bio": bio,
            "linkedin": "https://www.linkedin.com/search/results/people/?keywords="
                        + urllib.parse.quote(f"{name or ''} {role or ''}".strip()) if name else None,
            "company": company}


def one_liner(subject, text):
    if not text or len(text) < 40:
        return None
    if llm.enabled():
        s = llm.complete("In <=18 words, state the investor-relevant fact in this filing. "
                         f"No fluff.\nSubject: {subject}\n{text[:1200]}", tier="cheap", max_tokens=50)
        if s:
            return s
    first = re.split(r"(?<=[.!?])\s", text.strip())[0]
    return first[:180] + ("…" if len(first) > 180 else "")


# ---------- digest ----------

def digest(hours=24):
    s = load_settings()
    portfolio = load_portfolio()
    names = _names_map()
    care = set(s["care_categories"])
    syms = [p["symbol"] for p in portfolio]
    ann = _pmap(lambda sym: announcements.for_symbol(sym, hours), syms)
    px = {st["symbol"]: st for st in _pmap(lambda sym: prices.eod_stats(sym, s["volume_lookback"]), syms)}
    items, sources = [], set()
    for src, lst in ann:
        sources.add(src)
        for a in lst:
            cat, how = C.classify(a["subject"], a["text"])
            pr, tier, why = C.priority(cat, a["subject"], a["text"], care, px.get(a["symbol"]))
            info = names.get(a["symbol"], {"name": a["symbol"], "sector": "NSE"})
            items.append({**a, "category": cat, "classified_by": how, "priority": pr, "tier": tier,
                          "why": why, "name": info["name"], "sector": info.get("sector", "NSE"),
                          "price": {k: px[a["symbol"]][k] for k in ("close", "change_pct", "volume_multiple")}})
    items.sort(key=lambda x: (-x["priority"], -x["ts"]))

    def enrich(it):
        if it["tier"] == "routine":
            return it
        if it["category"] == "results" and not C.ROUTINE_HINT.search(it["subject"]):
            it["results"] = results_card(it["symbol"])
            it["summary"] = one_liner(it["subject"], it["text"])
        elif it["category"] == "management_change":
            it["person"] = person_card(it["symbol"], it["subject"], it["text"])
        else:
            it["summary"] = one_liner(it["subject"], it["text"])
        return it

    items = _pmap(enrich, items)
    counts = {t: sum(1 for i in items if i["tier"] == t) for t in ("act", "watch", "routine")}
    return {"hours": hours, "generated": time.time(), "counts": counts, "items": items,
            "portfolio_size": len(portfolio), "sources": sorted(sources), "llm": llm.enabled()}


# ---------- alerts ----------

def alerts():
    s = load_settings()
    portfolio = load_portfolio()
    names = _names_map()
    syms = [p["symbol"] for p in portfolio]
    stats = _pmap(lambda sym: prices.eod_stats(sym, s["volume_lookback"]), syms)
    for st in stats:
        info = names.get(st["symbol"], {"name": st["symbol"], "sector": "NSE"})
        st["name"] = info["name"]
        st["sector"] = info.get("sector", "NSE")
    out = []
    for st in stats:
        reasons = []
        if st["volume_multiple"] >= s["volume_multiple"]:
            reasons.append(f"Volume {st['volume_multiple']}× its {s['volume_lookback']}-day average")
        if abs(st["change_pct"]) >= s["price_move_pct"]:
            reasons.append(f"Price {st['change_pct']:+.1f}% (threshold ±{s['price_move_pct']}%)")
        if reasons:
            out.append({"kind": "market", "symbol": st["symbol"], "name": st["name"], "sector": st["sector"],
                        "reasons": reasons, "stats": st,
                        "severity": round(st["volume_multiple"] / s["volume_multiple"] + abs(st["change_pct"]) / s["price_move_pct"], 2)})
    d = digest(48)
    moved = {a["symbol"] for a in out}
    for it in d["items"]:
        if it["category"] in s["care_categories"] and it["tier"] == "act" and it["symbol"] not in moved and it["ts"] >= time.time() - 24 * 3600:
            out.append({"kind": "filing", "symbol": it["symbol"], "name": it["name"], "sector": it.get("sector", "NSE"),
                        "reasons": [f"{it['category'].replace('_', ' ')}: {it['subject']}"],
                        "item": it, "severity": round(it["priority"] / 50, 2)})
    out.sort(key=lambda a: -a["severity"])
    # Join: link market moves with same-day/48h filings ("why did it move?")
    filings_by_sym = {}
    for it in d["items"]:
        if it["tier"] != "routine":
            filings_by_sym.setdefault(it["symbol"], []).append(it)
    for a in out:
        if a["kind"] == "market":
            matched = (filings_by_sym.get(a["symbol"]) or [None])[0]
            a["possible_cause"] = matched["subject"] if matched else None
            a["cause_category"] = matched["category"] if matched else None
    return {"alerts": out, "watchlist": sorted(stats, key=lambda x: -abs(x["change_pct"])),
            "settings": s, "sources": sorted({st["source"] for st in stats})}
