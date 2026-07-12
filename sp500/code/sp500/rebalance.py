"""
S&P 500 rebalancer: excludes specified tickers and redistributes weights
proportionally across the remaining constituents.

Usage:
    python sp500_rebalance.py --amount 100000
    python sp500_rebalance.py --amount 100000 --exclude TSLA,MSFT,NVDA,INTC,AMD,DELL,HPQ
    python sp500_rebalance.py --amount 100000 --top 20          # preview top 20 allocations
    python sp500_rebalance.py --amount 100000 --csv out.csv     # save full plan
"""

from __future__ import annotations

import argparse
import io
import sys
from dataclasses import dataclass

import pandas as pd
import requests

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_EXCLUDE = [
    "TSLA",   # Elon Musk (CEO)
    "MSFT",   # OpenAI investor + Windows OEM exposure
    "NVDA",   # Heavy OpenAI exposure
    "INTC",   # Windows laptop CPUs
    "AMD",    # Windows laptop CPUs
    "DELL",   # Windows laptop OEM
    "HPQ",    # Windows laptop OEM
    "PLTR",   # No Palantir
    "HD",     # No Home Depot
    "ORCL",   # No Oracle
]

UA = {"User-Agent": "Mozilla/5.0 (compatible; sp500-rebalance/1.0)"}

FIDELITY_BASKET_SIZE = 50


# ---------------------------------------------------------------------------
# Data sources for live S&P 500 weights
# ---------------------------------------------------------------------------

def fetch_from_ssga() -> pd.DataFrame:
    """
    State Street's SPDR S&P 500 ETF (SPY) holdings file. This is the
    authoritative source for real index weights. Returns DataFrame with
    columns: ticker, name, weight (as fraction, summing to ~1.0).
    """
    url = (
        "https://www.ssga.com/us/en/intermediary/library-content/"
        "products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx"
    )
    resp = requests.get(url, headers=UA, timeout=30)
    resp.raise_for_status()

    # The file has ~4 rows of header metadata before the actual table
    raw = pd.read_excel(io.BytesIO(resp.content), header=None)
    header_row = raw.index[raw.iloc[:, 0].astype(str).str.strip() == "Ticker"][0]
    df = pd.read_excel(io.BytesIO(resp.content), skiprows=header_row + 1)
    df.columns = [c.strip() for c in df.columns]

    df = df.rename(columns={"Ticker": "ticker", "Name": "name", "Weight": "weight"})
    df = df[["ticker", "name", "weight"]].dropna(subset=["ticker"])
    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()
    # Weight comes as percent (e.g. 7.1234) -> convert to fraction
    df["weight"] = pd.to_numeric(df["weight"], errors="coerce") / 100.0
    df = df.dropna(subset=["weight"])
    # Drop the fund's cash / non-equity line items
    df = df[~df["ticker"].isin(["-", "CASH_USD", "USD"])]
    return df.reset_index(drop=True)


def fetch_from_slickcharts() -> pd.DataFrame:
    """
    Fallback source: slickcharts.com publishes daily index weights.
    """
    url = "https://www.slickcharts.com/sp500"
    resp = requests.get(url, headers=UA, timeout=30)
    resp.raise_for_status()
    tables = pd.read_html(io.StringIO(resp.text))
    t = tables[0]
    t = t.rename(columns={"Symbol": "ticker", "Company": "name", "Weight": "weight"})
    t["ticker"] = t["ticker"].astype(str).str.strip().str.upper()
    t["weight"] = (
        t["weight"].astype(str).str.replace("%", "", regex=False).astype(float) / 100.0
    )
    return t[["ticker", "name", "weight"]].reset_index(drop=True)


def load_weights() -> tuple[pd.DataFrame, str]:
    """Try sources in order; return (df, source_name)."""
    for fn, label in [
        (fetch_from_ssga, "SSGA SPY holdings"),
        (fetch_from_slickcharts, "slickcharts.com"),
    ]:
        try:
            df = fn()
            if len(df) > 400:  # sanity check
                return df, label
        except Exception as e:
            print(f"[warn] {label} failed: {e}", file=sys.stderr)
    raise RuntimeError("Could not fetch S&P 500 weights from any source.")


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

@dataclass
class Plan:
    df: pd.DataFrame            # full allocation table
    excluded_found: list[str]   # excluded tickers that actually existed in the index
    excluded_missing: list[str] # excluded tickers not found (typos / no longer in index)
    excluded_weight: float      # sum of weights removed (fraction, 0-1)
    total_amount: float
    source: str


def rebalance(
    weights: pd.DataFrame,
    exclude: list[str],
    amount: float,
    source: str,
) -> Plan:
    exclude_up = [t.strip().upper() for t in exclude]
    in_index = set(weights["ticker"])
    excluded_found = [t for t in exclude_up if t in in_index]
    excluded_missing = [t for t in exclude_up if t not in in_index]

    excluded_mask = weights["ticker"].isin(excluded_found)
    excluded_weight = float(weights.loc[excluded_mask, "weight"].sum())

    kept = weights.loc[~excluded_mask].copy()
    # Proportional redistribution: new_weight_i = w_i / sum(w_kept)
    kept_total = kept["weight"].sum()
    if kept_total <= 0:
        raise ValueError("All weights excluded — nothing to allocate.")
    kept["rebalanced_weight"] = kept["weight"] / kept_total
    kept["dollars"] = kept["rebalanced_weight"] * amount

    kept = kept.sort_values("rebalanced_weight", ascending=False).reset_index(drop=True)
    return Plan(
        df=kept,
        excluded_found=excluded_found,
        excluded_missing=excluded_missing,
        excluded_weight=excluded_weight,
        total_amount=amount,
        source=source,
    )


# ---------------------------------------------------------------------------
# Fidelity basket grouping
# ---------------------------------------------------------------------------

def assign_baskets(plan: Plan, basket_size: int = FIDELITY_BASKET_SIZE) -> pd.DataFrame:
    """
    Split the rebalanced plan into groups sized for Fidelity basket portfolios.
    Tickers are already sorted by descending rebalanced weight, so basket 1
    holds the heaviest names. Adds:
      - basket: 1-indexed basket number
      - basket_weight_pct: ticker's share of its own basket's dollars (0-100,
        sums to 100 per basket — what you'd paste into Fidelity)
    """
    if basket_size <= 0:
        raise ValueError("basket_size must be positive")
    df = plan.df.copy().reset_index(drop=True)
    df["basket"] = (df.index // basket_size) + 1
    basket_totals = df.groupby("basket")["dollars"].transform("sum")
    df["basket_weight_pct"] = df["dollars"] / basket_totals * 100.0
    return df


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_report(plan: Plan, top: int | None) -> None:
    print(f"\nData source: {plan.source}")
    print(f"Investment amount: ${plan.total_amount:,.2f}")
    print(f"Constituents in index: {len(plan.df) + len(plan.excluded_found)}")
    print(
        f"Excluded (found in index): {len(plan.excluded_found)} "
        f"=> {', '.join(plan.excluded_found) or '(none)'}"
    )
    if plan.excluded_missing:
        print(
            f"Excluded (NOT found in index, check ticker): "
            f"{', '.join(plan.excluded_missing)}"
        )
    print(
        f"Original weight removed: {plan.excluded_weight * 100:.2f}% "
        f"(redistributed proportionally across the remaining "
        f"{len(plan.df)} holdings)\n"
    )

    view = plan.df.copy()
    view["weight_%"] = view["weight"] * 100
    view["rebalanced_%"] = view["rebalanced_weight"] * 100
    view = view[["ticker", "name", "weight_%", "rebalanced_%", "dollars"]]

    if top:
        print(f"Top {top} allocations:")
        shown = view.head(top)
    else:
        shown = view

    # Pretty print
    with pd.option_context("display.max_rows", None, "display.width", 140):
        print(
            shown.to_string(
                index=False,
                formatters={
                    "weight_%": "{:,.3f}".format,
                    "rebalanced_%": "{:,.3f}".format,
                    "dollars": "${:,.2f}".format,
                },
            )
        )

    total_dollars = view["dollars"].sum()
    print(f"\nTotal allocated: ${total_dollars:,.2f} "
          f"(rounding diff: ${plan.total_amount - total_dollars:,.4f})")


def print_baskets(plan: Plan, basket_size: int = FIDELITY_BASKET_SIZE) -> None:
    df = assign_baskets(plan, basket_size)
    n_baskets = int(df["basket"].max())

    print(
        f"\nFidelity basket grouping "
        f"(max {basket_size} tickers per basket, {n_baskets} baskets total):"
    )

    summary = (
        df.groupby("basket")
        .agg(tickers=("ticker", "count"), dollars=("dollars", "sum"))
        .reset_index()
    )
    summary["portfolio_pct"] = summary["dollars"] / plan.total_amount * 100.0
    print(
        summary.to_string(
            index=False,
            formatters={
                "dollars": "${:,.2f}".format,
                "portfolio_pct": "{:,.3f}".format,
            },
        )
    )

    for b in range(1, n_baskets + 1):
        rows = df[df["basket"] == b][
            ["ticker", "name", "basket_weight_pct", "dollars"]
        ]
        print(f"\n--- Basket {b} ({len(rows)} tickers) ---")
        with pd.option_context("display.max_rows", None, "display.width", 140):
            print(
                rows.to_string(
                    index=False,
                    formatters={
                        "basket_weight_pct": "{:,.3f}".format,
                        "dollars": "${:,.2f}".format,
                    },
                )
            )


def write_basket_csvs(plan: Plan, prefix: str, basket_size: int = FIDELITY_BASKET_SIZE) -> list[str]:
    df = assign_baskets(plan, basket_size)
    n_baskets = int(df["basket"].max())
    written: list[str] = []
    for b in range(1, n_baskets + 1):
        rows = df[df["basket"] == b][
            ["ticker", "name", "basket_weight_pct", "dollars"]
        ]
        path = f"{prefix}_{b:02d}.csv"
        rows.to_csv(path, index=False)
        written.append(path)
    return written


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="Rebalance S&P 500 with exclusions.")
    ap.add_argument("--amount", type=float, required=True,
                    help="Dollar amount to invest (e.g. 100000)")
    ap.add_argument("--exclude", type=str, default=",".join(DEFAULT_EXCLUDE),
                    help="Comma-separated tickers to exclude "
                         f"(default: {','.join(DEFAULT_EXCLUDE)})")
    ap.add_argument("--top", type=int, default=None,
                    help="Only show the top N holdings in stdout")
    ap.add_argument("--csv", type=str, default=None,
                    help="Write full allocation plan to this CSV path")
    ap.add_argument("--baskets", action="store_true",
                    help="Print Fidelity basket groupings (≤50 tickers per basket)")
    ap.add_argument("--basket-csv-prefix", type=str, default=None,
                    help="Write one CSV per basket as PREFIX_01.csv, PREFIX_02.csv, ...")
    ap.add_argument("--basket-size", type=int, default=FIDELITY_BASKET_SIZE,
                    help=f"Tickers per basket (default: {FIDELITY_BASKET_SIZE})")
    args = ap.parse_args()

    weights, source = load_weights()
    exclude = [t for t in args.exclude.split(",") if t.strip()]
    plan = rebalance(weights, exclude, args.amount, source)

    print_report(plan, args.top)

    if args.csv:
        out = plan.df.copy()
        out["weight_pct"] = out["weight"] * 100
        out["rebalanced_weight_pct"] = out["rebalanced_weight"] * 100
        out = out[["ticker", "name", "weight_pct", "rebalanced_weight_pct", "dollars"]]
        out.to_csv(args.csv, index=False)
        print(f"\nWrote {args.csv}")

    if args.baskets:
        print_baskets(plan, args.basket_size)

    if args.basket_csv_prefix:
        written = write_basket_csvs(plan, args.basket_csv_prefix, args.basket_size)
        print("\nWrote basket CSVs:")
        for p in written:
            print(f"  {p}")


if __name__ == "__main__":
    main()
