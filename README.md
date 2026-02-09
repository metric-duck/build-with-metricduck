# MetricDuck Labs

Practical labs for building stock analysis tools with the [MetricDuck API](https://www.metricduck.com).

**No API key required.** Guest access gives you all 70 metrics and 12 statistical dimensions.

**Start here:** [Lab 02 - Stock Showdown](./labs/02-stock-showdown/) — compare two stocks in 30 seconds.

## Labs

### Free Labs (no API key needed)

| Lab | Description | What You'll Build |
|-----|-------------|-------------------|
| [02 - Stock Showdown](./labs/02-stock-showdown/) | Compare two stocks on Valuation + Quality | 2-panel comparison with 7 metrics (5 exclusive) |
| [03 - Stock Pulse](./labs/03-stock-pulse/) | Check any stock vs its own 2-year history | Value trap detector with Q.MED8 and Q.TREND8 |
| [04 - Stock Screener](./labs/04-stock-screener/) | Rank 50+ stocks by Quality + Value | Composite scoring with percentile ranks |

### Developer Labs (API key required)

| Lab | Description | What You'll Build |
|-----|-------------|-------------------|
| [10 - PE Alert](./labs/10-pe-ratio-alert/) | Alert when PE drops below threshold | Automated valuation monitoring |
| [50 - Enterprise Screener](./labs/50-enterprise-screener/) | Advanced screening with bulk data access | Production data pipeline |

## Quick Start

```bash
git clone https://github.com/metric-duck/build-with-metricduck.git
cd build-with-metricduck/labs/02-stock-showdown
pip install -r requirements.txt
python showdown.py NVDA AMD
```

Works immediately. No API key, no signup, no config.

Or try the stock screener:

```bash
cd labs/04-stock-screener
pip install -r requirements.txt
python screener.py
```

**What you'll see:**

```
PANEL 1: VALUATION  (Who's cheaper today?)
PE Ratio                   37.18          24.99         MSFT ->
EV/EBITDA                  23.97          18.29         MSFT ->
```

## What MetricDuck Provides That yfinance Can't

5 of the 7 metrics in Stock Showdown are not available in yfinance:

- **ROIC** - Return on Invested Capital
- **FCF Margin** - Free cash flow as % of revenue
- **FCF Yield** - Free cash flow / market cap
- **EV/EBIT** - Enterprise value / operating income
- **Total Shareholder Yield** - Dividends + buybacks + debt paydown

## API Access

| Tier | Access | Cost |
|------|--------|------|
| Guest (no key) | 5 requests/day, 10 tickers max | Free |
| Free (registered) | 500 credits/day, 200 tickers | Free |
| Developer | 200,000+ credits/month | From $29/mo |

Free labs include a `--dry-run` flag to preview credit costs before calling the API.

[Get an API key](https://www.metricduck.com/auth/register)

## Links

- [Full metric catalog](https://www.metricduck.com/metrics) - Browse all 70 API metrics
- [API Documentation](https://www.metricduck.com/docs)
- [Blog tutorials](https://www.metricduck.com/blog/build-it-with-metricduck)

## License

MIT License - see [LICENSE](./LICENSE) for details.
