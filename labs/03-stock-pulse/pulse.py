#!/usr/bin/env python3
"""
Lab 03: Stock Pulse - Value Trap Detector

Check any stock against its own 2-year history. Is ROIC improving
or declining? Is the valuation expanding or compressing? The diagnosis
tells you: OPPORTUNITY, EARNING IT, WATCH, VALUE TRAP, or STABLE.

Uses MetricDuck API statistical dimensions (Q.MED8, Q.TREND8)
that are not available in yfinance or any free alternative.

Usage:
    python pulse.py              # Default: AAPL
    python pulse.py INTC         # Any single stock
    python pulse.py INTC --json  # Machine-readable output
"""

import json
import os
import sys

import httpx

# =============================================================================
# CONFIGURATION - Edit these to customize
# =============================================================================

DEFAULT_TICKER = "AAPL"

API_BASE_URL = "https://api.metricduck.com/api/v1"

# Vital signs: margin/return metrics compared to their 2-year median (Q.MED8)
# These are ratios where quarterly and TTM values are directly comparable.
# Format: (display_name, metric_id, unit_type)
VITAL_SIGNS = [
    ("ROIC", "roic", "pct"),
    ("Gross Margin", "gross_margin", "pct"),
    ("Oper Margin", "oper_margin", "pct"),
    ("FCF Margin", "fcf_margin", "pct"),
]

# Valuation snapshot: show current value + trend direction only.
# Note: PE and EV/EBITDA Q.MED8 values use quarterly earnings (not TTM),
# making them ~4x the TTM value. So we only show the trend, not the median.
VALUATION_SNAPSHOT = [
    ("PE Ratio", "pe_ratio", "ratio"),
    ("EV/EBITDA", "ev_ebitda", "ratio"),
]

# Growth metrics: YoY and 3-year CAGR from TTM dimensions
GROWTH_METRICS = [
    ("Revenue YoY", "revenues", "TTM.YOY"),
    ("Revenue 3yr CAGR", "revenues", "TTM.CAGR3"),
]

# Leverage: current value only (no Q-based dimensions available)
LEVERAGE_METRICS = [
    ("Debt/Equity", "debt_to_equity", "ratio"),
]

# All metric IDs for the API call (deduplicated)
ALL_METRIC_IDS = list(dict.fromkeys(
    [m[1] for m in VITAL_SIGNS]
    + [m[1] for m in VALUATION_SNAPSHOT]
    + [m[1] for m in GROWTH_METRICS]
    + [m[1] for m in LEVERAGE_METRICS]
))

# All dimensions to request
ALL_DIMENSIONS = ["Q.MED8", "Q.TREND8", "TTM.YOY", "TTM.CAGR3"]

DISPLAY_WIDTH = 58


# =============================================================================
# DATA FETCHING
# =============================================================================


def fetch_stock_data(ticker: str) -> dict | None:
    """
    Fetch metrics with statistical dimensions from MetricDuck API.

    Uses guest access (no API key) — all 70 metrics + 12 dimensions free.
    """
    api_key = os.getenv("METRICDUCK_API_KEY")
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        response = httpx.get(
            f"{API_BASE_URL}/data/metrics",
            params={
                "tickers": ticker,
                "metrics": ",".join(ALL_METRIC_IDS),
                "period": "ttm",      # Trailing Twelve Months
                "price": "current",   # Recompute valuations at today's price
                "years": 1,           # 1 year of history
                "dimensions": ",".join(ALL_DIMENSIONS),  # Q.MED8, Q.TREND8, etc.
            },
            headers=headers,
            timeout=30.0,
        )

        if response.status_code == 401:
            print("Error: Invalid API key. Check your METRICDUCK_API_KEY.")
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
            print(f"Error: API returned {response.status_code}",
                  file=sys.stderr)
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

        return response.json()

    except httpx.ConnectError:
        print("Error: Could not connect to MetricDuck API.")
        print("Check your internet connection and try again.")
        sys.exit(1)
    except httpx.TimeoutException:
        print("Error: API request timed out. Try again.")
        sys.exit(1)


def extract_metric(api_data: dict, ticker: str, metric_id: str) -> float | None:
    """Extract the base (non-dimension) metric value."""
    company = api_data.get("data", {}).get(ticker, {})
    metric = company.get("metrics", {}).get(metric_id, {})
    for v in metric.get("values", []):
        if v.get("dimension") is None and v.get("value") is not None:
            return v["value"]
    return None


def extract_dimension(
    api_data: dict, ticker: str, metric_id: str, dimension: str
) -> float | None:
    """Extract a dimension value (Q.MED8, Q.TREND8, TTM.YOY, etc.)."""
    company = api_data.get("data", {}).get(ticker, {})
    metric = company.get("metrics", {}).get(metric_id, {})
    for v in metric.get("values", []):
        if v.get("dimension") == dimension and v.get("value") is not None:
            return v["value"]
    return None


def get_company_name(api_data: dict, ticker: str) -> str:
    """Extract company name from API response."""
    return api_data.get("data", {}).get(ticker, {}).get("company_name", ticker)


# =============================================================================
# FORMATTING
# =============================================================================


def format_value(value: float | None, unit_type: str) -> str:
    """Format a metric value for display."""
    if value is None:
        return "N/A"
    if unit_type == "pct":
        return f"{value * 100:.1f}%"
    if abs(value) >= 1000:
        return f"{value:,.0f}"
    return f"{value:.2f}"


def format_pct_change(value: float | None) -> str:
    """Format a percentage change value (already a ratio)."""
    if value is None:
        return "N/A"
    sign = "+" if value > 0 else ""
    return f"{sign}{value * 100:.1f}%"


def format_vs_median(current: float | None, median: float | None) -> str:
    """Format the current-vs-median comparison as a signal string."""
    if current is None or median is None or median == 0:
        return "N/A"
    pct = (current - median) / abs(median) * 100
    if pct > 5:
        return f"^ {abs(pct):.0f}% above"
    elif pct < -5:
        return f"v {abs(pct):.0f}% below"
    else:
        return "~ Near norm"


def format_trend(trend_value: float | None) -> str:
    """Convert Q.TREND8 slope to a human-readable direction."""
    if trend_value is None:
        return "N/A"
    if trend_value > 0.003:
        return "Rising"
    elif trend_value < -0.003:
        return "Falling"
    else:
        return "Stable"


# =============================================================================
# DIAGNOSIS
# =============================================================================


def _compute_diagnosis(api_data: dict, ticker: str) -> tuple[str, str]:
    """
    Compute the diagnostic signal word and explanation text.

    Returns (signal, diagnosis_text) where signal is one of:
    OPPORTUNITY, EARNING IT, WATCH, VALUE TRAP, STABLE.
    """
    roic_trend = extract_dimension(api_data, ticker, "roic", "Q.TREND8")
    pe_trend = extract_dimension(api_data, ticker, "pe_ratio", "Q.TREND8")

    if roic_trend is None or pe_trend is None:
        return "STABLE", (
            f"{ticker} — insufficient trend data for diagnosis. "
            "ROIC or PE trend not available."
        )

    r_trend = format_trend(roic_trend)
    p_trend = format_trend(pe_trend)

    if r_trend == "Rising" and p_trend == "Falling":
        return "OPPORTUNITY", (
            f"{ticker}'s quality is improving while valuation compresses — "
            "the market may not be pricing in the improvement yet."
        )
    elif r_trend == "Falling" and p_trend == "Rising":
        return "VALUE TRAP", (
            f"{ticker}'s quality is declining while valuation expands — "
            "paying more for a deteriorating business. "
            "Investigate before assuming it's cheap."
        )
    elif r_trend == "Rising" and p_trend == "Rising":
        return "EARNING IT", (
            f"{ticker}'s quality is improving and the market is recognizing it. "
            "Is the premium justified?"
        )
    elif r_trend == "Falling" and p_trend == "Falling":
        return "WATCH", (
            f"{ticker}'s quality and valuation are both declining — "
            "the market may be right to de-rate. Investigate the cause."
        )
    else:
        return "STABLE", (
            f"{ticker} shows no strong trend signal — "
            "ROIC and valuation are both near 2-year norms."
        )


# =============================================================================
# JSON OUTPUT
# =============================================================================


def build_pulse_data(api_data: dict, ticker: str) -> dict:
    """Build structured data for JSON output."""
    signal, diagnosis_text = _compute_diagnosis(api_data, ticker)

    # Vital signs
    vital_signs = {}
    for display_name, metric_id, unit_type in VITAL_SIGNS:
        current = extract_metric(api_data, ticker, metric_id)
        median = extract_dimension(api_data, ticker, metric_id, "Q.MED8")
        trend = extract_dimension(api_data, ticker, metric_id, "Q.TREND8")
        vs_median = None
        if current is not None and median is not None and median != 0:
            vs_median = round((current - median) / abs(median), 4)
        vital_signs[metric_id] = {
            "label": display_name,
            "current": current,
            "median": median,
            "trend": format_trend(trend).lower() if trend is not None else None,
            "vs_median": vs_median,
        }

    # Valuation
    valuation = {}
    for display_name, metric_id, unit_type in VALUATION_SNAPSHOT:
        current = extract_metric(api_data, ticker, metric_id)
        trend = extract_dimension(api_data, ticker, metric_id, "Q.TREND8")
        valuation[metric_id] = {
            "label": display_name,
            "current": current,
            "trend": format_trend(trend).lower() if trend is not None else None,
        }

    # Growth
    growth = {}
    for display_name, metric_id, dimension in GROWTH_METRICS:
        val = extract_dimension(api_data, ticker, metric_id, dimension)
        growth[dimension.lower()] = {"label": display_name, "value": val}

    # Leverage
    leverage = {}
    for display_name, metric_id, unit_type in LEVERAGE_METRICS:
        current = extract_metric(api_data, ticker, metric_id)
        leverage[metric_id] = {"label": display_name, "current": current}

    return {
        "ticker": ticker,
        "company_name": get_company_name(api_data, ticker),
        "signal": signal.replace(" ", "_"),
        "vital_signs": vital_signs,
        "valuation": valuation,
        "growth": growth,
        "leverage": leverage,
        "diagnosis": diagnosis_text,
    }


# =============================================================================
# DISPLAY
# =============================================================================


def display_pulse(api_data: dict, ticker: str):
    """Display the full stock pulse analysis."""
    name = get_company_name(api_data, ticker)

    # Header
    print()
    print("=" * DISPLAY_WIDTH)
    print(f"{'STOCK PULSE: ' + ticker:^{DISPLAY_WIDTH}}")
    print(f"{name:^{DISPLAY_WIDTH}}")
    print("=" * DISPLAY_WIDTH)

    # Vital Signs: margins and returns vs 2-year median
    print()
    print("VITAL SIGNS  (current vs 2-year median)")
    print("-" * DISPLAY_WIDTH)
    print(f"{'':18} {'Current':>10} {'2yr Med':>10} {'Signal':>16}")
    print("-" * DISPLAY_WIDTH)

    for display_name, metric_id, unit_type in VITAL_SIGNS:
        current = extract_metric(api_data, ticker, metric_id)
        median = extract_dimension(api_data, ticker, metric_id, "Q.MED8")
        signal = format_vs_median(current, median)

        print(
            f"{display_name:18} "
            f"{format_value(current, unit_type):>10} "
            f"{format_value(median, unit_type):>10} "
            f"{signal:>16}"
        )

    # Valuation snapshot: current value + trend direction
    print()
    print("VALUATION  (current + 2-year trend)")
    print("-" * DISPLAY_WIDTH)
    print(f"{'':18} {'Current':>10} {'':>10} {'Trend':>16}")
    print("-" * DISPLAY_WIDTH)

    for display_name, metric_id, unit_type in VALUATION_SNAPSHOT:
        current = extract_metric(api_data, ticker, metric_id)
        trend = extract_dimension(api_data, ticker, metric_id, "Q.TREND8")

        print(
            f"{display_name:18} "
            f"{format_value(current, unit_type):>10} "
            f"{'':>10} "
            f"{format_trend(trend):>16}"
        )

    # Growth
    print()
    print("GROWTH")
    print("-" * DISPLAY_WIDTH)

    for display_name, metric_id, dimension in GROWTH_METRICS:
        val = extract_dimension(api_data, ticker, metric_id, dimension)
        print(f"{display_name:18} {'':>10} {'':>10} {format_pct_change(val):>16}")

    # Leverage
    print()
    print("LEVERAGE")
    print("-" * DISPLAY_WIDTH)

    for display_name, metric_id, unit_type in LEVERAGE_METRICS:
        current = extract_metric(api_data, ticker, metric_id)
        print(f"{display_name:18} {'':>10} {'':>10} {format_value(current, unit_type):>16}")

    # Diagnosis
    signal, diagnosis_text = _compute_diagnosis(api_data, ticker)

    print()
    print("=" * DISPLAY_WIDTH)
    print(f"DIAGNOSIS: {signal}")
    print("-" * DISPLAY_WIDTH)

    roic_current = extract_metric(api_data, ticker, "roic")
    roic_median = extract_dimension(api_data, ticker, "roic", "Q.MED8")
    roic_trend = extract_dimension(api_data, ticker, "roic", "Q.TREND8")
    pe_trend = extract_dimension(api_data, ticker, "pe_ratio", "Q.TREND8")

    # Quality assessment
    if roic_current is not None:
        trend_word = format_trend(roic_trend).lower()
        if roic_current > 0.20:
            quality = "strong"
        elif roic_current > 0.10:
            quality = "adequate"
        else:
            quality = "weak"

        if roic_median is not None and roic_median != 0:
            roic_pct = (roic_current - roic_median) / abs(roic_median) * 100
            if roic_pct > 5:
                position = "above its 2-year median"
            elif roic_pct < -5:
                position = "below its 2-year median"
            else:
                position = "near its 2-year median"
            print(f"Quality is {quality} — ROIC {roic_current*100:.1f}%,")
            print(f"{position}, trend {trend_word}.")
        else:
            print(f"Quality is {quality} — ROIC {roic_current*100:.1f}%,")
            print(f"trend {trend_word}.")
    else:
        print("ROIC not available (financial or recently listed).")

    # Valuation trend
    print()
    if pe_trend is not None:
        pe_word = format_trend(pe_trend).lower()
        pe_current = extract_metric(api_data, ticker, "pe_ratio")
        if pe_current is not None:
            if pe_word == "rising":
                print(f"Valuation trend: PE {pe_current:.1f} and rising —")
                print("market is paying more per dollar of earnings.")
            elif pe_word == "falling":
                print(f"Valuation trend: PE {pe_current:.1f} and falling —")
                print("valuation is compressing.")
            else:
                print(f"Valuation trend: PE {pe_current:.1f}, stable.")
    else:
        print("PE trend data not available.")

    # Synthesis
    print()
    print(diagnosis_text)

    # Summary line
    r_word = format_trend(roic_trend).lower() if roic_trend is not None else "n/a"
    p_word = format_trend(pe_trend).lower() if pe_trend is not None else "n/a"
    print()
    print(f"Signal: {signal} | ROIC trend: {r_word} | PE trend: {p_word}")

    print()
    print("-" * DISPLAY_WIDTH)
    print("All dimensions computed from SEC filings.")
    print("Not available in yfinance or other free tools.")
    print()
    print("  70 metrics: https://www.metricduck.com/metrics")
    print("=" * DISPLAY_WIDTH)
    print()


# =============================================================================
# MAIN
# =============================================================================


def display_dry_run(ticker: str):
    """Show estimated credit cost without making API calls."""
    periods_factor = 1 + len(ALL_DIMENSIONS)  # 1 year + 4 dimensions
    credits = 1 * len(ALL_METRIC_IDS) * periods_factor
    api_key = os.getenv("METRICDUCK_API_KEY")

    print()
    print("Dry run — no API calls made.")
    print()
    print(f"Request: {ticker}")
    print(f"  1 ticker x {len(ALL_METRIC_IDS)} metrics x {periods_factor} "
          f"periods (1 year + {len(ALL_DIMENSIONS)} dimensions)")
    print(f"  Estimated cost: ~{credits} credits")
    print()
    if not api_key:
        print("  Guest (no key):     No credit cost (5 requests/day limit)")
    print(f"  Free (registered):  {credits} of 500 daily credits")
    print(f"  Formula:            tickers x metrics x (years + dimensions)")
    print()


def main():
    """Main entry point."""
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    json_output = "--json" in sys.argv
    dry_run = "--dry-run" in sys.argv

    if len(args) == 1:
        ticker = args[0].upper()
    elif len(args) == 0:
        ticker = DEFAULT_TICKER
    else:
        print("Usage: python pulse.py [TICKER] [--json] [--dry-run]", file=sys.stderr)
        print("Example: python pulse.py NVDA", file=sys.stderr)
        sys.exit(1)

    if dry_run:
        display_dry_run(ticker)
        sys.exit(0)

    if not json_output:
        print(f"Fetching data for {ticker}...")

    api_data = fetch_stock_data(ticker)

    if not api_data or not api_data.get("data"):
        if json_output:
            print('{"error": "No data returned from API"}', file=sys.stderr)
        else:
            print("Error: No data returned from API.")
        sys.exit(1)

    if ticker not in api_data.get("data", {}):
        if json_output:
            print(f'{{"error": "No data for {ticker}"}}', file=sys.stderr)
        else:
            print(f"Error: No data for {ticker}. Check the ticker symbol.")
        sys.exit(1)

    if json_output:
        print(json.dumps(build_pulse_data(api_data, ticker), indent=2))
        return

    display_pulse(api_data, ticker)


if __name__ == "__main__":
    main()
