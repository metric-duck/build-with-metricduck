# Lab 03: Stock Pulse - Check Any Stock Against Its Own History

**Is AAPL's ROIC improving or declining? Is NVDA's valuation compressing?**

Compare a stock's current quality metrics to their 2-year medians and spot
valuation trends. Uses MetricDuck statistical dimensions (Q.MED8, Q.TREND8)
that are not available in yfinance or any free alternative.

## Quick Start

**Requirements:** Python 3.10+

```bash
pip install -r requirements.txt
python pulse.py NVDA
```

No API key required. No yfinance needed. 100% MetricDuck.

## What This Does That Nothing Else Can

yfinance tells you AAPL's ROIC is 67%. Is that improving or declining?
Is NVDA's PE compression a buying signal or a warning?

**Stock Pulse answers these questions** by comparing current quality metrics to
their 2-year rolling medians (Q.MED8) and showing trend directions (Q.TREND8).

| Feature | yfinance | Stock Pulse |
|---------|----------|-------------|
| Current ROIC, margins | Not available | Yes |
| ROIC vs own 2-year median | **No** | Yes |
| ROIC/margin trend direction | **No** | Yes |
| PE/EV trend direction | **No** | Yes |
| "Above/below norm" signals | **No** | Yes |
| Automated diagnosis | **No** | Yes |

MetricDuck's statistical dimensions compute rolling statistics across 8 quarters
of SEC filing data. This is not available in any free tool.

## Example Output

```
==========================================================
                    STOCK PULSE: AAPL
                        Apple Inc.
==========================================================

VITAL SIGNS  (current vs 2-year median)
----------------------------------------------------------
                      Current    2yr Med           Signal
----------------------------------------------------------
ROIC                    67.6%      58.8%      ^ 15% above
Gross Margin            46.9%      46.5%      ~ Near norm
Oper Margin             32.0%      31.1%      ~ Near norm
FCF Margin              23.7%      25.5%       v 7% below

VALUATION  (current + 2-year trend)
----------------------------------------------------------
                      Current                       Trend
----------------------------------------------------------
PE Ratio                37.18                      Rising
EV/EBITDA               23.97                      Rising

GROWTH
----------------------------------------------------------
Revenue YoY                                         +6.4%
Revenue 3yr CAGR                                    +1.8%

LEVERAGE
----------------------------------------------------------
Debt/Equity                                           N/A

==========================================================
DIAGNOSIS
----------------------------------------------------------
Quality is strong — ROIC 67.6%,
above its 2-year median, trend rising.

Valuation trend: PE 37.2 and rising —
market is paying more per dollar of earnings.

Quality improving but valuation expanding too.
Market recognizes the improvement — premium justified?

----------------------------------------------------------
All dimensions computed from SEC filings.
Not available in yfinance or other free tools.

  70 metrics: https://www.metricduck.com/metrics
==========================================================
```

## Stocks to Try

| Stock | Command | What You'll See |
|-------|---------|-----------------|
| AAPL | `python pulse.py` | Tech giant — premium justified? |
| NVDA | `python pulse.py NVDA` | AI leader — how extended is the valuation? |
| META | `python pulse.py META` | After the pivot — quality improving? |
| MSFT | `python pulse.py MSFT` | Blue chip — expensive or fair? |
| JPM | `python pulse.py JPM` | Bank — ROIC may be N/A (financial company) |
| COST | `python pulse.py COST` | Retail — always looks expensive, but is it? |

## Understanding the Output

### Vital Signs

Compares each metric's current value to its **8-quarter (2-year) rolling median**:

| Signal | Meaning |
|--------|---------|
| `^ X% above` | Current value is above the 2-year norm |
| `v X% below` | Current value is below the 2-year norm |
| `~ Near norm` | Within 5% of the 2-year median |

### Trends

Shows the 2-year directional trend (Q.TREND8 slope):

| Trend | Meaning |
|-------|---------|
| Rising | Metric improving over 2 years |
| Falling | Metric declining over 2 years |
| Stable | No significant directional change |

### Diagnosis

Combines ROIC quality trends + PE valuation trends into an actionable signal:

- **Improving quality + compressing valuation** = potential opportunity
- **Declining quality + expanding valuation** = caution warranted
- **Improving quality + expanding valuation** = market recognizes improvement, premium justified?
- **Declining quality + compressing valuation** = market de-rating, investigate cause

## Customization

Edit the metric lists in `pulse.py` to check different vital signs:

```python
VITAL_SIGNS = [
    ("ROIC", "roic", "pct"),
    ("Gross Margin", "gross_margin", "pct"),
    ("Oper Margin", "oper_margin", "pct"),
    ("FCF Margin", "fcf_margin", "pct"),
]
```

Browse all 70 available metrics at [metricduck.com/metrics](https://www.metricduck.com/metrics).

## How It Works

Single API call with statistical dimensions:

```
GET /api/v1/data/metrics?
  tickers=AAPL&
  metrics=pe_ratio,roic,fcf_margin,net_margin,revenues,debt_to_equity&
  period=ttm&price=current&
  dimensions=Q.MED8,Q.TREND8,TTM.YOY,TTM.CAGR3
```

The `dimensions` parameter tells MetricDuck to return 8-quarter rolling medians,
trend slopes, and growth rates alongside base values. All in one request, all free.

## Data Source

MetricDuck computes all metrics and statistical dimensions from **SEC filings**
(10-K, 10-Q) using standardized XBRL extraction. The Q.MED8 dimension computes
the rolling median across 8 quarters of actual filed data.

## Next Steps

- **Lab 02: Stock Showdown** — Compare two stocks head-to-head
- **Lab 04: Stock Screener** — Rank 50+ stocks by Quality + Value composite score
- [Full metric catalog](https://www.metricduck.com/metrics) — Browse all 70 API metrics + 12 dimensions

## Troubleshooting

**"Rate limit reached"** — Guest access allows 10 requests/minute. Wait and retry, or use `--dry-run` to preview without API calls.

**"N/A" for some metrics** — Metrics like ROIC are not applicable for financial companies (banks, insurance). The diagnosis handles this gracefully.

**Signals all show "N/A"** — The stock may be recently IPO'd with fewer than 8 quarters of data. Medians need at least 8 quarters to compute.
