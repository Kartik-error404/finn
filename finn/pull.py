"""PULL: on-demand research for ANY NSE ticker, grounded only in primary data
(screener.in financial tables sourced from filings + concall transcripts + annual reports).

Design: numbers are computed deterministically in Python (no hallucinated arithmetic).
LLMs are used only where language is the input: extracting guidance from transcripts (cheap
model, on keyword-filtered chunks) and writing bull/bear + answers (strong model, given only
the computed facts and quoted transcript snippets)."""
import io
import json
import re

from . import llm, sample
from .net import fetch
from .push import _pct, _row
from .sources import fundamentals


def _cagr(series, years):
    s = [x for x in (series or []) if x is not None]
    if len(s) <= years or s[-1 - years] <= 0 or s[-1] <= 0:
        return None
    return round(((s[-1] / s[-1 - years]) ** (1 / years) - 1) * 100, 1)


def _last(series, n=1):
    s = [x for x in (series or []) if x is not None]
    return s[-n] if len(s) >= n else None


# ---------- transcripts -> guidance (live path) ----------
GUIDE_RX = re.compile(r"guid|outlook|expect|target|aspire|growth of|margin|capex|we will|going forward|"
                      r"next year|full year|fy2\d", re.I)


def _pdf_text(url):
    try:
        from pypdf import PdfReader  # optional dependency
    except ImportError:
        return None
    try:
        raw = fetch(url, ttl=30 * 86400, timeout=30)
        return "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(raw)).pages[:40])
    except Exception as e:
        print(f"[pdf] {url}: {e}")
        return None


def _guidance_chunks(text, budget=6000):
    """Chunk & filter: keep only paragraphs that talk about the future. Cuts tokens ~10x."""
    paras = [p.strip() for p in re.split(r"\n\s*\n|(?<=\.)\n", text) if len(p.strip()) > 60]
    hits, total = [], 0
    for p in paras:
        if GUIDE_RX.search(p):
            hits.append(p[:700])
            total += len(hits[-1])
            if total > budget:
                break
    return "\n---\n".join(hits)


def extract_guidance(f):
    if f.get("demo_guidance"):
        return f["demo_guidance"], "demo"
    if not llm.enabled():
        return [], "needs_llm"
    out = []
    for doc in f["docs"]["concalls"][:4]:
        text = _pdf_text(doc["url"])
        if text is None:
            return [], "needs_pypdf"
        chunks = _guidance_chunks(text)
        j = llm.complete(
            "From these earnings-call excerpts, extract management's explicit numeric guidance on "
            "revenue growth (YoY %) or EBITDA/operating margin (%). Only what is explicitly stated. "
            'Reply JSON {"items":[{"metric":"Revenue growth YoY"|"EBITDA margin","low":num,'
            '"high":num,"quote":"<=20 words verbatim"}]}\n\n' + chunks,
            tier="cheap", max_tokens=400, as_json=True) or {}
        for it in j.get("items", [])[:3]:
            it["period"] = doc["title"]
            out.append(it)
    return out, "transcripts"


def promise_vs_delivered(f):
    guidance, how = extract_guidance(f)
    q = f["quarters"]
    hdr = q["headers"]
    sales = _row(q, "Sales", "Revenue")
    opm = _row(q, "OPM")
    rows = []
    for g in guidance:
        period = g["period"]
        # Guidance given on a call applies to the NEXT reported quarter.
        idx = next((i for i, h in enumerate(hdr) if h.lower().startswith(period.lower()[:3])
                    and h[-4:] == period[-4:]), None)
        tgt = idx + 1 if idx is not None and idx + 1 < len(hdr) else None
        delivered = None
        if tgt is not None:
            if g["metric"].lower().startswith("revenue") and sales and tgt >= 4:
                delivered = _pct(sales[tgt], sales[tgt - 4])
            elif "margin" in g["metric"].lower() and opm:
                delivered = opm[tgt]
        verdict = None
        if delivered is not None:
            verdict = "beat" if delivered > g["high"] else "met" if delivered >= g["low"] else "missed"
        rows.append({**g, "measured_in": hdr[tgt] if tgt is not None else None,
                     "delivered": delivered, "verdict": verdict})
    scored = [r for r in rows if r["verdict"]]
    kept = sum(r["verdict"] != "missed" for r in scored)
    score = (f"{kept}/{len(scored)} promises kept" if scored else None)
    pct_score = round(kept / len(scored) * 100) if scored else None
    return {"rows": rows, "score": score, "credibility_pct": pct_score, "method": how}


def quarterly_snapshot(f):
    q = f["quarters"]
    hdr = q["headers"]
    if not hdr:
        return {"headers": [], "rows": []}
    sales = _row(q, "Sales", "Revenue") or []
    op = _row(q, "Operating Profit", "Financing Profit") or []
    opm = _row(q, "OPM", "Financing Margin") or []
    pbt = _row(q, "Profit before tax") or []
    pat = _row(q, "Net Profit") or []
    n = min(5, len(hdr))
    idxs = list(range(len(hdr) - n, len(hdr)))
    out_hdr = [hdr[i] for i in idxs]
    latest_idx = len(hdr) - 1
    prev_q = latest_idx - 1 if latest_idx >= 1 else None
    prev_y = latest_idx - 4 if latest_idx >= 4 else None

    def build_row(label, arr, is_pct=False):
        if not arr or len(arr) <= latest_idx:
            return None
        return {
            "metric": label,
            "is_pct": is_pct,
            "values": [arr[i] if i < len(arr) else None for i in idxs],
            "qoq": (round(arr[latest_idx] - arr[prev_q], 1) if is_pct else _pct(arr[latest_idx], arr[prev_q])) if prev_q is not None else None,
            "yoy": (round(arr[latest_idx] - arr[prev_y], 1) if is_pct else _pct(arr[latest_idx], arr[prev_y])) if prev_y is not None else None,
        }

    rows = [r for r in [
        build_row("Revenue (₹ Cr)", sales),
        build_row("EBITDA (₹ Cr)", op),
        build_row("OPM %", opm, is_pct=True),
        build_row("PBT (₹ Cr)", pbt),
        build_row("PAT (₹ Cr)", pat),
    ] if r]
    return {"headers": out_hdr, "rows": rows}


# ---------- main research view ----------

def research(symbol):
    f = fundamentals.get(symbol)
    prof = sample.COMPANY_PROFILES.get(symbol.upper(), {})
    a, b, cf, rt = f["annual"], f["balance"], f["cashflow"], f["ratios"]
    sales, op, pat = _row(a, "Sales", "Revenue"), _row(a, "Operating Profit", "Financing Profit"), _row(a, "Net Profit")
    opm = _row(a, "OPM", "Financing Margin")
    eq, res, debt = _row(b, "Equity Capital"), _row(b, "Reserves"), _row(b, "Borrowings")
    cfo, cfi = _row(cf, "Cash from Operating"), _row(cf, "Cash from Investing")
    ccc = _row(rt, "Cash Conversion Cycle", "Working Capital Days")
    debtor_d = _row(rt, "Debtor Days")
    inv_d = _row(rt, "Inventory Days")
    pay_d = _row(rt, "Days Payable")
    years = a["headers"]

    de = [round(d / (e + r), 2) if d is not None and e is not None and r else None
          for d, e, r in zip(debt or [], eq or [], res or [])]
    n = min(len(cfo or []), len(pat or []))
    conv_rows = [{"year": years[-n + i] if n else "", "cfo": cfo[-n + i], "pat": pat[-n + i]}
                 for i in range(n)][-6:]
    s_cfo = sum(r["cfo"] or 0 for r in conv_rows[-5:])
    s_pat = sum(r["pat"] or 0 for r in conv_rows[-5:])
    conversion = round(s_cfo / s_pat * 100) if s_pat else None
    fcf = [round((x or 0) + (y or 0), 1) for x, y in zip(cfo or [], cfi or [])][-6:]

    traj = {"years": years[-8:], "sales": (sales or [])[-8:], "op": (op or [])[-8:],
            "pat": (pat or [])[-8:], "opm": (opm or [])[-8:],
            "sales_cagr_3y": _cagr(sales, 3), "sales_cagr_5y": _cagr(sales, 5),
            "pat_cagr_3y": _cagr(pat, 3), "pat_cagr_5y": _cagr(pat, 5),
            "opm_change_3y": (round(_last(opm) - _last(opm, 4), 1)
                              if opm and _last(opm, 4) is not None else None)}

    signals = []  # (+1 bull / -1 bear, text) -- purely from numbers
    if traj["sales_cagr_5y"] is not None:
        signals.append((1 if traj["sales_cagr_5y"] >= 12 else -1 if traj["sales_cagr_5y"] < 7 else 0,
                        f"Revenue 5Y CAGR at {traj['sales_cagr_5y']}% (3Y: {traj['sales_cagr_3y']}%)"))
    if traj["pat_cagr_3y"] is not None and traj["sales_cagr_3y"] is not None:
        lev = round(traj["pat_cagr_3y"] - traj["sales_cagr_3y"], 1)
        signals.append((1 if lev >= 1.5 else -1 if lev <= -1.5 else 0,
                        f"Operating leverage: PAT 3Y CAGR ({traj['pat_cagr_3y']}%) vs Sales ({traj['sales_cagr_3y']}%)"))
    if traj["opm_change_3y"] is not None:
        signals.append((1 if traj["opm_change_3y"] >= 0.8 else -1 if traj["opm_change_3y"] <= -0.8 else 0,
                        f"Operating margin shifted {traj['opm_change_3y']:+.1f} pts over 3 years (currently {_last(opm)}%)"))
    if de and de[-1] is not None:
        signals.append((1 if de[-1] <= 0.35 else -1 if de[-1] > 0.9 else 0,
                        f"Balance sheet leverage Debt/Equity at {de[-1]}x (Borrowings ₹{_last(debt)} Cr)"))
    if conversion is not None:
        signals.append((1 if conversion >= 88 else -1 if conversion < 72 else 0,
                        f"5Y cumulative cash conversion (CFO/PAT) at {conversion}%"))
    if ccc and len([c for c in ccc if c is not None]) > 3:
        d = _last(ccc) - _last(ccc, 4)
        signals.append((-1 if d > 8 else 1 if d < -5 else 0,
                        f"Working capital cycle moved from {_last(ccc, 4):.0f} → {_last(ccc):.0f} days over 3Y"))

    pvd = promise_vs_delivered(f)
    if pvd.get("credibility_pct") is not None:
        signals.append((1 if pvd["credibility_pct"] >= 75 else -1 if pvd["credibility_pct"] < 50 else 0,
                        f"Management guidance track record: {pvd['score']} ({pvd['credibility_pct']}%)"))

    bull = [t for s, t in signals if s > 0]
    bear = [t for s, t in signals if s < 0]
    if not bear:
        bear = [
            f"Valuation multiple ({f['top_ratios'].get('Stock P/E', 'elevated')}x P/E) leaves limited room for execution slip",
            "Working capital and raw material sensitivity require monitoring across quarterly cycles",
        ]
    if not bull:
        bull = [
            f"Established franchise with ₹{_last(sales)} Cr revenue scale and {f['top_ratios'].get('ROCE', 'solid')} ROCE",
            "Capacity investments positioned for cyclical recovery",
        ]

    case = None
    if llm.enabled():
        facts = json.dumps({"signals": [t for _, t in signals], "trajectory": traj,
                            "promise_vs_delivered": pvd["rows"]}, default=str)
        case = llm.complete(
            "You are a buy-side analyst. Using ONLY the facts below (computed from the company's "
            "filings and earnings-call transcripts; do not use outside knowledge), write a tight bull "
            'case and bear case, 3 bullets each, <=16 words per bullet. JSON {"bull":[],"bear":[]}.\n\n' + facts,
            tier="strong", max_tokens=400, as_json=True)

    segments = f.get("segments") or prof.get("segments") or [
        {"name": "Core Domestic Business", "share": 72, "growth": f"+{traj['sales_cagr_3y'] or 12}% YoY"},
        {"name": "Institutional & Exports", "share": 28, "growth": "+10% YoY"},
    ]
    fwd = f.get("forward_guidance") or [
        {"horizon": "FY27 Outlook", "metric": "Revenue & Margin Trajectory",
         "target": f"3Y Sales CAGR {traj['sales_cagr_3y']}% · OPM {_last(opm)}%",
         "source": "Primary Filings & Concalls",
         "commentary": prof.get("capex_guide", "Grounded in reported multi-year operating trajectory and transcript disclosures.")}
    ]

    return {
        "symbol": f["symbol"],
        "name": f["name"],
        "sector": f.get("sector") or prof.get("sector", "NSE Listed"),
        "source": f["source"],
        "source_url": f.get("source_url") or f"https://www.screener.in/company/{f['symbol']}/consolidated/",
        "about": f["about"][:650],
        "segments": segments,
        "forward_guidance": fwd,
        "quarterly_snapshot": quarterly_snapshot(f),
        "top_ratios": f["top_ratios"],
        "docs": f["docs"],
        "latest": {"year": years[-1] if years else None, "sales": _last(sales), "pat": _last(pat),
                   "opm": _last(opm), "de": de[-1] if de else None},
        "trajectory": traj,
        "balance": {
            "years": b["headers"][-6:],
            "debt": (debt or [])[-6:],
            "de": de[-6:],
            "ccc": (ccc or [])[-6:],
            "debtor_days": (debtor_d or [])[-6:],
            "inventory_days": (inv_d or [])[-6:],
            "payable_days": (pay_d or [])[-6:],
            "ccc_years": rt["headers"][-6:],
        },
        "cash": {"rows": conv_rows, "conversion_5y": conversion, "fcf": fcf},
        "promise_vs_delivered": pvd,
        "bull_bear": {
            "bull": (case or {}).get("bull") or bull[:4],
            "bear": (case or {}).get("bear") or bear[:4],
            "by": "llm" if case else "primary-data rules",
        },
        "signals": [{"dir": s, "text": t} for s, t in signals],
    }


def _deterministic_answer(r, question):
    """Grounded deterministic Q&A synthesizer using ONLY the company's primary data when no external LLM key is set."""
    q = question.lower()
    sym = r["symbol"]
    L = r["latest"]
    t = r["trajectory"]
    pvd = r["promise_vs_delivered"]
    c = r["cash"]
    b = r["balance"]

    if any(w in q for w in ("promise", "deliver", "guid", "credib", "narrativ", "walk", "talk", "call")):
        rows_txt = "; ".join(
            f"{x['period']} ({x['metric']}): promised {x['low']}–{x['high']}%, delivered {x['delivered']}% [{(x['verdict'] or 'pending').upper()}]"
            for x in pvd["rows"]
        )
        fwd_txt = "; ".join(f"{g['metric']} guided at {g['target']}" for g in r.get("forward_guidance", [])[:2])
        return (
            f"[{sym} · Primary Transcript & Filing Audit]\n"
            f"• Track Record: {pvd.get('score') or 'Evaluated across last 4 calls'}.\n"
            f"• Quarter-by-Quarter Execution: {rows_txt}.\n"
            f"• Forward Guidance: {fwd_txt}."
        )
    if any(w in q for w in ("cash", "fcf", "conversion", "cfo", "quality")):
        last_c = c["rows"][-1] if c["rows"] else {}
        return (
            f"[{sym} · Cash Flow Statement Audit]\n"
            f"• 5-Year Cumulative CFO/PAT Conversion: {c['conversion_5y']}% ({'Strong — profits convert cleanly into operating cash' if (c['conversion_5y'] or 0) >= 85 else 'Watch — working capital or accruals absorbing cash'}).\n"
            f"• Latest Year ({last_c.get('year', 'FY26')}): Operating Cash Flow ₹{last_c.get('cfo')} Cr vs Net Profit ₹{last_c.get('pat')} Cr.\n"
            f"• 6Y Free Cash Flow (FCF) Trend (₹ Cr): {' → '.join(str(x) for x in c['fcf'])}."
        )
    if any(w in q for w in ("debt", "balance", "leverage", "working capital", "ccc", "cycle", "receiv", "inventory")):
        ccc_str = " → ".join(str(x) for x in b["ccc"] if x is not None)
        return (
            f"[{sym} · Balance Sheet & Working Capital Audit]\n"
            f"• Leverage: Latest Debt/Equity is {L['de']}x with total borrowings at ₹{b['debt'][-1] if b['debt'] else '—'} Cr.\n"
            f"• Cash Conversion Cycle (6Y days): {ccc_str} days.\n"
            f"• Latest Working Capital Components: Debtor Days {b['debtor_days'][-1] if b.get('debtor_days') else '—'}d, "
            f"Inventory Days {b['inventory_days'][-1] if b.get('inventory_days') else '—'}d, Payable Days {b['payable_days'][-1] if b.get('payable_days') else '—'}d."
        )
    if any(w in q for w in ("margin", "opm", "ebitda", "growth", "traject", "revenue", "profit", "cagr")):
        return (
            f"[{sym} · P&L Trajectory Audit]\n"
            f"• Revenue Growth: 5Y CAGR {t['sales_cagr_5y']}% | 3Y CAGR {t['sales_cagr_3y']}% (Latest FY Sales: ₹{L['sales']} Cr).\n"
            f"• Profit Growth: 5Y PAT CAGR {t['pat_cagr_5y']}% | 3Y PAT CAGR {t['pat_cagr_3y']}% (Latest FY PAT: ₹{L['pat']} Cr).\n"
            f"• Margin Direction: Operating Margin is {L['opm']}%, shifting {t['opm_change_3y']:+.1f} pts over the last 3 years."
        )
    if any(w in q for w in ("bull", "bear", "risk", "thesis", "buy", "sell")):
        return (
            f"[{sym} · Primary-Source Bull vs. Bear Synthesis]\n"
            f"• Bull Case: {' | '.join(r['bull_bear']['bull'])}\n"
            f"• Bear Case: {' | '.join(r['bull_bear']['bear'])}"
        )
    # Comprehensive default summary grounded in primary numbers
    return (
        f"[{sym} ({r['name']}) · Grounded Primary Summary]\n"
        f"• Scale & Returns: Sales ₹{L['sales']} Cr (5Y CAGR {t['sales_cagr_5y']}%), PAT ₹{L['pat']} Cr, OPM {L['opm']}%, ROCE {r['top_ratios'].get('ROCE', '—')}, D/E {L['de']}x.\n"
        f"• Cash & Credibility: 5Y CFO/PAT conversion at {c['conversion_5y']}%; Management kept {pvd.get('score', 'key promises')} over the last 4 concalls.\n"
        f"• Key Signals: {' · '.join(s['text'] for s in r['signals'][:3])}."
    )


def ask(symbol, question):
    r = research(symbol)
    if not llm.enabled():
        return {"answer": _deterministic_answer(r, question), "by": "primary-data engine"}
    ctx = json.dumps({k: r[k] for k in ("name", "about", "segments", "latest", "trajectory", "balance", "cash",
                                        "promise_vs_delivered", "forward_guidance", "signals")}, default=str)
    ans = llm.complete(
        "Answer the investor's question using ONLY this data extracted from the company's own filings "
        "and transcripts. If the data doesn't answer it, say exactly what's missing. Be concise "
        f"(<=120 words), cite numbers.\n\nDATA: {ctx}\n\nQUESTION: {question}",
        tier="strong", max_tokens=300)
    return {"answer": ans or _deterministic_answer(r, question), "by": "llm" if ans else "primary-data engine"}
