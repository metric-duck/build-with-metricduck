#!/usr/bin/env python3
"""
Data API Quality Validation — MetricDuck vs yfinance

Fetches the same 5 valuation metrics from both MetricDuck API and yfinance,
compares them side-by-side, and produces a JSON results file + markdown report.

Usage:
    pip install -r requirements.txt
    python validate.py
    python validate.py AAPL MSFT NVDA   # custom tickers
"""

import json
import os
import sys
from datetime import datetime, timezone

import httpx
import yfinance as yf

# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_TICKERS = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "META",
    "AMZN", "JPM", "TSLA", "V", "JNJ",
]

API_BASE_URL = "https://api.metricduck.com/api/v1"

# MetricDuck metric_id → yfinance field name + display info
METRIC_MAP = {
    "pe_ratio": {
        "name": "PE Ratio",
        "yf_field": "trailingPE",
        "format": "ratio",
    },
    "ps_ratio": {
        "name": "Price/Sales",
        "yf_field": "priceToSalesTrailing12Months",
        "format": "ratio",
    },
    "ev_ebitda": {
        "name": "EV/EBITDA",
        "yf_field": "enterpriseToEbitda",
        "format": "ratio",
    },
    "ev_ebit": {
        "name": "EV/EBIT",
        "yf_field": None,  # Computed from enterpriseValue / ebit
        "format": "ratio",
    },
    "dividend_yield": {
        "name": "Div Yield",
        "yf_field": "dividendYield",
        "format": "pct",
    },
}

METRIC_IDS = list(METRIC_MAP.keys())

# Comparison thresholds
THRESHOLD_OK = 5          # <5% difference
THRESHOLD_INVESTIGATE = 15  # 5-15% difference
# >15% = CRITICAL


# =============================================================================
# DATA FETCHING
# =============================================================================


def fetch_metricduck(tickers: list[str], batch_size: int = 4) -> dict:
    """
    Fetch metrics from MetricDuck API (guest access).

    Batches requests to stay within free-tier limits.

    Returns:
        {ticker: {metric_id: {"value": float|None, "period_end": str|None}}}
    """
    api_key = os.getenv("METRICDUCK_API_KEY")
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        batch_size = len(tickers)  # Authenticated users have higher limits

    result = {}

    # Batch tickers to respect free-tier limits
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i : i + batch_size]
        print(f"  Batch {i // batch_size + 1}: {', '.join(batch)}")

        try:
            response = httpx.get(
                f"{API_BASE_URL}/data/metrics",
                params={
                    "tickers": ",".join(batch),
                    "metrics": ",".join(METRIC_IDS),
                    "period": "ttm",
                    "price": "current",
                },
                headers=headers,
                timeout=30.0,
            )
        except httpx.ConnectError:
            print("ERROR: Could not connect to MetricDuck API.")
            return result
        except httpx.TimeoutException:
            print("ERROR: MetricDuck API request timed out.")
            return result

        if response.status_code == 429:
            print("ERROR: Rate limit reached. Try again in a minute.")
            return result

        if response.status_code != 200:
            print(f"ERROR: MetricDuck API returned {response.status_code}")
            print(response.text[:500])
            return result

        data = response.json().get("data", {})

        for ticker in batch:
            company = data.get(ticker, {})
            metrics = company.get("metrics", {})
            result[ticker] = {}

            for metric_id in METRIC_IDS:
                metric = metrics.get(metric_id, {})
                values = metric.get("values", [])
                if values and values[0].get("value") is not None:
                    result[ticker][metric_id] = {
                        "value": values[0]["value"],
                        "period_end": values[0].get("period_end"),
                    }
                else:
                    result[ticker][metric_id] = {"value": None, "period_end": None}

    return result


def fetch_yfinance(tickers: list[str]) -> dict:
    """
    Fetch equivalent metrics from yfinance.

    Returns:
        {ticker: {metric_id: float|None}}
    """
    result = {}

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
        except Exception as e:
            print(f"  yfinance error for {ticker}: {e}")
            result[ticker] = {m: None for m in METRIC_IDS}
            continue

        ticker_data = {}

        for metric_id, config in METRIC_MAP.items():
            if metric_id == "ev_ebit":
                # yfinance doesn't provide EV/EBIT directly.
                # Compute from enterpriseValue and operatingIncome (EBIT proxy).
                ev = info.get("enterpriseValue")
                ebit = info.get("ebit") or info.get("operatingIncome")
                if ev is not None and ebit is not None and ebit != 0:
                    ticker_data[metric_id] = ev / ebit
                else:
                    ticker_data[metric_id] = None
            elif metric_id == "dividend_yield":
                # yfinance returns dividendYield as a direct percentage
                # (e.g., 0.37 = 0.37%), while MetricDuck returns as a ratio
                # (0.004 = 0.4%). Normalize yfinance to ratio form.
                raw = info.get(config["yf_field"])
                if raw is not None:
                    ticker_data[metric_id] = raw / 100
                else:
                    ticker_data[metric_id] = None
            else:
                ticker_data[metric_id] = info.get(config["yf_field"])

        result[ticker] = ticker_data

    return result


# =============================================================================
# COMPARISON
# =============================================================================


def pct_diff(a: float | None, b: float | None) -> float | None:
    """Percentage difference: |a - b| / |b| * 100. Returns None if either is None."""
    if a is None or b is None:
        return None
    if b == 0:
        return None
    return abs(a - b) / abs(b) * 100


def verdict(diff: float | None) -> str:
    """Classify a percentage difference."""
    if diff is None:
        return "N/A"
    if diff < THRESHOLD_OK:
        return "OK"
    if diff < THRESHOLD_INVESTIGATE:
        return "INVESTIGATE"
    return "CRITICAL"


def compare(md_data: dict, yf_data: dict, tickers: list[str]) -> list[dict]:
    """
    Compare MetricDuck vs yfinance data.

    Returns list of per-ticker-metric comparison dicts.
    """
    results = []

    for ticker in tickers:
        md_ticker = md_data.get(ticker, {})
        yf_ticker = yf_data.get(ticker, {})

        for metric_id in METRIC_IDS:
            md_entry = md_ticker.get(metric_id, {})
            md_val = md_entry.get("value") if isinstance(md_entry, dict) else None
            period_end = md_entry.get("period_end") if isinstance(md_entry, dict) else None
            yf_val = yf_ticker.get(metric_id)

            diff = pct_diff(md_val, yf_val)

            results.append({
                "ticker": ticker,
                "metric_id": metric_id,
                "metric_name": METRIC_MAP[metric_id]["name"],
                "metricduck": md_val,
                "yfinance": yf_val,
                "pct_diff": round(diff, 1) if diff is not None else None,
                "verdict": verdict(diff),
                "period_end": period_end,
            })

    return results


# =============================================================================
# OUTPUT
# =============================================================================


def fmt_val(value: float | None, metric_id: str) -> str:
    """Format a metric value for display."""
    if value is None:
        return "N/A"
    if METRIC_MAP[metric_id]["format"] == "pct":
        return f"{value * 100:.2f}%"
    if abs(value) >= 1000:
        return f"{value:,.0f}"
    return f"{value:.2f}"


def write_json(results: list[dict], tickers: list[str], output_dir: str):
    """Write timestamped JSON results file."""
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")

    payload = {
        "generated_at": now.isoformat(),
        "tickers": tickers,
        "metrics": METRIC_IDS,
        "api_base_url": API_BASE_URL,
        "results": results,
    }

    path = os.path.join(output_dir, f"results_{date_str}.json")
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"\nJSON results: {path}")


def write_report(results: list[dict], tickers: list[str], output_dir: str):
    """Write markdown report."""
    now = datetime.now(timezone.utc)
    lines = [
        "# Data API Quality Report",
        "",
        f"**Generated:** {now.strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Tickers:** {', '.join(tickers)}",
        f"**Metrics:** {', '.join(METRIC_IDS)}",
        f"**Source:** MetricDuck API (guest access) vs yfinance",
        "",
        "---",
        "",
    ]

    # Summary stats
    comparable = [r for r in results if r["pct_diff"] is not None]
    ok_count = sum(1 for r in comparable if r["verdict"] == "OK")
    inv_count = sum(1 for r in comparable if r["verdict"] == "INVESTIGATE")
    crit_count = sum(1 for r in comparable if r["verdict"] == "CRITICAL")
    na_count = sum(1 for r in results if r["verdict"] == "N/A")

    lines.extend([
        "## Summary",
        "",
        f"| Verdict | Count |",
        f"|---------|-------|",
        f"| OK (<{THRESHOLD_OK}%) | {ok_count} |",
        f"| INVESTIGATE ({THRESHOLD_OK}-{THRESHOLD_INVESTIGATE}%) | {inv_count} |",
        f"| CRITICAL (>{THRESHOLD_INVESTIGATE}%) | {crit_count} |",
        f"| N/A (missing data) | {na_count} |",
        f"| **Total comparisons** | **{len(results)}** |",
        "",
    ])

    if comparable:
        avg_diff = sum(r["pct_diff"] for r in comparable) / len(comparable)
        max_diff = max(comparable, key=lambda r: r["pct_diff"])
        lines.extend([
            f"**Average difference:** {avg_diff:.1f}%",
            f"**Worst discrepancy:** {max_diff['ticker']} {max_diff['metric_name']} — {max_diff['pct_diff']:.1f}%",
            "",
        ])

    # Per-ticker table
    lines.extend([
        "---",
        "",
        "## Detailed Results",
        "",
        "| Ticker | Metric | MetricDuck | yfinance | Diff | Verdict | Period End |",
        "|--------|--------|-----------|----------|------|---------|------------|",
    ])

    for r in results:
        md_str = fmt_val(r["metricduck"], r["metric_id"])
        yf_str = fmt_val(r["yfinance"], r["metric_id"])
        diff_str = f"{r['pct_diff']:.1f}%" if r["pct_diff"] is not None else "—"
        pe_str = r["period_end"] or "—"
        lines.append(
            f"| {r['ticker']} | {r['metric_name']} | {md_str} | {yf_str} | {diff_str} | {r['verdict']} | {pe_str} |"
        )

    # Critical issues section
    criticals = [r for r in results if r["verdict"] == "CRITICAL"]
    if criticals:
        lines.extend([
            "",
            "---",
            "",
            "## Critical Issues",
            "",
        ])
        for r in criticals:
            lines.append(
                f"- **{r['ticker']} {r['metric_name']}**: MetricDuck={fmt_val(r['metricduck'], r['metric_id'])}, "
                f"yfinance={fmt_val(r['yfinance'], r['metric_id'])}, diff={r['pct_diff']:.1f}% "
                f"(period_end: {r['period_end'] or 'N/A'})"
            )
        lines.append("")

    lines.append("")

    path = os.path.join(output_dir, "REPORT.md")
    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"Markdown report: {path}")


def print_console(results: list[dict]):
    """Print comparison table to console."""
    print()
    print(f"{'Ticker':<8} {'Metric':<12} {'MetricDuck':>12} {'yfinance':>12} {'Diff':>8} {'Verdict':<12} {'Period End':<12}")
    print("─" * 80)

    current_ticker = None
    for r in results:
        if r["ticker"] != current_ticker:
            if current_ticker is not None:
                print("─" * 80)
            current_ticker = r["ticker"]

        md_str = fmt_val(r["metricduck"], r["metric_id"])
        yf_str = fmt_val(r["yfinance"], r["metric_id"])
        diff_str = f"{r['pct_diff']:.1f}%" if r["pct_diff"] is not None else "—"
        pe_str = r["period_end"] or "—"

        print(f"{r['ticker']:<8} {r['metric_name']:<12} {md_str:>12} {yf_str:>12} {diff_str:>8} {r['verdict']:<12} {pe_str:<12}")

    print("─" * 80)


# =============================================================================
# MAIN
# =============================================================================


def main():
    if len(sys.argv) > 1:
        tickers = [t.upper() for t in sys.argv[1:]]
    else:
        tickers = DEFAULT_TICKERS

    output_dir = os.path.dirname(os.path.abspath(__file__))

    print(f"Validating {len(tickers)} tickers: {', '.join(tickers)}")
    print(f"Metrics: {', '.join(METRIC_IDS)}")
    print()

    # Fetch MetricDuck
    print("Fetching MetricDuck API (guest access)...")
    md_data = fetch_metricduck(tickers)
    if not md_data:
        print("Failed to fetch MetricDuck data. Aborting.")
        sys.exit(1)

    # Check which tickers returned data
    md_tickers = [t for t in tickers if any(
        md_data.get(t, {}).get(m, {}).get("value") is not None
        for m in METRIC_IDS
    )]
    missing = set(tickers) - set(md_tickers)
    if missing:
        print(f"  Warning: No MetricDuck data for: {', '.join(sorted(missing))}")
    print(f"  Got data for {len(md_tickers)} tickers")

    # Fetch yfinance
    print("Fetching yfinance...")
    yf_data = fetch_yfinance(tickers)
    print(f"  Got data for {len(yf_data)} tickers")

    # Compare
    results = compare(md_data, yf_data, tickers)

    # Output
    print_console(results)
    write_json(results, tickers, output_dir)
    write_report(results, tickers, output_dir)

    # Summary
    comparable = [r for r in results if r["pct_diff"] is not None]
    criticals = [r for r in results if r["verdict"] == "CRITICAL"]
    if criticals:
        print(f"\n{len(criticals)} CRITICAL discrepancies found. Check REPORT.md for details.")
    elif comparable:
        avg = sum(r["pct_diff"] for r in comparable) / len(comparable)
        print(f"\nAll comparisons within tolerance. Average difference: {avg:.1f}%")
    else:
        print("\nNo comparable data points found.")


if __name__ == "__main__":
    main()
