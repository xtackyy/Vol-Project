# Results: EEM

Out-of-sample window: **2007-04-17 → 2026-11-23** (4,934 trading days). Refit every 21 days, expanding window, 756-day burn-in. Fills: next open. Costs: 3.0 bps per unit traded.

## Model A: 5-day forward realized volatility

|                       |   n_oos |   r2_oos_vs_mean |   rmse |   mae |   corr |   rmse_vol_pts |   qlike |   mz_alpha |   mz_beta |   mz_r2 |   mz_wald_p |   dm_stat |   dm_p_value |
|:----------------------|--------:|-----------------:|-------:|------:|-------:|---------------:|--------:|-----------:|----------:|--------:|------------:|----------:|-------------:|
| Ridge-HAR (Model A)   |    4929 |            0.599 |  0.317 | 0.244 |  0.773 |          9.236 |   0.252 |     -0.021 |     1.004 |   0.597 |       0.005 |    -6.375 |            0 |
| HAR-RV OLS (baseline) |    4929 |            0.562 |  0.331 | 0.255 |  0.746 |          9.74  |   0.282 |     -0.05  |     0.977 |   0.557 |       0.321 |   nan     |          nan |

`r2_oos_vs_mean` is the Campbell-Thompson R² against the training-window mean; `dm_stat` < 0 means Ridge beats HAR-OLS on squared error.

## Model B: 5-day forward excess return

|                     |   n_oos |   r2_oos_vs_mean |   rmse |    mae |   corr |   hit_rate_sign |    ic |   ic_t |   view_share |   n_view |
|:--------------------|--------:|-----------------:|-------:|-------:|-------:|----------------:|------:|-------:|-------------:|---------:|
| Lasso (Model B, 5d) |    4929 |           0.0012 | 0.0345 | 0.0243 | 0.0127 |          0.5372 | 0.073 | 1.2319 |       0.2897 |     1428 |

## Strategy performance (net of costs)

|                                  | ann_return   | ann_vol   |   sharpe |   sortino | max_drawdown   |   calmar |   skew |   sharpe_gross |   cost_drag_bps | ann_turnover   |   avg_exposure | pct_short   |
|:---------------------------------|:-------------|:----------|---------:|----------:|:---------------|---------:|-------:|---------------:|----------------:|:---------------|---------------:|:------------|
| Vol target + signal              | 2.4%         | 11.3%     |     0.14 |      0.19 | -30.3%         |     0.08 |  -0.27 |           0.15 |              18 | 6.1x           |           0.56 | 0.0%        |
| Vol target + signal (long-short) | 2.4%         | 11.4%     |     0.13 |      0.18 | -31.3%         |     0.08 |  -0.25 |           0.15 |              23 | 7.5x           |           0.55 | 2.0%        |
| Vol target only                  | 2.5%         | 11.4%     |     0.14 |      0.19 | -29.0%         |     0.08 |  -0.27 |           0.15 |              15 | 4.8x           |           0.58 | 0.0%        |
| Signal only                      | 4.0%         | 27.9%     |     0.22 |      0.32 | -66.4%         |     0.06 |   0.59 |           0.23 |               8 | 2.5x           |           0.98 | 0.0%        |
| Buy & hold                       | 3.9%         | 28.1%     |     0.22 |      0.32 | -66.4%         |     0.06 |   0.55 |           0.22 |               0 | 0.0x           |           1    | 0.0%        |

`sharpe` is net of trading costs, `sharpe_gross` before them; `cost_drag_bps` is the annual trading-cost drag. Signal settings: EMA span=5, hold=1d, no-trade band=0.1.

## Regime breakdown (net of costs)

|                                                                 |   sharpe |   sharpe_gross | ann_return   | max_drawdown   | ann_turnover   |
|:----------------------------------------------------------------|---------:|---------------:|:-------------|:---------------|:---------------|
| ('2004-2007 pre-GFC', 'Vol target + signal')                    |     0.91 |           0.92 | 17.4%        | -8.3%          | 4.8x           |
| ('2004-2007 pre-GFC', 'Vol target + signal (long-short)')       |     0.91 |           0.92 | 17.4%        | -8.3%          | 4.8x           |
| ('2004-2007 pre-GFC', 'Vol target only')                        |     0.91 |           0.92 | 17.4%        | -8.3%          | 4.8x           |
| ('2004-2007 pre-GFC', 'Signal only')                            |     0.93 |           0.93 | 35.5%        | -17.7%         | 1.4x           |
| ('2004-2007 pre-GFC', 'Buy & hold')                             |     0.93 |           0.93 | 35.5%        | -17.7%         | 1.4x           |
| ('2008-2009 GFC', 'Vol target + signal')                        |    -0.07 |          -0.06 | -0.5%        | -18.1%         | 2.4x           |
| ('2008-2009 GFC', 'Vol target + signal (long-short)')           |    -0.1  |          -0.09 | -0.9%        | -18.7%         | 2.7x           |
| ('2008-2009 GFC', 'Vol target only')                            |    -0.1  |          -0.09 | -0.8%        | -19.2%         | 2.2x           |
| ('2008-2009 GFC', 'Signal only')                                |     0.12 |           0.12 | -7.9%        | -64.3%         | 2.0x           |
| ('2008-2009 GFC', 'Buy & hold')                                 |     0.14 |           0.14 | -7.1%        | -64.3%         | 0.0x           |
| ('2010-2019 post-GFC', 'Vol target + signal')                   |     0.1  |           0.12 | 1.1%         | -30.3%         | 7.3x           |
| ('2010-2019 post-GFC', 'Vol target + signal (long-short)')      |     0.1  |           0.13 | 1.0%         | -31.3%         | 10.1x          |
| ('2010-2019 post-GFC', 'Vol target only')                       |     0.11 |           0.12 | 1.2%         | -29.0%         | 4.9x           |
| ('2010-2019 post-GFC', 'Signal only')                           |     0.23 |           0.24 | 3.2%         | -36.1%         | 4.4x           |
| ('2010-2019 post-GFC', 'Buy & hold')                            |     0.22 |           0.22 | 2.9%         | -37.5%         | 0.0x           |
| ('2020-2026 Covid & after', 'Vol target + signal')              |     0.14 |           0.15 | 3.9%         | -26.9%         | 5.6x           |
| ('2020-2026 Covid & after', 'Vol target + signal (long-short)') |     0.14 |           0.15 | 3.9%         | -26.9%         | 5.6x           |
| ('2020-2026 Covid & after', 'Vol target only')                  |     0.14 |           0.15 | 3.9%         | -26.9%         | 5.6x           |
| ('2020-2026 Covid & after', 'Signal only')                      |     0.24 |           0.24 | 5.9%         | -39.8%         | 0.0x           |
| ('2020-2026 Covid & after', 'Buy & hold')                       |     0.24 |           0.24 | 5.9%         | -39.8%         | 0.0x           |

## HAR loadings, full sample, Newey-West t-stats (in-sample inference only)

|       |   coef |   hac_t |   p_value |
|:------|-------:|--------:|----------:|
| const | -0.32  |  -9.225 |         0 |
| har_d |  0.121 |   9.84  |         0 |
| har_w |  0.295 |   9.41  |         0 |
| har_m |  0.399 |  12.131 |         0 |
