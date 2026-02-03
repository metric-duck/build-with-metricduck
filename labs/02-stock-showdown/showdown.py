#!/usr/bin/env python3
"""
Lab 02: Stock Showdown - Compare Two Stocks Head-to-Head

Which stock is the better VALUE? Compare metrics AND historical context.
Uses yfinance (free) - no API key needed!

Usage:
    python showdown.py              # Uses default AAPL vs MSFT
    python showdown.py NVDA AMD     # Compare any two stocks
"""

import sys

import yfinance as yf

# =============================================================================
# CONFIGURATION - Edit these to customize
# =============================================================================

STOCK_A = "AAPL"
STOCK_B = "MSFT"

# Add/remove metrics here. Format: (display_name, yfinance_field, "lower"/"higher")
# Find more fields: stock.info.keys() or https://github.com/ranaroussi/yfinance
VALUATION_METRICS = [
    ("PE Ratio", "trailingPE", "lower"),
    ("Forward PE", "forwardPE", "lower"),
    ("Div Yield", "dividendYield", "higher"),  # Higher yield = more income
    ("Price/Book", "priceToBook", "lower"),
    ("Price/Sales", "priceToSalesTrailing12Months", "lower"),
    ("EV/EBITDA", "enterpriseToEbitda", "lower"),
]

# Thresholds for 52-week range classification (adjust to taste)
EXPENSIVE_THRESHOLD = 0.85  # >85% of range = Expensive
CHEAP_THRESHOLD = 0.25  # <25% of range = Cheap


# =============================================================================
# DATA FETCHING
# =============================================================================


def fetch_stock_data(ticker: str) -> dict | None:
    """Fetch stock info from yfinance. Returns None if fetch fails."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        if not info or info.get("regularMarketPrice") is None:
            return None

        return {"info": info, "ticker": ticker}
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None


# =============================================================================
# COMPARISON LOGIC
# =============================================================================


def compare_metric(val_a: float | None, val_b: float | None, prefer: str) -> str:
    """
    Compare two values and determine winner.

    Args:
        val_a: Value for stock A
        val_b: Value for stock B
        prefer: "lower" or "higher" indicates which is better

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


def calculate_historical_context(info: dict) -> dict:
    """Calculate where current price sits in 52-week range (0=low, 1=high)."""
    fifty_two_week_high = info.get("fiftyTwoWeekHigh")
    fifty_two_week_low = info.get("fiftyTwoWeekLow")
    current_price = info.get("currentPrice") or info.get("regularMarketPrice")

    if not all([fifty_two_week_high, fifty_two_week_low, current_price]):
        return {"status": "Unknown", "detail": "Insufficient data", "score": 0.5}

    if fifty_two_week_high == fifty_two_week_low:
        return {"status": "Unknown", "detail": "No price range", "score": 0.5}

    range_position = (current_price - fifty_two_week_low) / (
        fifty_two_week_high - fifty_two_week_low
    )
    range_pct = int(range_position * 100)

    if range_position > EXPENSIVE_THRESHOLD:
        return {
            "status": "Expensive",
            "detail": f"Near 52-wk high ({range_pct}%)",
            "score": range_position,
        }
    elif range_position < CHEAP_THRESHOLD:
        return {
            "status": "Cheap",
            "detail": f"Near 52-wk low ({range_pct}%)",
            "score": range_position,
        }
    elif range_position < 0.45:
        return {
            "status": "Fair Value",
            "detail": f"Lower half ({range_pct}%)",
            "score": range_position,
        }
    elif range_position > 0.65:
        return {
            "status": "Pricey",
            "detail": f"Upper half ({range_pct}%)",
            "score": range_position,
        }
    else:
        return {
            "status": "Fair Value",
            "detail": f"Mid-range ({range_pct}%)",
            "score": range_position,
        }


def format_market_cap(value: float | None) -> str:
    """Format market cap in human-readable form (e.g., $3.4T)."""
    if value is None:
        return "N/A"
    if value >= 1e12:
        return f"${value / 1e12:.1f}T"
    if value >= 1e9:
        return f"${value / 1e9:.1f}B"
    if value >= 1e6:
        return f"${value / 1e6:.1f}M"
    return f"${value:,.0f}"


def format_metric_value(value: float | None, is_percentage: bool = False) -> str:
    """Format metric value for display."""
    if value is None:
        return "N/A"
    if is_percentage:
        # yfinance returns dividend yield as percentage already (0.39 = 0.39%)
        return f"{value:.2f}%"
    if abs(value) >= 1000:
        return f"{value:,.0f}"
    return f"{value:.2f}"


def generate_progress_bar(score: float, width: int = 10) -> str:
    """Generate a visual progress bar for 52-week range position."""
    filled = int(score * width)
    empty = width - filled
    return f"[{'▓' * filled}{'░' * empty}]"


# =============================================================================
# DISPLAY
# =============================================================================


def display_showdown(a_data: dict, b_data: dict):
    """Display the full comparison with metrics, historical context, and verdict."""
    a_info = a_data["info"]
    b_info = b_data["info"]
    a_ticker = a_data["ticker"]
    b_ticker = b_data["ticker"]

    a_context = calculate_historical_context(a_info)
    b_context = calculate_historical_context(b_info)

    a_wins = 0
    b_wins = 0
    total_compared = 0

    print()
    print("═" * 66)
    print(f"{'STOCK SHOWDOWN: ' + a_ticker + ' vs ' + b_ticker:^66}")
    print("═" * 66)

    print()
    print("COMPANY INFO")
    print("─" * 66)
    print(f"{'':20} {a_ticker:>20} {b_ticker:>20}")
    print(
        f"{'Name':20} {a_info.get('shortName', 'N/A')[:20]:>20} {b_info.get('shortName', 'N/A')[:20]:>20}"
    )
    print(
        f"{'Sector':20} {a_info.get('sector', 'N/A')[:20]:>20} {b_info.get('sector', 'N/A')[:20]:>20}"
    )
    print(
        f"{'Market Cap':20} {format_market_cap(a_info.get('marketCap')):>20} {format_market_cap(b_info.get('marketCap')):>20}"
    )

    print()
    print("VALUATION METRICS")
    print("─" * 66)
    print(f"{'':20} {a_ticker:>15} {b_ticker:>15} {'Better Value':>12}")
    print("─" * 66)

    for display_name, field_name, prefer in VALUATION_METRICS:
        a_val = a_info.get(field_name)
        b_val = b_info.get(field_name)
        winner = compare_metric(a_val, b_val, prefer)

        if winner == "A":
            a_wins += 1
            total_compared += 1
            winner_display = f"{a_ticker} ✓"
        elif winner == "B":
            b_wins += 1
            total_compared += 1
            winner_display = f"{b_ticker} ✓"
        else:
            if a_val is not None or b_val is not None:
                total_compared += 1
            winner_display = "Tie"

        is_pct = field_name == "dividendYield"
        print(
            f"{display_name:20} {format_metric_value(a_val, is_pct):>15} {format_metric_value(b_val, is_pct):>15} {winner_display:>12}"
        )

    print()
    print("HISTORICAL CONTEXT (52-Week Range Position)")
    print("─" * 66)
    print(f"{'':20} {a_ticker:>20} {b_ticker:>20}")
    print(
        f"{'Current Price':20} ${a_info.get('currentPrice') or a_info.get('regularMarketPrice', 0):>19,.2f} ${b_info.get('currentPrice') or b_info.get('regularMarketPrice', 0):>19,.2f}"
    )
    print(
        f"{'52-Week Low':20} ${a_info.get('fiftyTwoWeekLow', 0):>19,.2f} ${b_info.get('fiftyTwoWeekLow', 0):>19,.2f}"
    )
    print(
        f"{'52-Week High':20} ${a_info.get('fiftyTwoWeekHigh', 0):>19,.2f} ${b_info.get('fiftyTwoWeekHigh', 0):>19,.2f}"
    )
    print(
        f"{'Position':20} {a_context['detail']:>20} {b_context['detail']:>20}"
    )

    print()
    print("VALUATION VERDICT")
    print("─" * 66)
    print(
        f"{a_ticker:8} {generate_progress_bar(a_context['score'])}  {a_context['status']}"
    )
    print(
        f"{b_ticker:8} {generate_progress_bar(b_context['score'])}  {b_context['status']}"
    )

    print()
    print("═" * 66)
    print("FINAL VERDICT")
    print("─" * 66)

    metrics_winner = (
        a_ticker if a_wins > b_wins else b_ticker if b_wins > a_wins else "Tie"
    )

    print(
        f"Raw Metrics Winner: {metrics_winner} ({max(a_wins, b_wins)} of {total_compared} metrics)"
    )
    print()

    # Verdict logic: historical context can override raw metrics winner
    if a_context["status"] in ["Expensive", "Pricey"] and b_context["status"] in [
        "Cheap",
        "Fair Value",
    ]:
        if a_wins > b_wins:
            print("But consider this:")
            print(
                f"  • {a_ticker} is trading {a_context['detail']} - potentially stretched"
            )
            print(f"  • {b_ticker} is trading {b_context['detail']} - better entry point")
            print()
            print(f"RECOMMENDATION: {b_ticker} may offer better value right now.")
            print("You'd be buying at a lower point in its historical range.")
        else:
            print("Historical context confirms this:")
            print(f"  • {b_ticker} is trading {b_context['detail']} - good entry point")
            print(
                f"  • {a_ticker} is trading {a_context['detail']} - potentially stretched"
            )
            print()
            print(f"RECOMMENDATION: {b_ticker} looks like the better value opportunity.")

    elif b_context["status"] in ["Expensive", "Pricey"] and a_context["status"] in [
        "Cheap",
        "Fair Value",
    ]:
        if b_wins > a_wins:
            print("But consider this:")
            print(
                f"  • {b_ticker} is trading {b_context['detail']} - potentially stretched"
            )
            print(f"  • {a_ticker} is trading {a_context['detail']} - better entry point")
            print()
            print(f"RECOMMENDATION: {a_ticker} may offer better value right now.")
            print("You'd be buying at a lower point in its historical range.")
        else:
            print("Historical context confirms this:")
            print(f"  • {a_ticker} is trading {a_context['detail']} - good entry point")
            print(
                f"  • {b_ticker} is trading {b_context['detail']} - potentially stretched"
            )
            print()
            print(f"RECOMMENDATION: {a_ticker} looks like the better value opportunity.")

    else:
        print("Historical context:")
        print(f"  • {a_ticker}: {a_context['detail']}")
        print(f"  • {b_ticker}: {b_context['detail']}")
        print()
        if metrics_winner != "Tie":
            print(f"RECOMMENDATION: {metrics_winner} appears to be the better value")
            print("based on current metrics. Both show similar historical positioning.")
        else:
            print("RECOMMENDATION: Both stocks show similar value characteristics.")
            print("Consider other factors like growth prospects and business quality.")

    print()
    print("═" * 66)
    print("Want 200+ metrics and 7 years of history? Try MetricDuck API")
    print("https://www.metricduck.com")
    print("═" * 66)
    print()


# =============================================================================
# MAIN
# =============================================================================


def main():
    """Main entry point."""
    if len(sys.argv) == 3:
        stock_a, stock_b = sys.argv[1].upper(), sys.argv[2].upper()
    elif len(sys.argv) == 1:
        stock_a, stock_b = STOCK_A, STOCK_B
    else:
        print("Usage: python showdown.py [TICKER1 TICKER2]")
        print("Example: python showdown.py NVDA AMD")
        sys.exit(1)

    if stock_a == stock_b:
        print(f"Error: Cannot compare {stock_a} to itself!")
        sys.exit(1)

    print(f"Fetching data for {stock_a} and {stock_b}...")

    a_data = fetch_stock_data(stock_a)
    b_data = fetch_stock_data(stock_b)

    if a_data is None:
        print(f"Error: Could not fetch data for {stock_a}. Check the ticker symbol.")
        sys.exit(1)
    if b_data is None:
        print(f"Error: Could not fetch data for {stock_b}. Check the ticker symbol.")
        sys.exit(1)

    display_showdown(a_data, b_data)


if __name__ == "__main__":
    main()
