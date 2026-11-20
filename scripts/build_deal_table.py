"""Step 1: discover European-bank FWP term sheets on EDGAR, parse them, write the deal table.

Usage (from the repo root, on a machine with internet access):

    export EDGAR_USER_AGENT="Your Name your.email@domain"
    python scripts/build_deal_table.py --start 2015-01-01

Outputs:
    data/processed/deals.parquet         one row per tranche (local only, git-ignored)
    data/processed/parse_failures.csv    term sheets that produced no tranche, for review
    results/deal_coverage.csv            counts by issuer / year / seniority / rate type (committed)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from primary_bond_pricer.data.edgar import EdgarClient  # noqa: E402
from primary_bond_pricer.data.issuers import resolve_ciks  # noqa: E402
from primary_bond_pricer.data.termsheet import parse_termsheet  # noqa: E402

# Pricing term sheets nearly always carry a CUSIP; marketing FWPs mostly don't.
QUERY = '"CUSIP"'


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2015-01-01")
    ap.add_argument("--end", default=None)
    args = ap.parse_args()

    client = EdgarClient()
    issuers = resolve_ciks(client.ticker_ciks())

    rows, failures = [], []
    for iss in issuers:
        docs = client.search(QUERY, forms="FWP", start=args.start, end=args.end, cik=iss["cik"])
        print(f"{iss['name']:<24} {len(docs):>4} FWP documents")
        for doc in docs:
            try:
                tranches = parse_termsheet(client.fetch(doc))
            except Exception as exc:  # keep going; log for review
                failures.append({**doc.__dict__, "url": doc.url, "error": repr(exc)})
                continue
            if not tranches:
                failures.append({**doc.__dict__, "url": doc.url, "error": "no tranche parsed"})
            for t in tranches:
                rows.append({
                    "group": iss["name"], "country": iss["country"], "filer_cik": doc.cik,
                    "adsh": doc.adsh, "filename": doc.filename, "file_date": doc.file_date,
                    "url": doc.url, **t,
                })

    deals = pd.DataFrame(rows)
    out = Path("data/processed")
    out.mkdir(parents=True, exist_ok=True)
    if deals.empty:
        print("No tranches parsed.")
        return

    # amendments / re-filed term sheets: keep the latest filing per CUSIP
    deals = (deals.sort_values("file_date")
                  .drop_duplicates(subset=["cusip"], keep="last")
                  .reset_index(drop=True))
    # sanity flag: on a fixed-rate tranche, reoffer yield should equal benchmark yield + spread
    deals["identity_gap_bp"] = (
        deals["reoffer_yield_pct"] - deals["benchmark_yield_pct"] - deals["spread_bp"] / 100
    ) * 100
    deals.to_parquet(out / "deals.parquet", index=False)
    pd.DataFrame(failures).to_csv(out / "parse_failures.csv", index=False)

    deals["year"] = pd.to_datetime(deals["trade_date"]).dt.year
    coverage = (deals.groupby(["group", "year", "seniority", "rate_type"], dropna=False)
                     .agg(tranches=("cusip", "count"),
                          with_spread=("spread_bp", "count"),
                          with_benchmark_yield=("benchmark_yield_pct", "count"))
                     .reset_index())
    Path("results").mkdir(exist_ok=True)
    coverage.to_csv("results/deal_coverage.csv", index=False)

    usable = deals.dropna(subset=["spread_bp", "benchmark_yield_pct", "trade_date", "maturity_date"])
    print(f"\nTranches parsed: {len(deals)} | with full pricing fields: {len(usable)} | "
          f"term sheets failed: {len(failures)}")
    print(usable.groupby("seniority").size().to_string())


if __name__ == "__main__":
    main()
