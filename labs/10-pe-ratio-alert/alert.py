#!/usr/bin/env python3
"""
Lab 1: PE Ratio Alert

Alert when a stock's PE ratio drops below your threshold.
Perfect for value investors looking to buy stocks when they're cheap.

Usage:
    1. Set your METRICDUCK_API_KEY in .env
    2. Customize WATCHLIST and PE_THRESHOLD below
    3. Run: python alert.py
"""

import os
import sys

import httpx
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# CONFIGURATION - Customize these values
# =============================================================================

# Your watchlist of stocks to monitor
WATCHLIST = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]

# Alert when PE ratio drops below this value
PE_THRESHOLD = 20

# =============================================================================
# API Configuration
# =============================================================================

API_BASE_URL = "https://api.metricduck.com/api/v1"
API_KEY = os.getenv("METRICDUCK_API_KEY")


def fetch_pe_ratios(tickers: list[str]) -> dict:
    """
    Fetch PE ratios for a list of tickers from MetricDuck API.

    Args:
        tickers: List of stock ticker symbols

    Returns:
        Dict mapping ticker to PE ratio (or None if not available)
    """
    if not API_KEY:
        print("Error: METRICDUCK_API_KEY not set in environment")
        print("Copy .env.example to .env and add your API key")
        sys.exit(1)

    response = httpx.get(
        f"{API_BASE_URL}/data/metrics",
        params={
            "tickers": ",".join(tickers),
            "metrics": "pe_ratio",
            "period": "ttm",       # Trailing Twelve Months
            "price": "current",    # Recompute valuations at today's price
            "years": 1,            # 1 year of history
        },
        headers={"Authorization": f"Bearer {API_KEY}"},
        timeout=30.0,
    )

    if response.status_code == 401:
        print("Error: Invalid API key. Check your METRICDUCK_API_KEY.")
        sys.exit(1)

    if response.status_code == 429:
        retry_after = response.headers.get("Retry-After", "60")
        print(f"Rate limit reached. Wait {retry_after}s and try again.")
        sys.exit(1)

    if response.status_code != 200:
        print(f"Error: API returned {response.status_code}")
        try:
            detail = response.json().get("detail", {})
            if isinstance(detail, dict):
                print(detail.get("error", "Unknown error"))
            else:
                print(str(detail)[:200])
        except Exception:
            print("Could not parse error response.")
        sys.exit(1)

    data = response.json()

    # Extract PE ratios from response
    pe_ratios = {}
    for ticker, company_data in data.get("data", {}).items():
        metrics = company_data.get("metrics", {})
        pe_data = metrics.get("pe_ratio", {})
        values = pe_data.get("values", [])

        if values and values[0].get("value") is not None:
            pe_ratios[ticker] = values[0]["value"]
        else:
            pe_ratios[ticker] = None

    return pe_ratios


def check_alerts(pe_ratios: dict, threshold: float) -> list[dict]:
    """
    Check which stocks have PE below threshold.

    Args:
        pe_ratios: Dict mapping ticker to PE ratio
        threshold: PE threshold for alerts

    Returns:
        List of alert dicts with ticker and pe_ratio
    """
    alerts = []

    for ticker, pe in pe_ratios.items():
        if pe is not None and pe < threshold:
            alerts.append({"ticker": ticker, "pe_ratio": pe})

    return alerts


def main():
    """Main entry point."""
    print(f"Checking PE ratios for watchlist: {', '.join(WATCHLIST)}")
    print(f"Alert threshold: PE < {PE_THRESHOLD}")
    print("-" * 50)

    # Fetch PE ratios
    pe_ratios = fetch_pe_ratios(WATCHLIST)

    # Display all PE ratios
    alerts = []
    for ticker in WATCHLIST:
        pe = pe_ratios.get(ticker)
        if pe is None:
            print(f"{ticker}: No PE data available")
        elif pe < PE_THRESHOLD:
            print(f"{ticker}: PE = {pe:.1f} ** ALERT! Below threshold **")
            alerts.append({"ticker": ticker, "pe_ratio": pe})
        else:
            print(f"{ticker}: PE = {pe:.1f}")

    # Summary
    print("-" * 50)
    if alerts:
        print(f"\n{len(alerts)} ALERT(S) TRIGGERED:")
        for alert in alerts:
            print(f"  - {alert['ticker']}: PE = {alert['pe_ratio']:.1f}")
    else:
        print("\nNo alerts triggered. All PE ratios above threshold.")

    return alerts


if __name__ == "__main__":
    main()
