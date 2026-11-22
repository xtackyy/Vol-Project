# HAR-Ridge Volatility Forecasting & Vol-Targeted ETF Strategies

[![tests](https://github.com/xtackyy/Vol-Project/actions/workflows/tests.yml/badge.svg)](https://github.com/xtackyy/Vol-Project/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Out-of-sample forecasting of 5-day realized volatility and 5-day excess returns, used to size
vol-targeted positions in SPY, TLT and GLD, backtested net of costs and financing.

## Executive summary

- **What is tested.** Ridge on HAR-RV features forecasts 5-day forward realized vol. Lasso forecasts
  5-day forward excess returns. Both run in a purged walk-forward (monthly refits, expanding window)
  and drive a long-only, vol-targeted strategy (12% target, 1.5x cap) on SPY, TLT and GLD.
- **The vol forecast works.** Ridge-HAR beats the classic HAR-OLS benchmark out of sample on all
  three assets: OOS R² 0.707 vs 0.651 on SPY (Diebold-Mariano t = −9.98).
- **The return forecast does not.** The 5-day Lasso IC is 0.087 (t = 1.74) on SPY, −0.128 (t = −1.60)
  on TLT and 0.016 (t = 0.22) on GLD. None is significant.
- **Vol targeting mainly cuts SPY's drawdowns.** Net Sharpe 0.57 vs 0.52 for buy & hold, max drawdown
  −31.1% vs −55.2%. For TLT and GLD, Sharpe barely changes.
- **The three sleeves are nearly uncorrelated** (average pairwise correlation 0.02). An equal-weight book
  has Sharpe 0.78 at 7.6% vol, vs 0.77 for the best single sleeve (SPY) on the same 2008-2026 window.

## Methodology & anti-leakage safeguards

**Data.** Daily adjusted OHLCV from Yahoo Finance (`yfinance`), cached in `data/`. The 13-week T-bill
yield (`^IRX`) is the risk-free rate. VIX and asset-specific macro series are features.

**Vol target.** Log annualized realized vol over days *t+1…t+5*. Daily realized variance is proxied by
overnight gap² + Garman-Klass (range-based, daily bars only).

**Features.** HAR daily / weekly / monthly / quarterly log-vol (Corsi 2009), leverage terms (negative 1d/5d
returns), vol-of-vol, RV slope, momentum and trend, abnormal volume, VIX. Each asset also has a macro block:

| | SPY | TLT | GLD |
|---|---|---|---|
| Macro features | VIX, variance risk premium | 10y yield changes; 10y–3m slope (level, 5d/21d change); SPY–TLT 21d correlation; SPY 5d return; VIX 5d change | Dollar index 5/21/63d returns; 10y yield change; real-rate proxy (−TIP 21d); breakeven proxy (TIP − IEF 21d); VIX stress flag and z-score |
| Cost per unit traded | 1.5 bps | 2.0 bps | 3.0 bps |
| Return prior | 4% p.a. | 1% p.a. | 2% p.a. |

**Safeguards**

| Risk | Control |
|---|---|
| Overlapping labels leaking into training | **Purged** walk-forward: a refit at position *T* trains only on rows with *i + h < T* |
| Hyper-parameter snooping | α tuned by `GridSearchCV` with `TimeSeriesSplit(gap=h)` *inside* each training window |
| Scaler fitted on future data | `StandardScaler` lives inside the sklearn `Pipeline`, refit per fold |
| Outside markets settle after the ETF | Every cross-asset series is lagged one day (`shift(1)`). VIX settles 16:15 ET, the ICE dollar index 17:00 ET, Treasury yield indices mid-afternoon; the ETF closes 16:00 ET |
| Different holiday calendars | `align_to()`: as-of join, last value **on or before** each ETF date, never later; feeds stale > 5 days become NaN |
| Trading on the forecast's own close | A weight decided at the close of *t* is held over *t+1* (one-day execution lag) |

**Backtest engine.** Daily, with weight drift between rebalances and a 0.10 no-trade band. Per-asset
trading costs as above. Cash earns T-bills, leverage above 1x pays T-bills + 0.5%, and shorts
(long-short variant only) pay a 0.25% borrow fee.

**Two point-in-time corrections**
- *Vol calibration.* The model forecasts the range-based proxy, but P&L variance is close-to-close. A
  trailing 3-year ratio √(Σr²/ΣRV) rescales the forecast. With it, a 12% target realizes 12.5% on SPY.
- *Return prior.* The Lasso intercept (training-window mean return) stayed negative for years after 2008
  and kept the strategy flat. It is replaced by a fixed per-asset prior, so only the feature *tilt* can
  move the position.

**Tests.** 35 tests pass (`pytest -q`). Most work by scrambling or shocking the future and asserting that
the past does not move:

| File | Tests | Checks |
|---|---|---|
| `tests/test_no_lookahead.py` | 7 | Features, vol calibration and targets are point-in-time; splits are purged; the full scaler → CV → Ridge → forecast stack ignores scrambled future data |
| `tests/test_cross_asset.py` | 12 | A shock to an outside series on day *t* leaves features on *t* unchanged; cross-asset features ignore the future; as-of alignment never looks forward; dead feeds become NaN |
| `tests/test_backtest.py` | 6 | Weights applied with a one-day lag; costs scale with turnover; no-trade band; leverage pays rf + spread |
| `tests/test_signal_refinements.py` | 10 | 5-day targets strictly future; 5-day return model ignores the future; EMA/hold smoothing is causal; long-short and short-fee accounting |

**A look-ahead the safeguards caught.** The first SPY model used VIX at the same day's close. VIX settles
15 minutes after SPY, so that value isn't known at the trade. With VIX lagged one day, SPY's vol R² fell from
0.716 to 0.707 (the pre-fix metrics are kept in `reports/pre_vix_fix/`). All results below use the corrected code.

## Empirical results

All results are out of sample and net of costs. SPY is evaluated 2004-01-08 to 2026-11-20, TLT
2006-07-31 to 2026-11-20 and GLD 2008-11-19 to 2026-11-20. Each starts after a 3-year burn-in that
follows the asset's own listing.

### 1. Volatility forecast (5-day forward realized vol)

| | Ridge-HAR R²_OS | HAR-OLS R²_OS | DM t (Ridge vs HAR) | QLIKE Ridge | QLIKE HAR |
|---|---|---|---|---|---|
| SPY | 0.707 | 0.651 | −9.98 | 0.225 | 0.262 |
| TLT | 0.568 | 0.550 | −2.51 | 0.188 | 0.192 |
| GLD | 0.537 | 0.518 | −3.44 | 0.200 | 0.210 |

R²_OS is measured against the training-window mean. Negative DM t means Ridge has the lower loss.

![SPY out-of-sample vol forecast](reports/SPY/figures/1_vol_forecast.png)

### 2. Return signal

**Information coefficient** (rank IC of the forecast tilt vs the realized 5-day excess return, on days the
model has a view; t-stat uses n/5 effective observations):

| | IC (5-day) | t-stat | Days with a view |
|---|---|---|---|
| SPY | 0.087 | 1.74 | 35.0% |
| TLT | −0.128 | −1.60 | 15.2% |
| GLD | 0.016 | 0.22 | 23.2% |

The 1-day SPY target is weaker still: IC 0.026, t = 1.35.

**Signal study (SPY, 2004-2026, long-only, 4% prior, 0.10 band):**

| Strategy | Gross Sharpe | Net Sharpe | Turnover (x/yr) | Cost drag (bps/yr) | Days flat |
|---|---|---|---|---|---|
| Vol target + 1-day raw signal | 0.47 | 0.42 | 40.5 | 60.8 | 21.3% |
| Vol target + 5-day signal, EMA(5) | 0.58 | 0.57 | 8.8 | 13.1 | 0.2% |
| Vol target only | 0.58 | 0.57 | 8.7 | 13.2 | 0.0% |
| Buy & hold | 0.52 | 0.52 | 0.0 | 0.1 | 0.0% |

The 5-day version matches vol-target-only because the signal overrides the prior on 0.2% of days.
In 2020-2026 the 1-day signal traded 103.7x a year, for a regime Sharpe of 0.16 vs 0.53 for vol target only.

### 3. Multi-asset

**Vol target vs buy & hold, each asset's full OOS window:**

| | VT Sharpe | B&H Sharpe | VT max DD | B&H max DD | VT vol | B&H vol | VT turnover |
|---|---|---|---|---|---|---|---|
| SPY | 0.57 | 0.52 | −31.1% | −55.2% | 12.5% | 18.6% | 8.7x |
| TLT | 0.19 | 0.16 | −43.0% | −48.4% | 13.3% | 14.9% | 4.6x |
| GLD | 0.50 | 0.49 | −41.0% | −45.6% | 12.8% | 17.3% | 3.7x |

**SPY at matched risk.** The vol target is raised to 18.6%, buy & hold's realized vol, to compare
returns at equal risk (2004-01-08 to 2026-11-20, leverage pays T-bills + 0.5%):

| | CAGR | Vol | Sharpe | Max DD | Turnover | Avg exposure |
|---|---|---|---|---|---|---|
| Vol target only (18.6%) | 10.8% | 17.7% | 0.57 | −46.0% | 7.3x | 1.28x |
| Buy & hold | 10.2% | 18.6% | 0.52 | −55.2% | 0.0x | 1.00x |

Realized vol falls short of the target because the 1.5x leverage cap binds in calm markets.
Source: `reports/risk_matched_18.6/`.

**Financing sensitivity.** At 1.28x average exposure, the edge depends on the cost of leverage.
Same forecasts, backtest rerun per borrow spread over T-bills:

| Borrow spread | VT CAGR | B&H CAGR | VT Sharpe | B&H Sharpe | VT max DD |
|---|---|---|---|---|---|
| 0.5% (base case) | 10.8% | 10.2% | 0.57 | 0.52 | −46.0% |
| 2.0% | 10.3% | 10.2% | 0.54 | 0.52 | −46.1% |
| 2.5% | 10.1% | 10.2% | 0.53 | 0.52 | −46.2% |
| 4.0% | 9.6% | 10.2% | 0.51 | 0.52 | −46.3% |

The return edge is gone at a spread between 2.0% and 2.5%, and the Sharpe edge between 3% and 4%.
The drawdown advantage holds at every spread tested.
Source: `reports/risk_matched_18.6/borrow_spread_sensitivity.csv`.

**Correlation of daily vol-targeted returns** (common window; buy & hold in brackets):

| | SPY | TLT | GLD |
|---|---|---|---|
| SPY | 1.00 | −0.24 (−0.30) | 0.08 (0.09) |
| TLT | −0.24 (−0.30) | 1.00 | 0.23 (0.19) |
| GLD | 0.08 (0.09) | 0.23 (0.19) | 1.00 |

**Equal-weight book of the three vol-targeted sleeves, 2008-11-19 to 2026-11-20 (18.0 years):**

| | CAGR | Vol | Sharpe | Max DD |
|---|---|---|---|---|
| SPY sleeve | 10.7% | 12.5% | 0.77 | −18.9% |
| TLT sleeve | 2.3% | 13.4% | 0.13 | −43.0% |
| GLD sleeve | 7.2% | 12.8% | 0.50 | −41.0% |
| **Equal-weight book** | **7.3%** | **7.6%** | **0.78** | **−18.7%** |

Average pairwise correlation 0.02. Diversification ratio (average sleeve vol / book vol) 1.69.
Rebalancing between sleeves is assumed free; trading costs are charged inside each sleeve.

![Vol-targeted sleeves and equal-weight book](reports/multi_asset/figures/1_vol_targeted_equity.png)

## Key research takeaways

- **Vol targeting de-risks equity drawdowns, and far less so elsewhere.** Equity vol rises as prices fall
  (the leverage effect), so cutting exposure as forecast vol rises sells into drawdowns. Max drawdown per
  unit of vol (computed from the table above) falls from 3.0 to 2.5 for SPY. For TLT it barely moves
  (3.3 to 3.2), and for GLD it rises (2.6 to 3.2). In SPY's 2008-09 regime the vol-targeted drawdown was
  −25.7% vs −51.9%. TLT's worst stretch, the 2022-23 rate shock, was a sustained trend rather than a
  crash. Vol targeting scales such a loss down but cannot sidestep it: the 2020-26 drawdown was −43.0% vs
  −48.4%. The Sharpe gain is small for every asset (+0.05 SPY, +0.03 TLT, +0.01 GLD).
- **Linear daily and weekly return signals are noise in these ETFs.** No IC t-stat exceeds 1.74 in absolute
  value. The 5-day signal "recovers" Sharpe only by staying inactive: it is flat on 0.2% of days and
  matches vol-target-only to two decimals.
- **The 1-day signal's damage comes before costs, not only from turnover.** Its gross Sharpe was 0.47 vs
  0.58 for vol target only. As a pure timing test (no prior, long-short), it loses money gross (Sharpe −0.11).
- **Diversification is the clearest gain from the multi-asset extension.** Correlations near zero cut book vol
  to 7.6%, with Sharpe 0.78 vs 0.77 for the best sleeve and a −18.7% max drawdown. In this window the gain
  is risk reduction, not added return. Reaching 12% vol would need about 1.6x leverage and its financing cost.
- **192 signal configurations were tested on one history** (96 settings × long-only / long-short). The best
  net Sharpe was 0.59 vs 0.57 for vol target only, an in-sample upper bound that is not evidence of skill.

## Quickstart

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest -q                                      # 35 tests, offline

python scripts\run_backtest.py --ticker SPY    # or TLT / GLD -> reports\<TICKER>\
python scripts\signal_experiments.py           # 192-configuration signal study -> reports\experiments\
python scripts\run_multi_asset.py              # SPY vs TLT vs GLD + equal-weight book -> reports\multi_asset\
python scripts\run_backtest.py --ticker SPY --target-vol 0.186 --output reports\risk_matched_18.6
python scripts\borrow_spread_sensitivity.py    # matched-risk edge vs cost of leverage
python scripts\run_backtest.py --synthetic     # offline: simulated GJR-GARCH market, no download
```

macOS / Linux: the same commands with forward slashes, after activating with `source`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]" && pytest -q
python scripts/run_backtest.py --ticker SPY
```

The first real-data run downloads prices from Yahoo Finance and caches them as CSVs in `data\`. Later runs
are offline. A full single-asset fit takes about 2-3 minutes. `run_multi_asset.py` fits the three assets in
parallel, and its `--synthetic` flag gives an offline smoke test.

## Repository structure

```
src/volcast/
  config.py        dataclass configs (data, model, strategy) and regime dates
  assets.py        per-ticker profiles: costs, return prior, macro tickers; build_config()
  data.py          yfinance download + cache, as-of alignment (align_to), synthetic market
  features.py      HAR-RV, leverage, trend and macro features; targets; vol calibration
  validation.py    purged walk-forward splits
  models.py        Ridge / Lasso pipelines (GridSearchCV + TimeSeriesSplit(gap)), HAR-OLS baseline
  strategy.py      vol targeting, return signal, EMA / hold smoothing, long-only and long-short
  backtest.py      daily engine: drift, no-trade band, costs, financing, short fee
  metrics.py       R²_OS, QLIKE, Mincer-Zarnowitz, Diebold-Mariano, IC, Sharpe/Sortino, regimes
  pipeline.py      fit_forecasts() (slow) and evaluate_strategy() (fast)
  plotting.py      report figures
scripts/           run_backtest.py, signal_experiments.py, run_multi_asset.py, borrow_spread_sensitivity.py
tests/             leakage, backtest, signal and cross-asset tests (35)
reports/           <TICKER>/, experiments/, multi_asset/: results.md, CSVs, figures
```

## Limitations & next steps

- **Noisy vol proxy.** Daily range-based RV. Intraday 5-minute RV would give a cleaner target and a better
  vol forecast.
- **Curve slope.** The 2-year Treasury yield isn't on Yahoo Finance, so TLT uses 10y minus 3-month (`^TNX − ^IRX`).
- **Execution.** Trades fill at the same close that generates the signal. Next-open execution would be more
  conservative.
- **One history.** Every result comes from a single path of each asset. The equal-weight book has 18 years of
  data, and GLD's sample starts after most of the 2008 crisis.
- **Next steps.** Intraday RV; risk-parity instead of equal weights; a deflated Sharpe ratio for the signal
  grid; more assets (QQQ, IEF) via profiles.

## References

- Corsi, F. (2009). A Simple Approximate Long-Memory Model of Realized Volatility. *Journal of Financial Econometrics*.
- Patton, A. (2011). Volatility Forecast Comparison Using Imperfect Volatility Proxies. *Journal of Econometrics*.
- Moreira, A. & Muir, T. (2017). Volatility-Managed Portfolios. *Journal of Finance*.
- Campbell, J. & Thompson, S. (2008). Predicting Excess Stock Returns Out of Sample. *Review of Financial Studies*.
- Diebold, F. & Mariano, R. (1995). Comparing Predictive Accuracy. *Journal of Business & Economic Statistics*.
- López de Prado, M. (2018). *Advances in Financial Machine Learning*. Wiley (ch. 7, purged cross-validation).

## License

MIT. See [LICENSE](LICENSE).
