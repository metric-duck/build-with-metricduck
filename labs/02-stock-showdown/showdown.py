#!/usr/bin/env python3
"""
Lab 02: Stock Showdown - Compare Two Stocks Head-to-Head

Two-panel comparison: Valuation + Business Quality.
Uses MetricDuck API exclusive metrics (ROIC, FCF Yield, EV/EBIT,
Total Shareholder Yield) that are not available in yfinance.

Usage:
    python showdown.py              # Uses default AAPL vs MSFT
    python showdown.py NVDA AMD     # Compare any two stocks
    python showdown.py NVDA AMD --json  # Output as JSON (pipe to other tools)
"""

import json
import os
import sys

import httpx

# Optional: yfinance for supplementary market context (sector, beta, 52-week range)
try:
    import yfinance as yf

    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False

# =============================================================================
# CONFIGURATION - Edit these to customize
# =============================================================================

STOCK_A = "AAPL"
STOCK_B = "MSFT"

API_BASE_URL = "https://api.metricduck.com/api/v1"

# Metric tuples: (display_name, metric_id, "lower"/"higher", is_metricduck_exclusive)
# Full metric list (70 metrics, all free): https://www.metricduck.com/metrics

VALUATION_METRICS = [
    ("PE Ratio", "pe_ratio", "lower", False),
    ("EV/EBITDA", "ev_ebitda", "lower", False),
    ("EV/EBIT", "ev_ebit", "lower", True),
    ("FCF Yield", "fcf_yield", "higher", True),
]

QUALITY_METRICS = [
    ("ROIC", "roic", "higher", True),
    ("FCF Margin", "fcf_margin", "higher", True),
    ("Shareholder Yield", "total_shareholder_yield", "higher", True),
]

# Metrics displayed as percentages (API returns as ratio, e.g. 0.04 = 4%)
PCT_METRICS = {"fcf_yield", "fcf_margin", "total_shareholder_yield", "roic"}

# All metric IDs for the API call (deduplicated)
ALL_METRIC_IDS = list(dict.fromkeys(
    [m[1] for m in VALUATION_METRICS] + [m[1] for m in QUALITY_METRICS]
))

DISPLAY_WIDTH = 70
EXCLUSIVE_MARKER = " *"


# =============================================================================
# DATA FETCHING
# =============================================================================


def fetch_stock_data(ticker_a: str, ticker_b: str) -> dict | None:
    """
    Fetch metrics for two stocks from MetricDuck API.

    Uses guest access (no API key) — all 70 metrics available free.
    Set METRICDUCK_API_KEY env var for higher rate limits.
    """
    api_key = os.getenv("METRICDUCK_API_KEY")
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        response = httpx.get(
            f"{API_BASE_URL}/data/metrics",
            params={
                "tickers": f"{ticker_a},{ticker_b}",
                "metrics": ",".join(ALL_METRIC_IDS),
                "period": "ttm",
                "price": "current",
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
    """Extract the base (non-dimension) metric value from API response."""
    company = api_data.get("data", {}).get(ticker, {})
    metric = company.get("metrics", {}).get(metric_id, {})
    values = metric.get("values", [])

    for v in values:
        if v.get("dimension") is None and v.get("value") is not None:
            return v["value"]
    return None


def get_company_name(api_data: dict, ticker: str) -> str:
    """Extract company name from API response."""
    return api_data.get("data", {}).get(ticker, {}).get("company_name", ticker)


def fetch_yfinance_context(ticker_a: str, ticker_b: str) -> dict | None:
    """Fetch supplementary market context from yfinance (optional)."""
    if not HAS_YFINANCE:
        return None

    result = {}
    for ticker in [ticker_a, ticker_b]:
        try:
            info = yf.Ticker(ticker).info
            result[ticker] = {
                "sector": info.get("sector", "N/A"),
                "beta": info.get("beta"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            }
        except Exception:
            result[ticker] = {"sector": "N/A", "beta": None,
                              "fifty_two_week_high": None, "fifty_two_week_low": None}
    return result


# =============================================================================
# COMPARISON LOGIC
# =============================================================================


def compare_metric(val_a: float | None, val_b: float | None, prefer: str) -> str:
    """
    Compare two values and determine winner.
    Returns: "A", "B", or "tie"
    """
    if val_a is None and val_b is None:
        return "tie"
    if val_a is None:
        return "B"
    if val_b is None:
        return "A"

    if prefer == "lower":
        return "A" if val_a < val_b else "B" if val_b < val_a else "tie"
    else:
        return "A" if val_a > val_b else "B" if val_b > val_a else "tie"


def format_value(value: float | None, metric_id: str) -> str:
    """Format metric value for display."""
    if value is None:
        return "N/A"
    if metric_id in PCT_METRICS:
        return f"{value * 100:.1f}%"
    if abs(value) >= 1000:
        return f"{value:,.0f}"
    return f"{value:.2f}"


# =============================================================================
# DISPLAY
# =============================================================================


def display_panel(
    title: str,
    subtitle: str,
    metrics: list[tuple],
    api_data: dict,
    ticker_a: str,
    ticker_b: str,
    winner_label: str,
) -> tuple[int, int]:
    """Render a comparison panel. Returns (a_wins, b_wins)."""
    a_wins, b_wins = 0, 0
    total = 0

    print()
    print(f"{title}  ({subtitle})")
    print("-" * DISPLAY_WIDTH)
    print(f"{'':22} {ticker_a:>14} {ticker_b:>14} {winner_label:>16}")
    print("-" * DISPLAY_WIDTH)

    for display_name, metric_id, prefer, exclusive in metrics:
        a_val = extract_metric(api_data, ticker_a, metric_id)
        b_val = extract_metric(api_data, ticker_b, metric_id)
        winner = compare_metric(a_val, b_val, prefer)

        marker = EXCLUSIVE_MARKER if exclusive else ""
        name_display = f"{display_name}{marker}"

        if winner == "A":
            a_wins += 1
            total += 1
            winner_display = f"<- {ticker_a}"
        elif winner == "B":
            b_wins += 1
            total += 1
            winner_display = f"{ticker_b} ->"
        else:
            if a_val is not None or b_val is not None:
                total += 1
            winner_display = "Tie"

        print(
            f"{name_display:22} "
            f"{format_value(a_val, metric_id):>14} "
            f"{format_value(b_val, metric_id):>14} "
            f"{winner_display:>14}"
        )

    # Panel summary
    panel_word = title.split(":")[-1].strip().split()[0] if ":" in title else title
    if a_wins > b_wins:
        print(f"{'':52}{panel_word}: {ticker_a} {a_wins}-{b_wins}")
    elif b_wins > a_wins:
        print(f"{'':52}{panel_word}: {ticker_b} {b_wins}-{a_wins}")
    else:
        print(f"{'':52}{panel_word}: Tied {a_wins}-{b_wins}")

    return a_wins, b_wins


def display_yfinance_context(yf_data: dict | None, ticker_a: str, ticker_b: str):
    """Display supplementary yfinance market context."""
    if not yf_data:
        return

    print()
    print("MARKET CONTEXT  (via yfinance)")
    print("-" * DISPLAY_WIDTH)
    print(f"{'':22} {ticker_a:>22} {ticker_b:>22}")

    a, b = yf_data.get(ticker_a, {}), yf_data.get(ticker_b, {})

    print(f"{'Sector':22} {a.get('sector', 'N/A'):>22} {b.get('sector', 'N/A'):>22}")

    beta_a = f"{a['beta']:.2f}" if a.get("beta") else "N/A"
    beta_b = f"{b['beta']:.2f}" if b.get("beta") else "N/A"
    print(f"{'Beta':22} {beta_a:>22} {beta_b:>22}")

    hi_a = f"${a['fifty_two_week_high']:,.2f}" if a.get("fifty_two_week_high") else "N/A"
    hi_b = f"${b['fifty_two_week_high']:,.2f}" if b.get("fifty_two_week_high") else "N/A"
    print(f"{'52-Week High':22} {hi_a:>22} {hi_b:>22}")

    lo_a = f"${a['fifty_two_week_low']:,.2f}" if a.get("fifty_two_week_low") else "N/A"
    lo_b = f"${b['fifty_two_week_low']:,.2f}" if b.get("fifty_two_week_low") else "N/A"
    print(f"{'52-Week Low':22} {lo_a:>22} {lo_b:>22}")


def display_verdict(
    api_data: dict,
    ticker_a: str,
    ticker_b: str,
    val_a_wins: int,
    val_b_wins: int,
    val_total: int,
    qual_a_wins: int,
    qual_b_wins: int,
    qual_total: int,
):
    """Display multi-dimensional verdict."""
    print()
    print("=" * DISPLAY_WIDTH)
    print("VERDICT")
    print("-" * DISPLAY_WIDTH)

    # Valuation line
    if val_a_wins > val_b_wins:
        strength = "clearly" if val_a_wins >= val_total - 1 else "marginally"
        print(f"Valuation: {ticker_a} is {strength} cheaper ({val_a_wins} of {val_total} metrics)")
    elif val_b_wins > val_a_wins:
        strength = "clearly" if val_b_wins >= val_total - 1 else "marginally"
        print(f"Valuation: {ticker_b} is {strength} cheaper ({val_b_wins} of {val_total} metrics)")
    else:
        print(f"Valuation: Tied ({val_a_wins}-{val_b_wins})")

    # Quality line with ROIC highlight
    roic_a = extract_metric(api_data, ticker_a, "roic")
    roic_b = extract_metric(api_data, ticker_b, "roic")
    roic_note = ""
    if roic_a is not None and roic_b is not None:
        roic_note = f" -- ROIC {format_value(roic_a, 'roic')} vs {format_value(roic_b, 'roic')}"
    elif roic_a is not None:
        roic_note = f" -- ROIC {format_value(roic_a, 'roic')} vs N/A"
    elif roic_b is not None:
        roic_note = f" -- ROIC N/A vs {format_value(roic_b, 'roic')}"

    if qual_a_wins > qual_b_wins:
        print(f"Quality:   {ticker_a} is stronger ({qual_a_wins} of {qual_total} metrics){roic_note}")
    elif qual_b_wins > qual_a_wins:
        print(f"Quality:   {ticker_b} is stronger ({qual_b_wins} of {qual_total} metrics){roic_note}")
    else:
        print(f"Quality:   Tied ({qual_a_wins}-{qual_b_wins}){roic_note}")

    # Overall synthesis
    print()
    val_winner = ticker_a if val_a_wins > val_b_wins else ticker_b if val_b_wins > val_a_wins else None
    qual_winner = ticker_a if qual_a_wins > qual_b_wins else ticker_b if qual_b_wins > qual_a_wins else None

    if val_winner and qual_winner and val_winner == qual_winner:
        print(f"{val_winner} wins on BOTH valuation and quality.")
    elif val_winner and qual_winner:
        print(f"{qual_winner} has higher quality, {val_winner} is cheaper.")
        print(f"Classic value-vs-quality tradeoff.")
    elif val_winner:
        print(f"{val_winner} is cheaper; quality is evenly matched.")
    elif qual_winner:
        print(f"{qual_winner} is the better business; valuations are similar.")
    else:
        print("Both stocks are evenly matched on valuation and quality.")

    # Pointer to Lab 03
    print()
    print("But is the cheaper stock cheap by its OWN standards?")
    print("Try Lab 03 (Stock Pulse) to check any stock vs its 2-year history.")

    print()
    print("-" * DISPLAY_WIDTH)
    print("* = MetricDuck exclusive (not available in yfinance)")
    print()
    print("  Data: SEC filings via MetricDuck API (free, no key needed)")
    print("  70 metrics available: https://www.metricduck.com/metrics")
    print("=" * DISPLAY_WIDTH)
    print()


# =============================================================================
# MAIN
# =============================================================================


def build_comparison_data(
    api_data: dict, ticker_a: str, ticker_b: str
) -> dict:
    """Build structured comparison result for JSON output."""
    result = {
        "tickers": [ticker_a, ticker_b],
        "companies": {
            ticker_a: get_company_name(api_data, ticker_a),
            ticker_b: get_company_name(api_data, ticker_b),
        },
        "panels": {},
    }

    for panel_name, metrics in [("valuation", VALUATION_METRICS), ("quality", QUALITY_METRICS)]:
        panel = {"metrics": [], "score": {ticker_a: 0, ticker_b: 0}}
        for display_name, metric_id, prefer, exclusive in metrics:
            a_val = extract_metric(api_data, ticker_a, metric_id)
            b_val = extract_metric(api_data, ticker_b, metric_id)
            winner = compare_metric(a_val, b_val, prefer)
            if winner == "A":
                panel["score"][ticker_a] += 1
            elif winner == "B":
                panel["score"][ticker_b] += 1
            panel["metrics"].append({
                "name": display_name,
                "id": metric_id,
                "prefer": prefer,
                "exclusive": exclusive,
                ticker_a: a_val,
                ticker_b: b_val,
                "winner": ticker_a if winner == "A" else ticker_b if winner == "B" else "tie",
            })
        result["panels"][panel_name] = panel

    val = result["panels"]["valuation"]["score"]
    qual = result["panels"]["quality"]["score"]
    result["verdict"] = {
        "valuation_winner": ticker_a if val[ticker_a] > val[ticker_b] else ticker_b if val[ticker_b] > val[ticker_a] else "tie",
        "quality_winner": ticker_a if qual[ticker_a] > qual[ticker_b] else ticker_b if qual[ticker_b] > qual[ticker_a] else "tie",
    }

    return result


def main():
    """Main entry point."""
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    json_output = "--json" in sys.argv

    if len(args) == 2:
        stock_a, stock_b = args[0].upper(), args[1].upper()
    elif len(args) == 0:
        stock_a, stock_b = STOCK_A, STOCK_B
    else:
        print("Usage: python showdown.py [TICKER1 TICKER2] [--json]")
        print("Example: python showdown.py NVDA AMD")
        print("         python showdown.py NVDA AMD --json")
        sys.exit(1)

    if stock_a == stock_b:
        print(f"Error: Cannot compare {stock_a} to itself!", file=sys.stderr)
        sys.exit(1)

    if not json_output:
        print(f"Fetching data for {stock_a} and {stock_b}...")

    api_data = fetch_stock_data(stock_a, stock_b)

    if not api_data or not api_data.get("data"):
        print("Error: No data returned from API.", file=sys.stderr)
        sys.exit(1)

    for t in [stock_a, stock_b]:
        if t not in api_data.get("data", {}):
            print(f"Error: No data for {t}. Check the ticker symbol.", file=sys.stderr)
            sys.exit(1)

    # JSON output mode
    if json_output:
        print(json.dumps(build_comparison_data(api_data, stock_a, stock_b), indent=2))
        return

    # Optional yfinance context
    yf_data = None
    if HAS_YFINANCE:
        yf_data = fetch_yfinance_context(stock_a, stock_b)

    # Header
    name_a = get_company_name(api_data, stock_a)
    name_b = get_company_name(api_data, stock_b)

    print()
    print("=" * DISPLAY_WIDTH)
    print(f"{'STOCK SHOWDOWN: ' + stock_a + ' vs ' + stock_b:^{DISPLAY_WIDTH}}")
    print("=" * DISPLAY_WIDTH)

    print()
    print("COMPANY INFO")
    print("-" * DISPLAY_WIDTH)
    print(f"{'':22} {stock_a:>22} {stock_b:>22}")
    print(f"{'Name':22} {name_a[:22]:>22} {name_b[:22]:>22}")

    # Panel 1: Valuation
    val_a, val_b = display_panel(
        "PANEL 1: VALUATION", "Who's cheaper today?",
        VALUATION_METRICS, api_data, stock_a, stock_b, "Better Value",
    )

    # Panel 2: Business Quality
    qual_a, qual_b = display_panel(
        "PANEL 2: QUALITY", "Who's the better business?",
        QUALITY_METRICS, api_data, stock_a, stock_b, "Better Quality",
    )

    # Optional: yfinance market context
    display_yfinance_context(yf_data, stock_a, stock_b)

    # Verdict
    display_verdict(
        api_data, stock_a, stock_b,
        val_a, val_b, len(VALUATION_METRICS),
        qual_a, qual_b, len(QUALITY_METRICS),
    )


if __name__ == "__main__":
    main()
