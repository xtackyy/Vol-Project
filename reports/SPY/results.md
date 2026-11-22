# Results: SPY

Out-of-sample window: **2004-01-08 → 2026-11-20** (5,755 trading days). Refit every 21 days, expanding window, 756-day burn-in. Costs: 1.5 bps per unit traded.

## Model A: 5-day forward realized volatility

|                       |   n_oos |   r2_oos_vs_mean |   rmse |   mae |   corr |   rmse_vol_pts |   qlike |   mz_alpha |   mz_beta |   mz_r2 |   mz_wald_p |   dm_stat |   dm_p_value |
|:----------------------|--------:|-----------------:|-------:|------:|-------:|---------------:|--------:|-----------:|----------:|--------:|------------:|----------:|-------------:|
| Ridge-HAR (Model A)   |    5750 |            0.707 |  0.291 | 0.221 |  0.829 |          6.501 |   0.225 |      0.018 |     1.016 |   0.687 |       0.104 |    -9.977 |            0 |
| HAR-RV OLS (baseline) |    5750 |            0.651 |  0.317 | 0.241 |  0.793 |          6.751 |   0.262 |     -0.107 |     0.955 |   0.628 |       0.015 |   nan     |          nan |

`r2_oos_vs_mean` is the Campbell-Thompson R² against the training-window mean; `dm_stat` < 0 means Ridge beats HAR-OLS on squared error.

## Model B: 5-day forward excess return

|                     |   n_oos |   r2_oos_vs_mean |   rmse |    mae |   corr |   hit_rate_sign |     ic |   ic_t |   view_share |   n_view |
|:--------------------|--------:|-----------------:|-------:|-------:|-------:|----------------:|-------:|-------:|-------------:|---------:|
| Lasso (Model B, 5d) |    5750 |           0.0012 | 0.0236 | 0.0163 | 0.0251 |          0.5643 | 0.0867 | 1.7416 |       0.3499 |     2012 |

## Strategy performance (net of costs)

|                                  | ann_return   | ann_vol   |   sharpe |   sortino | max_drawdown   |   calmar |   skew |   sharpe_gross |   cost_drag_bps | ann_turnover   |   avg_exposure | pct_short   |
|:---------------------------------|:-------------|:----------|---------:|----------:|:---------------|---------:|-------:|---------------:|----------------:|:---------------|---------------:|:------------|
| Vol target + signal              | 8.4%         | 12.5%     |     0.57 |      0.77 | -31.1%         |     0.27 |  -0.58 |           0.58 |              13 | 8.8x           |           0.97 | 0.0%        |
| Vol target + signal (long-short) | 8.4%         | 12.5%     |     0.57 |      0.77 | -31.1%         |     0.27 |  -0.58 |           0.58 |              13 | 8.8x           |           0.97 | 0.2%        |
| Vol target only                  | 8.4%         | 12.5%     |     0.57 |      0.77 | -31.1%         |     0.27 |  -0.58 |           0.58 |              13 | 8.7x           |           0.97 | 0.0%        |
| Signal only                      | 10.2%        | 18.6%     |     0.52 |      0.73 | -55.2%         |     0.18 |  -0.01 |           0.52 |               0 | 0.0x           |           1    | 0.0%        |
| Buy & hold                       | 10.2%        | 18.6%     |     0.52 |      0.73 | -55.2%         |     0.19 |  -0.01 |           0.52 |               0 | 0.0x           |           1    | 0.0%        |

`sharpe` is net of trading costs, `sharpe_gross` before them; `cost_drag_bps` is the annual trading-cost drag. Signal settings: EMA span=5, hold=1d, no-trade band=0.1.

## Regime breakdown (net of costs)

|                                                                 |   sharpe |   sharpe_gross | ann_return   | max_drawdown   | ann_turnover   |
|:----------------------------------------------------------------|---------:|---------------:|:-------------|:---------------|:---------------|
| ('2004-2007 pre-GFC', 'Vol target + signal')                    |     0.31 |           0.32 | 6.7%         | -9.0%          | 8.2x           |
| ('2004-2007 pre-GFC', 'Vol target + signal (long-short)')       |     0.31 |           0.32 | 6.7%         | -9.0%          | 8.5x           |
| ('2004-2007 pre-GFC', 'Vol target only')                        |     0.31 |           0.32 | 6.7%         | -9.0%          | 8.1x           |
| ('2004-2007 pre-GFC', 'Signal only')                            |     0.46 |           0.46 | 8.6%         | -9.9%          | 0.3x           |
| ('2004-2007 pre-GFC', 'Buy & hold')                             |     0.46 |           0.46 | 8.6%         | -9.9%          | 0.0x           |
| ('2008-2009 GFC', 'Vol target + signal')                        |    -0.38 |          -0.38 | -4.7%        | -25.7%         | 3.7x           |
| ('2008-2009 GFC', 'Vol target + signal (long-short)')           |    -0.38 |          -0.38 | -4.7%        | -25.7%         | 3.7x           |
| ('2008-2009 GFC', 'Vol target only')                            |    -0.38 |          -0.38 | -4.7%        | -25.7%         | 3.7x           |
| ('2008-2009 GFC', 'Signal only')                                |    -0.17 |          -0.17 | -10.6%       | -51.9%         | 0.0x           |
| ('2008-2009 GFC', 'Buy & hold')                                 |    -0.17 |          -0.17 | -10.6%       | -51.9%         | 0.0x           |
| ('2010-2019 post-GFC', 'Vol target + signal')                   |     0.89 |           0.9  | 11.4%        | -15.9%         | 8.8x           |
| ('2010-2019 post-GFC', 'Vol target + signal (long-short)')      |     0.89 |           0.9  | 11.4%        | -15.9%         | 8.8x           |
| ('2010-2019 post-GFC', 'Vol target only')                       |     0.89 |           0.9  | 11.4%        | -15.9%         | 8.8x           |
| ('2010-2019 post-GFC', 'Signal only')                           |     0.9  |           0.9  | 13.5%        | -19.3%         | 0.0x           |
| ('2010-2019 post-GFC', 'Buy & hold')                            |     0.9  |           0.9  | 13.5%        | -19.3%         | 0.0x           |
| ('2020-2026 Covid & after', 'Vol target + signal')              |     0.53 |           0.54 | 9.2%         | -18.9%         | 10.4x          |
| ('2020-2026 Covid & after', 'Vol target + signal (long-short)') |     0.53 |           0.54 | 9.2%         | -18.9%         | 10.4x          |
| ('2020-2026 Covid & after', 'Vol target only')                  |     0.53 |           0.54 | 9.2%         | -18.9%         | 10.4x          |
| ('2020-2026 Covid & after', 'Signal only')                      |     0.58 |           0.58 | 13.3%        | -33.7%         | 0.0x           |
| ('2020-2026 Covid & after', 'Buy & hold')                       |     0.58 |           0.58 | 13.3%        | -33.7%         | 0.0x           |

## HAR loadings, full sample, Newey-West t-stats (in-sample inference only)

|       |   coef |   hac_t |   p_value |
|:------|-------:|--------:|----------:|
| const | -0.288 |  -9.334 |         0 |
| har_d |  0.177 |  12.778 |         0 |
| har_w |  0.354 |  11.212 |         0 |
| har_m |  0.325 |  10.847 |         0 |
