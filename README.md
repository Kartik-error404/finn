# FINN — Financial Investment Agent (Mobile-First Prototype)

FINN is an investor's daily triage and primary-source research layer. It doesn't try to show you everything—it surfaces the few filings and moves that matter, links every market anomaly to its catalyst, and grounds deep-dive company research strictly in audited filings and concall transcripts.

```bash
python run.py                  # → http://localhost:8000 (open on phone via LAN IP or desktop browser)
FINN_MODE=demo python run.py   # fully offline deterministic primary-data mode
```

Zero mandatory external dependencies: the server runs on the Python standard library and serves a mobile-first frontend (`web/index.html`, `web/style.css`, `web/app.js`). Optional `pip install pypdf` enables live concall PDF extraction.

---

## Mobile-First Interaction Model: 4 Core Workflows

| Tab | Mode | What It Does |
|---|---|---|
| **1. Brief** | **Push (Windowed Digest)** | Triages every corporate announcement across your 18+ NSE holdings for any window (`6h`, `24h`, `3d`, `7d`, `30d`) into **Act On → Watch → Routine (Collapsed)**. Includes an **Inbox-Zero progress bar**, category filter pills (`Results`, `Mgmt Change`, `M&A`, `Capex`, `Risk`), 1-tap filing excerpt modal, bookmarking, and a **60-Second Spoken Morning Audio Brief**. |
| **2. Radar** | **Push (Triggered Alerts)** | Live interactive sliders let you configure **Volume Spike (`> N×` 20d avg)**, **Daily Price Move (`±X%`)**, and **Tracked Filing Categories** with instant reactive rescanning. Joins every EOD anomaly to same-day filings (*"Joined Filing Catalyst → ..."*) or explicitly flags **Unexplained Moves**, alongside a sortable 30-day sparkline portfolio tape. |
| **3. Research** | **Pull (8-Pillar Primary Engine)** | Works for **any NSE ticker** (portfolio holdings, ad-hoc picks like `PIDILITIND`, `HAL`, `NESTLEIND`, `DMART`, `ZOMATO`, or any custom NSE symbol). Delivers all 8 pull outputs grounded strictly in primary filings & concalls: **1. Narrative vs. Numbers (4-Quarter Promise vs. Delivered Ledger + Management Credibility Score)**, **2. Quarterly Headline Snapshot (QoQ & YoY)**, **3. Business Snapshot & Revenue Mix Segments**, **4. Forward Guidance Tracker**, **5. Bull vs. Bear Case**, **6. 8-Year Trajectory Chart**, **7. Cash Quality (`CFO/PAT` & `FCF`)**, and **8. Balance Sheet & Working Capital Cycle (`Debtor/Inventory/Payable/CCC Days`)**. |
| **4. Copilot** | **Portfolio & Grounded Q&A** | Cross-portfolio **Credibility & Cash Conversion Matrix**, grounded analyst Q&A with 1-tap prompt chips, and an interactive **Portfolio Manager** to add or remove any NSE ticker dynamically. |

---

## Architecture & Cost Discipline

```text
finn/
  sources/prices.py         Yahoo Finance chart API (.NS tickers), 6h TTL cache
  sources/announcements.py  NSE corporate-announcements JSON (cookie-warmed), 15m TTL cache
  sources/fundamentals.py   screener.in consolidated P&L, BS, CF, ratios, AR + concall links
  classify.py               Stage-1 regex rules (~90% of filings at ₹0 cost) + Stage-2 cheap LLM fallback
  push.py                   Windowed digest, EOD threshold alerts, results/person cards, move↔filing join
  pull.py                   8-pillar research engine for any ticker, Promise-vs-Delivered ledger, grounded Q&A
  llm.py                    3-tier model router + permanent SHA-1 on-disk response cache
  sample.py                 Curated primary-source fallback data & generalizable ticker generator
  server.py                 Zero-dependency ThreadingHTTPServer: JSON API + static mobile web app
web/                        Mobile-first frontend (index.html, style.css, app.js) + standalone Canvas build
```

1. **Zero-Hallucination Arithmetic:** Every number—QoQ/YoY growth, 3Y/5Y CAGRs, `CFO/PAT` cash conversion, `D/E`, Cash Conversion Cycle days, and `BEAT / MET / MISSED` guidance verdicts—is computed deterministically in Python/JS from reported tables, never by an LLM.
2. **Three-Tier Model Routing & 10× Transcript Chunking:**
   - **Tier 0 (Regex Rules + Deterministic Synthesizer):** Classifies ~90% of NSE filings, computes priority scores, and synthesizes structured primary-data Q&A with zero API cost.
   - **Tier 1 (Cheap Model — e.g. `llama-3.1-8b-instant` / `gemini-2.5-flash-lite`):** Extracts guidance only from regex-filtered forward-looking concall paragraphs (cutting input tokens ~10×).
   - **Tier 2 (Strong Model — e.g. `llama-3.3-70b-versatile`):** Used only for Bull/Bear refinement and free-form Q&A over pre-computed JSON facts.
3. **Strict Primary-Source Grounding:** Pull analysis uses only audited financial statements, annual reports, and earnings-call transcripts—zero broker notes, zero news articles, and zero outside model memory.
