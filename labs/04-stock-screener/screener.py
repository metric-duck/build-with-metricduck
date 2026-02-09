#!/usr/bin/env python3
"""
Lab 04: Stock Screener — Rank Stocks by Quality + Value

Screen 50+ stocks by ROIC, FCF Yield, FCF Margin, PE, and EV/EBITDA.
Composite score: Quality (60%) + Value (40%), percentile-ranked.

Five of the screening metrics — ROIC, FCF Yield, FCF Margin, EV/EBIT,
and Total Shareholder Yield — are not available in yfinance.

Uses MetricDuck API statistical dimensions (Q.MED8, Q.TREND8)
that are not available in yfinance or any free alternative.

Usage:
    python screener.py                          # Top 50 by market cap
    python screener.py --tickers AAPL,MSFT,GOOGL,AMZN,META,NVDA
    python screener.py --count 100 --top 20     # Screen 100, show top 20
    python screener.py --json                   # Machine-readable output
"""

import json
import os
import sys

import httpx

# =============================================================================
# CONFIGURATION — Edit these to customize
# =============================================================================

API_BASE_URL = "https://api.metricduck.com/api/v1"

DEFAULT_COUNT = 50   # Number of stocks to screen from universe
DEFAULT_TOP = 10     # Number of results to display

# Quality metrics: higher is better.
# Format: (display_name, metric_id, direction)
QUALITY_METRICS = [
    ("ROIC",       "roic",       "higher"),
    ("FCF Margin", "fcf_margin", "higher"),
]

# Value metrics: mixed directions.
VALUE_METRICS = [
    ("PE Ratio",  "pe_ratio",  "lower"),
    ("FCF Yield", "fcf_yield", "higher"),
    ("EV/EBITDA", "ev_ebitda", "lower"),
]

QUALITY_WEIGHT = 0.6
VALUE_WEIGHT = 0.4

# All metric IDs for the API call (deduplicated)
ALL_METRIC_IDS = list(dict.fromkeys(
    [m[1] for m in QUALITY_METRICS]
    + [m[1] for m in VALUE_METRICS]
))

DISPLAY_WIDTH = 74

# Guest access limits (no API key)
GUEST_MAX_TICKERS = 10


# =============================================================================
# DATA FETCHING
# =============================================================================


def _get_headers() -> dict:
    """Build authorization headers if API key is set."""
    api_key = os.getenv("METRICDUCK_API_KEY")
    if api_key:
        return {"Authorization": f"Bearer {api_key}"}
    return {}


def _handle_error(response: httpx.Response) -> None:
    """Handle common API errors."""
    if response.status_code == 401:
        print("Error: Invalid API key. Check your METRICDUCK_API_KEY.",
              file=sys.stderr)
        sys.exit(1)

    if response.status_code == 429:
        retry_after = response.headers.get("Retry-After", "60")
        try:
            detail = response.json().get("detail", {})
        except Exception:
            detail = {}

        if isinstance(detail, dict):
            error = detail.get("error", "")
            if error == "Daily credit limit reached":
                print(f"Daily credit limit reached "
                      f"({detail.get('daily_limit', '?')} credits/day).",
                      file=sys.stderr)
                print(f"Resets at {detail.get('resets_at', 'midnight UTC')}.",
                      file=sys.stderr)
                print("Upgrade: https://www.metricduck.com/pricing",
                      file=sys.stderr)
            elif error == "Insufficient credits":
                print(f"Monthly credit limit reached "
                      f"({detail.get('monthly_limit', '?')} credits).",
                      file=sys.stderr)
                print("Upgrade at https://www.metricduck.com/pricing",
                      file=sys.stderr)
            elif error == "Daily request limit reached":
                limit = detail.get("daily_limit", 5)
                print(f"Daily request limit reached ({limit}/day for guests).",
                      file=sys.stderr)
                print("Register free for 500 credits/day: "
                      "https://www.metricduck.com/auth/register",
                      file=sys.stderr)
            else:
                print(f"Rate limit reached. Wait {retry_after}s and try again.",
                      file=sys.stderr)
                print("Register free for higher limits: "
                      "https://www.metricduck.com/auth/register",
                      file=sys.stderr)
        else:
            print(f"Rate limit reached. Wait {retry_after}s and try again.",
                  file=sys.stderr)
        sys.exit(1)

    if response.status_code != 200:
        print(f"Error: API returned {response.status_code}", file=sys.stderr)
        try:
            detail = response.json().get("detail", {})
            if isinstance(detail, dict):
                print(detail.get("error", response.text[:200]),
                      file=sys.stderr)
            else:
                print(str(detail)[:200], file=sys.stderr)
        except Exception:
            print(response.text[:200], file=sys.stderr)
        sys.exit(1)


def fetch_universe(count: int) -> list[dict]:
    """
    Fetch top companies by market cap from the universe endpoint.

    Returns list of dicts with 'ticker', 'company_name', 'sic', 'rank'.
    """
    try:
        response = httpx.get(
            f"{API_BASE_URL}/companies/universe",
            params={"limit": count},
            headers=_get_headers(),
            timeout=30.0,
        )
    except httpx.ConnectError:
        print("Error: Could not connect to MetricDuck API.", file=sys.stderr)
        sys.exit(1)
    except httpx.TimeoutException:
        print("Error: API request timed out.", file=sys.stderr)
        sys.exit(1)

    _handle_error(response)
    data = response.json()
    return data.get("companies", [])


def fetch_metrics(tickers: list[str]) -> dict:
    """
    Fetch screening metrics for a batch of tickers.

    Returns the full API response dict with data keyed by ticker.
    Handles batching if more than 100 tickers.
    """
    BATCH_SIZE = 100
    merged = {}

    for i in range(0, len(tickers), BATCH_SIZE):
        batch = tickers[i:i + BATCH_SIZE]

        try:
            response = httpx.get(
                f"{API_BASE_URL}/data/metrics",
                params={
                    "tickers": ",".join(batch),
                    "metrics": ",".join(ALL_METRIC_IDS),
                    "period": "ttm",      # Trailing Twelve Months
                    "price": "current",   # Recompute valuations at today's price
                    "years": 1,           # 1 year of history
                },
                headers=_get_headers(),
                timeout=60.0,
            )
        except httpx.ConnectError:
            print("Error: Could not connect to MetricDuck API.",
                  file=sys.stderr)
            sys.exit(1)
        except httpx.TimeoutException:
            print("Error: API request timed out.", file=sys.stderr)
            sys.exit(1)

        _handle_error(response)
        batch_data = response.json().get("data", {})
        merged.update(batch_data)

    return merged


def extract_metric(api_data: dict, ticker: str, metric_id: str) -> float | None:
    """Extract the base (non-dimension) metric value for a ticker."""
    company = api_data.get(ticker, {})
    metric = company.get("metrics", {}).get(metric_id, {})
    for v in metric.get("values", []):
        if v.get("dimension") is None and v.get("value") is not None:
            return v["value"]
    return None


def get_company_name(api_data: dict, ticker: str) -> str:
    """Extract company name from API response."""
    return api_data.get(ticker, {}).get("company_name", ticker)


# =============================================================================
# SCORING
# =============================================================================


def compute_percentile_ranks(
    values: dict[str, float | None], direction: str
) -> dict[str, float]:
    """
    Compute percentile ranks (0-100) for a dict of ticker -> value.

    direction: "higher" means higher values get higher percentile.
               "lower" means lower values get higher percentile.
    Returns only tickers with non-None values.
    """
    valid = {t: v for t, v in values.items() if v is not None}
    if not valid:
        return {}

    # Sort: for "higher", ascending order so highest is last (rank N).
    # For "lower", descending order so lowest is last (rank N).
    reverse = direction == "lower"
    sorted_tickers = sorted(valid, key=lambda t: valid[t], reverse=reverse)

    n = len(sorted_tickers)
    return {
        ticker: (i / (n - 1)) * 100 if n > 1 else 50.0
        for i, ticker in enumerate(sorted_tickers)
    }


def score_stocks(api_data: dict) -> list[dict]:
    """
    Score all stocks by Quality + Value composite.

    Returns list of dicts sorted by composite score (highest first):
    [{"ticker": "AAPL", "company_name": "...", "metrics": {...}, "scores": {...}}]
    """
    tickers = list(api_data.keys())

    # Compute percentile ranks for each metric
    quality_ranks = {}
    for display_name, metric_id, direction in QUALITY_METRICS:
        values = {t: extract_metric(api_data, t, metric_id) for t in tickers}
        quality_ranks[metric_id] = compute_percentile_ranks(values, direction)

    value_ranks = {}
    for display_name, metric_id, direction in VALUE_METRICS:
        values = {t: extract_metric(api_data, t, metric_id) for t in tickers}
        value_ranks[metric_id] = compute_percentile_ranks(values, direction)

    # Compute composite score for each ticker
    results = []
    for ticker in tickers:
        # Average percentiles within each category
        q_scores = [
            quality_ranks[m_id][ticker]
            for _, m_id, _ in QUALITY_METRICS
            if ticker in quality_ranks.get(m_id, {})
        ]
        v_scores = [
            value_ranks[m_id][ticker]
            for _, m_id, _ in VALUE_METRICS
            if ticker in value_ranks.get(m_id, {})
        ]

        if not q_scores and not v_scores:
            continue

        q_avg = sum(q_scores) / len(q_scores) if q_scores else 0
        v_avg = sum(v_scores) / len(v_scores) if v_scores else 0

        # Weighted composite (handle missing categories)
        if not q_scores:
            composite = v_avg
        elif not v_scores:
            composite = q_avg
        else:
            composite = QUALITY_WEIGHT * q_avg + VALUE_WEIGHT * v_avg

        # Determine signal
        if q_avg >= 70 and v_avg >= 70:
            signal = "BALANCED"
        elif q_avg >= 70:
            signal = "QUALITY"
        elif v_avg >= 70:
            signal = "VALUE"
        else:
            signal = ""

        results.append({
            "ticker": ticker,
            "company_name": get_company_name(api_data, ticker),
            "metrics": {
                m_id: extract_metric(api_data, ticker, m_id)
                for _, m_id, _ in QUALITY_METRICS + VALUE_METRICS
            },
            "scores": {
                "quality": round(q_avg, 1),
                "value": round(v_avg, 1),
                "composite": round(composite, 1),
            },
            "signal": signal,
        })

    results.sort(key=lambda x: x["scores"]["composite"], reverse=True)
    return results


# =============================================================================
# DISPLAY
# =============================================================================


def format_pct(value: float | None) -> str:
    """Format a ratio as percentage."""
    if value is None:
        return "N/A"
    return f"{value * 100:.1f}%"


def format_ratio(value: float | None) -> str:
    """Format a ratio value."""
    if value is None:
        return "N/A"
    if abs(value) >= 1000:
        return f"{value:,.0f}"
    return f"{value:.2f}"


def display_results(results: list[dict], top: int, total_screened: int):
    """Display the ranked results table."""
    shown = results[:top]

    print()
    print("=" * DISPLAY_WIDTH)
    title = f"STOCK SCREENER: TOP {len(shown)} OF {total_screened} STOCKS"
    print(f"{title:^{DISPLAY_WIDTH}}")
    print("=" * DISPLAY_WIDTH)
    print(f"Quality weight: {QUALITY_WEIGHT:.0%} | "
          f"Value weight: {VALUE_WEIGHT:.0%}")
    print()

    # Header
    print(f"{'Rank':>4}  {'Ticker':<6} {'Company':<20} "
          f"{'ROIC':>7} {'FCF Yld':>7} {'PE':>7} {'Score':>6} {'':>8}")
    print("-" * DISPLAY_WIDTH)

    for i, stock in enumerate(shown, 1):
        m = stock["metrics"]
        roic = format_pct(m.get("roic"))
        fcf_yield = format_pct(m.get("fcf_yield"))
        pe = format_ratio(m.get("pe_ratio"))
        score = f"{stock['scores']['composite']:.1f}"
        signal = stock["signal"]

        # Truncate company name
        name = stock["company_name"][:20]

        print(f"{i:>4}  {stock['ticker']:<6} {name:<20} "
              f"{roic:>7} {fcf_yield:>7} {pe:>7} {score:>6} {signal:>8}")

    print("-" * DISPLAY_WIDTH)

    # Credit estimate
    credits = total_screened * len(ALL_METRIC_IDS) * 1
    print(f"Screened {total_screened} stocks | "
          f"{len(ALL_METRIC_IDS)} metrics | ~{credits} credits")
    print()
    print("  QUALITY = top 30% quality | VALUE = top 30% value")
    print("  BALANCED = top 30% in both")
    print()
    print("  70 metrics: https://www.metricduck.com/metrics")
    print("=" * DISPLAY_WIDTH)

    # CTA for guests
    if not os.getenv("METRICDUCK_API_KEY"):
        print()
        print("Register free for full screening (50+ stocks):")
        print("  https://www.metricduck.com/auth/register")

    print()


# =============================================================================
# JSON OUTPUT
# =============================================================================


def build_screener_data(
    results: list[dict], top: int, total_screened: int
) -> dict:
    """Build structured data for JSON output."""
    return {
        "screened": total_screened,
        "showing": min(top, len(results)),
        "quality_weight": QUALITY_WEIGHT,
        "value_weight": VALUE_WEIGHT,
        "metrics": [m[1] for m in QUALITY_METRICS + VALUE_METRICS],
        "results": results[:top],
    }


# =============================================================================
# MAIN
# =============================================================================


def parse_args() -> dict:
    """Parse command-line arguments using sys.argv."""
    args_list = sys.argv[1:]
    opts = {
        "tickers": None,
        "count": DEFAULT_COUNT,
        "top": DEFAULT_TOP,
        "json": False,
        "dry_run": False,
    }

    i = 0
    while i < len(args_list):
        arg = args_list[i]
        if arg == "--json":
            opts["json"] = True
        elif arg == "--dry-run":
            opts["dry_run"] = True
        elif arg == "--tickers" and i + 1 < len(args_list):
            i += 1
            opts["tickers"] = [t.strip().upper() for t in args_list[i].split(",")]
        elif arg == "--count" and i + 1 < len(args_list):
            i += 1
            opts["count"] = int(args_list[i])
        elif arg == "--top" and i + 1 < len(args_list):
            i += 1
            opts["top"] = int(args_list[i])
        elif arg in ("--help", "-h"):
            print("Usage: python screener.py [OPTIONS]")
            print()
            print("Options:")
            print("  --tickers AAPL,MSFT,...  Custom ticker list")
            print("  --count N               Stocks to screen (default 50)")
            print("  --top N                 Results to show (default 10)")
            print("  --json                  Machine-readable output")
            print("  --dry-run               Preview credit cost (no API calls)")
            sys.exit(0)
        i += 1

    return opts


def main():
    """Main entry point."""
    opts = parse_args()
    json_output = opts["json"]
    api_key = os.getenv("METRICDUCK_API_KEY")

    # Step 1: Determine ticker count
    if opts["tickers"]:
        ticker_count = len(opts["tickers"])
        if not opts["dry_run"] and not json_output:
            print(f"Screening {ticker_count} custom tickers...")
    else:
        ticker_count = opts["count"]

        # Guest auto-cap: without API key, limit to GUEST_MAX_TICKERS
        if not api_key and ticker_count > GUEST_MAX_TICKERS:
            ticker_count = GUEST_MAX_TICKERS
            if not json_output:
                print(f"Guest mode: screening top {ticker_count} "
                      f"(register free for up to 200 tickers)")

    # Dry run: show credit estimate and exit
    if opts["dry_run"]:
        credits = ticker_count * len(ALL_METRIC_IDS) * 1
        print()
        print("Dry run — no API calls made.")
        print()
        print(f"Request: {ticker_count} tickers x {len(ALL_METRIC_IDS)} metrics"
              f" x 1 year (TTM)")
        print(f"Estimated cost: ~{credits} credits")
        print()
        if not api_key:
            print(f"  Guest (no key):     No credit cost (5 requests/day limit)")
        print(f"  Free (registered):  {credits} of 500 daily credits")
        print(f"  Formula:            tickers x metrics x years")
        print()
        sys.exit(0)

    # Step 2: Get ticker list
    if opts["tickers"]:
        tickers = opts["tickers"]
    else:
        count = ticker_count

        if not json_output:
            print(f"Fetching top {count} companies by market cap...")
        universe = fetch_universe(count)
        tickers = [c["ticker"] for c in universe]
        if not tickers:
            print("Error: No companies returned from universe.",
                  file=sys.stderr)
            sys.exit(1)
        if not json_output:
            print(f"Got {len(tickers)} companies. Fetching metrics...")

    # Step 3: Fetch metrics
    api_data = fetch_metrics(tickers)
    if not api_data:
        print("Error: No metric data returned.", file=sys.stderr)
        sys.exit(1)

    # Step 4: Score and rank
    results = score_stocks(api_data)

    if not results:
        print("Error: No stocks had enough data to score.", file=sys.stderr)
        sys.exit(1)

    # Step 5: Output
    total_screened = len(tickers)
    if json_output:
        print(json.dumps(
            build_screener_data(results, opts["top"], total_screened),
            indent=2,
        ))
    else:
        display_results(results, opts["top"], total_screened)


if __name__ == "__main__":
    main()
