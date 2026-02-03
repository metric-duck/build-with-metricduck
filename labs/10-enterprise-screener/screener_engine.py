"""
Lab 10: Screener Query Engine
Run stock screeners against your local database.
"""

import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")


def get_supabase_client():
    """Create Supabase client with anon key for read access."""
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def run_screener(filters: dict) -> list:
    """
    Run a screener with the given filters.

    Args:
        filters: Dict of metric filters, e.g.:
            {
                "pe_ratio": {"lt": 15},
                "roic": {"gt": 0.12},
                "net_margin": {"gt": 0.05}
            }

            Supported operators:
            - lt: less than
            - gt: greater than
            - eq: equals
            - between: [min, max]

    Returns:
        List of matching companies with their metrics
    """
    supabase = get_supabase_client()
    result = supabase.rpc("run_screener", {
        "filters": filters
    }).execute()
    return result.data


def get_company_metrics(ticker: str) -> dict:
    """
    Get all latest metrics for a single company.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dict with company info and metrics
    """
    supabase = get_supabase_client()

    company = supabase.table("companies").select("*").eq("ticker", ticker).single().execute()
    metrics = supabase.table("metrics_latest").select("*").eq("ticker", ticker).execute()

    return {
        "company": company.data,
        "metrics": {m["metric_id"]: m.get("value") for m in metrics.data}
    }


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Run stock screeners against your database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find cheap quality stocks
  python screener_engine.py --filters '{"pe_ratio": {"lt": 15}, "roic": {"gt": 0.12}}'

  # Get metrics for a single company
  python screener_engine.py --company AAPL

Filter operators:
  lt: less than       {"pe_ratio": {"lt": 15}}
  gt: greater than    {"roic": {"gt": 0.12}}
  eq: equals          {"sic": {"eq": "7372"}}
  between: range      {"pe_ratio": {"between": [10, 20]}}
"""
    )
    parser.add_argument("--filters", help="Filter conditions as JSON")
    parser.add_argument("--company", help="Get metrics for a single company")

    args = parser.parse_args()

    if args.company:
        result = get_company_metrics(args.company)
        print(f"\n{result['company']['company_name']} ({args.company})")
        print(f"SIC: {result['company'].get('sic', 'N/A')}")
        print("\nMetrics:")
        for metric, value in sorted(result['metrics'].items()):
            if value is not None:
                print(f"  {metric}: {value}")

    elif args.filters:
        filters = json.loads(args.filters)
        results = run_screener(filters)
        print(f"\nFound {len(results)} matches:\n")
        for r in results[:20]:
            print(f"  {r['ticker']}: {r['company_name']}")
        if len(results) > 20:
            print(f"  ... and {len(results) - 20} more")

    else:
        parser.print_help()
