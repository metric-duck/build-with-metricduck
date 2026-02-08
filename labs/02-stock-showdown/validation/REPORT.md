# Data API Quality Report

**Generated:** 2026-02-08 19:26 UTC
**Tickers:** AAPL, MSFT, NVDA, META
**Metrics:** pe_ratio, ps_ratio, ev_ebitda, ev_ebit, dividend_yield
**Source:** MetricDuck API (guest access) vs yfinance

---

## Summary

| Verdict | Count |
|---------|-------|
| OK (<5%) | 11 |
| INVESTIGATE (5-15%) | 4 |
| CRITICAL (>15%) | 1 |
| N/A (missing data) | 4 |
| **Total comparisons** | **20** |

**Average difference:** 4.3%
**Worst discrepancy:** MSFT Price/Sales — 20.6%

---

## Detailed Results

| Ticker | Metric | MetricDuck | yfinance | Diff | Verdict | Period End |
|--------|--------|-----------|----------|------|---------|------------|
| AAPL | PE Ratio | 37.18 | 35.21 | 5.6% | INVESTIGATE | 2026-02-06 |
| AAPL | Price/Sales | 9.18 | 9.38 | 2.2% | OK | 2025-09-27 |
| AAPL | EV/EBITDA | 23.97 | 26.86 | 10.8% | INVESTIGATE | 2025-09-27 |
| AAPL | EV/EBIT | 26.08 | N/A | — | N/A | 2025-09-27 |
| AAPL | Div Yield | 0.37% | 0.37% | 0.9% | OK | 2026-02-06 |
| MSFT | PE Ratio | 24.99 | 25.12 | 0.5% | OK | 2026-02-06 |
| MSFT | Price/Sales | 11.77 | 9.76 | 20.6% | CRITICAL | 2025-12-31 |
| MSFT | EV/EBITDA | 18.29 | 17.19 | 6.4% | INVESTIGATE | 2025-12-31 |
| MSFT | EV/EBIT | 23.70 | N/A | — | N/A | 2025-12-31 |
| MSFT | Div Yield | 0.87% | 0.91% | 4.7% | OK | 2026-02-06 |
| NVDA | PE Ratio | 45.67 | 45.89 | 0.5% | OK | 2026-02-06 |
| NVDA | Price/Sales | 24.29 | 24.12 | 0.7% | OK | 2025-10-26 |
| NVDA | EV/EBITDA | 40.17 | 39.54 | 1.6% | OK | 2025-10-26 |
| NVDA | EV/EBIT | 40.90 | N/A | — | N/A | 2025-10-26 |
| NVDA | Div Yield | 0.02% | 0.02% | 7.9% | INVESTIGATE | 2026-02-06 |
| META | PE Ratio | 27.60 | 28.17 | 2.0% | OK | 2026-02-06 |
| META | Price/Sales | 8.28 | 8.33 | 0.5% | OK | 2025-12-31 |
| META | EV/EBITDA | 16.04 | 16.46 | 2.5% | OK | 2025-12-31 |
| META | EV/EBIT | 19.63 | N/A | — | N/A | 2025-12-31 |
| META | Div Yield | 0.32% | 0.32% | 0.8% | OK | 2026-02-06 |

---

## Critical Issues

- **MSFT Price/Sales**: MetricDuck=11.77, yfinance=9.76, diff=20.6% (period_end: 2025-12-31)

