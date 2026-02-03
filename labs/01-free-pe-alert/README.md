# Lab 1: Free PE Ratio Alert

**Build a working stock alert with zero cost - today.**

This lab shows you how to get email alerts when stocks drop below your PE ratio threshold. Everything is free:
- **Data:** yfinance (free, no API key)
- **Email:** Gmail SMTP (free)
- **Scheduling:** GitHub Actions (free for public repos)

## Quick Start (5 minutes)

### Option 1: Run Locally

```bash
# 1. Clone and navigate to the lab
git clone https://github.com/metric-duck/labs.git
cd labs/labs/01-free-pe-alert

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the alert script
python alert.py
```

**Output:**
```
Checking PE ratios for watchlist: AAPL, MSFT, GOOGL, AMZN, META
Alert threshold: PE < 20
--------------------------------------------------
AAPL: PE = 28.5
MSFT: PE = 32.1
GOOGL: PE = 18.2 ** ALERT! Below threshold **
AMZN: PE = 42.3
META: PE = 19.8 ** ALERT! Below threshold **
--------------------------------------------------

2 ALERT(S) TRIGGERED:
  - GOOGL: PE = 18.2
  - META: PE = 19.8
```

### Option 2: Automated Daily Alerts (Recommended)

Get PE alerts delivered to your email every day after market close.

1. **Fork this repository** to your GitHub account

2. **Add email secrets** (Settings > Secrets and variables > Actions):
   - `EMAIL_USER`: your Gmail address
   - `EMAIL_PASSWORD`: your Gmail [App Password](https://myaccount.google.com/apppasswords)
   - `EMAIL_TO`: where to receive alerts

3. **Enable GitHub Actions** (Actions tab > Enable workflows)

4. **Done!** You'll get daily emails at 6 PM ET (weekdays only)

## Customize Your Watchlist

Edit `alert.py` to change the stocks and threshold:

```python
# Your watchlist of stocks to monitor
WATCHLIST = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]

# Alert when PE ratio drops below this value
PE_THRESHOLD = 20
```

## How It Works

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   yfinance  │ --> │  alert.py   │ --> │    Email    │
│  (free API) │     │  (compare)  │     │ (optional)  │
└─────────────┘     └─────────────┘     └─────────────┘
        │                   │                   │
   Free data          Your logic          Gmail SMTP
   No API key         Threshold           (free)
                      PE < 20
```

## Email Setup (Optional)

To receive email alerts:

1. **Enable 2-Step Verification** on your Google account
2. **Create an App Password** at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. **Copy `.env.example` to `.env`** and fill in your credentials:

```bash
EMAIL_ENABLED=true
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_16_char_app_password
EMAIL_TO=your_email@gmail.com
```

## Limitations

yfinance is great for getting started, but has limitations:
- ~20 metrics available (vs 200+ with MetricDuck)
- Data can be delayed or occasionally unavailable
- No historical analysis beyond what Yahoo provides

**Ready for more?** Check out [Lab 2: PE Alert with MetricDuck API](../02-pe-ratio-alert/) for:
- 200+ fundamental metrics
- 7 years of historical data
- Higher data accuracy (SEC filings)
- Statistical analysis (rolling averages, standard deviations)

## Files

| File | Purpose |
|------|---------|
| `alert.py` | Main script - fetches PE ratios and checks threshold |
| `requirements.txt` | Python dependencies |
| `.env.example` | Email configuration template |
| `.github/workflows/daily-alert.yml` | GitHub Actions for daily scheduling |

## Next Steps

- [Lab 2: PE Alert with MetricDuck API](../02-pe-ratio-alert/) - 200+ metrics, historical data
- [Lab 3: Dividend Yield Alert](../03-dividend-yield-alert/) - Income investor alerts
- [Lab 4: Quality Watchlist](../04-quality-watchlist/) - ROIC monitoring
