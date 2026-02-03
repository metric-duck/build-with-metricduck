# Lab 10: Enterprise Screener

Build a stock screener for your startup. All enterprise tiers have full universe and metrics access - credits are the only limiter.

## Quick Start

```bash
cd labs/10-enterprise-screener
pip install -r requirements.txt
cp .env.example .env   # Add your API keys

psql $DATABASE_URL < schema.sql
python sync_service.py --top-n 100 --metrics pe_ratio roic gross_margin
python screener_engine.py --filters '{"pe_ratio": {"lt": 15}}'
```

## How It Works

```
1. Discover Universe     2. Sync Metrics           3. Run Screeners
   GET /companies           POST /screener/sync       SELECT * FROM
   /universe                {"tickers": [...]}        metrics_latest
        |                         |                   WHERE pe < 15
        v                         v                         |
   [AAPL, MSFT,...]        Your Database             Your Results
```

---

## Step 1: Discover Your Universe

Use the universe endpoint to get available companies with SEC-provided classifications:

```python
import httpx

response = httpx.get(
    "https://api.metricduck.com/api/v1/companies/universe",
    headers={"Authorization": f"Bearer {API_KEY}"}
)
companies = response.json()

# Each company has: ticker, company_name, cik, sic, rank
# - rank: market cap rank (1 = largest)
# - sic: SEC industry code (e.g., "7372" = software)

# Filter by size
large_caps = [c for c in companies if c["rank"] <= 500]

# Filter by industry (tech SIC codes: 7370-7379)
tech = [c for c in companies if c["sic"].startswith("73")]

# Get tickers for sync
tickers = [c["ticker"] for c in large_caps]
```

---

## Step 2: Sync Metrics

Sync your selected tickers to your database:

```bash
# Initial sync (full)
python sync_service.py --tickers AAPL MSFT GOOGL AMZN

# Daily updates (delta - only changed companies)
python sync_service.py --delta
```

**Tip:** Use `--delta` for daily syncs to minimize API calls.

### Preview Credit Cost (Dry Run)

Before committing to a sync, preview the cost:

```python
response = httpx.post(
    "https://api.metricduck.com/api/v1/screener/sync",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={
        "tickers": ["AAPL", "MSFT", "GOOGL"],
        "metrics": ["pe_ratio", "roic", "revenues"],
        "dry_run": True  # Preview only, no credits consumed
    }
)
# Returns: {"dry_run": true, "estimated_credits": 45, "companies_count": 3, ...}
```

### Sync API Request

**Required parameters:**
- **Company selection** (one required): `top_n` (1-1000) OR `tickers` list (max 1000)
- **metrics**: List of metric IDs (required, max 100)

```python
# Option 1: Top N by market cap
response = httpx.post(
    "https://api.metricduck.com/api/v1/screener/sync",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={
        "top_n": 500,
        "metrics": ["pe_ratio", "roic", "gross_margin", "fcf_yield"]
    }
)

# Option 2: Specific tickers
response = httpx.post(
    "https://api.metricduck.com/api/v1/screener/sync",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={
        "tickers": ["AAPL", "MSFT", "GOOGL"],
        "metrics": ["pe_ratio", "roic", "revenues"],
        "delta_since": "2024-01-15T00:00:00Z"  # Optional: for delta sync
    }
)
```

**Response:**
```json
{
  "sync_id": "sync_abc123",
  "tier": "seed",
  "data_scope": {"companies_count": 3, "metrics_count": 50},
  "data": [
    {
      "ticker": "AAPL",
      "company_name": "Apple Inc",
      "metrics": {"pe_ratio": 28.5, "roic": 0.52, ...}
    }
  ],
  "credits": {"used": 750, "remaining": 199250}
}
```

See [Tier Limits & Credits](https://metricduck.com/pricing) for details.

---

## Step 3: Run Screeners

Query your local database with filters:

```bash
# Find cheap quality stocks
python screener_engine.py --filters '{"pe_ratio": {"lt": 15}, "roic": {"gt": 0.12}}'

# Get single company metrics
python screener_engine.py --company AAPL
```

### Filter Operators

| Operator | Example | Meaning |
|----------|---------|---------|
| `lt` | `{"pe_ratio": {"lt": 15}}` | Less than 15 |
| `gt` | `{"roic": {"gt": 0.12}}` | Greater than 12% |
| `eq` | `{"sic": {"eq": "7372"}}` | Equals "7372" |
| `between` | `{"pe_ratio": {"between": [10, 20]}}` | Between 10 and 20 |

### Python Usage

```python
from screener_engine import run_screener

results = run_screener({
    "pe_ratio": {"lt": 20, "gt": 0},
    "roic": {"gt": 0.10},
    "net_margin": {"gt": 0.05}
})

for company in results:
    print(f"{company['ticker']}: {company['company_name']}")
```

---

## Discover Available Metrics

Get the list of metrics available for your tier:

```python
response = httpx.get(
    "https://api.metricduck.com/api/v1/screener/metrics",
    headers={"Authorization": f"Bearer {API_KEY}"}
)
metrics = response.json()
# Returns: {"tier": "seed", "metrics": [...]}  # All metrics available

for m in metrics["metrics"]:
    print(f"{m['id']}: {m['name']} ({m['category']})")
```

See [Full Metrics Catalog](https://metricduck.com/docs/api-reference) for complete list with descriptions.

---

## Check Status

Check your usage without consuming credits:

```bash
python sync_service.py --check-status
```

Or via API:
```python
response = httpx.get(
    "https://api.metricduck.com/api/v1/screener/sync/status",
    headers={"Authorization": f"Bearer {API_KEY}"}
)
# Returns: tier, limits, usage stats
```

---

## Environment Variables

```bash
METRICDUCK_API_KEY=your_api_key
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
SUPABASE_ANON_KEY=eyJ...  # For read-only screener queries
```

---

## Automation

The included GitHub Actions workflow runs delta sync on weekdays:

```yaml
# .github/workflows/daily-sync.yml
on:
  schedule:
    - cron: '0 23 * * 1-5'  # 6 PM ET
```

Add secrets: `METRICDUCK_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`

---

*Data powered by [MetricDuck](https://metricduck.com)* (attribution required for Seed tier)
