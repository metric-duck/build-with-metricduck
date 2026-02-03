# MetricDuck Labs Roadmap

> **Planning Document** - Outlines planned labs and numbering scheme.

---

## Lab Numbering Scheme

```
01-09    Free Labs (yfinance, no signup required)
10-49    Builder Labs ($29/mo MetricDuck API)
50+      Enterprise Labs (custom pricing)
```

---

## Current State

| Lab | Name | Status | Tier |
|-----|------|--------|------|
| 01 | Free PE Alert | ✅ Implemented | FREE |
| 02 | Stock Showdown | ✅ Implemented | FREE |
| 03 | Sector Value Finder | Planned | FREE |
| 04-09 | Reserved | - | FREE |
| 10 | PE Alert (API) | ✅ Implemented | Builder |
| 11 | Dividend Yield Alert | ✅ Implemented | Builder |
| 12 | Quality Watchlist | ✅ Implemented | Builder |
| 13 | GARP Screener | Planned | Builder |
| 14 | Historical Value | Planned | Builder |
| 50 | Enterprise Screener | ✅ Implemented | Enterprise |

---

## Free Labs (01-09)

### Lab 02: Stock Showdown

**Status:** ✅ Implemented

**Concept:** Compare two stocks head-to-head on valuation metrics.

**Features:**
- User specifies two tickers to compare
- Fetches: PE, Forward PE, Dividend Yield, Price/Book, Price/Sales, EV/EBITDA
- Visual table output showing winner per metric
- Historical context using 52-week range
- Smart verdict combining metrics + context

**Files:** `labs/02-stock-showdown/`

---

### Lab 03: Sector Value Finder

**Status:** Planned

**Concept:** Find which market sector is cheapest by PE ratio.

**Features:**
- Pre-defined representative stocks per sector (configurable)
- Fetches PE ratio for each sector representative
- Ranks sectors from cheapest to most expensive
- Shows sector rotation insights

**Files:** `labs/03-sector-value-finder/`

---

## Builder Labs (10-49)

These labs use the MetricDuck API ($29/mo Builder tier).

### Lab 13: GARP Screener

**Status:** Planned

**Concept:** Find Growth at Reasonable Price stocks.

### Lab 14: Historical Value Context

**Status:** Planned

**Concept:** Answer "Is this stock cheap vs its own history?"

**Features:**
- Fetches current PE + 5-year historical PE data
- Calculates: average, high, low, percentile
- Visual output showing where current valuation sits

---

## Future Lab Ideas

### Alerts & Monitoring
- Multi-metric Alert - Alert on PE + ROIC + margin thresholds
- Watchlist Monitor - Daily summary of portfolio fundamentals
- Earnings Calendar - Alert before earnings with valuation context

### Screening
- Value Screener - Find stocks with PE < X and ROIC > Y
- Quality Filter - High ROIC, high margins, low debt

### Analysis
- Peer Comparison - Compare one stock to industry peers
- Historical Trends - Chart metrics over 5 years
- Valuation Bands - Plot price vs historical PE range

### Integration
- Slack/Discord Bot - Get metrics on demand in chat
- Google Sheets - Pull metrics into spreadsheets

---

## Developer Journey

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     TARGET DEVELOPER JOURNEY                            │
│                                                                         │
│   1. Discovers MetricDuck Labs (GitHub, blog, referral)                 │
│                         │                                               │
│                         ▼                                               │
│   2. Tries Lab 01 or 02 (free, no signup)                               │
│      "Cool, this works!"                                                │
│                         │                                               │
│                         ▼                                               │
│   3. Tries Lab 10+ (Builder tier, quick signup)                         │
│      "Wow, 200+ metrics and historical data!"                           │
│                         │                                               │
│                         ▼                                               │
│   4. Builds custom tools, explores Enterprise (50+)                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Changelog

| Date | Change |
|------|--------|
| 2026-02-02 | Renumbered labs: 01-09 Free, 10-49 Builder, 50+ Enterprise |
| 2026-02-02 | Lab 02 (formerly 1.5): Replaced PEG Ratio with Dividend Yield |
| 2026-02-02 | Lab 02 Stock Showdown implemented |
| 2026-02-02 | Initial roadmap created |
