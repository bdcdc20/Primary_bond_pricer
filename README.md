# Primary_bond_pricer

A new-issue pricer for **USD bank bonds issued by European banks ("Yankee" FIG)**, built entirely on public data.

The pricer has two parts:

1. **A fair-value (FV) engine.** It builds each issuer's secondary spread curve from public trade data and reads off where a new bond *should* price.
2. **A new-issue premium (NIP) model.** It measures the NIP actually paid on historical deals, then regresses it on market conditions known before pricing to predict the NIP on the next deal.

Scope for now: USD, Senior Preferred / Senior Non-Preferred / HoldCo senior, SEC-registered deals. EUR covered and senior come later, once the EU bond consolidated tape is live.

> Built from scratch on public data. No code, constants or data from any previous employer is used.

---

## 1. Measuring the NIP

```
NIP = reoffer spread − fair-value spread of the same bond, measured before the deal is announced
```

### 1.1 Reoffer spread (exact)

Taken from the deal's SEC term sheet (FWP / 424B2), which states:
- the benchmark Treasury and its yield at pricing
- the spread to the benchmark (T+X)
- the reoffer yield, coupon, maturity, call date, CUSIP, size and ratings

Every spread in the project is measured against **the deal's own benchmark Treasury**. As a result, the rates move during the pricing day drops out by construction.

### 1.2 Fair value (the hard part)

- **Snapshot:** the T−1 close. FIG deals are usually announced before the US open, so the T−1 close is the last level not yet moved by the deal.
- **Secondary levels:** TRACE trades, filtered to institutional size (≥ $1mm). A Kalman filter tracks each bond's true spread as a hidden state, driven by a common market factor (ICE BofA IG OAS on FRED) plus its own drift. Trades are noisy observations, weighted by size. On days with no trades the estimate rolls forward with the market factor, and its uncertainty grows.
- **Issuer curve:** same seniority only (SP / SNP / HoldCo kept separate). Callables are measured to the call date and compared only with other callables. Comps fill in when the issuer's curve is sparse, and those deals are flagged as lower quality.
- **Seasoned vs new bonds:** a dollar-price / coupon control for comparing discount bonds with par-priced new issues.

### 1.3 Intraday error

| Source | Fix | Expected error left |
|---|---|---|
| Intraday rates | Same-benchmark spreads; term-sheet benchmark yield compared with the EOD yield, used to align the curve and size measurement noise | ~0 |
| Intraday credit (T−1 close → pricing) | Pricing time ≈ first TRACE print of the new CUSIP; FV rolled forward using **peer** FIG bond moves up to that time | ~0.5–1bp |
| Stale or noisy secondary data | Kalman filter; uncertainty reported for each deal | varies by deal |
| Spread rounding | — | ±0.5bp floor |

### 1.4 Ex-post cross-check

Ex-post NIP = reoffer spread − where the new bond trades after N days, adjusted for the market move over the same window (this follows the corporate bond underpricing literature). The ex-ante and ex-post estimates should broadly agree. Deals where they disagree sharply point to a bad FV and are reviewed.

## 2. NIP regression

- Target: NIP in bp. Weighted least squares, with each deal weighted by the inverse of its measurement variance.
- Inputs: T−1 close values only, so nothing from after pricing leaks in.
  - Market variables: VIX, MOVE, IG OAS level and change, Treasury level and recent volatility, equity return.
  - Calendar effects, modelled through the underlying mechanism: earnings blackout windows, weekly IG supply (counted from EDGAR), trailing 5-day NIP (new-issue momentum), FOMC and CPI days.
  - Deal variables: size relative to the issuer's outstanding debt, tenor, seniority, rating, issuer frequency, days since the issuer's last deal.
- Evaluation: standard errors clustered by issuer, train/test split by time, and a naive benchmark of the trailing average NIP.
- Sample: European-bank SEC-registered deals. If that's too small for a stable regression, widen to all USD IG issuers with a FIG dummy.

## 3. Roadmap

| Step | What | Status |
|---|---|---|
| 0 | Data reconnaissance: sources, access, coverage (see `docs/data_reconnaissance.md`) | in progress |
| 1 | EDGAR term-sheet discovery and parser → deal table (one row per tranche) | code written + unit-tested on synthetic term sheets; first live run pending (`scripts/build_deal_table.py`) |
| 2 | Treasury curves (FRED / Treasury) + market variables (FRED, FINRA market breadth API) | to do |
| 3 | TRACE secondary history per CUSIP for issuer and peer curves | blocked: FINRA site terms forbid scraping; needs licensed/academic access or scoped manual collection (see recon doc) |
| 4 | Kalman filter for secondary spreads + issuer FV curves | to do |
| 5 | NIP labels (ex-ante and ex-post) with per-deal uncertainty | to do |
| 6 | NIP regression and out-of-sample evaluation | to do |
| 7 | Pricer front end: given issuer / tenor / seniority / date → FV, predicted NIP, guidance range | to do |

## 4. Repository layout

```
docs/                 methodology and data notes
src/primary_bond_pricer/
    data/             fetchers and parsers (EDGAR, FRED, TRACE)
    fv/               secondary-spread filter and issuer curves
    nip/              NIP labels and regression
notebooks/            exploration and results
data/                 local only, git-ignored (raw downloads, caches)
```
