"""Deterministic DEMO data so the prototype always runs (offline, rate-limited, or sandboxed).
Everything here is synthetic/curated for demo resilience and flagged `source: demo` in the UI.
People named in demo filings are fictional."""
import random
import time

H = 3600


def _rng(key):
    return random.Random(sum(ord(c) * (i + 7) for i, c in enumerate(key)))


# Planted EOD anomalies so the alert engine has rich, varied signals to show.
_SHOCKS = {
    "DIXON": (6.2, 3.1),
    "DEEPAKNTR": (-5.4, 2.4),
    "IRCTC": (1.1, 2.3),
    "SUNPHARMA": (-3.1, 1.9),
    "TRENT": (4.6, 2.5),
    "POLYCAB": (3.8, 2.1),
}

# Rich company metadata: realistic business overview, revenue mix segments, and execution archetype
COMPANY_PROFILES = {
    "RELIANCE": {
        "name": "Reliance Industries Ltd",
        "sector": "Conglomerate",
        "about": "India's largest private sector enterprise operating across Digital Services (Jio), Organised Retail, Oil-to-Chemicals (O2C), and New Energy gigafactories. Consumer businesses (Retail + Digital) now contribute over 52% of consolidated EBITDA.",
        "segments": [
            {"name": "Oil to Chemicals (O2C)", "share": 54, "growth": "+4% YoY"},
            {"name": "Reliance Retail", "share": 26, "growth": "+14% YoY"},
            {"name": "Digital Services (Jio)", "share": 15, "growth": "+18% YoY"},
            {"name": "Oil & Gas E&P", "share": 5, "growth": "+9% YoY"},
        ],
        "archetype": "steady",
        "capex_guide": "₹1,15,000 Cr annual capex intensity moderating as 5G pan-India rollout completes; focus shifting to New Energy electrolyser & solar gigafactories.",
    },
    "HDFCBANK": {
        "name": "HDFC Bank Ltd",
        "sector": "Banks",
        "about": "India's largest private sector bank post the merger with HDFC Ltd, with a pan-India network of 8,800+ branches. Focused on granularity of retail deposits, calibrating loan growth to bring Credit-Deposit (CD) ratio below 90%, and expanding high-yield retail & CRB books.",
        "segments": [
            {"name": "Retail Banking & Mortgages", "share": 51, "growth": "+11% YoY"},
            {"name": "Commercial & Rural (CRB)", "share": 27, "growth": "+17% YoY"},
            {"name": "Corporate & Wholesale", "share": 22, "growth": "+5% YoY"},
        ],
        "archetype": "beat",
        "capex_guide": "Adding 750–900 branches annually in semi-urban catchments; opex-to-assets guided toimprove 25bps over 4 quarters.",
    },
    "ICICIBANK": {
        "name": "ICICI Bank Ltd",
        "sector": "Banks",
        "about": "Premier private sector bank delivering industry-leading RoA (>2.2%) through risk-calibrated core operating profit, digital 360-degree corporate ecosystem, and disciplined unsecured retail underwriting.",
        "segments": [
            {"name": "Retail Banking", "share": 54, "growth": "+16% YoY"},
            {"name": "SME & Business Banking", "share": 24, "growth": "+24% YoY"},
            {"name": "Domestic Corporate", "share": 22, "growth": "+12% YoY"},
        ],
        "archetype": "beat",
        "capex_guide": "Tech & digital infrastructure spend maintained at ~9.5% of operating expenses; Net NPA guided below 0.50%.",
    },
    "INFY": {
        "name": "Infosys Ltd",
        "sector": "IT Services",
        "about": "Global leader in next-generation digital services, cloud (Cobalt), enterprise AI (Topaz), and core engineering consulting across 56 countries, with 317,000+ employees.",
        "segments": [
            {"name": "Financial Services", "share": 28, "growth": "+5% YoY"},
            {"name": "Manufacturing & Auto", "share": 16, "growth": "+11% YoY"},
            {"name": "Retail & CPG", "share": 14, "growth": "+2% YoY"},
            {"name": "Energy, Utilities & Hi-Tech", "share": 42, "growth": "+7% YoY"},
        ],
        "archetype": "mixed",
        "capex_guide": "FY27 constant-currency revenue growth guided at 4.5%–5.0% with operating margin band strictly held at 20%–22% under Project Maximus.",
    },
    "TCS": {
        "name": "Tata Consultancy Services Ltd",
        "sector": "IT Services",
        "about": "Flagship IT consulting and digital transformation powerhouse of the Tata Group with industry-benchmark operating margins, $42B+ TCV order book, and deep vertical integration across BFSI and consumer markets.",
        "segments": [
            {"name": "BFSI", "share": 31, "growth": "+3% YoY"},
            {"name": "Consumer Business", "share": 16, "growth": "+4% YoY"},
            {"name": "Life Sciences & Healthcare", "share": 11, "growth": "+8% YoY"},
            {"name": "Manufacturing, Tech & Regional", "share": 42, "growth": "+12% YoY"},
        ],
        "archetype": "steady",
        "capex_guide": "Aspirational operating margin band of 26%–28% with 80%–100% of Free Cash Flow returned to shareholders via dividends and buybacks.",
    },
    "KPITTECH": {
        "name": "KPIT Technologies Ltd",
        "sector": "IT Services",
        "about": "Pure-play global automotive ER&D software specialist focused on Software-Defined Vehicles (SDV), autonomous driving middleware, electric powertrain, and connected cockpit architecture for top global OEMs.",
        "segments": [
            {"name": "Passenger Cars ER&D", "share": 76, "growth": "+24% YoY"},
            {"name": "Commercial Vehicles", "share": 22, "growth": "+14% YoY"},
            {"name": "Off-Highway & Others", "share": 2, "growth": "+8% YoY"},
        ],
        "archetype": "beat",
        "capex_guide": "Constant-currency revenue growth guided at 18%–22% with EBITDA margins expanding to 20.5%+ on offshoring leverage.",
    },
    "ITC": {
        "name": "ITC Ltd",
        "sector": "FMCG",
        "about": "Diversified conglomerate spanning market-leading Cigarettes, scaled branded FMCG (Aashirvaad, Sunfeast, Bingo!, Yippee!), Agri Business leaf/spices exports, and Paperboards & Packaging.",
        "segments": [
            {"name": "FMCG - Cigarettes", "share": 44, "growth": "+7% YoY"},
            {"name": "FMCG - Others (Branded)", "share": 29, "growth": "+11% YoY"},
            {"name": "Agri Business", "share": 16, "growth": "+14% YoY"},
            {"name": "Paperboards & Packaging", "share": 11, "growth": "-2% YoY"},
        ],
        "archetype": "steady",
        "capex_guide": "₹3,000–3,500 Cr annual capex into integrated food parks and value-added paperboard capacity; FMCG-Others EBITDA margin targeted to expand 80–100bps annually.",
    },
    "ASIANPAINT": {
        "name": "Asian Paints Ltd",
        "sector": "Consumer",
        "about": "India's largest decorative coatings and home décor company with 160,000+ dealer touchpoints, backward-integrated VAM/white cement manufacturing, and growing waterproofing & industrial coatings verticals.",
        "segments": [
            {"name": "Domestic Decorative Coatings", "share": 84, "growth": "+2% YoY"},
            {"name": "Industrial & Auto Coatings", "share": 7, "growth": "+12% YoY"},
            {"name": "International Operations", "share": 5, "growth": "+4% YoY"},
            {"name": "Home Décor & Bath/Kitchen", "share": 4, "growth": "+9% YoY"},
        ],
        "archetype": "miss",
        "capex_guide": "₹2,200 Cr backward-integration capex for Vinyl Acetate Monomer (VAM) and white cement; PBDIT margin guided in 18%–20% band amidst heightened competitive discounting.",
    },
    "TITAN": {
        "name": "Titan Company Ltd",
        "sector": "Consumer",
        "about": "Tata Group lifestyle powerhouse anchoring India's organised jewellery transition via Tanishq, Mia, Zoya, and CaratLane, alongside Watches & Wearables, Titan EyeCare, and Taneira ethnic wear.",
        "segments": [
            {"name": "Jewellery (Tanishq / CaratLane)", "share": 88, "growth": "+21% YoY"},
            {"name": "Watches & Wearables", "share": 8, "growth": "+15% YoY"},
            {"name": "EyeCare & Emerging Lifestyle", "share": 4, "growth": "+11% YoY"},
        ],
        "archetype": "beat",
        "capex_guide": "Jewellery EBIT margin band guided at 11.5%–12.5% after customs duty normalisation; adding 40–50 new Tanishq stores and 60+ Mia/CaratLane stores in FY27.",
    },
    "TRENT": {
        "name": "Trent Ltd",
        "sector": "Retail",
        "about": "Fastest-growing fashion and lifestyle retailer in India operating Westside (department stores), Zudio (value fast-fashion phenomenon with 580+ stores), and Star Bazaar grocery hypermarkets.",
        "segments": [
            {"name": "Zudio (Value Fast Fashion)", "share": 58, "growth": "+52% YoY"},
            {"name": "Westside (Apparel & Lifestyle)", "share": 36, "growth": "+18% YoY"},
            {"name": "Emerging Formats & Star JV", "share": 6, "growth": "+29% YoY"},
        ],
        "archetype": "beat",
        "capex_guide": "Targeting 180–200 net new Zudio stores and 30 Westside stores annually with 100% private-label inventory and <45 day design-to-rack cycle.",
    },
    "LT": {
        "name": "Larsen & Toubro Ltd",
        "sector": "Capital Goods",
        "about": "India's premier EPC, hi-tech manufacturing, defense, and green infrastructure conglomerate with a record ₹5.1 Lakh Crore order book spanning India, Middle East energy transition, and renewables.",
        "segments": [
            {"name": "Infrastructure Projects", "share": 51, "growth": "+16% YoY"},
            {"name": "Energy & Hydrocarbon", "share": 18, "growth": "+28% YoY"},
            {"name": "IT & Technology Services", "share": 21, "growth": "+7% YoY"},
            {"name": "Hi-Tech Mfg & Defence", "share": 10, "growth": "+22% YoY"},
        ],
        "archetype": "beat",
        "capex_guide": "Order inflow growth guided at 12%–15% YoY with core Projects & Manufacturing EBITDA margin improving to 8.3%–8.5% and working capital held at 12% of sales.",
    },
    "POLYCAB": {
        "name": "Polycab India Ltd",
        "sector": "Capital Goods",
        "about": "Market leader in India's organised Wires & Cables industry (~26% market share) with expanding Extra-High-Voltage (EHV) capabilities, export footprint across 79 countries, and FMEG electrical appliances.",
        "segments": [
            {"name": "Wires & Cables (Domestic + Export)", "share": 88, "growth": "+24% YoY"},
            {"name": "Fast Moving Electrical Goods (FMEG)", "share": 7, "growth": "+14% YoY"},
            {"name": "EPC & Turnkey Projects", "share": 5, "growth": "+35% YoY"},
        ],
        "archetype": "beat",
        "capex_guide": "Project Spring: ₹1,100–1,200 Cr annual capex over 3 years into EHV cables in Halol, Gujarat; W&C EBIT margin guided at 13%–14%.",
    },
    "DIXON": {
        "name": "Dixon Technologies (India) Ltd",
        "sector": "Electronics Mfg",
        "about": "India's largest Electronic Manufacturing Services (EMS) leader across smartphones/PLI, LED TVs, washing machines, IT hardware/laptops, and backward-integrated display modules.",
        "segments": [
            {"name": "Mobile & EMS Division", "share": 64, "growth": "+95% YoY"},
            {"name": "Consumer Electronics (TVs)", "share": 17, "growth": "+6% YoY"},
            {"name": "Home Appliances", "share": 11, "growth": "+18% YoY"},
            {"name": "Lighting & IT Hardware", "share": 8, "growth": "+22% YoY"},
        ],
        "archetype": "beat",
        "capex_guide": "₹650 Cr capex into Noida display module JV & Chennai IT hardware plant; backward integration expected to lift blended EBITDA margin by 60–80bps.",
    },
    "BAJFINANCE": {
        "name": "Bajaj Finance Ltd",
        "sector": "NBFC",
        "about": "India's premier diversified consumer and SME non-bank lender with ₹3.7 Lakh Crore AUM, 92M+ customer franchise, and omnichannel payments/wealth distribution platform.",
        "segments": [
            {"name": "Urban B2C & Consumer Durable", "share": 39, "growth": "+26% YoY"},
            {"name": "Mortgages (BHFL)", "share": 31, "growth": "+24% YoY"},
            {"name": "SME & Commercial Lending", "share": 21, "growth": "+29% YoY"},
            {"name": "Rural & Auto Finance", "share": 9, "growth": "+15% YoY"},
        ],
        "archetype": "steady",
        "capex_guide": "AUM growth guided at 25%–27% YoY with credit cost contained at 1.75%–1.85% and RoE strictly maintained at 21%–22%.",
    },
    "SUNPHARMA": {
        "name": "Sun Pharmaceutical Industries Ltd",
        "sector": "Pharma",
        "about": "World's 4th largest specialty generic pharmaceutical company and #1 in India domestic formulations (8.5% market share), powered by a $1.1B+ global dermatology, ophthalmology, and oncology specialty portfolio (Ilumya, Cequa, Winlevi).",
        "segments": [
            {"name": "India Branded Formulations", "share": 33, "growth": "+12% YoY"},
            {"name": "US Specialty & Generics", "share": 32, "growth": "+15% YoY"},
            {"name": "Emerging Markets", "share": 18, "growth": "+9% YoY"},
            {"name": "Rest of World & API", "share": 17, "growth": "+7% YoY"},
        ],
        "archetype": "mixed",
        "capex_guide": "R&D spend guided at 8%–9% of sales (42% allocated to global specialty clinical trials); high single-digit consolidated top-line growth despite USFDA Halol remediation.",
    },
    "MARUTI": {
        "name": "Maruti Suzuki India Ltd",
        "sector": "Auto",
        "about": "India's passenger vehicle market leader (~41% market share) pivoting towards Utility Vehicles (Brezza, Grand Vitara, Fronx), CNG powertrains (32% of mix), strong hybrids, and rapidly scaling exports to 100+ markets.",
        "segments": [
            {"name": "Utility Vehicles & SUVs", "share": 48, "growth": "+22% YoY"},
            {"name": "Compact & Mini Hatchbacks", "share": 34, "growth": "-4% YoY"},
            {"name": "Exports (Africa, LatAm, ME)", "share": 14, "growth": "+16% YoY"},
            {"name": "Spares & Light Commercial", "share": 4, "growth": "+9% YoY"},
        ],
        "archetype": "steady",
        "capex_guide": "₹10,000 Cr FY27 capex for Kharkhoda Phase-2 plant and e-Vitara EV assembly line; EBIT margin supported by higher SUV/CNG realization and yen hedging.",
    },
    "DEEPAKNTR": {
        "name": "Deepak Nitrite Ltd",
        "sector": "Chemicals",
        "about": "Leading Indian chemical intermediates manufacturer commanding >65% domestic market share in Phenol, Acetone, and Isopropyl Alcohol (IPA), alongside Advanced Intermediates for agrochemicals, dyes, and pharma.",
        "segments": [
            {"name": "Phenolics (Phenol, Acetone, IPA)", "share": 68, "growth": "+9% YoY"},
            {"name": "Advanced Intermediates", "share": 32, "growth": "-7% YoY"},
        ],
        "archetype": "miss",
        "capex_guide": "₹14,000 Cr multi-year integrated polycarbonate & MIBK/MIBC downstream capex at Dahej; near-term agrochemical destocking and Chinese dumping pressuring spreads.",
    },
    "IRCTC": {
        "name": "Indian Railway Catering & Tourism Corp",
        "sector": "Travel",
        "about": "Statutory monopoly for Indian Railways online ticketing (~83% reserved ticket share), packaged drinking water (Rail Neer), and onboard/station hospitality including Vande Bharat & Bharat Gaurav tourist trains.",
        "segments": [
            {"name": "Catering Services", "share": 46, "growth": "+17% YoY"},
            {"name": "Internet Ticketing (High Margin)", "share": 32, "growth": "+14% YoY"},
            {"name": "Tourism & Bharat Gaurav", "share": 14, "growth": "+24% YoY"},
            {"name": "Rail Neer (19 Plants)", "share": 8, "growth": "+11% YoY"},
        ],
        "archetype": "steady",
        "capex_guide": "Asset-light model with >82% EBIT margin in Internet Ticketing; expanding UPI convenience fee share and adding 2 new Rail Neer bottling plants.",
    },
    "PIDILITIND": {
        "name": "Pidilite Industries Ltd",
        "sector": "Chemicals / Consumer",
        "about": "Undisputed pioneer in consumer adhesives, sealants, and construction waterproofing in India (Fevicol, Fevikwik, Dr. Fixit, M-Seal, Roff tile adhesives) with an unmatched moat of 6M+ carpenter and mason loyalty relationships.",
        "segments": [
            {"name": "Consumer & Bazaar (Adhesives/Dr. Fixit)", "share": 79, "growth": "+13% YoY"},
            {"name": "B2B Industrial Resins & Pigments", "share": 21, "growth": "+16% YoY"},
        ],
        "archetype": "beat",
        "capex_guide": "Underlying volume growth (UVG) guided at 10%–12% with EBITDA margin maintained at the upper end of the 20%–24% band due to benign VAM input costs (<$950/MT).",
    },
    "HAL": {
        "name": "Hindustan Aeronautics Ltd",
        "sector": "Defence & Aerospace",
        "about": "Sovereign aerospace and defence prime manufacturer producing LCA Tejas Mk1A fighters, LCH Prachand & ALH Dhruv helicopters, aero-engines, and fleet Repair & Overhaul (ROH) with an order book exceeding ₹1.2 Lakh Crore (~4x revenue).",
        "segments": [
            {"name": "Repair, Overhaul & Spares (ROH)", "share": 66, "growth": "+15% YoY"},
            {"name": "Manufacturing (Tejas / Helicopters)", "share": 27, "growth": "+24% YoY"},
            {"name": "Design & Development", "share": 7, "growth": "+11% YoY"},
        ],
        "archetype": "beat",
        "capex_guide": "₹3,000 Cr annual capex for Nashik 3rd LCA Tejas production line and GE-F404/F414 engine integration; EBITDA margins guided at 29%–31%.",
    },
    "NESTLEIND": {
        "name": "Nestlé India Ltd",
        "sector": "FMCG",
        "about": "Blue-chip nutrition and packaged foods leader dominating Infant Nutrition (Cerelac, Lactogen), Prepared Dishes (Maggi), Confectionery (KitKat, Munch), and Powdered/Liquid Beverages (Nescafé) with deep RURBAN village penetration.",
        "segments": [
            {"name": "Milk Products & Infant Nutrition", "share": 40, "growth": "+8% YoY"},
            {"name": "Prepared Dishes & Cooking Aids (Maggi)", "share": 31, "growth": "+11% YoY"},
            {"name": "Confectionery (KitKat / Munch)", "share": 16, "growth": "+14% YoY"},
            {"name": "Beverages (Nescafé)", "share": 13, "growth": "+17% YoY"},
        ],
        "archetype": "steady",
        "capex_guide": "₹5,000 Cr capex through FY28 including the new 10th factory in Odisha; operating margins guided at 23%–24% managing green coffee & cocoa inflation.",
    },
    "DMART": {
        "name": "Avenue Supermarts Ltd (DMart)",
        "sector": "Retail",
        "about": "High-efficiency value supermarket chain operating 380+ owned-real-estate stores on an Everyday Low Cost / Everyday Low Price (EDLC/EDLP) model, complemented by scaling DMart Ready e-commerce pickup points across 24 cities.",
        "segments": [
            {"name": "Foods & Staples", "share": 57, "growth": "+19% YoY"},
            {"name": "Non-Foods (FMCG / Personal Care)", "share": 21, "growth": "+16% YoY"},
            {"name": "General Merchandise & Apparel", "share": 22, "growth": "+14% YoY"},
        ],
        "archetype": "mixed",
        "capex_guide": "Targeting 45–50 new brick-and-mortar store additions in FY27 (~₹2,800 Cr self-funded land+building capex); EBITDA margin held in 7.8%–8.4% band amidst quick-commerce competition.",
    },
    "ZOMATO": {
        "name": "Eternal Ltd (Zomato / Blinkit)",
        "sector": "Consumer Tech",
        "about": "Hyperlocal commerce platform combining cash-generative Food Delivery, hyper-growth Quick Commerce (Blinkit with 1,000+ dark stores), Hyperpure B2B restaurant supplies, and District Going-Out ticketing.",
        "segments": [
            {"name": "Food Delivery", "share": 46, "growth": "+23% YoY"},
            {"name": "Blinkit (Quick Commerce)", "share": 28, "growth": "+118% YoY"},
            {"name": "Hyperpure (B2B Supplies)", "share": 22, "growth": "+58% YoY"},
            {"name": "Going-Out & Ticketing", "share": 4, "growth": "+85% YoY"},
        ],
        "archetype": "beat",
        "capex_guide": "Scaling Blinkit dark-store count to 2,000 by Dec 2026 while maintaining positive adjusted EBITDA; consolidated GOV growth guided at 30%+ YoY.",
    },
}


def prices(symbol, days=65):
    r = _rng(symbol)
    px = r.uniform(350, 4200)
    base_vol = r.uniform(4.5e5, 5.5e6)
    now = int(time.time())
    rows = []
    for i in range(days):
        px *= 1 + r.gauss(0.0005, 0.012)
        rows.append({
            "date": now - (days - i) * 86400,
            "close": px,
            "volume": base_vol * r.uniform(0.68, 1.32),
        })
    if symbol in _SHOCKS:
        move, vm = _SHOCKS[symbol]
        rows[-1]["close"] = rows[-2]["close"] * (1 + move / 100)
        rows[-1]["volume"] = base_vol * vm
    return rows


def announcements():
    now = time.time()
    A = lambda sym, hrs, subj, text="", url="": {
        "symbol": sym,
        "subject": subj,
        "text": text,
        "ts": now - hrs * H,
        "url": url or f"https://www.nseindia.com/get-quotes/equity?symbol={sym}",
    }
    return [
        A("INFY", 2.5, "Outcome of Board Meeting - Audited Q2 FY27 Financial Results",
          "Board approved audited consolidated financial results for the quarter and half year ended September 30, 2026. "
          "Constant currency revenue grew 3.8% YoY; large deal TCV stood at $3.1 billion with 58% net new wins. "
          "FY27 revenue guidance revised to 4.5%-5.0% CC while operating margin guidance retained at 20%-22%."),
        A("HDFCBANK", 4.5, "Change in Management - Appointment of Chief Financial Officer",
          "The Board approved the appointment of Ms. Ananya Rao (DEMO PERSON) as Chief Financial Officer "
          "w.e.f. November 15, 2026, consequent to the superannuation of the current CFO. "
          "Brief profile: Ms. Rao is a Chartered Accountant and Wharton AMP alumna with 22 years of leadership experience. "
          "She served as Group CFO at ICICI Lombard for 6 years and previously spent 12 years in treasury, ALM, and "
          "balance-sheet management at Citibank in Mumbai and Singapore."),
        A("DIXON", 6.0, "Outcome of Board Meeting - Unaudited Q2 FY27 Financial Results & Display JV",
          "Board approved Q2 FY27 unaudited financial results with quarterly revenue surging 68% YoY led by mobile EMS PLI ramp-up, "
          "and executed definitive JV agreement with HKC Corp for display module manufacturing in Noida (Rs 650 crore Phase-1 capex)."),
        A("SUNPHARMA", 7.2, "Receipt of Warning Letter from USFDA for Halol Facility",
          "The Company has received a Warning Letter from the USFDA for its Halol parenteral facility in Gujarat following an "
          "inspection conducted in May 2026 summarizing cGMP observations. Existing commercial supplies from Halol will continue "
          "subject to import alert exemptions, while new ANDA approvals from this plant remain on hold pending remediation."),
        A("POLYCAB", 9.0, "Board Approves Rs 1,200 Crore Capex for EHV Cable Plant",
          "Board approved capital expenditure of Rs 1,200 crore under Project Spring for setting up a state-of-the-art Extra-High-Voltage (EHV) "
          "220kV-550kV underground cable manufacturing facility at Halol, Gujarat, funded 100% via internal accruals and scheduled for commissioning by Q4 FY28."),
        A("TRENT", 10.8, "Acquisition - 51% Controlling Stake in Regional Value Fashion Chain",
          "The Company has signed definitive agreements to acquire a 51% controlling stake in a 42-store South India regional apparel retailer "
          "for a cash consideration of Rs 640 crore (0.9x EV/Sales), accelerating Zudio's footprint in Tier-3 clusters subject to CCI approval."),
        A("BAJFINANCE", 14.5, "Credit Rating - CRISIL AAA/Stable Reaffirmed on Rs 15,000 Cr NCDs",
          "CRISIL Ratings has reaffirmed its highest long-term rating at CRISIL AAA/Stable on the Company's Non-Convertible Debentures and Subordinated Debt."),
        A("ICICIBANK", 16.5, "Fund Raising - Issue of Rs 5,000 Crore Basel III Tier II Bonds",
          "Board approved raising up to Rs 5,000 crore through long-term Basel III compliant Tier II bonds at 7.42% coupon on a private placement basis."),
        A("ITC", 18.5, "Declaration of Interim Dividend of Rs 6.50/Share and Record Date",
          "Board declared an interim dividend of Rs 6.50 per ordinary share of Re 1 each for FY27. Record date fixed as November 7, 2026."),
        A("RELIANCE", 20.0, "Transcript of Q2 FY27 Earnings Conference Call",
          "Full verbatim transcript of the institutional analyst/investor earnings conference call held on October 24, 2026 covering Jio ARPU hike impact and New Energy gigafactory timelines."),
        A("DEEPAKNTR", 21.0, "Disclosure under SAST Reg 31 - Release of Promoter Pledge",
          "Promoter group entity has released encumbrance/pledge over 1.2% of total equity share capital following scheduled debt prepayment."),
        A("KPITTECH", 22.0, "Disclosure under SEBI (PIT) Regulations - Insider Market Sale",
          "Designated person (Executive Director) has sold 40,000 equity shares (Rs 6.1 crore value) in the open market for personal tax and liquidity purposes."),
        A("TCS", 22.8, "Analyst / Institutional Investor Meet - Intimation under Reg 30",
          "Management will participate in 1-on-1 institutional investor meetings at the Global Tech Conference in Mumbai on November 4, 2026."),
        A("ASIANPAINT", 23.3, "Allotment of 4,512 Equity Shares under ESOP Scheme",
          "Allotment of 4,512 equity shares of face value Re 1 each to eligible employees under the Employee Stock Option Plan 2021."),
        A("MARUTI", 23.7, "Compliance Certificate under Regulation 74(5) of SEBI (DP) Regulations",
          "Routine quarterly confirmation from Registrar and Share Transfer Agent regarding dematerialisation of share certificates."),
        A("TITAN", 30.0, "Clarification on Media Report Regarding Eyewear Business",
          "With reference to news appearing in financial media, the Company clarifies it has no proposal under consideration for divesting or spinning off the Titan EyeCare division."),
        A("LT", 34.0, "Press Release - L&T Wins Major Rs 2,500-5,000 Cr HVDC Grid Order in Middle East",
          "L&T Power Transmission & Distribution vertical has secured a major EPC order (Rs 2,500-5,000 crore) for a 500kV HVDC renewable integration grid in Saudi Arabia."),
        A("IRCTC", 40.0, "Board Meeting Intimation for Unaudited Q2 FY27 Financial Results",
          "Notice that a meeting of the Board of Directors will be held on November 10, 2026 to consider unaudited financial results for Q2 FY27."),
        A("KPITTECH", 52.0, "Change in Management - Resignation of Independent Director",
          "Mr. Vikram Sethi (DEMO PERSON) has stepped down as Non-Executive Independent Director w.e.f. October 28, 2026 citing increasing international board commitments. "
          "Brief profile: Mr. Sethi is a former automotive Tier-1 CEO based in Munich with 28 years in embedded powertrain systems. Confirmation provided that there are no other material reasons."),
        A("MARUTI", 60.0, "Scrutinizer's Report and Postal Ballot Voting Results",
          "Results of postal ballot for appointment of Independent Director — ordinary and special resolutions passed with 98.4% majority."),
        A("HDFCBANK", 75.0, "Newspaper Publication - Notice of Loss of Physical Share Certificates",
          "Public notice issued pursuant to Regulation 39(3) regarding issue of duplicate letters of confirmation."),
        A("ITC", 90.0, "Filing of Business Responsibility and Sustainability Report (BRSR)",
          "Submission of audited BRSR Core ESG disclosures for the financial year."),
        A("TRENT", 110.0, "Outcome of Board Meeting - Q2 FY27 Financial Results",
          "Board approved Q2 FY27 financial results with standalone revenue up 39% YoY and 44 new Zudio stores opened during the quarter."),
        A("SUNPHARMA", 130.0, "Notice of Extraordinary General Meeting",
          "Notice convening EGM via video conferencing for approval of material related-party transactions."),
    ]


def _series(r, start, growth, vol, n):
    out, v = [], start
    for _ in range(n):
        out.append(round(v, 1))
        v *= 1 + growth + r.gauss(0, vol)
    return out


def fundamentals(symbol):
    symbol = symbol.upper().strip()
    r = _rng(symbol + "f_v2")
    prof = COMPANY_PROFILES.get(symbol, {})
    archetype = prof.get("archetype") or r.choice(["beat", "steady", "mixed"])

    years = [f"Mar {y}" for y in range(2017, 2027)]
    quarters = [
        "Sep 2024", "Dec 2024", "Mar 2025", "Jun 2025",
        "Sep 2025", "Dec 2025", "Mar 2026", "Jun 2026", "Sep 2026"
    ]

    if archetype == "beat":
        g = r.uniform(0.15, 0.24)
        opm0 = r.uniform(0.16, 0.27)
        drift = 0.004
    elif archetype == "miss":
        g = r.uniform(0.06, 0.11)
        opm0 = r.uniform(0.15, 0.22)
        drift = -0.005
    elif archetype == "mixed":
        g = r.uniform(0.09, 0.15)
        opm0 = r.uniform(0.18, 0.25)
        drift = 0.001
    else:
        g = r.uniform(0.11, 0.17)
        opm0 = r.uniform(0.17, 0.26)
        drift = 0.002

    def pl(sales, opm_list):
        op = [s * (m / 100.0) for s, m in zip(sales, opm_list)]
        oi = [s * 0.016 for s in sales]
        intr = [s * r.uniform(0.004, 0.022) for s in sales]
        dep = [s * 0.032 for s in sales]
        pbt = [a + b - c - d for a, b, c, d in zip(op, oi, intr, dep)]
        np_ = [p * 0.75 for p in pbt]
        R = lambda xs: [round(x, 1) for x in xs]
        return {
            "Sales": R(sales),
            "Expenses": R([s - o for s, o in zip(sales, op)]),
            "Operating Profit": R(op),
            "OPM %": [round(m, 1) for m in opm_list],
            "Other Income": R(oi),
            "Interest": R(intr),
            "Depreciation": R(dep),
            "Profit before tax": R(pbt),
            "Tax %": [25] * len(sales),
            "Net Profit": R(np_),
        }

    annual_sales = _series(r, r.uniform(2500, 38000), g, 0.025, len(years))
    annual_opm = [round(max(8.0, (opm0 + drift * i + r.gauss(0, 0.006)) * 100), 1) for i in range(len(years))]
    annual = pl(annual_sales, annual_opm)

    # Construct quarterly series with controlled YoY growth & OPM so Promise vs. Delivered is realistic!
    base_q = annual_sales[-2] / 4.0
    q_sales_first4 = [round(base_q * (1 + 0.02 * i), 1) for i in range(4)]  # Sep 24 .. Jun 25
    guided_rev_low = round(g * 100)
    guided_rev_high = guided_rev_low + 2
    guided_opm_low = round(opm0 * 100)
    guided_opm_high = guided_opm_low + 2

    if archetype == "beat":
        # Beat or met all 4 quarters!
        yoy_growths = [
            (guided_rev_high + 1.8) / 100.0,  # Sep 25
            (guided_rev_high + 1.4) / 100.0,  # Dec 25 -> BEAT
            (guided_rev_low + 1.2) / 100.0,   # Mar 26 -> MET
            (guided_rev_high + 2.1) / 100.0,  # Jun 26 -> BEAT
            (guided_rev_high + 2.6) / 100.0,  # Sep 26 -> BEAT
        ]
        q_opms = [
            guided_opm_low, guided_opm_low, guided_opm_low + 0.5, guided_opm_low + 1.0,
            guided_opm_low + 1.0, guided_opm_high + 0.5, guided_opm_high + 0.8,
            guided_opm_high + 1.1, guided_opm_high + 1.4
        ]
    elif archetype == "steady":
        # Met 3/4, Beat 1/4
        yoy_growths = [
            (guided_rev_low + 0.8) / 100.0,
            (guided_rev_low + 1.1) / 100.0,   # Dec 25 -> MET
            (guided_rev_high + 0.9) / 100.0,  # Mar 26 -> BEAT
            (guided_rev_low + 0.6) / 100.0,   # Jun 26 -> MET
            (guided_rev_low + 1.4) / 100.0,   # Sep 26 -> MET
        ]
        q_opms = [
            guided_opm_low, guided_opm_low, guided_opm_low, guided_opm_low + 0.5,
            guided_opm_low + 0.6, guided_opm_low + 1.0, guided_opm_low + 1.2,
            guided_opm_low + 1.1, guided_opm_high + 0.4
        ]
    elif archetype == "mixed":
        # Missed top-line once, Met once, Beat margins
        yoy_growths = [
            (guided_rev_low - 1.2) / 100.0,
            (guided_rev_low - 1.6) / 100.0,   # Dec 25 -> MISSED rev
            (guided_rev_low + 0.7) / 100.0,   # Mar 26 -> MET rev
            (guided_rev_low - 0.8) / 100.0,   # Jun 26
            (guided_rev_low + 1.1) / 100.0,   # Sep 26
        ]
        q_opms = [
            guided_opm_low, guided_opm_low, guided_opm_low, guided_opm_low,
            guided_opm_low + 0.5, guided_opm_low + 1.0, guided_opm_low + 1.4,
            guided_opm_high + 0.6, guided_opm_high + 0.9
        ]
    else:  # "miss" -> Narrative vs Numbers divergence (management optimistic, delivery lagged)
        yoy_growths = [
            (guided_rev_low - 2.5) / 100.0,
            (guided_rev_low - 3.4) / 100.0,   # Dec 25 -> MISSED
            (guided_rev_low - 2.1) / 100.0,   # Mar 26 -> MISSED
            (guided_rev_low + 0.4) / 100.0,   # Jun 26 -> MET
            (guided_rev_low - 1.9) / 100.0,   # Sep 26 -> MISSED
        ]
        q_opms = [
            guided_opm_low + 1.0, guided_opm_low + 0.5, guided_opm_low, guided_opm_low - 0.5,
            guided_opm_low - 1.0, guided_opm_low - 1.5, guided_opm_low - 1.8,
            guided_opm_low + 0.3, guided_opm_low - 2.1
        ]

    q_sales_last5 = [
        round(q_sales_first4[0] * (1 + yoy_growths[0]), 1),  # Sep 25
        round(q_sales_first4[1] * (1 + yoy_growths[1]), 1),  # Dec 25
        round(q_sales_first4[2] * (1 + yoy_growths[2]), 1),  # Mar 26
        round(q_sales_first4[3] * (1 + yoy_growths[3]), 1),  # Jun 26
    ]
    q_sales_last5.append(round(q_sales_last5[0] * (1 + yoy_growths[4]), 1))  # Sep 26
    q_sales = q_sales_first4 + q_sales_last5

    eq = 100.0
    reserves = _series(r, annual_sales[0] * 0.52, g * 0.92, 0.02, len(years))
    debt_mult = 0.08 if archetype in ("beat", "steady") else 0.42
    borrow = _series(r, annual_sales[0] * debt_mult, -0.05 if archetype == "beat" else 0.06, 0.04, len(years))
    cfo_mult = 0.98 if archetype in ("beat", "steady") else 0.72
    cfo = [round(p * (cfo_mult + r.uniform(-0.08, 0.14)), 1) for p in annual["Net Profit"]]
    cfi = [round(-s * r.uniform(0.04, 0.08), 1) for s in annual_sales]
    debtor = _series(r, r.uniform(28, 62), -0.02 if archetype == "beat" else 0.03, 0.03, len(years))
    inv = _series(r, r.uniform(24, 75), -0.02 if archetype == "beat" else 0.03, 0.03, len(years))
    pay = _series(r, r.uniform(32, 65), 0.0, 0.03, len(years))

    guidance = [
        {
            "period": "Sep 2025",
            "metric": "Revenue growth YoY",
            "low": guided_rev_low,
            "high": guided_rev_high,
            "quote": f"We are confident of delivering {guided_rev_low}–{guided_rev_high}% YoY top-line growth in Q3 backed by order book execution.",
        },
        {
            "period": "Dec 2025",
            "metric": "Revenue growth YoY",
            "low": guided_rev_low,
            "high": guided_rev_high,
            "quote": f"Demand pipeline supports {guided_rev_low}–{guided_rev_high}% YoY revenue trajectory entering Q4.",
        },
        {
            "period": "Mar 2026",
            "metric": "EBITDA margin",
            "low": guided_opm_low,
            "high": guided_opm_high,
            "quote": f"Operating leverage and input cost stability will keep EBITDA margin within {guided_opm_low}–{guided_opm_high}%.",
        },
        {
            "period": "Jun 2026",
            "metric": "EBITDA margin",
            "low": guided_opm_low,
            "high": guided_opm_high,
            "quote": f"We reiterate our {guided_opm_low}–{guided_opm_high}% operating margin band for Q2 FY27.",
        },
    ]

    forward_guidance = [
        {
            "horizon": "FY27 Full Year",
            "metric": "Revenue Growth YoY",
            "target": f"{guided_rev_low}–{guided_rev_high}%",
            "source": "Q2 FY27 Concall Transcript",
            "commentary": "Volume-led expansion across core domestic and export verticals with stable realizations.",
        },
        {
            "horizon": "FY27–FY28",
            "metric": "Operating Margin (EBITDA)",
            "target": f"{guided_opm_low}–{guided_opm_high}%",
            "source": "Q2 FY27 Concall Transcript",
            "commentary": "Supported by premium product mix, backward integration, and disciplined SG&A control.",
        },
        {
            "horizon": "FY27 Capex & Allocation",
            "metric": "Capital Expenditure",
            "target": prof.get("capex_guide", "Funded 100% through internal operating cash flows with zero net debt dilution.")[:95],
            "source": "FY26 Annual Report & Q2 Call",
            "commentary": prof.get("capex_guide", "Capacity additions targeted at high-ROCE downstream segments."),
        },
    ]

    default_segments = [
        {"name": "Core Domestic Operations", "share": 68, "growth": f"+{guided_rev_low + 1}% YoY"},
        {"name": "Specialty & Value-Added", "share": 21, "growth": f"+{guided_rev_high + 3}% YoY"},
        {"name": "Exports & International", "share": 11, "growth": f"+{max(4, guided_rev_low - 2)}% YoY"},
    ]

    return {
        "symbol": symbol,
        "name": prof.get("name", f"{symbol.title()} Industries Ltd"),
        "sector": prof.get("sector", "NSE Listed"),
        "about": prof.get(
            "about",
            f"{symbol.title()} Industries Ltd is an NSE-listed enterprise operating across core domestic manufacturing, value-added specialty solutions, and institutional exports. Data synthesized from primary filings for offline resilience."
        ),
        "segments": prof.get("segments", default_segments),
        "forward_guidance": forward_guidance,
        "top_ratios": {
            "Market Cap": f"₹ {int(annual_sales[-1] * r.uniform(3.2, 7.8)):,} Cr.",
            "Stock P/E": f"{r.uniform(22, 58):.1f}",
            "ROCE": f"{r.uniform(16, 34):.1f} %",
            "ROE": f"{r.uniform(14, 29):.1f} %",
        },
        "quarters": {"headers": quarters, "rows": pl(q_sales, q_opms)},
        "annual": {"headers": years, "rows": annual},
        "balance": {
            "headers": years,
            "rows": {
                "Equity Capital": [eq] * len(years),
                "Reserves": reserves,
                "Borrowings": borrow,
            },
        },
        "cashflow": {
            "headers": years,
            "rows": {
                "Cash from Operating Activity": cfo,
                "Cash from Investing Activity": cfi,
            },
        },
        "ratios": {
            "headers": years,
            "rows": {
                "Debtor Days": [round(x) for x in debtor],
                "Inventory Days": [round(x) for x in inv],
                "Days Payable": [round(x) for x in pay],
                "Cash Conversion Cycle": [round(a + b - c) for a, b, c in zip(debtor, inv, pay)],
            },
        },
        "docs": {
            "annual_reports": [
                {"title": "Annual Report FY26 (Audited Primary Filing)", "url": f"https://www.screener.in/company/{symbol}/consolidated/"},
                {"title": "Annual Report FY25 (Audited Primary Filing)", "url": f"https://www.screener.in/company/{symbol}/consolidated/"},
            ],
            "concalls": [
                {"title": q, "url": f"https://www.screener.in/company/{symbol}/consolidated/"}
                for q in reversed(quarters[-4:])
            ],
        },
        "demo_guidance": guidance,
    }
