#!/usr/bin/env python3
"""
Lab 03: Stock Pulse - Check Any Stock Against Its Own History

Is AAPL's ROIC improving or declining? Is its FCF margin above or below normal?
Compare current metrics to 2-year medians and trend directions.

Uses MetricDuck API statistical dimensions (Q.MED8, Q.TREND8)
that are not available in yfinance or any free alternative.

Usage:
    python pulse.py              # Default: AAPL
    python pulse.py MSFT         # Any single stock
"""

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
                "period": "ttm",
                "price": "current",
                "dimensions": ",".join(ALL_DIMENSIONS),
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

            if isinstance(detail, dict) and detail.get("error") == "Insufficient credits":
                print(f"Monthly credit limit reached ({detail.get('monthly_limit', '?')} credits).")
                print("Upgrade at https://www.metricduck.com/pricing")
            else:
                print(f"Rate limit reached. Wait {retry_after} seconds and try again.")
                print("Register free for higher limits: https://www.metricduck.com/auth/register")
            sys.exit(1)

        if response.status_code != 200:
            print(f"Error: API returned {response.status_code}")
            print(response.text[:500])
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
    print()
    print("=" * DISPLAY_WIDTH)
    print("DIAGNOSIS")
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

        # Compare to median
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
                print("valuation is compressing (could be opportunity).")
            else:
                print(f"Valuation trend: PE {pe_current:.1f}, stable.")
    else:
        print("PE trend data not available.")

    # Synthesis
    print()
    if roic_current is not None and roic_trend is not None and pe_trend is not None:
        r_trend = format_trend(roic_trend)
        p_trend = format_trend(pe_trend)

        if r_trend == "Rising" and p_trend == "Falling":
            print("Improving quality + compressing valuation =")
            print("potential opportunity worth investigating.")
        elif r_trend == "Falling" and p_trend == "Rising":
            print("Declining quality + expanding valuation =")
            print("caution warranted.")
        elif r_trend == "Rising" and p_trend == "Rising":
            print("Quality improving but valuation expanding too.")
            print("Market recognizes the improvement — premium justified?")
        elif r_trend == "Falling" and p_trend == "Falling":
            print("Quality and valuation both declining.")
            print("Market may be right to de-rate — investigate cause.")
        else:
            print("No strong signal — fundamentals and valuation")
            print("are both near historical norms.")

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


def main():
    """Main entry point."""
    if len(sys.argv) == 2:
        ticker = sys.argv[1].upper()
    elif len(sys.argv) == 1:
        ticker = DEFAULT_TICKER
    else:
        print("Usage: python pulse.py [TICKER]")
        print("Example: python pulse.py NVDA")
        sys.exit(1)

    print(f"Fetching data for {ticker}...")

    api_data = fetch_stock_data(ticker)

    if not api_data or not api_data.get("data"):
        print("Error: No data returned from API.")
        sys.exit(1)

    if ticker not in api_data.get("data", {}):
        print(f"Error: No data for {ticker}. Check the ticker symbol.")
        sys.exit(1)

    display_pulse(api_data, ticker)


if __name__ == "__main__":
    main()
