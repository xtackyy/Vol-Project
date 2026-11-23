# Short-variance backtests: synthetic 21-day SPY variance swaps

Entries 1998-02-23 to 2026-11-20. Vega notional $10,000 per vol point, strike = VIX - 1 vol pt, daily mark-to-market, no cap on realized variance. Returns are P&L / $1,000,000 capital (not compounded). Headline conditional threshold (0) fixed before running; 7 thresholds shown. 192 backtest configurations in total in this file.

## Headline

|                                                                                    | ann_return   | ann_vol   |   sharpe |   sortino | max_drawdown   | worst_month   | worst_21d   |   skew_daily |   skew_monthly | time_in_market   |   avg_vega_in_market |
|:-----------------------------------------------------------------------------------|:-------------|:----------|---------:|----------:|:---------------|:--------------|:------------|-------------:|---------------:|:-----------------|---------------------:|
| Always short | monthly                                                             | 16.5%        | 29.9%     |     0.55 |      0.62 | -140.9%        | -96.2%        | -140.2%     |        -9.17 |          -5.65 | 100.0%           |               10,000 |
| Conditional (spread > 0) | monthly                                                 | 13.2%        | 28.5%     |     0.46 |      0.52 | -142.9%        | -96.2%        | -140.2%     |       -10.41 |          -6.12 | 80.5%            |               10,000 |
| Sized by spread | monthly                                                          | 19.3%        | 50.7%     |     0.38 |      0.42 | -292.0%        | -189.1%       | -270.5%     |       -11.58 |          -6.78 | 78.2%            |               15,922 |
| Always short, vol-targeted | monthly                                               | 11.7%        | 21.9%     |     0.53 |      0.6  | -78.6%         | -31.8%        | -77.8%      |       -18.2  |          -3.31 | 100.0%           |                7,310 |
| Conditional (spread > 0), vol-targeted | monthly                                   | 10.0%        | 21.2%     |     0.47 |      0.53 | -81.5%         | -31.8%        | -77.8%      |       -19.96 |          -3.48 | 80.5%            |                7,381 |
| Always short | staggered                                                           | 15.1%        | 28.6%     |     0.53 |      0.58 | -176.0%        | -124.9%       | -174.8%     |       -10.41 |          -7.49 | 100.0%           |                9,986 |
| Conditional (spread > 0) | staggered                                               | 11.6%        | 25.6%     |     0.45 |      0.49 | -177.2%        | -126.5%       | -173.8%     |       -12.55 |          -9.07 | 96.6%            |                8,141 |
| Sized by spread | staggered                                                        | 20.8%        | 42.1%     |     0.49 |      0.54 | -305.9%        | -217.9%       | -301.1%     |       -13.32 |          -9.51 | 93.2%            |               13,128 |
| Always short, vol-targeted | staggered                                             | 9.3%         | 21.0%     |     0.44 |      0.49 | -137.7%        | -72.0%        | -100.8%     |       -15.62 |          -6.44 | 100.0%           |                7,324 |
| Conditional (spread > 0), vol-targeted | staggered                                 | 7.0%         | 19.9%     |     0.35 |      0.38 | -139.0%        | -72.1%        | -100.7%     |       -17.76 |          -7.42 | 96.6%            |                6,020 |
| Always short, constant size at the same average risk (hindsight scale) | staggered | 11.1%        | 21.0%     |     0.53 |      0.58 | -128.9%        | -91.6%        | -128.1%     |       -10.41 |          -7.49 | 100.0%           |                7,317 |

## Threshold grid (all values)

|                     | ann_return   | ann_vol   |   sharpe |   sortino | max_drawdown   | worst_month   | worst_21d   |   skew_daily |   skew_monthly | time_in_market   |   avg_vega_in_market |
|:--------------------|:-------------|:----------|---------:|----------:|:---------------|:--------------|:------------|-------------:|---------------:|:-----------------|---------------------:|
| (-2.0, 'monthly')   | 14.6%        | 29.4%     |     0.5  |      0.56 | -140.9%        | -96.2%        | -140.2%     |        -9.6  |          -5.85 | 92.1%            |               10,000 |
| (-2.0, 'staggered') | 13.3%        | 27.1%     |     0.49 |      0.54 | -174.9%        | -126.5%       | -173.8%     |       -11.3  |          -8.08 | 99.5%            |                9,226 |
| (-1.0, 'monthly')   | 14.2%        | 28.9%     |     0.49 |      0.55 | -142.9%        | -96.2%        | -140.2%     |       -10.01 |          -6.08 | 88.1%            |               10,000 |
| (-1.0, 'staggered') | 12.4%        | 26.6%     |     0.47 |      0.51 | -174.9%        | -126.5%       | -173.8%     |       -11.73 |          -8.33 | 98.1%            |                8,863 |
| (0.0, 'monthly')    | 13.2%        | 28.5%     |     0.46 |      0.52 | -142.9%        | -96.2%        | -140.2%     |       -10.41 |          -6.12 | 80.5%            |               10,000 |
| (0.0, 'staggered')  | 11.6%        | 25.6%     |     0.45 |      0.49 | -177.2%        | -126.5%       | -173.8%     |       -12.55 |          -9.07 | 96.6%            |                8,141 |
| (1.0, 'monthly')    | 8.9%         | 27.3%     |     0.33 |      0.36 | -163.0%        | -96.2%        | -140.2%     |       -11.43 |          -6.34 | 62.2%            |               10,000 |
| (1.0, 'staggered')  | 10.2%        | 23.2%     |     0.44 |      0.48 | -175.8%        | -120.3%       | -166.4%     |       -13.68 |          -9.82 | 93.2%            |                6,884 |
| (2.0, 'monthly')    | 6.9%         | 23.9%     |     0.29 |      0.32 | -157.8%        | -96.2%        | -140.2%     |       -12.08 |          -7.09 | 46.6%            |               10,000 |
| (2.0, 'staggered')  | 8.4%         | 19.5%     |     0.43 |      0.47 | -156.7%        | -112.0%       | -153.9%     |       -15.53 |         -10.86 | 84.6%            |                5,451 |
| (3.0, 'monthly')    | 5.6%         | 21.9%     |     0.26 |      0.28 | -107.4%        | -84.5%        | -105.3%     |       -14.68 |          -7.42 | 31.2%            |               10,000 |
| (3.0, 'staggered')  | 8.1%         | 13.8%     |     0.59 |      0.67 | -79.0%         | -56.6%        | -78.4%      |       -10.9  |          -6.85 | 68.0%            |                4,397 |
| (4.0, 'monthly')    | 5.5%         | 19.9%     |     0.27 |      0.3  | -107.4%        | -84.5%        | -105.3%     |       -18.02 |          -8.74 | 21.2%            |               10,000 |
| (4.0, 'staggered')  | 7.3%         | 10.2%     |     0.71 |      0.84 | -39.3%         | -28.4%        | -39.2%      |        -8.61 |          -3.21 | 52.1%            |                3,728 |

## Roll-date sensitivity: all 21 monthly roll dates (min / median / max)

| strategy                               |   ('sharpe', 'min') |   ('sharpe', '50%') |   ('sharpe', 'max') |   ('max_drawdown', 'min') |   ('max_drawdown', '50%') |   ('max_drawdown', 'max') |   ('worst_month', 'min') |   ('worst_month', '50%') |   ('worst_month', 'max') |
|:---------------------------------------|--------------------:|--------------------:|--------------------:|--------------------------:|--------------------------:|--------------------------:|-------------------------:|-------------------------:|-------------------------:|
| Always short                           |               0.323 |               0.497 |               0.647 |                    -2.737 |                    -1.579 |                    -1.257 |                   -1.898 |                   -1.138 |                   -0.813 |
| Conditional (spread > 0)               |               0.196 |               0.432 |               0.565 |                    -2.745 |                    -1.58  |                    -1.1   |                   -1.946 |                   -1.138 |                   -0.753 |
| Sized by spread                        |               0.167 |               0.428 |               0.649 |                    -5.565 |                    -3.024 |                    -1.16  |                   -3.892 |                   -1.937 |                   -0.767 |
| Always short, vol-targeted             |               0.189 |               0.408 |               0.644 |                    -2.491 |                    -1.074 |                    -0.675 |                   -1.591 |                   -0.468 |                   -0.285 |
| Conditional (spread > 0), vol-targeted |               0.072 |               0.319 |               0.527 |                    -2.474 |                    -1.057 |                    -0.675 |                   -1.591 |                   -0.468 |                   -0.285 |
| Always short (from VIX3M start)        |               0.122 |               0.346 |               0.53  |                    -2.737 |                    -1.579 |                    -1.257 |                   -1.898 |                   -1.138 |                   -0.813 |
| Always short, flat in backwardation    |               0.062 |               0.651 |               1.059 |                    -2.742 |                    -0.858 |                    -0.45  |                   -2.025 |                   -0.517 |                   -0.252 |

## Flat in backwardation (VIX > VIX3M), entries from 2006-07-17

|                                                             | ann_return   | ann_vol   |   sharpe |   sortino | max_drawdown   | worst_month   | worst_21d   |   skew_daily |   skew_monthly | time_in_market   |   avg_vega_in_market |
|:------------------------------------------------------------|:-------------|:----------|---------:|----------:|:---------------|:--------------|:------------|-------------:|---------------:|:-----------------|---------------------:|
| Always short | monthly                                      | 14.3%        | 33.5%     |     0.43 |      0.48 | -140.9%        | -96.2%        | -140.2%     |        -9.01 |          -5.48 | 100.0%           |               10,000 |
| Always short, flat in backwardation | monthly               | 17.8%        | 24.5%     |     0.73 |      0.83 | -55.7%         | -46.5%        | -55.3%      |        -8.84 |          -3.33 | 87.1%            |               10,000 |
| Always short | staggered                                    | 11.0%        | 32.2%     |     0.34 |      0.37 | -176.0%        | -124.9%       | -174.8%     |       -10.05 |          -6.96 | 100.0%           |               10,000 |
| Always short, flat in backwardation | staggered             | 13.6%        | 22.8%     |     0.6  |      0.66 | -115.4%        | -72.9%        | -103.1%     |        -7.09 |          -5.24 | 98.1%            |                9,068 |
| Conditional (spread > 0) | monthly                          | 11.5%        | 32.7%     |     0.35 |      0.39 | -142.9%        | -96.2%        | -140.2%     |        -9.54 |          -5.6  | 92.6%            |               10,000 |
| Conditional (spread > 0), flat in backwardation | monthly   | 16.3%        | 24.2%     |     0.67 |      0.77 | -55.7%         | -46.5%        | -55.3%      |        -9.15 |          -3.39 | 81.8%            |               10,000 |
| Conditional (spread > 0) | staggered                        | 10.2%        | 29.5%     |     0.35 |      0.38 | -177.2%        | -126.5%       | -173.8%     |       -11.41 |          -8.13 | 100.0%           |                9,011 |
| Conditional (spread > 0), flat in backwardation | staggered | 11.8%        | 21.7%     |     0.54 |      0.6  | -120.1%        | -72.9%        | -103.1%     |        -7.57 |          -5.73 | 97.6%            |                8,295 |

## Deflated Sharpe of the best of the 14 threshold-grid configurations (annualised Sharpe)

|                         | vs zero             | excess over always short   |
|:------------------------|:--------------------|:---------------------------|
| best_config             | 4 staggered         | -1 monthly                 |
| n_trials                | 14.0                | 14.0                       |
| sharpe_best_ann         | 0.7148085292915889  | -0.30392230167160206       |
| sharpe_trials_sd_ann    | 0.12580998394496845 | 0.09431445508106888        |
| expected_max_sharpe_ann | 0.21871418574623633 | 0.1639608288653703         |
| psr_vs_zero             | 0.9991808780030604  | 0.06259249228869097        |
| deflated_sharpe         | 0.9855734961847817  | 0.00912282382347016        |

## Robustness (staggered)

|                                                          | ann_return   | ann_vol   |   sharpe |   sortino | max_drawdown   | worst_month   | worst_21d   |   skew_daily |   skew_monthly | time_in_market   |   avg_vega_in_market |
|:---------------------------------------------------------|:-------------|:----------|---------:|----------:|:---------------|:--------------|:------------|-------------:|---------------:|:-----------------|---------------------:|
| Always short | cost 0.5 vol pt                           | 20.7%        | 27.9%     |     0.74 |      0.82 | -170.4%        | -121.1%       | -169.7%     |       -10.42 |          -7.48 | 100.0%           |                9,986 |
| Always short | enter at t+1                              | 15.1%        | 28.6%     |     0.53 |      0.58 | -176.0%        | -124.9%       | -174.8%     |       -10.41 |          -7.49 | 100.0%           |                9,986 |
| Conditional (spread > 0) | cost 0.5 vol pt               | 16.0%        | 24.9%     |     0.64 |      0.7  | -169.5%        | -122.8%       | -168.7%     |       -12.58 |          -9.01 | 96.6%            |                8,141 |
| Conditional (spread > 0) | enter at t+1                  | 11.5%        | 25.5%     |     0.45 |      0.49 | -178.3%        | -125.5%       | -172.8%     |       -12.49 |          -9.01 | 96.6%            |                8,140 |
| Sized by spread | cost 0.5 vol pt                        | 27.6%        | 41.0%     |     0.67 |      0.74 | -293.6%        | -211.2%       | -292.2%     |       -13.34 |          -9.39 | 93.2%            |               13,128 |
| Sized by spread | enter at t+1                           | 20.6%        | 41.8%     |     0.49 |      0.54 | -306.4%        | -215.0%       | -298.1%     |       -13.17 |          -9.4  | 93.2%            |               13,128 |
| Always short, vol-targeted | cost 0.5 vol pt             | 13.4%        | 20.2%     |     0.66 |      0.73 | -124.7%        | -69.7%        | -97.4%      |       -15.34 |          -6.35 | 100.0%           |                7,324 |
| Always short, vol-targeted | enter at t+1                | 9.1%         | 21.5%     |     0.42 |      0.46 | -142.8%        | -75.5%        | -105.3%     |       -16.05 |          -6.72 | 100.0%           |                7,325 |
| Conditional (spread > 0), vol-targeted | cost 0.5 vol pt | 10.2%        | 19.2%     |     0.53 |      0.58 | -126.5%        | -69.8%        | -97.4%      |       -17.48 |          -7.31 | 96.6%            |                6,020 |
| Conditional (spread > 0), vol-targeted | enter at t+1    | 6.8%         | 20.4%     |     0.33 |      0.36 | -144.9%        | -75.6%        | -105.1%     |       -18.23 |          -7.74 | 96.6%            |                6,020 |
| Always short, flat in backwardation | enter at t+1       | 13.2%        | 23.6%     |     0.56 |      0.62 | -121.9%        | -78.9%        | -109.7%     |        -7.47 |          -5.66 | 98.1%            |                9,068 |
| Always short (same sample) | enter at t+1                | 11.0%        | 32.2%     |     0.34 |      0.37 | -176.0%        | -124.9%       | -174.8%     |       -10.05 |          -6.96 | 100.0%           |               10,000 |

## Vol-targeted size on the first day of each stress window (target 10%, 63-day trailing vol, cap 2)

The rule sizes from the last 63 days. Before the sharp crashes (2008, 2011, 2018, 2020) those were calm, so it entered at a normal size or larger (1.8x into Feb 2018, after the calm of 2017) and only cut after the first shock. The realized P&L vol overshoots the 10% target because a few crash days dominate the full-sample standard deviation.

|                       |   size_at_start |   vix_at_start |
|:----------------------|----------------:|---------------:|
| 1998 LTCM / Russia    |            0.67 |          24.8  |
| 2008 GFC              |            0.54 |          20.65 |
| Aug 2011 US downgrade |            0.76 |          19.53 |
| Feb 2018 Volmageddon  |            1.8  |          11.03 |
| Mar 2020 Covid        |            0.79 |          14.38 |
| 2022 bear market      |            0.4  |          17.22 |

## P&L in stress windows and calm years, % of capital (staggered)

|                       | Always short | staggered   | Conditional (spread > 0) | staggered   | Sized by spread | staggered   | Always short, vol-targeted | staggered   | Conditional (spread > 0), vol-targeted | staggered   | Always short, constant size at the same average risk (hindsight scale) | staggered   | Always short | staggered (from 2006)   | Always short, flat in backwardation | staggered (from 2006)   |
|:----------------------|:---------------------------|:---------------------------------------|:------------------------------|:-----------------------------------------|:-----------------------------------------------------|:-------------------------------------------------------------------------------------|:---------------------------------------|:--------------------------------------------------------------|
| 1998 LTCM / Russia    | -2.8%                      | -8.3%                                  | 0.0%                          | -4.5%                                    | -5.9%                                                | -2.0%                                                                                | 0.0%                                   | 0.0%                                                          |
| 2008 GFC              | -98.7%                     | -61.8%                                 | -116.5%                       | -39.5%                                   | -21.3%                                               | -72.3%                                                                               | -98.7%                                 | -20.1%                                                        |
| Aug 2011 US downgrade | -24.0%                     | -24.0%                                 | -42.9%                        | -24.4%                                   | -24.4%                                               | -17.6%                                                                               | -24.0%                                 | -22.9%                                                        |
| Feb 2018 Volmageddon  | -18.6%                     | -18.7%                                 | -21.1%                        | -40.9%                                   | -40.9%                                               | -13.6%                                                                               | -18.6%                                 | -21.6%                                                        |
| Mar 2020 Covid        | -147.7%                    | -151.3%                                | -260.4%                       | -96.5%                                   | -96.8%                                               | -108.2%                                                                              | -147.7%                                | -101.3%                                                       |
| 2022 bear market      | 1.0%                       | -1.6%                                  | 4.6%                          | -0.8%                                    | -1.6%                                                | 0.7%                                                                                 | 1.0%                                   | -2.4%                                                         |
| Calm: 2005-2006       | 38.6%                      | 26.3%                                  | 45.2%                         | 41.2%                                    | 29.8%                                                | 28.3%                                                                                | 18.3%                                  | 13.7%                                                         |
| Calm: 2017            | 33.6%                      | 33.2%                                  | 49.9%                         | 39.2%                                    | 38.5%                                                | 24.6%                                                                                | 33.6%                                  | 33.0%                                                         |

## Tradable proxies (compounded daily returns; SVXY leverage changed on 2018-02-28)

|                                                | start      | ann_return   | ann_vol   |   sharpe | max_drawdown   | worst_month   | time_in_market   |
|:-----------------------------------------------|:-----------|:-------------|:----------|---------:|:---------------|:--------------|:-----------------|
| SVXY long, always                              | 2011-10-05 | 10.6%        | 54.9%     | 0.537579 | -95.2%         | -89.6%        | 99.7%            |
| SVXY long, always, to 2018-02-27 (-1x)         | 2011-10-05 | 14.4%        | 72.3%     | 0.68682  | -93.1%         | -89.5%        | 99.9%            |
| SVXY long, always, from 2018-02-28 (-0.5x)     | 2018-02-28 | 7.9%         | 37.2%     | 0.395598 | -62.2%         | -38.9%        | 99.5%            |
| SVXY long, spread > 0                          | 2011-10-05 | 4.4%         | 53.5%     | 0.430016 | -95.1%         | -89.6%        | 91.0%            |
| SVXY long, spread > 0, to 2018-02-27 (-1x)     | 2011-10-05 | 2.0%         | 71.1%     | 0.525248 | -93.1%         | -89.5%        | 93.3%            |
| SVXY long, spread > 0, from 2018-02-28 (-0.5x) | 2018-02-28 | 6.2%         | 35.5%     | 0.352523 | -66.8%         | -51.7%        | 89.3%            |
| VXX short, always                              | 2018-01-26 | -7.6%        | 73.8%     | 0.289238 | -91.0%         | -68.7%        | 99.1%            |
| VXX short, spread > 0                          | 2018-01-26 | -9.1%        | 70.6%     | 0.245617 | -90.9%         | -79.3%        | 89.3%            |
