"""
Simplified S&P 500 + FTSE Developed (ex-US) rebalancer.

Builds a blended portfolio using SPY (S&P 500) and VEA (Vanguard FTSE
Developed Markets ex-US) holdings, removes excluded tickers, and caps
the buy list to the top N names by blended weight (default 100) so the
plan can actually be executed by a single trader.

Usage:
    python -m sp500.rebalance --amount 100000
    python -m sp500.rebalance --amount 100000 --max-stocks 50
    python -m sp500.rebalance --amount 100000 --us-weight 0.7
    python -m sp500.rebalance --amount 100000 --us-only
    python -m sp500.rebalance --amount 100000 --exclude TSLA,MSFT --csv plan.csv
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
    "ORCL",   # Oracle
    "PLTR",   # Palantir
]

DEFAULT_MAX_STOCKS = 100
DEFAULT_US_WEIGHT = 0.60   # 60% S&P 500 / 40% FTSE Developed ex-US

UA = {"User-Agent": "Mozilla/5.0 (compatible; sp500-rebalance/2.0)"}


# ---------------------------------------------------------------------------
# Data sources
# ---------------------------------------------------------------------------

def fetch_spy() -> pd.DataFrame:
    """SSGA SPDR S&P 500 ETF (SPY) holdings file."""
    url = (
        "https://www.ssga.com/us/en/intermediary/library-content/"
        "products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx"
    )
    resp = requests.get(url, headers=UA, timeout=30)
    resp.raise_for_status()

    raw = pd.read_excel(io.BytesIO(resp.content), header=None)
    header_row = raw.index[raw.iloc[:, 0].astype(str).str.strip() == "Ticker"][0]
    df = pd.read_excel(io.BytesIO(resp.content), skiprows=header_row + 1)
    df.columns = [c.strip() for c in df.columns]

    df = df.rename(columns={"Ticker": "ticker", "Name": "name", "Weight": "weight"})
    df = df[["ticker", "name", "weight"]].dropna(subset=["ticker"])
    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()
    df["weight"] = pd.to_numeric(df["weight"], errors="coerce") / 100.0
    df = df.dropna(subset=["weight"])
    df = df[~df["ticker"].isin(["-", "CASH_USD", "USD"])]
    df["region"] = "US"
    return df.reset_index(drop=True)


def fetch_slickcharts() -> pd.DataFrame:
    """Fallback for SPY: slickcharts.com index weights."""
    url = "https://www.slickcharts.com/sp500"
    resp = requests.get(url, headers=UA, timeout=30)
    resp.raise_for_status()
    tables = pd.read_html(io.StringIO(resp.text))
    t = tables[0].rename(
        columns={"Symbol": "ticker", "Company": "name", "Weight": "weight"}
    )
    t["ticker"] = t["ticker"].astype(str).str.strip().str.upper()
    t["weight"] = (
        t["weight"].astype(str).str.replace("%", "", regex=False).astype(float) / 100.0
    )
    t["region"] = "US"
    return t[["ticker", "name", "weight", "region"]].reset_index(drop=True)


def fetch_vea() -> pd.DataFrame:
    """
    Vanguard FTSE Developed Markets ETF (VEA) holdings via Vanguard's
    public JSON endpoint. VEA tracks FTSE Developed All-Cap ex-US.
    """
    url = (
        "https://api.vanguard.com/rs/ire/01/ind/fund/0936/"
        "portfolio-holding/stock.json"
    )
    resp = requests.get(url, headers=UA, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    rows = (
        payload.get("fund", {})
        .get("entity", [{}])[0]
        .get("portfolioHolding", [])
    )
    if not rows:
        rows = payload.get("portfolioHolding", [])
    if not rows:
        raise RuntimeError("VEA payload had no holdings rows")

    df = pd.DataFrame(rows)
    df = df.rename(
        columns={
            "ticker": "ticker",
            "shortName": "name",
            "longName": "name",
            "percentWeight": "weight",
        }
    )
    df = df[[c for c in ["ticker", "name", "weight"] if c in df.columns]]
    df = df.dropna(subset=["ticker", "weight"])
    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()
    df["weight"] = pd.to_numeric(df["weight"], errors="coerce") / 100.0
    df = df.dropna(subset=["weight"])
    df = df[df["weight"] > 0]
    df = df[~df["ticker"].isin(["-", "CASH", "USD", "N/A"])]
    df["region"] = "INTL"
    return df.reset_index(drop=True)


def fetch_iefa() -> pd.DataFrame:
    """
    Fallback for VEA: iShares Core MSCI EAFE ETF (IEFA) holdings CSV.
    MSCI EAFE != FTSE Developed exactly, but it's a close ex-US developed
    proxy and iShares CSVs are reliably downloadable.
    """
    url = (
        "https://www.ishares.com/us/products/244049/"
        "ishares-core-msci-eafe-etf/1467271812596.ajax"
        "?fileType=csv&fileName=IEFA_holdings&dataType=fund"
    )
    resp = requests.get(url, headers=UA, timeout=30)
    resp.raise_for_status()
    text = resp.content.decode("utf-8", errors="replace")
    lines = text.splitlines()
    header_idx = next(
        i for i, ln in enumerate(lines) if ln.lstrip().startswith("Ticker,")
    )
    df = pd.read_csv(io.StringIO("\n".join(lines[header_idx:])))
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(
        columns={
            "Ticker": "ticker",
            "Name": "name",
            "Weight (%)": "weight",
        }
    )
    df = df[["ticker", "name", "weight"]].dropna(subset=["ticker"])
    df["ticker"] = df["ticker"].astype(str).str.strip().str.upper()
    df["weight"] = pd.to_numeric(df["weight"], errors="coerce") / 100.0
    df = df.dropna(subset=["weight"])
    df = df[df["weight"] > 0]
    df = df[~df["ticker"].isin(["-", "CASH", "USD", "N/A"])]
    df["region"] = "INTL"
    return df.reset_index(drop=True)


def _try_sources(sources: list[tuple], min_rows: int) -> tuple[pd.DataFrame, str]:
    for fn, label in sources:
        try:
            df = fn()
            if len(df) >= min_rows:
                return df, label
            print(
                f"[warn] {label} returned only {len(df)} rows, trying next source",
                file=sys.stderr,
            )
        except Exception as e:
            print(f"[warn] {label} failed: {e}", file=sys.stderr)
    raise RuntimeError("No data source succeeded.")


def load_us() -> tuple[pd.DataFrame, str]:
    return _try_sources(
        [(fetch_spy, "SSGA SPY holdings"), (fetch_slickcharts, "slickcharts.com")],
        min_rows=400,
    )


def load_intl() -> tuple[pd.DataFrame, str]:
    return _try_sources(
        [(fetch_vea, "Vanguard VEA holdings"), (fetch_iefa, "iShares IEFA holdings")],
        min_rows=200,
    )


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

@dataclass
class Plan:
    df: pd.DataFrame              # final allocation table (top-N)
    us_source: str
    intl_source: str | None
    us_weight: float
    intl_weight: float
    excluded_found: list[str]
    excluded_missing: list[str]
    excluded_weight: float        # fraction of blended index removed (0-1)
    max_stocks: int
    universe_size: int            # blended universe size before top-N cut
    us_coverage: float            # fraction of US index captured by final picks
    intl_coverage: float          # fraction of intl index captured by final picks
    total_amount: float


def _blend(
    us: pd.DataFrame | None,
    intl: pd.DataFrame | None,
    us_weight: float,
) -> pd.DataFrame:
    """
    Combine the two universes. Each fund's weights already sum to ~1
    within its own region; we scale by us_weight / (1 - us_weight) so
    blended weights sum to ~1 across both.
    """
    parts = []
    if us is not None and us_weight > 0:
        u = us.copy()
        u["weight"] = u["weight"] * us_weight
        parts.append(u)
    if intl is not None and us_weight < 1:
        i = intl.copy()
        i["weight"] = i["weight"] * (1 - us_weight)
        parts.append(i)
    if not parts:
        raise ValueError("No regions selected.")

    blended = pd.concat(parts, ignore_index=True)
    # In the unlikely case the same ticker appears in both feeds
    # (cross-listings), sum the weights.
    blended = (
        blended.groupby("ticker", as_index=False)
        .agg({"name": "first", "weight": "sum", "region": "first"})
    )
    return blended.sort_values("weight", ascending=False).reset_index(drop=True)


def rebalance(
    us: pd.DataFrame | None,
    us_source: str | None,
    intl: pd.DataFrame | None,
    intl_source: str | None,
    exclude: list[str],
    amount: float,
    max_stocks: int,
    us_weight: float,
) -> Plan:
    blended = _blend(us, intl, us_weight)

    exclude_up = {t.strip().upper() for t in exclude if t.strip()}
    in_universe = set(blended["ticker"])
    excluded_found = sorted(t for t in exclude_up if t in in_universe)
    excluded_missing = sorted(t for t in exclude_up if t not in in_universe)

    excl_mask = blended["ticker"].isin(excluded_found)
    excluded_weight = float(blended.loc[excl_mask, "weight"].sum())

    kept = blended.loc[~excl_mask].copy()
    if kept.empty:
        raise ValueError("All weights excluded - nothing to allocate.")

    # Cap to the top N by blended weight
    universe_size = len(kept)
    picked = kept.head(max_stocks).copy()

    # Coverage diagnostics: how much of each underlying index do the
    # picks cover? Compute against the original (pre-blend) weights.
    def _coverage(orig: pd.DataFrame | None) -> float:
        if orig is None or orig.empty:
            return 0.0
        chosen = orig[orig["ticker"].isin(picked["ticker"])]
        return float(chosen["weight"].sum())

    us_coverage = _coverage(us)
    intl_coverage = _coverage(intl)

    # Renormalize so the chosen names sum to 1
    total_w = picked["weight"].sum()
    picked["rebalanced_weight"] = picked["weight"] / total_w
    picked["dollars"] = picked["rebalanced_weight"] * amount

    picked = picked.sort_values("rebalanced_weight", ascending=False).reset_index(
        drop=True
    )

    return Plan(
        df=picked,
        us_source=us_source or "(none)",
        intl_source=intl_source,
        us_weight=us_weight,
        intl_weight=1 - us_weight,
        excluded_found=excluded_found,
        excluded_missing=excluded_missing,
        excluded_weight=excluded_weight,
        max_stocks=max_stocks,
        universe_size=universe_size,
        us_coverage=us_coverage,
        intl_coverage=intl_coverage,
        total_amount=amount,
    )


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_report(plan: Plan, top: int | None) -> None:
    print(f"\nUS source:   {plan.us_source}  (target weight {plan.us_weight:.0%})")
    print(
        f"Intl source: {plan.intl_source or '(disabled)'}  "
        f"(target weight {plan.intl_weight:.0%})"
    )
    print(f"Investment amount: ${plan.total_amount:.2f}")
    print(
        f"Universe (post-exclude, pre-cap): {plan.universe_size} names; "
        f"capped to top {plan.max_stocks} -> {len(plan.df)} actual holdings"
    )
    print(
        f"Excluded (found): {len(plan.excluded_found)} "
        f"=> {', '.join(plan.excluded_found) or '(none)'}"
    )
    if plan.excluded_missing:
        print(
            f"Excluded (NOT found, check ticker): "
            f"{', '.join(plan.excluded_missing)}"
        )
    print(
        f"Blended weight removed by exclusions: "
        f"{plan.excluded_weight * 100:.2f}%"
    )
    print(
        f"Index coverage by final picks: "
        f"S&P 500 {plan.us_coverage * 100:.1f}%, "
        f"FTSE Dev ex-US {plan.intl_coverage * 100:.1f}%\n"
    )

    view = plan.df.copy()
    view["weight_%"] = view["weight"] * 100
    view["rebalanced_%"] = view["rebalanced_weight"] * 100
    view = view[["ticker", "name", "region", "weight_%", "rebalanced_%", "dollars"]]

    if top:
        print(f"Top {top} of {len(view)} allocations:")
        shown = view.head(top)
    else:
        shown = view

    with pd.option_context("display.max_rows", None, "display.width", 160):
        print(
            shown.to_string(
                index=False,
                formatters={
                    "weight_%": "{:,.3f}".format,
                    "rebalanced_%": "{:,.3f}".format,
                    "dollars": "${:.2f}".format,
                },
            )
        )

    total_dollars = view["dollars"].sum()
    print(
        f"\nTotal allocated: ${total_dollars:.2f} "
        f"(rounding diff: ${plan.total_amount - total_dollars:.4f})"
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Simplified blended SP500 + FTSE Developed rebalancer."
    )
    ap.add_argument("--amount", type=float, required=True,
                    help="Dollar amount to invest (e.g. 100000)")
    ap.add_argument("--exclude", type=str, default=",".join(DEFAULT_EXCLUDE),
                    help=f"Comma-separated tickers to exclude "
                         f"(default: {','.join(DEFAULT_EXCLUDE)})")
    ap.add_argument("--max-stocks", type=int, default=DEFAULT_MAX_STOCKS,
                    help=f"Hard cap on number of holdings "
                         f"(default: {DEFAULT_MAX_STOCKS})")
    ap.add_argument("--us-weight", type=float, default=DEFAULT_US_WEIGHT,
                    help=f"Fraction allocated to S&P 500 vs FTSE Developed "
                         f"ex-US (default: {DEFAULT_US_WEIGHT})")
    region = ap.add_mutually_exclusive_group()
    region.add_argument("--us-only", action="store_true",
                        help="Use S&P 500 only (equivalent to --us-weight 1.0)")
    region.add_argument("--intl-only", action="store_true",
                        help="Use FTSE Developed ex-US only "
                             "(equivalent to --us-weight 0.0)")
    ap.add_argument("--top", type=int, default=None,
                    help="Only show the top N rows in stdout (display only)")
    ap.add_argument("--csv", type=str, default=None,
                    help="Write full allocation plan to this CSV path")
    args = ap.parse_args()

    if args.us_only:
        us_weight = 1.0
    elif args.intl_only:
        us_weight = 0.0
    else:
        us_weight = args.us_weight
    if not 0.0 <= us_weight <= 1.0:
        ap.error("--us-weight must be between 0 and 1")
    if args.max_stocks <= 0:
        ap.error("--max-stocks must be > 0")

    us_df: pd.DataFrame | None = None
    us_src: str | None = None
    intl_df: pd.DataFrame | None = None
    intl_src: str | None = None
    if us_weight > 0:
        us_df, us_src = load_us()
    if us_weight < 1:
        intl_df, intl_src = load_intl()

    exclude = [t for t in args.exclude.split(",") if t.strip()]
    plan = rebalance(
        us=us_df,
        us_source=us_src,
        intl=intl_df,
        intl_source=intl_src,
        exclude=exclude,
        amount=args.amount,
        max_stocks=args.max_stocks,
        us_weight=us_weight,
    )

    print_report(plan, args.top)

    if args.csv:
        out = plan.df.copy()
        out["weight_pct"] = out["weight"] * 100
        out["rebalanced_weight_pct"] = out["rebalanced_weight"] * 100
        out = out[
            ["ticker", "name", "region", "weight_pct",
             "rebalanced_weight_pct", "dollars"]
        ]
        out.to_csv(args.csv, index=False)
        print(f"\nWrote {args.csv}")


if __name__ == "__main__":
    main()
