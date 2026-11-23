# Results: IEF

Out-of-sample window: **2006-07-31 → 2026-11-20** (5,111 trading days). Refit every 21 days, expanding window, 756-day burn-in. Fills: next open. Costs: 2.0 bps per unit traded.

## Model A: 5-day forward realized volatility

|                       |   n_oos |   r2_oos_vs_mean |   rmse |   mae |   corr |   rmse_vol_pts |   qlike |   mz_alpha |   mz_beta |   mz_r2 |   mz_wald_p |   dm_stat |   dm_p_value |
|:----------------------|--------:|-----------------:|-------:|------:|-------:|---------------:|--------:|-----------:|----------:|--------:|------------:|----------:|-------------:|
| Ridge-HAR (Model A)   |    5106 |            0.533 |  0.285 | 0.22  |  0.725 |          2.239 |   0.206 |      0.11  |     1.037 |   0.526 |       0.421 |    -2.389 |        0.017 |
| HAR-RV OLS (baseline) |    5106 |            0.513 |  0.29  | 0.223 |  0.711 |          2.26  |   0.211 |     -0.022 |     0.993 |   0.505 |       0.961 |   nan     |      nan     |

`r2_oos_vs_mean` is the Campbell-Thompson R² against the training-window mean; `dm_stat` < 0 means Ridge beats HAR-OLS on squared error.

## Model B: 5-day forward excess return

|                     |   n_oos |   r2_oos_vs_mean |   rmse |   mae |    corr |   hit_rate_sign |     ic |   ic_t |   view_share |   n_view |
|:--------------------|--------:|-----------------:|-------:|------:|--------:|----------------:|-------:|-------:|-------------:|---------:|
| Lasso (Model B, 5d) |    5106 |           0.0001 | 0.0092 | 0.007 | -0.0037 |           0.527 | 0.1176 | 0.2995 |       0.0082 |       42 |

## Strategy performance (net of costs)

|                                  | ann_return   | ann_vol   |   sharpe |   sortino | max_drawdown   |   calmar |   skew |   sharpe_gross |   cost_drag_bps | ann_turnover   |   avg_exposure | pct_short   |
|:---------------------------------|:-------------|:----------|---------:|----------:|:---------------|---------:|-------:|---------------:|----------------:|:---------------|---------------:|:------------|
| Vol target + signal              | 3.6%         | 9.4%      |     0.25 |      0.36 | -33.5%         |     0.11 |   0.02 |           0.25 |               4 | 1.7x           |           1.44 | 0.0%        |
| Vol target + signal (long-short) | 3.8%         | 9.5%      |     0.27 |      0.38 | -31.7%         |     0.12 |   0.03 |           0.27 |               4 | 1.9x           |           1.43 | 0.4%        |
| Vol target only                  | 3.4%         | 9.5%      |     0.23 |      0.33 | -35.6%         |     0.1  |   0.02 |           0.24 |               3 | 1.6x           |           1.44 | 0.0%        |
| Signal only                      | 3.4%         | 6.8%      |     0.28 |      0.41 | -22.6%         |     0.15 |   0.14 |           0.28 |               0 | 0.1x           |           1    | 0.0%        |
| Buy & hold                       | 3.3%         | 6.9%      |     0.27 |      0.38 | -23.9%         |     0.14 |   0.14 |           0.27 |               0 | 0.0x           |           1    | 0.0%        |

`sharpe` is net of trading costs, `sharpe_gross` before them; `cost_drag_bps` is the annual trading-cost drag. Signal settings: EMA span=5, hold=1d, no-trade band=0.1.

## Regime breakdown (net of costs)

|                                                                 |   sharpe |   sharpe_gross | ann_return   | max_drawdown   | ann_turnover   |
|:----------------------------------------------------------------|---------:|---------------:|:-------------|:---------------|:---------------|
| ('2004-2007 pre-GFC', 'Vol target + signal')                    |     0.92 |           0.92 | 12.3%        | -6.4%          | 1.1x           |
| ('2004-2007 pre-GFC', 'Vol target + signal (long-short)')       |     0.92 |           0.92 | 12.3%        | -6.4%          | 1.1x           |
| ('2004-2007 pre-GFC', 'Vol target only')                        |     0.92 |           0.92 | 12.3%        | -6.4%          | 1.1x           |
| ('2004-2007 pre-GFC', 'Signal only')                            |     0.94 |           0.94 | 9.9%         | -3.9%          | 0.7x           |
| ('2004-2007 pre-GFC', 'Buy & hold')                             |     0.94 |           0.94 | 9.9%         | -3.9%          | 0.7x           |
| ('2008-2009 GFC', 'Vol target + signal')                        |     0.39 |           0.39 | 4.6%         | -12.3%         | 3.8x           |
| ('2008-2009 GFC', 'Vol target + signal (long-short)')           |     0.39 |           0.39 | 4.6%         | -12.3%         | 3.8x           |
| ('2008-2009 GFC', 'Vol target only')                            |     0.39 |           0.39 | 4.6%         | -12.3%         | 3.8x           |
| ('2008-2009 GFC', 'Signal only')                                |     0.47 |           0.47 | 4.9%         | -10.4%         | 0.0x           |
| ('2008-2009 GFC', 'Buy & hold')                                 |     0.47 |           0.47 | 4.9%         | -10.4%         | 0.0x           |
| ('2010-2019 post-GFC', 'Vol target + signal')                   |     0.65 |           0.65 | 5.9%         | -14.0%         | 0.6x           |
| ('2010-2019 post-GFC', 'Vol target + signal (long-short)')      |     0.65 |           0.65 | 5.9%         | -14.0%         | 0.6x           |
| ('2010-2019 post-GFC', 'Vol target only')                       |     0.65 |           0.65 | 5.9%         | -14.0%         | 0.6x           |
| ('2010-2019 post-GFC', 'Signal only')                           |     0.66 |           0.66 | 4.4%         | -9.1%          | 0.0x           |
| ('2010-2019 post-GFC', 'Buy & hold')                            |     0.66 |           0.66 | 4.4%         | -9.1%          | 0.0x           |
| ('2020-2026 Covid & after', 'Vol target + signal')              |    -0.39 |          -0.39 | -1.6%        | -33.5%         | 3.1x           |
| ('2020-2026 Covid & after', 'Vol target + signal (long-short)') |    -0.34 |          -0.34 | -1.2%        | -31.7%         | 3.5x           |
| ('2020-2026 Covid & after', 'Vol target only')                  |    -0.43 |          -0.43 | -2.1%        | -35.6%         | 2.7x           |
| ('2020-2026 Covid & after', 'Signal only')                      |    -0.33 |          -0.33 | 0.2%         | -22.6%         | 0.3x           |
| ('2020-2026 Covid & after', 'Buy & hold')                       |    -0.37 |          -0.37 | -0.2%        | -23.9%         | 0.0x           |

## HAR loadings, full sample, Newey-West t-stats (in-sample inference only)

|       |   coef |   hac_t |   p_value |
|:------|-------:|--------:|----------:|
| const | -0.59  |  -9.343 |         0 |
| har_d |  0.082 |   7.618 |         0 |
| har_w |  0.234 |   6.575 |         0 |
| har_m |  0.485 |  11.778 |         0 |
