# Lab 04: Stock Screener - Rank Stocks by Quality + Value

**Screen 50+ stocks and find the best combination of quality and value.**

Rank stocks using a composite score: Quality (ROIC, FCF Margin) at 60% weight
plus Value (PE Ratio, FCF Yield, EV/EBITDA) at 40% weight.

## Quick Start

**Requirements:** Python 3.10+

```bash
pip install -r requirements.txt
python screener.py
```

No API key required. Guest access screens the top 10 stocks by market cap.
Register free for full 50-stock screening.

## What This Does That yfinance Can't

| Metric | yfinance | MetricDuck | Why It Matters |
|--------|----------|------------|----------------|
| **ROIC** | Not available | Yes | The single best measure of business quality |
| **FCF Margin** | Not pre-computed | Yes | Cash generation efficiency |
| **FCF Yield** | Not available | Yes | Free cash flow relative to market cap |
| **EV/EBITDA** | Available | Yes | Enterprise value per $1 of cash earnings |
| **PE Ratio** | Available | Yes | Price per $1 of earnings, from SEC filings |

3 of the 5 screening metrics are MetricDuck exclusives.

## Example Output

```
==========================================================================
              STOCK SCREENER: TOP 10 OF 10 STOCKS
==========================================================================
Quality weight: 60% | Value weight: 40%

Rank  Ticker Company               ROIC  FCF Yld      PE  Score
--------------------------------------------------------------------------
   1  MA     Mastercard Inc        97.8%    2.5%   35.12   75.6 QUALITY
   2  V      Visa Inc              34.3%    3.1%   31.82   73.2 QUALITY
   3  NVDA   NVIDIA CORP           96.5%    1.7%   45.67   60.0 QUALITY
   4  MSFT   MICROSOFT CORP        27.4%    2.2%   24.99   48.3   VALUE
   5  AAPL   Apple Inc.            67.6%    2.6%   37.18   41.7
   6  META   Meta Platforms, I     33.2%    2.5%   25.35   40.0
   7  AMZN   AMAZON COM INC         8.3%    1.3%   35.77   20.0
   8  JPM    JPMORGAN CHASE &        N/A    N/A    13.06   16.7   VALUE
   9  GOOGL  Alphabet Inc.         18.2%    2.3%   22.71   15.0
  10  BRK.B  BERKSHIRE HATHAW       5.5%    N/A    10.57    5.6
--------------------------------------------------------------------------
Screened 10 stocks | 5 metrics | ~50 credits

  QUALITY = top 30% quality | VALUE = top 30% value
  BALANCED = top 30% in both

  70 metrics: https://www.metricduck.com/metrics
==========================================================================
```

## Usage

| Command | What You Get |
|---------|-------------|
| `python screener.py` | Top 10 of 50 stocks (guest: top 10 of 10) |
| `python screener.py --count 100 --top 20` | Screen 100, show top 20 |
| `python screener.py --tickers AAPL,MSFT,GOOGL,AMZN,META,NVDA` | Screen specific stocks |
| `python screener.py --json` | Machine-readable output |
| `python screener.py --dry-run` | Preview credit cost without calling API |

## How It Works

### Scoring Algorithm

1. **Fetch metrics** for N stocks via the MetricDuck API
2. **Percentile rank** each metric (0-100) within the screened universe
3. **Average percentiles** within Quality and Value categories
4. **Weighted composite**: Quality (60%) + Value (40%)
5. **Signal labels**: QUALITY (top 30% quality), VALUE (top 30% value), BALANCED (both)

### Credit Cost

`tickers x metrics x years` — screening 50 stocks with 5 metrics costs 250 credits.

| Screen Size | Credits |
|-------------|---------|
| 10 stocks (guest default) | 50 |
| 50 stocks | 250 |
| 100 stocks | 500 |

Use `--dry-run` to preview cost before calling the API.

## Customization

Edit the metric lists and weights in `screener.py`:

```python
QUALITY_METRICS = [
    ("ROIC",       "roic",       "higher"),
    ("FCF Margin", "fcf_margin", "higher"),
]

VALUE_METRICS = [
    ("PE Ratio",  "pe_ratio",  "lower"),
    ("FCF Yield", "fcf_yield", "higher"),
    ("EV/EBITDA", "ev_ebitda", "lower"),
]

QUALITY_WEIGHT = 0.6
VALUE_WEIGHT = 0.4
```

Browse all 70 available metrics at [metricduck.com/metrics](https://www.metricduck.com/metrics).

### Chain with Other Labs

Screen the top 50, then check the #1 pick for value traps:

```bash
python screener.py
python ../03-stock-pulse/pulse.py MA
```

Compare two top picks head-to-head:

```bash
python ../02-stock-showdown/showdown.py MA V
```

## Data Source

MetricDuck computes all metrics from **SEC filings** (10-K, 10-Q) using standardized
XBRL extraction. This means consistent cross-company comparisons, not scraped or estimated data.

## Troubleshooting

**"Could not connect to MetricDuck API"** — Check your internet connection.

**"Rate limit reached"** — Guest access allows 10 requests/minute. Wait and retry.

**Screener shows only 10 stocks** — Guest mode (no API key) is limited to 10 tickers. Register free at [metricduck.com/auth/register](https://www.metricduck.com/auth/register) for up to 200 tickers.

**Missing metric values (N/A)** — Some stocks don't report all metrics (e.g., banks may not have ROIC). The screener scores each stock only on available metrics.
