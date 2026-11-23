# Holdout plan (written 2026-11-23, before any holdout run)

Every design choice in this repo was made with the full 2004-2026 SPY / TLT / GLD history (and the
1998-2026 VIX history) in view. Splitting off the last 30% of that history now would not be a real
holdout, because it has already been seen. These are the holdouts that are still clean.

The code is frozen at the commit that adds this file (git tag `holdout-freeze-2026-11`). Nothing
below may be changed after the runs. Results are reported as they come out, good or bad.

## 1. Vol-targeting pipeline on four new ETFs

`python scripts/holdout.py` → `reports/holdout/`

| Ticker | Asset class (feature block) | Cost per unit traded | Return prior |
|---|---|---|---|
| IWM (US small caps) | equity | 2.0 bps | 4% |
| EFA (developed ex-US) | equity | 2.5 bps | 4% |
| EEM (emerging markets) | equity | 3.0 bps | 4% |
| IEF (7-10y Treasuries) | rates | 2.0 bps | 1% |

Costs were set from typical spreads before the run. Everything else is the frozen default:
- Ridge-HAR, 5-day horizon, monthly refits, 3-year burn-in.
- 12% target, 1.5x cap, 10% no-trade band.
- Next-open fills.

None of these four has been run through the pipeline before. IEF closes were already used as an
input feature for GLD, but never as the traded asset.

**Reported:**
- Vol-forecast R²_OS for Ridge-HAR and for HAR-OLS, and the Diebold-Mariano t-stat.
- For vol target only and for buy and hold: Sharpe, max drawdown, realized vol and turnover.
- The Sharpe gap without 2008-09, and the number of years in which vol targeting beats buy and hold.

**Pass / fail, declared now:**
- (a) Ridge-HAR beats HAR-OLS (DM t < 0) on at least 3 of 4.
- (b) Vol targeting has a smaller max drawdown than buy and hold on the 3 equity ETFs.
- (c) The Sharpe gap is reported as is; no threshold is claimed.

## 2. VRP study on QQQ with VXN

`python scripts/run_vrp.py --underlying QQQ --vol-index ^VXN --output reports/holdout/vrp_QQQ`

The same code and settings as the SPY study:
- 21-day horizon, HAR without implied vol.
- Threshold 0, vol target 10%, 1 vol point cost, entry one day after the signal.

VXN starts in 2001. Caveats, stated in advance:
- QQQ is highly correlated with SPY, so this is a weaker holdout than a different asset class.
- The backwardation filter still uses the S&P curve (VIX vs VIX3M).
- The SVXY / VXX check is skipped because those are VIX products.

**Reported:** the same three results files as the SPY study.

**Pass / fail, declared now:**
- (a) The mean VRP is positive with a Newey-West t > 2.
- (b) The conditional rule does **not** beat always short on Sharpe (the SPY result).
- (c) Always short loses more than 100% of capital in at least one crash.

## 3. Forward test

From 2026-12-01, the frozen code is rerun at each month end, unchanged. Only data dated after
2026-11-30 counts as forward out-of-sample, and it is reported separately from the backtest.
