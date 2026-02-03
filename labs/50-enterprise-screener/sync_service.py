"""
Lab 10: MetricDuck Sync Service
Syncs fundamental data from MetricDuck to your Supabase database.

Supports both full syncs (initial load) and delta syncs (daily updates).
Delta sync uses the delta_since parameter to only fetch companies
that have been updated since your last sync, saving credits.
"""

import httpx
import os
from datetime import datetime, timezone
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

# Configuration
METRICDUCK_API = "https://api.metricduck.com/api/v1"
API_KEY = os.getenv("METRICDUCK_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")


def get_supabase_client():
    """Create Supabase client with service key for write access."""
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def get_last_sync_timestamp() -> Optional[datetime]:
    """
    Get the timestamp of the last successful sync.

    Used for delta sync to only fetch companies updated since this time.
    Returns None if no previous sync exists (triggers full sync).
    """
    supabase = get_supabase_client()
    result = (
        supabase.table("sync_log")
        .select("synced_at")
        .eq("status", "success")
        .order("synced_at", desc=True)
        .limit(1)
        .execute()
    )
    if result.data and result.data[0].get("synced_at"):
        return datetime.fromisoformat(result.data[0]["synced_at"].replace("Z", "+00:00"))
    return None


def sync_metrics(
    metrics: List[str],
    tickers: Optional[List[str]] = None,
    top_n: Optional[int] = None,
    delta_since: Optional[datetime] = None,
) -> dict:
    """
    Sync metrics from MetricDuck to local database.

    All enterprise tiers have full universe and metrics access.
    Credits are the only rate limiter:
    - Seed: 200K credits/month
    - Launch: 800K credits/month
    - Growth: 3.2M credits/month
    - Scale: 12M credits/month

    Credit formula: (companies × metrics × new_quarters × 5) + (historical × 1)
    See pricing page for full details.

    Args:
        metrics: List of metric IDs to fetch (required, max 100)
        tickers: Explicit list of tickers (max 1000, mutually exclusive with top_n)
        top_n: Select top N companies by market cap rank (1-1000, mutually exclusive with tickers)
        delta_since: Only fetch companies updated since this timestamp (UTC).
                     Pass None for full sync. Use get_last_sync_timestamp() for delta.

    Returns:
        dict with sync statistics including credits used and is_delta flag

    Raises:
        ValueError: If neither tickers nor top_n is provided, or if both are provided
    """
    if not API_KEY:
        raise ValueError("METRICDUCK_API_KEY not set")

    # Validate: must provide either top_n or tickers, not both
    if top_n is None and tickers is None:
        raise ValueError("Must provide either 'top_n' or 'tickers' to select companies")
    if top_n is not None and tickers is not None:
        raise ValueError("Provide either 'top_n' or 'tickers', not both")

    supabase = get_supabase_client()

    # Build request - metrics is required
    request_body = {"format": "json", "metrics": metrics}

    if delta_since:
        request_body["delta_since"] = delta_since.isoformat()
        print(f"Delta sync: fetching updates since {delta_since.isoformat()}")
    else:
        print("Full sync...")

    print(f"Syncing {len(metrics)} metrics")

    if tickers:
        request_body["tickers"] = tickers
        print(f"Companies: {len(tickers)} specific tickers")
    elif top_n:
        request_body["top_n"] = top_n
        print(f"Companies: top {top_n} by market cap")

    # Fetch from MetricDuck
    response = httpx.post(
        f"{METRICDUCK_API}/screener/sync",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json=request_body,
        timeout=120.0
    )
    response.raise_for_status()
    data = response.json()

    # Log response info
    is_delta = data.get("is_delta", False)
    credits = data.get("credits", {})
    scope = data.get("data_scope", {})

    print(f"Sync type: {'Delta' if is_delta else 'Full'}")
    print(f"Companies: {scope.get('companies_count', 'N/A')}")
    print(f"Metrics: {scope.get('metrics_count', 'N/A')}")
    print(f"Credits used: {credits.get('used', 'N/A'):,}")
    print(f"Credits remaining: {credits.get('remaining', 'N/A'):,}")

    # Process companies
    companies_data = []
    metrics_data = []
    now = datetime.now(timezone.utc).isoformat()

    for company in data.get("data", []):
        # Company master data
        companies_data.append({
            "ticker": company["ticker"],
            "company_name": company["company_name"],
            "sic": company.get("sic"),  # SIC code (API returns sic, not sector/industry)
            "cik": company.get("cik"),
            "updated_at": company.get("updated_at", now)
        })

        # Metric values (single latest value per metric)
        for metric_id, value in company.get("metrics", {}).items():
            metrics_data.append({
                "ticker": company["ticker"],
                "metric_id": metric_id,
                "value": value,  # Single value (TTM for flows, SS for snapshots)
                "updated_at": now
            })

    # Upsert to database
    if companies_data:
        supabase.table("companies").upsert(companies_data).execute()
        print(f"Upserted {len(companies_data)} companies")

    if metrics_data:
        supabase.table("metrics_latest").upsert(metrics_data).execute()
        print(f"Upserted {len(metrics_data)} metric records")

    # Log sync with timestamp for future delta syncs
    sync_log = {
        "sync_id": data.get("sync_id"),
        "credits_used": credits.get("used"),
        "companies_count": len(companies_data),
        "metrics_count": len(metrics_data),
        "is_delta": is_delta,
        "status": "success",
        "synced_at": now
    }
    supabase.table("sync_log").insert(sync_log).execute()

    return {
        "sync_id": data.get("sync_id"),
        "is_delta": is_delta,
        "companies": len(companies_data),
        "metrics": len(metrics_data),
        "credits_used": credits.get("used"),
        "credits_remaining": credits.get("remaining")
    }


def check_status() -> dict:
    """Check current sync status and credit limits without consuming credits."""
    response = httpx.get(
        f"{METRICDUCK_API}/screener/sync/status",
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Sync MetricDuck data to your database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sync top 500 companies with core metrics
  python sync_service.py --top-n 500 --metrics pe_ratio roic gross_margin fcf_yield

  # Sync specific tickers
  python sync_service.py --tickers AAPL MSFT GOOGL --metrics revenues net_income

  # Delta sync (Day 2+) - only fetch updates since last sync
  python sync_service.py --top-n 500 --metrics pe_ratio roic --delta

  # Check credit status
  python sync_service.py --check-status

Credit Budget (Seed tier):
  - Monthly limit: 200,000 credits
  - Example: 500 companies × 20 metrics × 5 = 50,000 credits
  - See https://metricduck.com/pricing for details

Required Parameters:
  - Company selection: --top-n OR --tickers (mutually exclusive)
  - Metrics: --metrics (required, max 100)
"""
    )
    parser.add_argument("--delta", action="store_true",
                        help="Delta sync: only fetch updates since last sync (saves credits)")
    parser.add_argument("--metrics", nargs="+", required=False,
                        help="Metrics to fetch (required for sync, max 100)")
    parser.add_argument("--tickers", nargs="+",
                        help="Specific tickers (max 1000, mutually exclusive with --top-n)")
    parser.add_argument("--top-n", type=int, dest="top_n",
                        help="Top N companies by market cap (1-1000, mutually exclusive with --tickers)")
    parser.add_argument("--check-status", action="store_true",
                        help="Check credit status without syncing")

    args = parser.parse_args()

    if args.check_status:
        status = check_status()
        print("Sync Status:")
        print(f"  Tier: {status.get('tier', 'N/A')}")
        if status.get("is_enterprise"):
            limits = status.get("limits", {})
            usage = status.get("usage", {})
            access = status.get("access", {})
            print(f"  Universe: {access.get('universe', 'N/A')}")
            print(f"  Metrics: {access.get('metrics', 'N/A')}")
            print(f"  Monthly credits: {limits.get('monthly_credits', 'N/A'):,}")
            print(f"  Syncs this month: {usage.get('syncs_used_this_month', 0)}")
            print(f"  Last sync: {usage.get('last_sync', 'Never')}")
        else:
            print("  Enterprise tier required for sync API")
    else:
        # Validate required params for sync
        if not args.metrics:
            parser.error("--metrics is required for sync (e.g., --metrics pe_ratio roic)")

        # Determine delta_since timestamp
        delta_since = None
        if args.delta:
            delta_since = get_last_sync_timestamp()
            if delta_since is None:
                print("No previous sync found. Running full sync instead.")

        result = sync_metrics(
            metrics=args.metrics,
            tickers=args.tickers,
            top_n=args.top_n,
            delta_since=delta_since
        )
        print(f"\nSync complete!")
        print(f"  Type: {'Delta' if result['is_delta'] else 'Full'}")
        print(f"  Companies: {result['companies']}")
        print(f"  Metrics: {result['metrics']}")
        print(f"  Credits used: {result['credits_used']:,}")
        print(f"  Credits remaining: {result['credits_remaining']:,}")
