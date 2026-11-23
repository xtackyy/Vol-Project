# Results: EFA

Out-of-sample window: **2005-09-01 → 2026-11-23** (5,340 trading days). Refit every 21 days, expanding window, 756-day burn-in. Fills: next open. Costs: 2.5 bps per unit traded.

## Model A: 5-day forward realized volatility

|                       |   n_oos |   r2_oos_vs_mean |   rmse |   mae |   corr |   rmse_vol_pts |   qlike |   mz_alpha |   mz_beta |   mz_r2 |   mz_wald_p |   dm_stat |   dm_p_value |
|:----------------------|--------:|-----------------:|-------:|------:|-------:|---------------:|--------:|-----------:|----------:|--------:|------------:|----------:|-------------:|
| Ridge-HAR (Model A)   |    5335 |            0.608 |  0.32  | 0.245 |  0.779 |          7.347 |   0.26  |      0.047 |     1.037 |   0.607 |       0.005 |    -8.509 |            0 |
| HAR-RV OLS (baseline) |    5335 |            0.548 |  0.344 | 0.264 |  0.738 |          7.964 |   0.306 |     -0.07  |     0.97  |   0.545 |       0.184 |   nan     |          nan |

`r2_oos_vs_mean` is the Campbell-Thompson R² against the training-window mean; `dm_stat` < 0 means Ridge beats HAR-OLS on squared error.

## Model B: 5-day forward excess return

|                     |   n_oos |   r2_oos_vs_mean |   rmse |    mae |    corr |   hit_rate_sign |    ic |   ic_t |   view_share |   n_view |
|:--------------------|--------:|-----------------:|-------:|-------:|--------:|----------------:|------:|-------:|-------------:|---------:|
| Lasso (Model B, 5d) |    5335 |           0.0001 | 0.0271 | 0.0188 | -0.0122 |          0.5567 | 0.038 | 0.9974 |       0.6457 |     3445 |

## Strategy performance (net of costs)

|                                  | ann_return   | ann_vol   |   sharpe |   sortino | max_drawdown   |   calmar |   skew |   sharpe_gross |   cost_drag_bps | ann_turnover   |   avg_exposure | pct_short   |
|:---------------------------------|:-------------|:----------|---------:|----------:|:---------------|---------:|-------:|---------------:|----------------:|:---------------|---------------:|:------------|
| Vol target + signal              | 3.4%         | 11.2%     |     0.2  |      0.27 | -31.4%         |     0.11 |  -0.48 |           0.22 |              23 | 9.2x           |           0.72 | 0.0%        |
| Vol target + signal (long-short) | 3.2%         | 11.4%     |     0.18 |      0.24 | -31.0%         |     0.1  |  -0.42 |           0.21 |              33 | 13.2x          |           0.68 | 4.8%        |
| Vol target only                  | 3.6%         | 11.4%     |     0.21 |      0.29 | -31.5%         |     0.11 |  -0.49 |           0.22 |              14 | 5.7x           |           0.75 | 0.0%        |
| Signal only                      | 6.0%         | 20.8%     |     0.3  |      0.42 | -60.5%         |     0.1  |  -0    |           0.31 |              13 | 5.3x           |           0.95 | 0.0%        |
| Buy & hold                       | 5.7%         | 21.2%     |     0.29 |      0.4  | -61.0%         |     0.09 |  -0.04 |           0.29 |               0 | 0.0x           |           1    | 0.0%        |

`sharpe` is net of trading costs, `sharpe_gross` before them; `cost_drag_bps` is the annual trading-cost drag. Signal settings: EMA span=5, hold=1d, no-trade band=0.1.

## Regime breakdown (net of costs)

|                                                                 |   sharpe |   sharpe_gross | ann_return   | max_drawdown   | ann_turnover   |
|:----------------------------------------------------------------|---------:|---------------:|:-------------|:---------------|:---------------|
| ('2004-2007 pre-GFC', 'Vol target + signal')                    |     0.87 |           0.87 | 15.8%        | -12.0%         | 4.0x           |
| ('2004-2007 pre-GFC', 'Vol target + signal (long-short)')       |     0.87 |           0.87 | 15.8%        | -12.0%         | 4.0x           |
| ('2004-2007 pre-GFC', 'Vol target only')                        |     0.87 |           0.87 | 15.8%        | -12.0%         | 4.0x           |
| ('2004-2007 pre-GFC', 'Signal only')                            |     0.84 |           0.84 | 18.1%        | -15.8%         | 0.4x           |
| ('2004-2007 pre-GFC', 'Buy & hold')                             |     0.84 |           0.84 | 18.1%        | -15.8%         | 0.4x           |
| ('2008-2009 GFC', 'Vol target + signal')                        |    -0.66 |          -0.66 | -7.4%        | -28.1%         | 3.4x           |
| ('2008-2009 GFC', 'Vol target + signal (long-short)')           |    -0.63 |          -0.62 | -7.1%        | -27.7%         | 4.3x           |
| ('2008-2009 GFC', 'Vol target only')                            |    -0.64 |          -0.64 | -7.2%        | -28.3%         | 2.4x           |
| ('2008-2009 GFC', 'Signal only')                                |    -0.17 |          -0.17 | -12.8%       | -57.7%         | 3.0x           |
| ('2008-2009 GFC', 'Buy & hold')                                 |    -0.18 |          -0.18 | -13.4%       | -58.3%         | 0.0x           |
| ('2010-2019 post-GFC', 'Vol target + signal')                   |     0.23 |           0.26 | 2.5%         | -19.6%         | 12.7x          |
| ('2010-2019 post-GFC', 'Vol target + signal (long-short)')      |     0.18 |           0.23 | 2.0%         | -21.8%         | 20.6x          |
| ('2010-2019 post-GFC', 'Vol target only')                       |     0.28 |           0.29 | 3.0%         | -21.6%         | 5.8x           |
| ('2010-2019 post-GFC', 'Signal only')                           |     0.37 |           0.38 | 5.6%         | -25.7%         | 9.4x           |
| ('2010-2019 post-GFC', 'Buy & hold')                            |     0.36 |           0.36 | 5.4%         | -25.9%         | 0.0x           |
| ('2020-2026 Covid & after', 'Vol target + signal')              |     0.15 |           0.17 | 4.0%         | -23.0%         | 7.7x           |
| ('2020-2026 Covid & after', 'Vol target + signal (long-short)') |     0.16 |           0.18 | 4.1%         | -23.0%         | 8.5x           |
| ('2020-2026 Covid & after', 'Vol target only')                  |     0.13 |           0.14 | 3.7%         | -23.0%         | 7.2x           |
| ('2020-2026 Covid & after', 'Signal only')                      |     0.39 |           0.39 | 8.7%         | -33.9%         | 1.7x           |
| ('2020-2026 Covid & after', 'Buy & hold')                       |     0.36 |           0.36 | 8.3%         | -33.9%         | 0.0x           |

## HAR loadings, full sample, Newey-West t-stats (in-sample inference only)

|       |   coef |   hac_t |   p_value |
|:------|-------:|--------:|----------:|
| const | -0.362 |  -9.416 |         0 |
| har_d |  0.128 |  10.268 |         0 |
| har_w |  0.272 |   8.25  |         0 |
| har_m |  0.417 |  12.136 |         0 |
