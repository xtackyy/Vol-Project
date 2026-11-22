# Results: TLT

Out-of-sample window: **2006-07-31 → 2026-11-20** (5,111 trading days). Refit every 21 days, expanding window, 756-day burn-in. Costs: 2.0 bps per unit traded.

## Model A: 5-day forward realized volatility

|                       |   n_oos |   r2_oos_vs_mean |   rmse |   mae |   corr |   rmse_vol_pts |   qlike |   mz_alpha |   mz_beta |   mz_r2 |   mz_wald_p |   dm_stat |   dm_p_value |
|:----------------------|--------:|-----------------:|-------:|------:|-------:|---------------:|--------:|-----------:|----------:|--------:|------------:|----------:|-------------:|
| Ridge-HAR (Model A)   |    5106 |            0.568 |  0.265 | 0.204 |  0.724 |          4.68  |   0.188 |      0.046 |     1.006 |   0.524 |       0     |    -2.512 |        0.012 |
| HAR-RV OLS (baseline) |    5106 |            0.55  |  0.27  | 0.207 |  0.707 |          4.652 |   0.192 |     -0.089 |     0.95  |   0.5   |       0.007 |   nan     |      nan     |

`r2_oos_vs_mean` is the Campbell-Thompson R² against the training-window mean; `dm_stat` < 0 means Ridge beats HAR-OLS on squared error.

## Model B: 5-day forward excess return

|                     |   n_oos |   r2_oos_vs_mean |   rmse |    mae |    corr |   hit_rate_sign |      ic |    ic_t |   view_share |   n_view |
|:--------------------|--------:|-----------------:|-------:|-------:|--------:|----------------:|--------:|--------:|-------------:|---------:|
| Lasso (Model B, 5d) |    5106 |          -0.0005 | 0.0196 | 0.0148 | -0.0318 |          0.5212 | -0.1057 | -1.2984 |       0.1481 |      756 |

## Strategy performance (net of costs)

|                                  | ann_return   | ann_vol   |   sharpe |   sortino | max_drawdown   |   calmar |   skew |   sharpe_gross |   cost_drag_bps | ann_turnover   |   avg_exposure | pct_short   |
|:---------------------------------|:-------------|:----------|---------:|----------:|:---------------|---------:|-------:|---------------:|----------------:|:---------------|---------------:|:------------|
| Vol target + signal              | 3.8%         | 11.3%     |     0.24 |      0.34 | -33.4%         |     0.11 |  -0.04 |           0.25 |              11 | 5.5x           |           0.84 | 0.0%        |
| Vol target + signal (long-short) | 3.9%         | 11.8%     |     0.24 |      0.34 | -32.2%         |     0.12 |  -0.03 |           0.26 |              16 | 7.8x           |           0.78 | 8.9%        |
| Vol target only                  | 3.5%         | 11.9%     |     0.21 |      0.3  | -37.1%         |     0.09 |  -0.04 |           0.22 |               8 | 3.8x           |           0.91 | 0.0%        |
| Signal only                      | 3.2%         | 14.0%     |     0.18 |      0.25 | -43.3%         |     0.07 |   0.09 |           0.18 |               6 | 2.8x           |           0.91 | 0.0%        |
| Buy & hold                       | 3.0%         | 14.9%     |     0.16 |      0.23 | -48.4%         |     0.06 |   0.08 |           0.16 |               0 | 0.0x           |           1    | 0.0%        |

`sharpe` is net of trading costs, `sharpe_gross` before them; `cost_drag_bps` is the annual trading-cost drag. Signal settings: EMA span=5, hold=1d, no-trade band=0.1.

## Regime breakdown (net of costs)

|                                                                 |   sharpe |   sharpe_gross | ann_return   | max_drawdown   | ann_turnover   |
|:----------------------------------------------------------------|---------:|---------------:|:-------------|:---------------|:---------------|
| ('2004-2007 pre-GFC', 'Vol target + signal')                    |     0.62 |           0.63 | 11.8%        | -12.9%         | 1.0x           |
| ('2004-2007 pre-GFC', 'Vol target + signal (long-short)')       |     0.62 |           0.63 | 11.8%        | -12.9%         | 1.0x           |
| ('2004-2007 pre-GFC', 'Vol target only')                        |     0.62 |           0.63 | 11.8%        | -12.9%         | 1.0x           |
| ('2004-2007 pre-GFC', 'Signal only')                            |     0.72 |           0.73 | 11.2%        | -8.0%          | 0.0x           |
| ('2004-2007 pre-GFC', 'Buy & hold')                             |     0.72 |           0.73 | 11.2%        | -8.0%          | 0.0x           |
| ('2008-2009 GFC', 'Vol target + signal')                        |     0.15 |           0.15 | 1.8%         | -16.4%         | 1.3x           |
| ('2008-2009 GFC', 'Vol target + signal (long-short)')           |     0.15 |           0.15 | 1.8%         | -16.4%         | 1.3x           |
| ('2008-2009 GFC', 'Vol target only')                            |     0.15 |           0.15 | 1.8%         | -16.4%         | 1.3x           |
| ('2008-2009 GFC', 'Signal only')                                |     0.18 |           0.18 | 2.3%         | -26.6%         | 0.0x           |
| ('2008-2009 GFC', 'Buy & hold')                                 |     0.18 |           0.18 | 2.3%         | -26.6%         | 0.0x           |
| ('2010-2019 post-GFC', 'Vol target + signal')                   |     0.6  |           0.61 | 7.2%         | -17.8%         | 4.3x           |
| ('2010-2019 post-GFC', 'Vol target + signal (long-short)')      |     0.6  |           0.61 | 7.2%         | -17.8%         | 4.3x           |
| ('2010-2019 post-GFC', 'Vol target only')                       |     0.6  |           0.61 | 7.2%         | -17.8%         | 4.3x           |
| ('2010-2019 post-GFC', 'Signal only')                           |     0.54 |           0.54 | 7.2%         | -20.7%         | 0.0x           |
| ('2010-2019 post-GFC', 'Buy & hold')                            |     0.54 |           0.54 | 7.2%         | -20.7%         | 0.0x           |
| ('2020-2026 Covid & after', 'Vol target + signal')              |    -0.41 |          -0.39 | -1.9%        | -33.4%         | 9.3x           |
| ('2020-2026 Covid & after', 'Vol target + signal (long-short)') |    -0.32 |          -0.29 | -1.7%        | -32.2%         | 16.1x          |
| ('2020-2026 Covid & after', 'Vol target only')                  |    -0.4  |          -0.39 | -2.7%        | -37.1%         | 4.5x           |
| ('2020-2026 Covid & after', 'Signal only')                      |    -0.41 |          -0.4  | -3.8%        | -43.3%         | 8.1x           |
| ('2020-2026 Covid & after', 'Buy & hold')                       |    -0.36 |          -0.36 | -4.3%        | -48.4%         | 0.0x           |

## HAR loadings, full sample, Newey-West t-stats (in-sample inference only)

|       |   coef |   hac_t |   p_value |
|:------|-------:|--------:|----------:|
| const | -0.401 |  -8.208 |         0 |
| har_d |  0.081 |   7.958 |         0 |
| har_w |  0.218 |   6.078 |         0 |
| har_m |  0.521 |  12.859 |         0 |
