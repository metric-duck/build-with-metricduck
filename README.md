# MetricDuck Labs

Practical labs for building stock screeners and alerts.

**Start free, upgrade when you need more.**

## Labs

**Numbering:** 01-09 Free | 10-49 Builder ($29/mo) | 50+ Enterprise

| Lab | Description | Tier | Complexity |
|-----|-------------|------|------------|
| [01 - Free PE Alert](./labs/01-free-pe-alert/) | Alert when PE drops below threshold (yfinance) | **FREE** | Simple |
| [02 - Stock Showdown](./labs/02-stock-showdown/) | Compare two stocks head-to-head + historical context | **FREE** | Simple |
| [10 - PE Alert (API)](./labs/10-pe-ratio-alert/) | PE alert with 200+ metrics | Builder | Simple |
| [11 - Dividend Yield Alert](./labs/11-dividend-yield-alert/) | Alert when yield rises above threshold | Builder | Simple |
| [12 - Quality Watchlist](./labs/12-quality-watchlist/) | Monitor ROIC for quality stocks | Builder | Simple |
| 13 - GARP Screener | Find growth at reasonable price | Builder | Simple |
| 14 - Historical Value | Alert when valuation below historical avg | Builder | Moderate |
| [50 - Enterprise Screener](./labs/50-enterprise-screener/) | Advanced screening with full API | Enterprise | Advanced |

## Quick Start (Free)

**No subscription required!** Lab 1 uses yfinance (free) with GitHub Actions for daily alerts.

```bash
# Clone the repo
git clone https://github.com/metricduck/metric-duck-public.git
cd metric-duck-public

# Start with Lab 1 (FREE)
cd labs/01-free-pe-alert
pip install -r requirements.txt

# Run the alert
python alert.py
```

**Want daily alerts?** Fork this repo, add email secrets, enable GitHub Actions. See [Lab 1 README](./labs/01-free-pe-alert/) for details.

## Why Upgrade to MetricDuck API?

Labs 01-02 are free and work great. Labs 10+ use the MetricDuck API for:

| Feature | Labs 01-02 (yfinance) | Labs 10+ (MetricDuck) |
|---------|------------------|---------------------|
| Metrics available | ~20 | 200+ |
| Historical data | Limited | 7 years |
| Data source | Yahoo Finance | SEC filings |
| Accuracy | Good | High |
| Statistical dimensions | None | Trend, Avg, StdDev |

## Getting Your API Key (Labs 10+)

1. Sign up for a [Builder subscription](https://www.metricduck.com/pricing) ($29/month)
2. Go to your [Dashboard](https://www.metricduck.com/dashboard)
3. Navigate to API Keys section
4. Generate a new API key

## API Limits (Builder Tier)

| Limit | Value |
|-------|-------|
| Tickers per request | 25 |
| Metrics per request | 100 |
| Years of history | 7 |
| Monthly requests | 5,000 |
| Rate limit | 300/min |

## Free Stack

Labs 01-02 demonstrate a complete free stack:

- **Data:** yfinance (free, unlimited for personal use)
- **Email:** Gmail SMTP (free)
- **Scheduling:** GitHub Actions (free for public repos)

No credit card required. Try it today.

## Support

- [API Documentation](https://www.metricduck.com/docs)
- [MetricDuck Discord](https://discord.gg/metricduck)
- [GitHub Issues](https://github.com/metricduck/metric-duck-public/issues)

## License

MIT License - see [LICENSE](./LICENSE) for details.
