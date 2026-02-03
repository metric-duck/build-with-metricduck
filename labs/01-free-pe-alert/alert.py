#!/usr/bin/env python3
"""
Lab 1: Free PE Ratio Alert (No Subscription Required)

Alert when a stock's PE ratio drops below your threshold.
Uses yfinance (free) for data - no API key needed!

Usage:
    1. Install dependencies: pip install -r requirements.txt
    2. Customize WATCHLIST and PE_THRESHOLD below
    3. Run: python alert.py

Optional email notifications:
    1. Copy .env.example to .env
    2. Add your Gmail credentials (use App Password, not regular password)
    3. Run: python alert.py
"""

import os
import smtplib
from email.mime.text import MIMEText

import yfinance as yf
from dotenv import load_dotenv

# Load environment variables (for optional email)
load_dotenv()

# =============================================================================
# CONFIGURATION - Customize these values
# =============================================================================

# Your watchlist of stocks to monitor
WATCHLIST = ["AAPL", "MSFT", "GOOGL", "AMZN", "META"]

# Alert when PE ratio drops below this value
PE_THRESHOLD = 20

# =============================================================================
# Email Configuration (Optional)
# =============================================================================

EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_TO = os.getenv("EMAIL_TO", "")


def fetch_pe_ratios(tickers: list[str]) -> dict:
    """
    Fetch PE ratios for a list of tickers using yfinance (free).

    Args:
        tickers: List of stock ticker symbols

    Returns:
        Dict mapping ticker to PE ratio (or None if not available)
    """
    pe_ratios = {}

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # yfinance provides trailingPE (TTM PE ratio)
            pe = info.get("trailingPE")
            pe_ratios[ticker] = pe
        except Exception as e:
            print(f"Warning: Could not fetch data for {ticker}: {e}")
            pe_ratios[ticker] = None

    return pe_ratios


def send_email_alert(alerts: list[dict]) -> bool:
    """
    Send email notification for triggered alerts.

    Args:
        alerts: List of alert dicts with ticker and pe_ratio

    Returns:
        True if email sent successfully, False otherwise
    """
    if not EMAIL_ENABLED or not alerts:
        return False

    if not all([EMAIL_USER, EMAIL_PASSWORD, EMAIL_TO]):
        print("Warning: Email enabled but credentials not configured")
        return False

    # Build email content
    subject = f"PE Alert: {len(alerts)} stock(s) below threshold"
    body_lines = [
        f"The following stocks have PE ratios below {PE_THRESHOLD}:",
        "",
    ]
    for alert in alerts:
        body_lines.append(f"  - {alert['ticker']}: PE = {alert['pe_ratio']:.1f}")

    body_lines.extend([
        "",
        "---",
        "Sent by MetricDuck Labs - Free PE Alert",
        "https://github.com/metric-duck/labs",
    ])

    body = "\n".join(body_lines)

    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_USER
        msg["To"] = EMAIL_TO

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)

        print(f"Email sent to {EMAIL_TO}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False


def main():
    """Main entry point."""
    print(f"Checking PE ratios for watchlist: {', '.join(WATCHLIST)}")
    print(f"Alert threshold: PE < {PE_THRESHOLD}")
    print("-" * 50)

    # Fetch PE ratios using yfinance (free!)
    pe_ratios = fetch_pe_ratios(WATCHLIST)

    # Check for alerts
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

        # Send email if configured
        if EMAIL_ENABLED:
            send_email_alert(alerts)
    else:
        print("\nNo alerts triggered. All PE ratios above threshold.")

    return alerts


if __name__ == "__main__":
    main()
