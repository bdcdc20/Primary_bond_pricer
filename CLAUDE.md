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

## Running
```
pip install -e ".[dev]"
pytest
export EDGAR_USER_AGENT="Name email@domain"
python scripts/build_deal_table.py --start 2015-01-01
```
