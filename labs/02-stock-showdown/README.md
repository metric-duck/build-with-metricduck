# Lab 02: Stock Showdown - Two-Panel Stock Comparison

**Which stock should you buy? Not just cheaper — better.**

Compare any two stocks across Valuation and Business Quality using metrics
that free alternatives like yfinance can't provide.

## Quick Start

**Requirements:** Python 3.10+

```bash
pip install -r requirements.txt
python showdown.py NVDA AMD
```

No API key required. All 70 metrics are free via guest access.

**Optional:** Install yfinance for supplementary market context (sector, beta, 52-week range):

```bash
pip install yfinance
```

## What This Does That yfinance Can't

| Metric | yfinance | MetricDuck | Why It Matters |
|--------|----------|------------|----------------|
| **ROIC** | Not available | Yes | The single best measure of business quality |
| **FCF Yield** | Not available | Yes | Free cash flow relative to market cap |
| **EV/EBIT** | Not available | Yes | Valuation using operating income |
| **Total Shareholder Yield** | Not available | Yes | Dividends + buybacks combined |
| **FCF Margin** | Not pre-computed | Yes | Cash generation efficiency |

Metrics marked `*` in the output are MetricDuck exclusives.

## Example Output

```
======================================================================
                   STOCK SHOWDOWN: AAPL vs MSFT
======================================================================

COMPANY INFO
----------------------------------------------------------------------
                                    AAPL                   MSFT
Name                           Apple Inc         Microsoft Corp

PANEL 1: VALUATION  (Who's cheaper today?)
----------------------------------------------------------------------
                            AAPL           MSFT     Better Value
----------------------------------------------------------------------
PE Ratio                   37.18          24.99         MSFT ->
EV/EBITDA                  23.97          18.29         MSFT ->
EV/EBIT *                  26.08          23.70         MSFT ->
FCF Yield *                 2.7%           3.0%         MSFT ->
                                             Valuation: MSFT 4-0

PANEL 2: QUALITY  (Who's the better business?)
----------------------------------------------------------------------
                            AAPL           MSFT   Better Quality
----------------------------------------------------------------------
ROIC *                     52.3%          25.1%         <- AAPL
FCF Margin *               26.4%          33.2%         MSFT ->
Shareholder Yield *         3.8%           2.1%         <- AAPL
                                               Quality: AAPL 2-1

======================================================================
VERDICT
----------------------------------------------------------------------
Valuation: MSFT is clearly cheaper (4 of 4 metrics)
Quality:   AAPL is stronger (2 of 3 metrics) -- ROIC 52.3% vs 25.1%

AAPL has higher quality, MSFT is cheaper.
Classic value-vs-quality tradeoff.

But is the cheaper stock cheap by its OWN standards?
Try Lab 03 (Stock Pulse) to check any stock vs its 2-year history.

----------------------------------------------------------------------
* = MetricDuck exclusive (not available in yfinance)

  Data: SEC filings via MetricDuck API (free, no key needed)
  70 metrics available: https://www.metricduck.com/metrics
======================================================================
```

## Popular Comparisons

| Matchup | Command | What You'll Learn |
|---------|---------|-------------------|
| NVDA vs AMD | `python showdown.py NVDA AMD` | GPU rivals: who has better ROIC? |
| GOOGL vs META | `python showdown.py GOOGL META` | Ad tech: valuation vs capital returns |
| JPM vs BAC | `python showdown.py JPM BAC` | Banks: quality comparison (ROIC may be N/A) |
| COST vs WMT | `python showdown.py COST WMT` | Retail: FCF efficiency showdown |
| V vs MA | `python showdown.py V MA` | Payments: the duopoly comparison |
| TSLA vs RIVN | `python showdown.py TSLA RIVN` | EV makers: profitability gap |

## Understanding the Metrics

### Panel 1: Valuation (lower = cheaper, except FCF Yield)

| Metric | What It Measures |
|--------|------------------|
| **PE Ratio** | Price per $1 of earnings |
| **EV/EBITDA** | Enterprise value per $1 of cash earnings |
| **EV/EBIT** * | Enterprise value per $1 of operating income |
| **FCF Yield** * | Free cash flow as % of market cap (higher = better value) |

### Panel 2: Business Quality (higher = better)

| Metric | What It Measures |
|--------|------------------|
| **ROIC** * | Return on Invested Capital — how well the business uses its capital |
| **FCF Margin** * | Free cash flow as % of revenue — cash generation efficiency |
| **Shareholder Yield** * | Dividends + buybacks as % of market cap — total capital returned |

All data uses **Trailing Twelve Months (TTM)** from SEC filings with today's market price.

## Customization

Edit the metric lists in `showdown.py` to add metrics from the [full catalog](https://www.metricduck.com/metrics) (70 metrics available):

```python
VALUATION_METRICS = [
    ("PE Ratio", "pe_ratio", "lower", False),
    ("EV/EBITDA", "ev_ebitda", "lower", False),
    ("EV/EBIT", "ev_ebit", "lower", True),     # True = MetricDuck exclusive
    ("FCF Yield", "fcf_yield", "higher", True),
]
```

## Data Source

MetricDuck computes all metrics from **SEC filings** (10-K, 10-Q) using standardized
XBRL extraction. This means consistent cross-company comparisons, not scraped or estimated data.

## Next Steps

- **Lab 03: Stock Pulse** — Check any stock vs its own 2-year history
- **Lab 04: Stock Screener** — Rank 50+ stocks by Quality + Value composite score
- [Full metric catalog](https://www.metricduck.com/metrics) — Browse all 70 API metrics

## Troubleshooting

**"Could not connect to MetricDuck API"** — Check your internet connection.

**"Rate limit reached"** — Guest access allows 10 requests/minute. Wait and retry, or use `--dry-run` to preview without API calls.

**Missing metric values (N/A)** — Some stocks don't report all metrics (e.g., banks may not have EBITDA or ROIC). The tool handles this gracefully.
