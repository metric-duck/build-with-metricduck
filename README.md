# MetricDuck Labs

Practical labs for building stock analysis tools with the [MetricDuck API](https://www.metricduck.com).

**No API key required.** Guest access gives you all 70 metrics and 12 statistical dimensions.

## Labs

### Free Labs (no API key needed)

| Lab | Description | What You'll Build |
|-----|-------------|-------------------|
| [02 - Stock Showdown](./labs/02-stock-showdown/) | Compare two stocks on Valuation + Quality | 2-panel comparison with 7 metrics (5 exclusive) |
| [03 - Stock Pulse](./labs/03-stock-pulse/) | Check any stock vs its own 2-year history | Historical analysis with Q.MED8 and Q.TREND8 |

### Builder Labs (API key required, $29/mo)

| Lab | Description | What You'll Build |
|-----|-------------|-------------------|
| [10 - PE Alert](./labs/10-pe-ratio-alert/) | Alert when PE drops below threshold | Automated valuation monitoring |
| [11 - Dividend Yield Alert](./labs/11-dividend-yield-alert/) | Alert on dividend yield changes | Income investing alerts |
| [12 - Quality Watchlist](./labs/12-quality-watchlist/) | Track ROIC and quality metrics | Portfolio quality monitoring |

### Enterprise Labs

| Lab | Description |
|-----|-------------|
| [50 - Enterprise Screener](./labs/50-enterprise-screener/) | Advanced screening with bulk data access |

## Quick Start

```bash
git clone https://github.com/metric-duck/build-with-metricduck.git
cd build-with-metricduck/labs/02-stock-showdown
pip install -r requirements.txt
python showdown.py NVDA AMD
```

Works immediately. No API key, no signup, no config.

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
| Guest (no key) | All 70 metrics, 5 req/min | Free |
| Free (registered) | 500 credits/month | Free |
| Builder | 200,000 credits/month, 300 req/min | $29/mo |
| Production | 1,000,000 credits/month, 1,000 req/min | $79/mo |

[Get an API key](https://www.metricduck.com/auth/register)

## Links

- [Full metric catalog](https://www.metricduck.com/metrics) - Browse all 70 API metrics
- [API Documentation](https://www.metricduck.com/docs)
- [Blog tutorials](https://www.metricduck.com/blog/build-it-with-metricduck)

## License

MIT License - see [LICENSE](./LICENSE) for details.
