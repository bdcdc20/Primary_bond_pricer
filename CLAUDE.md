# CLAUDE.md — Primary_bond_pricer

Context for Claude sessions working in this repo.

## What this is
A public-data new-issue pricer for USD bonds issued by European banks (Yankee FIG). Two parts: an FV engine (issuer secondary curves from TRACE) and a NIP model (NIP labels from EDGAR term sheets, regressed on market conditions known before pricing). Methodology lives in `README.md`; data findings in `docs/data_reconnaissance.md`.

## Hard rules
- **Public data only. Nothing from Bruno's previous employer:** no code, constants, issuer groupings, deal data or screenshots, even from memory. Methodology ideas are fine; implementations are written fresh.
- Don't commit raw third-party data (TRACE, EDGAR bulk downloads). `data/` is git-ignored. Commit code, derived results and small summary tables only.
- All market inputs to the NIP regression must be **T−1 close**, with no look-ahead.
- Spreads are measured against **the deal's own benchmark Treasury** unless a step explicitly needs an interpolated curve.

## Conventions
- Python ≥3.11, package under `src/primary_bond_pricer/`.
- Spreads in bp, yields in %, dates ISO.
- EDGAR requests: descriptive User-Agent with a real contact email, ≤10 req/s, cache everything under `data/raw/edgar/`.

## Where the project stands
- Step 1 code exists: `data/edgar.py` (search + cached download), `data/termsheet.py` (parser, side-by-side and sequential layouts), `data/issuers.py`, `scripts/build_deal_table.py`. Tests in `tests/` pass on synthetic fixtures; **it has not been run against live EDGAR yet**. Expect to extend `FIELD_PATTERNS` after the first run, using `parse_failures.csv`. Add a real-filing regression fixture for each layout fixed.
- **Never write a TRACE scraper**: the FINRA site's User Agreement forbids automated collection. TRACE route options are in `docs/data_reconnaissance.md` §2.

## Next session: tasks in order
This repo was set up from a cloud chat that couldn't reach sec.gov / FRED. The local session picks up from here.

1. **Setup.** `pip install -e ".[dev]"`, run `pytest` (4 tests should pass). Ask Bruno for the contact email for `EDGAR_USER_AGENT`; never invent one.
2. **First live run of step 1.** `python scripts/build_deal_table.py --start 2015-01-01`. Report:
   - FWP documents found per issuer (a 0 for BBVA / UBS / ING means a CIK problem in `issuers.py`);
   - tranches parsed vs `parse_failures.csv` count;
   - rows with a non-zero `identity_gap_bp` (> 0.5bp means a mis-parsed field; FRNs and reset notes can legitimately differ).
3. **Fix the parser using real filings.** For each failing layout, open the cached HTML under `data/raw/edgar/docs/`, extend `FIELD_PATTERNS` or the block logic in `termsheet.py`, and add a **minimal hand-made fixture reproducing that layout** to `tests/` (don't commit raw filings). Rerun until failures are mostly non-pricing FWPs (marketing docs, FRN-only).
4. **Check coverage gaps.** Look for groups that file under a second entity (e.g. Barclays Bank PLC vs Barclays PLC, Lloyds Bank plc, HSBC USA). Add their CIKs if they carry European-bank senior USD deals.
5. **Classify seniority properly.** `SENIOR` is a catch-all; split HoldCo senior (HSBC, Barclays, Lloyds, NatWest HoldCos) from SP/SNP using the issuer entity + title text.
6. **Commit** code, tests and `results/deal_coverage.csv`. Update the README roadmap and this section with the real sample size.
7. **Then step 2:** FRED pulls (H.15 Treasury constant-maturity curve, VIXCLS, ICE BofA IG OAS series, SP500) + FINRA Query API corporate market breadth/sentiment (public credentials, aggregates only), all stored as T−1-aligned daily series.

Don't start TRACE work. It waits on Bruno's decision about the access route (recon doc §2).

## Running
```
pip install -e ".[dev]"
pytest
export EDGAR_USER_AGENT="Name email@domain"
python scripts/build_deal_table.py --start 2015-01-01
```
