# Results: GLD

Out-of-sample window: **2008-11-19 → 2026-11-20** (4,529 trading days). Refit every 21 days, expanding window, 756-day burn-in. Costs: 3.0 bps per unit traded.

## Model A: 5-day forward realized volatility

|                       |   n_oos |   r2_oos_vs_mean |   rmse |   mae |   corr |   rmse_vol_pts |   qlike |   mz_alpha |   mz_beta |   mz_r2 |   mz_wald_p |   dm_stat |   dm_p_value |
|:----------------------|--------:|-----------------:|-------:|------:|-------:|---------------:|--------:|-----------:|----------:|--------:|------------:|----------:|-------------:|
| Ridge-HAR (Model A)   |    4524 |            0.537 |  0.289 | 0.225 |  0.69  |          5.416 |    0.2  |     -0.139 |     0.941 |   0.477 |       0.001 |    -3.442 |        0.001 |
| HAR-RV OLS (baseline) |    4524 |            0.518 |  0.295 | 0.229 |  0.678 |          5.507 |    0.21 |     -0.203 |     0.91  |   0.46  |       0     |   nan     |      nan     |

`r2_oos_vs_mean` is the Campbell-Thompson R² against the training-window mean; `dm_stat` < 0 means Ridge beats HAR-OLS on squared error.

## Model B: 5-day forward excess return

|                     |   n_oos |   r2_oos_vs_mean |   rmse |    mae |    corr |   hit_rate_sign |     ic |   ic_t |   view_share |   n_view |
|:--------------------|--------:|-----------------:|-------:|-------:|--------:|----------------:|-------:|-------:|-------------:|---------:|
| Lasso (Model B, 5d) |    4524 |          -0.0017 | 0.0239 | 0.0178 | -0.0072 |          0.5418 | 0.0155 | 0.2238 |       0.2321 |     1050 |

## Strategy performance (net of costs)

|                                  | ann_return   | ann_vol   |   sharpe |   sortino | max_drawdown   |   calmar |   skew |   sharpe_gross |   cost_drag_bps | ann_turnover   |   avg_exposure | pct_short   |
|:---------------------------------|:-------------|:----------|---------:|----------:|:---------------|---------:|-------:|---------------:|----------------:|:---------------|---------------:|:------------|
| Vol target + signal              | 6.1%         | 12.5%     |     0.43 |      0.6  | -39.8%         |     0.15 |  -0.38 |           0.44 |              14 | 4.7x           |           0.81 | 0.0%        |
| Vol target + signal (long-short) | 4.9%         | 12.8%     |     0.33 |      0.46 | -42.5%         |     0.12 |  -0.33 |           0.34 |              18 | 5.9x           |           0.78 | 4.7%        |
| Vol target only                  | 7.2%         | 12.8%     |     0.5  |      0.7  | -41.0%         |     0.18 |  -0.38 |           0.51 |              11 | 3.7x           |           0.85 | 0.0%        |
| Signal only                      | 6.5%         | 16.6%     |     0.38 |      0.52 | -42.8%         |     0.15 |  -0.53 |           0.38 |               5 | 1.6x           |           0.95 | 0.0%        |
| Buy & hold                       | 8.7%         | 17.3%     |     0.49 |      0.68 | -45.6%         |     0.19 |  -0.43 |           0.49 |               0 | 0.0x           |           1    | 0.0%        |

`sharpe` is net of trading costs, `sharpe_gross` before them; `cost_drag_bps` is the annual trading-cost drag. Signal settings: EMA span=5, hold=1d, no-trade band=0.1.

## Regime breakdown (net of costs)

|                                                                 |   sharpe |   sharpe_gross | ann_return   | max_drawdown   | ann_turnover   |
|:----------------------------------------------------------------|---------:|---------------:|:-------------|:---------------|:---------------|
| ('2008-2009 GFC', 'Vol target + signal')                        |     0.99 |           1.03 | 8.4%         | -6.4%          | 11.4x          |
| ('2008-2009 GFC', 'Vol target + signal (long-short)')           |    -0.36 |          -0.3  | -4.6%        | -11.5%         | 22.5x          |
| ('2008-2009 GFC', 'Vol target only')                            |     1.76 |           1.76 | 21.6%        | -6.6%          | 1.6x           |
| ('2008-2009 GFC', 'Signal only')                                |     0.61 |           0.64 | 9.4%         | -14.9%         | 17.1x          |
| ('2008-2009 GFC', 'Buy & hold')                                 |     1.66 |           1.66 | 42.5%        | -12.9%         | 0.0x           |
| ('2010-2019 post-GFC', 'Vol target + signal')                   |     0.14 |           0.15 | 1.5%         | -39.8%         | 4.9x           |
| ('2010-2019 post-GFC', 'Vol target + signal (long-short)')      |     0.09 |           0.1  | 0.9%         | -42.5%         | 5.9x           |
| ('2010-2019 post-GFC', 'Vol target only')                       |     0.19 |           0.2  | 2.1%         | -41.0%         | 4.3x           |
| ('2010-2019 post-GFC', 'Signal only')                           |     0.18 |           0.18 | 2.2%         | -42.8%         | 1.0x           |
| ('2010-2019 post-GFC', 'Buy & hold')                            |     0.23 |           0.23 | 2.9%         | -45.6%         | 0.0x           |
| ('2020-2026 Covid & after', 'Vol target + signal')              |     0.75 |           0.76 | 12.8%        | -19.7%         | 3.2x           |
| ('2020-2026 Covid & after', 'Vol target + signal (long-short)') |     0.75 |           0.76 | 12.8%        | -19.7%         | 3.2x           |
| ('2020-2026 Covid & after', 'Vol target only')                  |     0.75 |           0.76 | 12.8%        | -19.7%         | 3.2x           |
| ('2020-2026 Covid & after', 'Signal only')                      |     0.57 |           0.57 | 12.6%        | -34.9%         | 0.0x           |
| ('2020-2026 Covid & after', 'Buy & hold')                       |     0.57 |           0.57 | 12.6%        | -34.9%         | 0.0x           |

## HAR loadings, full sample, Newey-West t-stats (in-sample inference only)

|       |   coef |   hac_t |   p_value |
|:------|-------:|--------:|----------:|
| const | -0.342 |  -8.194 |         0 |
| har_d |  0.036 |   3.729 |         0 |
| har_w |  0.184 |   6.015 |         0 |
| har_m |  0.613 |  16.885 |         0 |
