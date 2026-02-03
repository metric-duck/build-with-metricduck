# Lab 02: Stock Showdown - Compare Stocks & Find Better Value

**Which stock should you buy? Find out in seconds.**

Compare any two stocks on valuation metrics AND historical context to find the better value opportunity. No signup required, completely free.

## What Makes This Different

Most stock comparison tools just show raw numbers. Stock Showdown goes further:

- **Raw Metrics** - PE, Dividend Yield, Price/Book side-by-side
- **Historical Context** - Is it cheap vs its OWN 52-week range?
- **Smart Verdict** - Clear recommendation, not just numbers

## Quick Start

**Requirements:** Python 3.10+

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Compare any two stocks
python showdown.py NVDA AMD

# Or use the default comparison (AAPL vs MSFT)
python showdown.py
```

## Example Output

```
══════════════════════════════════════════════════════════════════
                    STOCK SHOWDOWN: AAPL vs MSFT
══════════════════════════════════════════════════════════════════

COMPANY INFO
──────────────────────────────────────────────────────────────────
                                 AAPL                 MSFT
Name                        Apple Inc       Microsoft Corp
Sector                     Technology           Technology
Market Cap                     $3.4T               $3.1T

VALUATION METRICS
──────────────────────────────────────────────────────────────────
                            AAPL            MSFT     Better Value
──────────────────────────────────────────────────────────────────
PE Ratio                   28.50           35.20          AAPL ✓
Forward PE                 26.10           30.80          AAPL ✓
Div Yield                  0.52%           0.74%          MSFT ✓
Price/Book                 45.20           12.30          MSFT ✓
Price/Sales                 7.20           11.50          AAPL ✓
EV/EBITDA                  22.10           25.80          AAPL ✓

HISTORICAL CONTEXT (52-Week Range Position)
──────────────────────────────────────────────────────────────────
                                 AAPL                 MSFT
Current Price                 $185.50              $420.30
52-Week Low                   $164.08              $385.12
52-Week High                  $199.62              $468.35
Position              Near 52-wk high (82%)   Mid-range (42%)

VALUATION VERDICT
──────────────────────────────────────────────────────────────────
AAPL     [▓▓▓▓▓▓▓▓░░]  Expensive
MSFT     [▓▓▓▓░░░░░░]  Fair Value

══════════════════════════════════════════════════════════════════
FINAL VERDICT
──────────────────────────────────────────────────────────────────
Raw Metrics Winner: AAPL (4 of 6 metrics)

But consider this:
  • AAPL is trading Near 52-wk high (82%) - potentially stretched
  • MSFT is trading Mid-range (42%) - better entry point

RECOMMENDATION: MSFT may offer better value right now.
You'd be buying at a lower point in its historical range.

══════════════════════════════════════════════════════════════════
```

## Popular Comparisons to Try

| Matchup | Command | Use Case |
|---------|---------|----------|
| NVDA vs AMD | `python showdown.py NVDA AMD` | GPU rivals - who's the better AI play? |
| GOOGL vs META | `python showdown.py GOOGL META` | Ad tech giants - which is cheaper? |
| TSLA vs RIVN | `python showdown.py TSLA RIVN` | EV makers - growth vs value |
| JPM vs BAC | `python showdown.py JPM BAC` | Big banks - quality vs price |
| COST vs WMT | `python showdown.py COST WMT` | Retail giants - which is undervalued? |
| V vs MA | `python showdown.py V MA` | Payment networks - duopoly comparison |
| DIS vs NFLX | `python showdown.py DIS NFLX` | Streaming wars - who's winning? |
| PFE vs JNJ | `python showdown.py PFE JNJ` | Pharma giants - value play? |

## Understanding the Output

### Valuation Metrics

| Metric | What It Measures | Better Value? |
|--------|------------------|---------------|
| **PE Ratio** | Price relative to earnings | Lower - cheaper per $1 of profit |
| **Forward PE** | Expected future PE | Lower - cheaper vs future earnings |
| **Div Yield** | Annual dividends / price | Higher - more income per $1 invested |
| **Price/Book** | Price vs company assets | Lower - closer to asset value |
| **Price/Sales** | Price vs revenue | Lower - cheaper per $1 of sales |
| **EV/EBITDA** | Enterprise value vs cash flow | Lower - cheaper cash flow |

### Historical Context

Shows where each stock is trading within its 52-week price range:

- **Near 52-week high (>85%)** - Expensive, potentially overextended
- **Upper half (65-85%)** - Pricey, showing strength
- **Mid-range (45-65%)** - Fair value
- **Lower half (25-45%)** - Fair value, potential opportunity
- **Near 52-week low (<25%)** - Cheap, potential value (or trouble)

### The Verdict

The tool combines raw metrics AND historical context:

1. **Metrics winner** - Who wins more valuation comparisons
2. **Historical check** - Is the winner actually at a good entry point?
3. **Smart recommendation** - Considers both factors

A stock can win on metrics but still be expensive vs its own history!

## How It Works

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   yfinance      │ --> │   showdown.py   │ --> │  Smart Verdict  │
│   (free API)    │     │   (compare)     │     │  + Recommendation│
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
   Free data              Compare metrics          Historical
   No API key             + 52-week range         context check
```

## Limitations

- Historical context uses 52-week range (yfinance limitation)
- **Dividend Yield** shows N/A or 0% for growth stocks that don't pay dividends (TSLA, NVDA, etc.)
- **EV/EBITDA** shows N/A for banks (EBITDA isn't meaningful for financials)
- Does not account for business quality, growth prospects, or sector differences

**For deeper analysis:**
- 5+ years of historical PE data
- 200+ fundamental metrics
- SEC-filed data accuracy

Try [MetricDuck API](https://www.metricduck.com) for professional-grade analysis.

## Customization

Edit `showdown.py` to change default stocks:

```python
# Default stocks to compare
STOCK_A = "NVDA"
STOCK_B = "AMD"
```

Or add/remove metrics:

```python
VALUATION_METRICS = [
    ("PE Ratio", "trailingPE", "lower"),
    ("Forward PE", "forwardPE", "lower"),
    ("Div Yield", "dividendYield", "higher"),  # Higher yield = more income
    ("Price/Book", "priceToBook", "lower"),
    ("Price/Sales", "priceToSalesTrailing12Months", "lower"),
    ("EV/EBITDA", "enterpriseToEbitda", "lower"),
]
```

## Next Steps

- [Lab 01: Free PE Alert](../01-free-pe-alert/) - Get alerts when stocks get cheap
- [Lab 10: PE Alert with API](../10-pe-ratio-alert/) - 200+ metrics, higher accuracy

## Troubleshooting

### "Could not fetch data for TICKER"

- Check the ticker symbol is correct
- Use the main listing symbol (e.g., `BRK-B` not `BRK.B`)
- Some international stocks may not be available

### Missing metric values

- Some stocks don't report all metrics (e.g., banks don't have EBITDA)
- Growth stocks that don't pay dividends will show N/A or 0% for Dividend Yield
- The tool handles missing data gracefully and excludes from comparison
