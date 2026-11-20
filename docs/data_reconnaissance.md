# Data reconnaissance (started 20 Nov 2026)

What public data exists for each input, how it is accessed, and what's still open.

## Summary

| Input | Source | Access | Status |
|---|---|---|---|
| Deal terms (reoffer spread, benchmark UST + yield, coupon, maturity, call, CUSIP, size, ratings) | SEC EDGAR FWP / 424B2 | Free; full-text search API + Archives | ✅ confirmed |
| Treasury curve (daily) | FRED (H.15 constant maturity), US Treasury par yield curve | Free API / CSV | ✅ standard |
| Market variables (VIX, IG OAS, equities) | FRED (VIXCLS, ICE BofA OAS series, SP500) | Free API | ✅ standard; MOVE is not on FRED, find a proxy |
| Secondary trades per bond | FINRA TRACE | Free per-security web page (3y intraday, 10y EOD), behind the Fixed Income User Agreement; bulk historical files are licensed and paid | ⚠️ **main open question** |
| Peer intraday moves | TRACE (same as above) | same | ⚠️ |
| Bond reference data (outstanding curve per issuer) | EDGAR FWPs themselves + FINRA bond pages | Free | ✅ for SEC-registered bonds |

## 1. EDGAR term sheets

Full-text search endpoint (JSON):
`https://efts.sec.gov/LATEST/search-index?q="<phrase>"&forms=FWP&dateRange=custom&startdt=YYYY-MM-DD&enddt=YYYY-MM-DD`

Documents are at `https://www.sec.gov/Archives/edgar/data/<CIK>/<accession without dashes>/<file>`.
SEC requires a descriptive User-Agent with a contact email, and fair-access limits apply (≤10 req/s).

### Confirmed field set (example: Santander SNP, priced 7 Jan 2025)

Two tranches in one FWP, each US$1bn, settling T+8:

| Field | SNP 2030 | SNP 2035 |
|---|---|---|
| Benchmark | UST 4.375% Dec-2029 | UST 4.250% Nov-2034 |
| Benchmark yield | 4.465% | 4.683% |
| Spread | T+110 | T+135 |
| Reoffer yield / coupon | 5.565% | 6.033% |
| Price | 100.000 | 100.000 |
| CUSIP | 05964HBJ3 | 05964HBK0 |
| Ratings (M/S/F) | Baa1 / A- / A- | Baa1 / A- / A- |

Notes:
- **No pricing time on the term sheet**, only the date. Pricing time has to be inferred (e.g. from the first TRACE print).
- Benchmark price is not always given, but benchmark yield is, which is what we need.
- Several tranches per filing is normal, so the parser must output one row per tranche.

### Rough sample size (FWPs mentioning "Benchmark Treasury", 2021-01 → 2026-11)

European banks seen among the top filers: HSBC (57), Barclays (38), Lloyds (27), Santander (21), Deutsche Bank (12), NatWest (12+). BBVA, UBS, ING and others are also present but weren't in the top-30 buckets.

- These counts are **filings**, not tranches (often 1–3 tranches each), and include amendments/duplicates.
- A first estimate is **a few hundred European-bank tranches over ~6 years**. Enough to start; tight for a rich multivariate model, so keep the all-USD-IG + FIG-dummy fallback open.
- **Coverage gap:** French, Nordic, Italian and most Dutch/German banks issue USD via **144A**, with no EDGAR term sheet. Excluded in phase 1.
- Wording varies across issuers ("Spread to Benchmark Treasury", "Re-offer Spread", …). Discovery should query by issuer CIK and form type, not by one phrase.

## 2. TRACE — open question

- Free route: FINRA bond page per CUSIP (up to 3 years of intraday trade history, 10 years of EOD). It requires accepting the Fixed Income User Agreement and is for **non-commercial** use. Check whether the terms allow automated collection before scripting it, and don't redistribute raw data in this repo.
- Paid routes: FINRA Historic / Enhanced Historic TRACE (licence + fees; CUSIP version needs a CUSIP licence), Academic TRACE (institutional agreement).
- University route: Bath's WRDS is **not available to undergraduates** (per the library page). Worth asking whether a project supervisor could sponsor access. Imperial MSc would likely have it.
- Fallback if bulk TRACE isn't viable: hand-collect a smaller sample of deals, or rely on the ex-post NIP from the new bond's own early trading, which only needs a few weeks of history per CUSIP.

## 3. Environment note

The cloud chat workspace can't reach sec.gov / FRED / FINRA from its shell (egress allowlist). **Data pulls run locally** (VS Code / Claude Code on Bruno's machine). Raw downloads go in `data/` (git-ignored).

## Next actions

1. Read the FINRA Fixed Income User Agreement terms on automated access → decide on the TRACE route.
2. EDGAR discovery: list CIKs of European banks with USD SEC-registered programmes; pull all FWPs 2015→today.
3. Term-sheet parser → `deals.parquet` (one row per tranche) + coverage stats by issuer / year / seniority.
