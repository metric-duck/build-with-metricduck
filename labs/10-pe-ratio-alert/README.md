# Lab 2: PE Ratio Alert with MetricDuck API

**Professional-grade PE alerts with 200+ metrics.**

This lab uses the MetricDuck API for higher accuracy data sourced directly from SEC filings.

**Requires:** MetricDuck Builder (D1) subscription - [$29/month](https://www.metricduck.com/pricing)

> **New to stock alerts?** Start with [Lab 1: Free PE Alert](../01-free-pe-alert/) which requires no subscription.

## What You'll Build

A Python script that:
1. Fetches PE ratios for your watchlist from MetricDuck API
2. Compares each stock's PE to your threshold
3. Alerts you when PE drops below the threshold

## Why MetricDuck API?

| Feature | Lab 1 (yfinance) | Lab 2 (MetricDuck) |
|---------|------------------|-------------------|
| Metrics available | ~20 | 200+ |
| Historical data | Limited | 7 years |
| Data source | Yahoo Finance | SEC filings |
| Accuracy | Good | High |
| Rate limits | Unofficial | 5,000 req/month |

## Prerequisites

- MetricDuck Builder (D1) subscription
- Python 3.8+
- Your API key from [MetricDuck Dashboard](https://www.metricduck.com/dashboard)

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure your API key

```bash
cp .env.example .env
```

Edit `.env` and add your API key:
```
METRICDUCK_API_KEY=your_api_key_here
```

### 3. Customize your watchlist

Edit `alert.py` and update:
```python
WATCHLIST = ["AAPL", "MSFT", "GOOGL"]  # Your stocks
PE_THRESHOLD = 15                       # Your threshold
```

## Run

```bash
python alert.py
```

### Example Output

```
Checking PE ratios for watchlist: AAPL, MSFT, GOOGL, AMZN, META
Alert threshold: PE < 20
--------------------------------------------------
AAPL: PE = 28.5
MSFT: PE = 35.2
GOOGL: PE = 18.2 ** ALERT! Below threshold **
AMZN: PE = 42.3
META: PE = 19.8 ** ALERT! Below threshold **
--------------------------------------------------

2 ALERT(S) TRIGGERED:
  - GOOGL: PE = 18.2
  - META: PE = 19.8
```

## How It Works

### API Call

The script makes one API call to fetch PE ratios for all stocks:

```
GET /api/v1/data/metrics
  ?tickers=AAPL,MSFT,GOOGL
  &metrics=pe_ratio
  &period=ttm
```

### Response Format

```json
{
  "data": {
    "AAPL": {
      "company_name": "Apple Inc",
      "metrics": {
        "pe_ratio": {
          "values": [{"period": "TTM", "value": 28.5}]
        }
      }
    }
  }
}
```

### Alert Logic

```python
if pe_ratio < PE_THRESHOLD:
    print(f"ALERT: {ticker} PE is below {PE_THRESHOLD}")
```

## Next Steps

### Add More Metrics

MetricDuck supports 200+ metrics. Try adding:

```python
params={
    "tickers": ",".join(WATCHLIST),
    "metrics": "pe_ratio,ev_ebitda,roe,roic",
    "period": "ttm",
}
```

### Add Historical Comparison

Fetch 5 years of quarterly data to compare current PE vs historical average:

```python
params={
    "tickers": ",".join(WATCHLIST),
    "metrics": "pe_ratio",
    "period": "quarterly",
    "years": 5,
}
```

### Add Scheduling

Run automatically every day:

**Linux/Mac (cron):**
```bash
# Run daily at 6pm (after market close)
0 18 * * 1-5 cd /path/to/lab && python alert.py >> alert.log 2>&1
```

**GitHub Actions:** See [Lab 1's workflow](../01-free-pe-alert/.github/workflows/daily-alert.yml) for an example.

## Troubleshooting

### "Invalid API key"
- Check your `.env` file has the correct key
- Ensure no extra spaces or quotes around the key

### "Rate limit exceeded"
- Builder tier allows 300 requests/minute
- Add a delay between requests if running frequently

### "No data for ticker"
- Verify the ticker symbol is correct (e.g., "BRK.B" not "BRK-B")
- Some smaller companies may not have PE data

## Files

| File | Purpose |
|------|---------|
| `alert.py` | Main script - fetches PE ratios and checks threshold |
| `requirements.txt` | Python dependencies |
| `.env.example` | API key template |

## Learn More

- [MetricDuck API Docs](https://www.metricduck.com/docs)
- [Available Metrics](https://www.metricduck.com/metrics)
- [Next Lab: Dividend Yield Alert](../03-dividend-yield-alert/)
