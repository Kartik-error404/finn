"""Static configuration: the mock portfolio, category taxonomy, and default thresholds."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
CACHE_DIR = os.path.join(ROOT, ".cache")
WEB_DIR = os.path.join(ROOT, "web")
SETTINGS_PATH = os.path.join(DATA_DIR, "settings.json")
PORTFOLIO_PATH = os.path.join(DATA_DIR, "portfolio.json")

# live | demo | auto  (auto = try live, fall back to demo per source)
MODE = os.environ.get("FINN_MODE", "auto").lower()

# Mock portfolio: 18 NSE names across sectors and sizes.
PORTFOLIO = [
    {"symbol": "RELIANCE",   "name": "Reliance Industries",   "sector": "Conglomerate"},
    {"symbol": "HDFCBANK",   "name": "HDFC Bank",             "sector": "Banks"},
    {"symbol": "ICICIBANK",  "name": "ICICI Bank",            "sector": "Banks"},
    {"symbol": "INFY",       "name": "Infosys",               "sector": "IT Services"},
    {"symbol": "TCS",        "name": "Tata Consultancy Svcs", "sector": "IT Services"},
    {"symbol": "KPITTECH",   "name": "KPIT Technologies",     "sector": "IT Services"},
    {"symbol": "ITC",        "name": "ITC",                   "sector": "FMCG"},
    {"symbol": "ASIANPAINT", "name": "Asian Paints",          "sector": "Consumer"},
    {"symbol": "TITAN",      "name": "Titan Company",         "sector": "Consumer"},
    {"symbol": "TRENT",      "name": "Trent",                 "sector": "Retail"},
    {"symbol": "LT",         "name": "Larsen & Toubro",       "sector": "Capital Goods"},
    {"symbol": "POLYCAB",    "name": "Polycab India",         "sector": "Capital Goods"},
    {"symbol": "DIXON",      "name": "Dixon Technologies",    "sector": "Electronics Mfg"},
    {"symbol": "BAJFINANCE", "name": "Bajaj Finance",         "sector": "NBFC"},
    {"symbol": "SUNPHARMA",  "name": "Sun Pharmaceutical",    "sector": "Pharma"},
    {"symbol": "MARUTI",     "name": "Maruti Suzuki",         "sector": "Auto"},
    {"symbol": "DEEPAKNTR",  "name": "Deepak Nitrite",        "sector": "Chemicals"},
    {"symbol": "IRCTC",      "name": "IRCTC",                 "sector": "Travel"},
]

# Suggested on-demand research names (the engine works for any NSE ticker).
RESEARCH_SUGGESTIONS = ["PIDILITIND", "HAL", "NESTLEIND", "DMART", "ZOMATO", "DIXON", "INFY", "DEEPAKNTR"]

# Category -> base priority (0-100). Higher = more likely to move the stock.
CATEGORY_PRIORITY = {
    "results": 90, "M&A": 85, "management_change": 80, "fund_raise": 75,
    "litigation": 72, "pledging": 70, "capex": 65, "credit_rating": 60,
    "bonus_split": 55, "insider_trading": 55, "dividend": 50,
    "press_release": 40, "earnings_call": 35, "agm_egm": 25,
    "postal_ballot": 20, "investor_meetings": 20, "unclassified": 5,
}

DEFAULT_SETTINGS = {
    "volume_multiple": 2.0,     # alert if EOD volume > N x 20-day average
    "price_move_pct": 4.0,      # alert if |daily move| > X %
    "volume_lookback": 20,
    "care_categories": ["results", "M&A", "management_change", "fund_raise",
                        "litigation", "pledging", "credit_rating", "capex"],
}


def load_settings():
    try:
        with open(SETTINGS_PATH) as f:
            return {**DEFAULT_SETTINGS, **json.load(f)}
    except (OSError, ValueError):
        return dict(DEFAULT_SETTINGS)


def save_settings(new):
    s = load_settings()
    for k in DEFAULT_SETTINGS:
        if k in new:
            s[k] = new[k]
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SETTINGS_PATH, "w") as f:
        json.dump(s, f, indent=2)
    return s


def load_portfolio():
    try:
        with open(PORTFOLIO_PATH) as f:
            p = json.load(f)
            if isinstance(p, list) and p:
                return p
    except (OSError, ValueError):
        pass
    return list(PORTFOLIO)


def save_portfolio(items):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(PORTFOLIO_PATH, "w") as f:
        json.dump(items, f, indent=2)
    return items
