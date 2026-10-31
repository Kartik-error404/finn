"""Two-stage classifier: fast regex rules (free, handles ~90% of filings), then the cheap LLM
only for filings the rules can't place. Priority = category weight + user care + context."""
import re

from . import llm
from .config import CATEGORY_PRIORITY

# Order matters: first match wins.
RULES = [
    ("unclassified", r"\besop|\besos|compliance certificate|regulation 74|loss of share|duplicate share|"
                     r"sustainability report|\bbrsr\b|trading window|regulation 39"),
    ("earnings_call", r"earnings call|conference call|concall|transcript|audio recording"),
    ("postal_ballot", r"postal ballot"),
    ("agm_egm", r"annual general meeting|extra-?ordinary general meeting|\bagm\b|\begm\b"),
    ("insider_trading", r"\(pit\)|\bpit\b regulations|insider trading|regulation 7\(2\)"),
    ("pledging", r"pledge|encumbrance"),
    ("credit_rating", r"credit rating|\brating\b|crisil|icra|care ratings|india ratings"),
    ("results", r"financial results?|quarterly results?|results for the quarter|unaudited|audited"),
    ("M&A", r"acqui|merger|amalgamation|demerger|joint venture|\bjv\b|scheme of arrangement|"
            r"stake in|divest|wholly owned subsidiary"),
    ("management_change", r"appointment|resign|cessation|change in management|superannuation|"
                          r"\bcfo\b|\bceo\b|managing director|key managerial"),
    ("fund_raise", r"fund ?raising|rights issue|\bqip\b|preferential|buy-?back|commercial paper|"
                   r"debenture|\bncds?\b|bonds|private placement"),
    ("bonus_split", r"bonus issue|stock split|sub-?division"),
    ("dividend", r"dividend"),
    ("capex", r"capex|capital expenditure|capacity expansion|new plant|greenfield|brownfield"),
    ("press_release", r"order win|bags .*order|wins .*order|won .*order"),
    ("litigation", r"warning letter|usfda|import alert|litigation|penalty|show cause|nclt|insolvency|"
                   r"court|tribunal|adjudication|regulatory order|\bfine\b"),
    ("investor_meetings", r"analyst|investor meet|investor conference|institutional investor"),
    ("press_release", r"press release|clarification|launch|partnership|media release|order"),
]
_COMPILED = [(c, re.compile(p, re.I)) for c, p in RULES]
ROUTINE_HINT = re.compile(r"intimation|notice of|newspaper|publication", re.I)
BIG_HINT = re.compile(r"significant|large|major|crore", re.I)


def classify(subject, text=""):
    blob = f"{subject} || {text}"
    for cat, rx in _COMPILED:
        if rx.search(blob):
            return cat, "rule"
    # Rules failed -> cheap model, one short call, cached forever.
    out = llm.complete(
        "Classify this Indian stock-exchange corporate announcement into exactly one of: "
        + ", ".join(CATEGORY_PRIORITY) + '. Reply JSON {"category": "..."}.\n\n'
        f"Subject: {subject}\nText: {text[:600]}",
        tier="cheap", max_tokens=30, as_json=True)
    if out and out.get("category") in CATEGORY_PRIORITY:
        return out["category"], "llm"
    return "unclassified", "default"


def priority(cat, subject, text, care, price_ctx=None):
    p = CATEGORY_PRIORITY.get(cat, 5)
    reasons = []
    if cat in care:
        p += 10
        reasons.append("type you track")
    if ROUTINE_HINT.search(subject):
        p -= 25
        reasons.append("procedural notice")
    if cat in ("press_release", "capex", "M&A") and BIG_HINT.search(text):
        p += 8
        reasons.append("sizeable")
    if price_ctx and (abs(price_ctx["change_pct"]) >= 3 or price_ctx["volume_multiple"] >= 2):
        p += 10
        reasons.append(f"stock moved {price_ctx['change_pct']:+.1f}% on {price_ctx['volume_multiple']}x vol")
    p = max(0, min(100, p))
    tier = "act" if p >= 75 else "watch" if p >= 40 else "routine"
    return p, tier, reasons
