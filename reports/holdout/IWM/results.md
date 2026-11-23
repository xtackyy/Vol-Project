# Results: IWM

Out-of-sample window: **2004-06-03 → 2026-11-23** (5,655 trading days). Refit every 21 days, expanding window, 756-day burn-in. Fills: next open. Costs: 2.0 bps per unit traded.

## Model A: 5-day forward realized volatility

|                       |   n_oos |   r2_oos_vs_mean |   rmse |   mae |   corr |   rmse_vol_pts |   qlike |   mz_alpha |   mz_beta |   mz_r2 |   mz_wald_p |   dm_stat |   dm_p_value |
|:----------------------|--------:|-----------------:|-------:|------:|-------:|---------------:|--------:|-----------:|----------:|--------:|------------:|----------:|-------------:|
| Ridge-HAR (Model A)   |    5650 |            0.662 |  0.255 | 0.19  |  0.813 |          7.42  |   0.173 |      0.117 |     1.063 |   0.661 |       0.001 |    -7.707 |            0 |
| HAR-RV OLS (baseline) |    5650 |            0.618 |  0.271 | 0.202 |  0.784 |          7.784 |   0.188 |      0.004 |     1.005 |   0.614 |       0.778 |   nan     |          nan |

`r2_oos_vs_mean` is the Campbell-Thompson R² against the training-window mean; `dm_stat` < 0 means Ridge beats HAR-OLS on squared error.

## Model B: 5-day forward excess return

|                     |   n_oos |   r2_oos_vs_mean |   rmse |    mae |    corr |   hit_rate_sign |    ic |   ic_t |   view_share |   n_view |
|:--------------------|--------:|-----------------:|-------:|-------:|--------:|----------------:|------:|-------:|-------------:|---------:|
| Lasso (Model B, 5d) |    5650 |          -0.0009 | 0.0316 | 0.0227 | -0.0198 |           0.543 | 0.061 | 1.3167 |       0.4127 |     2332 |

## Strategy performance (net of costs)

|                                  | ann_return   | ann_vol   |   sharpe |   sortino | max_drawdown   |   calmar |   skew |   sharpe_gross |   cost_drag_bps | ann_turnover   |   avg_exposure | pct_short   |
|:---------------------------------|:-------------|:----------|---------:|----------:|:---------------|---------:|-------:|---------------:|----------------:|:---------------|---------------:|:------------|
| Vol target + signal              | 5.1%         | 11.4%     |     0.34 |      0.47 | -25.8%         |     0.2  |  -0.28 |           0.35 |              13 | 6.6x           |           0.58 | 0.0%        |
| Vol target + signal (long-short) | 5.4%         | 11.8%     |     0.35 |      0.49 | -25.8%         |     0.21 |  -0.23 |           0.37 |              21 | 10.7x          |           0.53 | 7.2%        |
| Vol target only                  | 4.8%         | 11.7%     |     0.31 |      0.43 | -25.8%         |     0.19 |  -0.27 |           0.32 |               7 | 3.2x           |           0.63 | 0.0%        |
| Signal only                      | 9.0%         | 23.3%     |     0.41 |      0.58 | -58.6%         |     0.15 |  -0.33 |           0.42 |              11 | 5.6x           |           0.93 | 0.0%        |
| Buy & hold                       | 8.5%         | 23.8%     |     0.39 |      0.55 | -58.6%         |     0.15 |  -0.32 |           0.39 |               0 | 0.0x           |           1    | 0.0%        |

`sharpe` is net of trading costs, `sharpe_gross` before them; `cost_drag_bps` is the annual trading-cost drag. Signal settings: EMA span=5, hold=1d, no-trade band=0.1.

## Regime breakdown (net of costs)

|                                                                 |   sharpe |   sharpe_gross | ann_return   | max_drawdown   | ann_turnover   |
|:----------------------------------------------------------------|---------:|---------------:|:-------------|:---------------|:---------------|
| ('2004-2007 pre-GFC', 'Vol target + signal')                    |     0.34 |           0.35 | 7.4%         | -10.3%         | 2.1x           |
| ('2004-2007 pre-GFC', 'Vol target + signal (long-short)')       |     0.34 |           0.35 | 7.4%         | -10.3%         | 2.1x           |
| ('2004-2007 pre-GFC', 'Vol target only')                        |     0.34 |           0.35 | 7.4%         | -10.3%         | 2.1x           |
| ('2004-2007 pre-GFC', 'Signal only')                            |     0.41 |           0.41 | 9.9%         | -14.1%         | 0.3x           |
| ('2004-2007 pre-GFC', 'Buy & hold')                             |     0.41 |           0.41 | 9.9%         | -14.1%         | 0.3x           |
| ('2008-2009 GFC', 'Vol target + signal')                        |    -0.3  |          -0.3  | -3.6%        | -21.3%         | 1.5x           |
| ('2008-2009 GFC', 'Vol target + signal (long-short)')           |    -0.3  |          -0.3  | -3.6%        | -21.3%         | 1.5x           |
| ('2008-2009 GFC', 'Vol target only')                            |    -0.3  |          -0.3  | -3.6%        | -21.3%         | 1.5x           |
| ('2008-2009 GFC', 'Signal only')                                |    -0.02 |          -0.02 | -8.0%        | -54.3%         | 0.0x           |
| ('2008-2009 GFC', 'Buy & hold')                                 |    -0.02 |          -0.02 | -8.0%        | -54.3%         | 0.0x           |
| ('2010-2019 post-GFC', 'Vol target + signal')                   |     0.51 |           0.53 | 5.6%         | -16.5%         | 8.4x           |
| ('2010-2019 post-GFC', 'Vol target + signal (long-short)')      |     0.44 |           0.46 | 4.9%         | -15.4%         | 13.8x          |
| ('2010-2019 post-GFC', 'Vol target only')                       |     0.55 |           0.56 | 6.3%         | -18.5%         | 4.1x           |
| ('2010-2019 post-GFC', 'Signal only')                           |     0.62 |           0.63 | 11.0%        | -28.9%         | 6.4x           |
| ('2010-2019 post-GFC', 'Buy & hold')                            |     0.65 |           0.65 | 11.8%        | -28.9%         | 0.0x           |
| ('2020-2026 Covid & after', 'Vol target + signal')              |     0.3  |           0.32 | 5.8%         | -18.2%         | 7.8x           |
| ('2020-2026 Covid & after', 'Vol target + signal (long-short)') |     0.43 |           0.45 | 7.6%         | -16.3%         | 13.5x          |
| ('2020-2026 Covid & after', 'Vol target only')                  |     0.15 |           0.16 | 4.0%         | -20.3%         | 3.2x           |
| ('2020-2026 Covid & after', 'Signal only')                      |     0.44 |           0.44 | 11.2%        | -41.1%         | 9.0x           |
| ('2020-2026 Covid & after', 'Buy & hold')                       |     0.33 |           0.33 | 8.4%         | -41.1%         | 0.0x           |

## HAR loadings, full sample, Newey-West t-stats (in-sample inference only)

|       |   coef |   hac_t |   p_value |
|:------|-------:|--------:|----------:|
| const | -0.274 |  -9.02  |         0 |
| har_d |  0.148 |  11.312 |         0 |
| har_w |  0.314 |   9.84  |         0 |
| har_m |  0.377 |  12.231 |         0 |
