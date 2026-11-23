# Results: SPY

Out-of-sample window: **2004-01-08 → 2026-11-20** (5,755 trading days). Refit every 21 days, expanding window, 756-day burn-in. Fills: next open. Costs: 1.5 bps per unit traded.

## Model A: 5-day forward realized volatility

|                       |   n_oos |   r2_oos_vs_mean |   rmse |   mae |   corr |   rmse_vol_pts |   qlike |   mz_alpha |   mz_beta |   mz_r2 |   mz_wald_p |   dm_stat |   dm_p_value |
|:----------------------|--------:|-----------------:|-------:|------:|-------:|---------------:|--------:|-----------:|----------:|--------:|------------:|----------:|-------------:|
| Ridge-HAR (Model A)   |    5750 |            0.707 |  0.291 | 0.221 |  0.829 |          6.501 |   0.225 |      0.018 |     1.016 |   0.687 |       0.104 |    -9.977 |            0 |
| HAR-RV OLS (baseline) |    5750 |            0.651 |  0.317 | 0.241 |  0.793 |          6.751 |   0.262 |     -0.107 |     0.955 |   0.628 |       0.015 |   nan     |          nan |

`r2_oos_vs_mean` is the Campbell-Thompson R² against the training-window mean; `dm_stat` < 0 means Ridge beats HAR-OLS on squared error.

## Model B: 5-day forward excess return

|                     |   n_oos |   r2_oos_vs_mean |   rmse |    mae |   corr |   hit_rate_sign |     ic |   ic_t |   view_share |   n_view |
|:--------------------|--------:|-----------------:|-------:|-------:|-------:|----------------:|-------:|-------:|-------------:|---------:|
| Lasso (Model B, 5d) |    5750 |           0.0012 | 0.0236 | 0.0163 | 0.0254 |          0.5642 | 0.0918 | 1.7352 |       0.3097 |     1781 |

## Strategy performance (net of costs)

|                                  | ann_return   | ann_vol   |   sharpe |   sortino | max_drawdown   |   calmar |   skew |   sharpe_gross |   cost_drag_bps | ann_turnover   |   avg_exposure | pct_short   |
|:---------------------------------|:-------------|:----------|---------:|----------:|:---------------|---------:|-------:|---------------:|----------------:|:---------------|---------------:|:------------|
| Vol target + signal              | 10.7%        | 16.9%     |     0.58 |      0.8  | -41.9%         |     0.26 |  -0.58 |           0.59 |              12 | 7.6x           |           1.24 | 0.0%        |
| Vol target + signal (long-short) | 10.7%        | 16.9%     |     0.58 |      0.8  | -41.9%         |     0.26 |  -0.58 |           0.59 |              12 | 7.6x           |           1.24 | 0.0%        |
| Vol target only                  | 10.7%        | 16.9%     |     0.58 |      0.8  | -41.9%         |     0.26 |  -0.58 |           0.59 |              12 | 7.6x           |           1.24 | 0.0%        |
| Signal only                      | 10.2%        | 18.6%     |     0.52 |      0.73 | -55.2%         |     0.19 |  -0.01 |           0.52 |               0 | 0.0x           |           1    | 0.0%        |
| Buy & hold                       | 10.2%        | 18.6%     |     0.52 |      0.73 | -55.2%         |     0.19 |  -0.01 |           0.52 |               0 | 0.0x           |           1    | 0.0%        |

`sharpe` is net of trading costs, `sharpe_gross` before them; `cost_drag_bps` is the annual trading-cost drag. Signal settings: EMA span=5, hold=1d, no-trade band=0.1.

## Regime breakdown (net of costs)

|                                                                 |   sharpe |   sharpe_gross | ann_return   | max_drawdown   | ann_turnover   |
|:----------------------------------------------------------------|---------:|---------------:|:-------------|:---------------|:---------------|
| ('2004-2007 pre-GFC', 'Vol target + signal')                    |     0.43 |           0.44 | 9.6%         | -12.3%         | 3.2x           |
| ('2004-2007 pre-GFC', 'Vol target + signal (long-short)')       |     0.43 |           0.44 | 9.6%         | -12.3%         | 3.2x           |
| ('2004-2007 pre-GFC', 'Vol target only')                        |     0.43 |           0.44 | 9.6%         | -12.3%         | 3.2x           |
| ('2004-2007 pre-GFC', 'Signal only')                            |     0.47 |           0.47 | 8.7%         | -9.9%          | 0.3x           |
| ('2004-2007 pre-GFC', 'Buy & hold')                             |     0.47 |           0.47 | 8.7%         | -9.9%          | 0.3x           |
| ('2008-2009 GFC', 'Vol target + signal')                        |    -0.38 |          -0.38 | -7.6%        | -35.4%         | 8.2x           |
| ('2008-2009 GFC', 'Vol target + signal (long-short)')           |    -0.38 |          -0.38 | -7.6%        | -35.4%         | 8.2x           |
| ('2008-2009 GFC', 'Vol target only')                            |    -0.38 |          -0.38 | -7.6%        | -35.4%         | 8.2x           |
| ('2008-2009 GFC', 'Signal only')                                |    -0.17 |          -0.17 | -10.6%       | -51.9%         | 0.0x           |
| ('2008-2009 GFC', 'Buy & hold')                                 |    -0.17 |          -0.17 | -10.6%       | -51.9%         | 0.0x           |
| ('2010-2019 post-GFC', 'Vol target + signal')                   |     0.88 |           0.89 | 14.7%        | -21.8%         | 6.9x           |
| ('2010-2019 post-GFC', 'Vol target + signal (long-short)')      |     0.88 |           0.89 | 14.7%        | -21.8%         | 6.9x           |
| ('2010-2019 post-GFC', 'Vol target only')                       |     0.88 |           0.89 | 14.7%        | -21.8%         | 6.9x           |
| ('2010-2019 post-GFC', 'Signal only')                           |     0.9  |           0.9  | 13.5%        | -19.3%         | 0.0x           |
| ('2010-2019 post-GFC', 'Buy & hold')                            |     0.9  |           0.9  | 13.5%        | -19.3%         | 0.0x           |
| ('2020-2026 Covid & after', 'Vol target + signal')              |     0.55 |           0.56 | 11.7%        | -26.6%         | 11.3x          |
| ('2020-2026 Covid & after', 'Vol target + signal (long-short)') |     0.55 |           0.56 | 11.7%        | -26.6%         | 11.3x          |
| ('2020-2026 Covid & after', 'Vol target only')                  |     0.55 |           0.56 | 11.7%        | -26.6%         | 11.3x          |
| ('2020-2026 Covid & after', 'Signal only')                      |     0.58 |           0.58 | 13.3%        | -33.7%         | 0.0x           |
| ('2020-2026 Covid & after', 'Buy & hold')                       |     0.58 |           0.58 | 13.3%        | -33.7%         | 0.0x           |

## HAR loadings, full sample, Newey-West t-stats (in-sample inference only)

|       |   coef |   hac_t |   p_value |
|:------|-------:|--------:|----------:|
| const | -0.288 |  -9.334 |         0 |
| har_d |  0.177 |  12.778 |         0 |
| har_w |  0.354 |  11.212 |         0 |
| har_m |  0.325 |  10.847 |         0 |
