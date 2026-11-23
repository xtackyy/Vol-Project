# Short-variance backtests: synthetic 21-day QQQ variance swaps (implied vol: ^VXN)

Signals 2004-04-12 to 2026-11-23; each swap is struck 1 trading day(s) after its signal, at that day's VIX close. Vega notional $10,000 per vol point, strike = VIX - 1 vol pt, daily mark-to-market, no cap on realized variance. Returns are P&L / $1,000,000 capital (not compounded). Headline conditional threshold (0) fixed before running; 7 thresholds shown. 204 backtest configurations in total in this file.

## Headline

|                                                                                    | ann_return   | ann_vol   |   sharpe |   sortino | max_drawdown   | worst_month   | worst_21d   |   skew_daily |   skew_monthly | time_in_market   |   avg_vega_in_market |
|:-----------------------------------------------------------------------------------|:-------------|:----------|---------:|----------:|:---------------|:--------------|:------------|-------------:|---------------:|:-----------------|---------------------:|
| Always short | monthly                                                             | 5.4%         | 32.4%     |     0.17 |      0.18 | -235.1%        | -141.1%       | -207.1%     |       -11.76 |          -7.13 | 100.0%           |               10,000 |
| Conditional (spread > 0) | monthly                                                 | 5.8%         | 30.3%     |     0.19 |      0.21 | -240.4%        | -141.1%       | -207.1%     |       -13.05 |          -7.96 | 88.9%            |               10,000 |
| Sized by spread | monthly                                                          | 0.6%         | 37.1%     |     0.02 |      0.02 | -328.6%        | -200.7%       | -282.3%     |       -16.7  |         -10.38 | 84.5%            |                8,699 |
| Always short, vol-targeted | monthly                                               | 1.4%         | 22.9%     |     0.06 |      0.07 | -198.3%        | -127.3%       | -173.9%     |       -16.47 |          -9.77 | 100.0%           |                6,907 |
| Conditional (spread > 0), vol-targeted | monthly                                   | 2.3%         | 22.3%     |     0.1  |      0.11 | -200.6%        | -127.3%       | -173.9%     |       -17.65 |         -10.32 | 88.9%            |                7,248 |
| Always short | staggered                                                           | 9.7%         | 27.4%     |     0.35 |      0.39 | -158.1%        | -100.8%       | -146.0%     |       -10.14 |          -5.72 | 100.0%           |                9,982 |
| Conditional (spread > 0) | staggered                                               | 9.7%         | 24.4%     |     0.4  |      0.43 | -156.4%        | -101.3%       | -142.3%     |       -11.27 |          -6.75 | 98.9%            |                8,874 |
| Sized by spread | staggered                                                        | 9.7%         | 27.7%     |     0.35 |      0.38 | -190.8%        | -118.7%       | -165.8%     |       -13.8  |          -7.71 | 94.5%            |                7,782 |
| Always short, vol-targeted | staggered                                             | 5.1%         | 16.8%     |     0.31 |      0.33 | -108.3%        | -63.2%        | -91.8%      |        -8.03 |          -5.65 | 100.0%           |                6,851 |
| Conditional (spread > 0), vol-targeted | staggered                                 | 5.3%         | 15.8%     |     0.34 |      0.37 | -108.7%        | -63.0%        | -90.5%      |        -8.62 |          -6.22 | 98.9%            |                6,368 |
| Always short, constant size at the same average risk (hindsight scale) | staggered | 5.9%         | 16.8%     |     0.35 |      0.39 | -96.8%         | -61.8%        | -89.4%      |       -10.14 |          -5.72 | 100.0%           |                6,114 |

## Threshold grid (all values)

|                     | ann_return   | ann_vol   |   sharpe |   sortino | max_drawdown   | worst_month   | worst_21d   |   skew_daily |   skew_monthly | time_in_market   |   avg_vega_in_market |
|:--------------------|:-------------|:----------|---------:|----------:|:---------------|:--------------|:------------|-------------:|---------------:|:-----------------|---------------------:|
| (-2.0, 'monthly')   | 7.0%         | 30.7%     |     0.23 |      0.25 | -235.1%        | -141.1%       | -207.1%     |       -12.57 |          -7.85 | 95.9%            |               10,000 |
| (-2.0, 'staggered') | 9.0%         | 26.4%     |     0.34 |      0.37 | -157.3%        | -101.6%       | -146.0%     |       -10.6  |          -5.95 | 99.9%            |                9,602 |
| (-1.0, 'monthly')   | 5.9%         | 30.7%     |     0.19 |      0.21 | -236.8%        | -141.1%       | -207.1%     |       -12.66 |          -7.83 | 93.3%            |               10,000 |
| (-1.0, 'staggered') | 9.5%         | 25.4%     |     0.38 |      0.41 | -154.1%        | -101.4%       | -143.4%     |       -10.51 |          -6.28 | 99.2%            |                9,397 |
| (0.0, 'monthly')    | 5.8%         | 30.3%     |     0.19 |      0.21 | -240.4%        | -141.1%       | -207.1%     |       -13.05 |          -7.96 | 88.9%            |               10,000 |
| (0.0, 'staggered')  | 9.7%         | 24.4%     |     0.4  |      0.43 | -156.4%        | -101.3%       | -142.3%     |       -11.27 |          -6.75 | 98.9%            |                8,874 |
| (1.0, 'monthly')    | 3.8%         | 30.0%     |     0.13 |      0.14 | -235.6%        | -141.1%       | -207.1%     |       -13.51 |          -8.02 | 80.4%            |               10,000 |
| (1.0, 'staggered')  | 8.9%         | 23.3%     |     0.38 |      0.42 | -160.5%        | -101.3%       | -142.3%     |       -12.55 |          -7.34 | 98.3%            |                7,969 |
| (2.0, 'monthly')    | 5.6%         | 26.4%     |     0.21 |      0.23 | -241.3%        | -152.3%       | -207.1%     |       -17.13 |         -10.65 | 64.5%            |               10,000 |
| (2.0, 'staggered')  | 8.5%         | 20.4%     |     0.41 |      0.45 | -145.3%        | -89.6%        | -123.3%     |       -12.56 |          -7.43 | 94.6%            |                6,761 |
| (3.0, 'monthly')    | 0.6%         | 25.5%     |     0.02 |      0.02 | -254.0%        | -152.3%       | -207.1%     |       -18.85 |         -11.25 | 49.1%            |               10,000 |
| (3.0, 'staggered')  | 7.3%         | 18.0%     |     0.4  |      0.44 | -133.5%        | -84.2%        | -114.0%     |       -14.62 |          -8.48 | 86.6%            |                5,625 |
| (4.0, 'monthly')    | -1.6%        | 24.3%     |    -0.07 |     -0.07 | -225.5%        | -152.3%       | -207.8%     |       -21.63 |         -11.91 | 32.8%            |               10,000 |
| (4.0, 'staggered')  | 8.8%         | 12.2%     |     0.73 |      0.84 | -57.0%         | -33.5%        | -47.1%      |        -8.26 |          -3.27 | 74.0%            |                4,564 |

## Roll-date sensitivity: all 21 monthly roll dates (min / median / max)

| strategy                               |   ('sharpe', 'min') |   ('sharpe', '50%') |   ('sharpe', 'max') |   ('max_drawdown', 'min') |   ('max_drawdown', '50%') |   ('max_drawdown', 'max') |   ('worst_month', 'min') |   ('worst_month', '50%') |   ('worst_month', 'max') |
|:---------------------------------------|--------------------:|--------------------:|--------------------:|--------------------------:|--------------------------:|--------------------------:|-------------------------:|-------------------------:|-------------------------:|
| Always short                           |               0.166 |               0.362 |               0.492 |                    -2.364 |                    -1.464 |                    -1.026 |                   -1.456 |                   -0.981 |                   -0.678 |
| Conditional (spread > 0)               |               0.167 |               0.346 |               0.641 |                    -2.404 |                    -1.491 |                    -1.022 |                   -1.597 |                   -0.977 |                   -0.678 |
| Sized by spread                        |               0.017 |               0.311 |               0.702 |                    -3.286 |                    -1.863 |                    -0.887 |                   -2.007 |                   -1.142 |                   -0.367 |
| Always short, vol-targeted             |               0.063 |               0.355 |               0.496 |                    -1.983 |                    -0.792 |                    -0.51  |                   -1.337 |                   -0.434 |                   -0.282 |
| Conditional (spread > 0), vol-targeted |               0.09  |               0.358 |               0.55  |                    -2.006 |                    -0.848 |                    -0.514 |                   -1.348 |                   -0.439 |                   -0.282 |
| Always short (from VIX3M start)        |               0.084 |               0.312 |               0.438 |                    -2.364 |                    -1.464 |                    -1.026 |                   -1.456 |                   -0.981 |                   -0.678 |
| Always short, flat in backwardation    |               0.57  |               0.842 |               1.17  |                    -0.58  |                    -0.324 |                    -0.179 |                   -0.393 |                   -0.176 |                   -0.084 |

## Flat in backwardation (VIX > VIX3M), entries from 2006-07-17

|                                                             | ann_return   | ann_vol   |   sharpe |   sortino | max_drawdown   | worst_month   | worst_21d   |   skew_daily |   skew_monthly | time_in_market   |   avg_vega_in_market |
|:------------------------------------------------------------|:-------------|:----------|---------:|----------:|:---------------|:--------------|:------------|-------------:|---------------:|:-----------------|---------------------:|
| Always short | monthly                                      | 2.8%         | 33.9%     |     0.08 |      0.09 | -235.1%        | -141.1%       | -207.1%     |       -11.39 |          -6.86 | 100.0%           |               10,000 |
| Always short, flat in backwardation | monthly               | 11.7%        | 10.9%     |     1.08 |      1.33 | -27.8%         | -17.6%        | -23.7%      |        -4.59 |          -0.28 | 34.8%            |               10,000 |
| Always short | staggered                                    | 8.3%         | 28.7%     |     0.29 |      0.31 | -158.1%        | -100.8%       | -146.0%     |        -9.82 |          -5.51 | 100.0%           |               10,000 |
| Always short, flat in backwardation | staggered             | 10.1%        | 9.4%      |     1.07 |      1.28 | -25.6%         | -16.1%        | -25.2%      |        -5.35 |          -0.24 | 55.6%            |                6,272 |
| Conditional (spread > 0) | monthly                          | 3.3%         | 31.7%     |     0.1  |      0.11 | -240.4%        | -141.1%       | -207.1%     |       -12.68 |          -7.68 | 87.7%            |               10,000 |
| Conditional (spread > 0), flat in backwardation | monthly   | 10.7%        | 10.6%     |     1.01 |      1.24 | -27.8%         | -17.6%        | -23.7%      |        -4.76 |          -0.27 | 32.0%            |               10,000 |
| Conditional (spread > 0) | staggered                        | 8.3%         | 25.5%     |     0.32 |      0.35 | -156.4%        | -101.3%       | -142.3%     |       -10.98 |          -6.54 | 98.8%            |                8,767 |
| Conditional (spread > 0), flat in backwardation | staggered | 9.5%         | 8.9%      |     1.07 |      1.27 | -25.6%         | -16.1%        | -25.2%      |        -5.5  |          -0.29 | 52.6%            |                6,048 |

## Deflated Sharpe of the best of the 14 threshold-grid configurations (annualised Sharpe)

|                         | vs zero             | excess over always short   |
|:------------------------|:--------------------|:---------------------------|
| best_config             | 4 staggered         | -2 monthly                 |
| n_trials                | 14.0                | 14.0                       |
| sharpe_best_ann         | 0.7269222901822907  | 0.15686769339483553        |
| sharpe_trials_sd_ann    | 0.19690589634306002 | 0.13075340501990076        |
| expected_max_sharpe_ann | 0.3423107724593866  | 0.22730806900813658        |
| psr_vs_zero             | 0.9978452326902115  | 0.8110866419367783         |
| deflated_sharpe         | 0.9345216699646235  | 0.3460470967050193         |

## Robustness (staggered)

|                                                                  | ann_return   | ann_vol   |   sharpe |   sortino | max_drawdown   | worst_month   | worst_21d   |   skew_daily |   skew_monthly | time_in_market   |   avg_vega_in_market |
|:-----------------------------------------------------------------|:-------------|:----------|---------:|----------:|:---------------|:--------------|:------------|-------------:|---------------:|:-----------------|---------------------:|
| Always short | cost 0.5 vol pt                                   | 15.4%        | 26.8%     |     0.58 |      0.63 | -143.9%        | -98.2%        | -142.5%     |       -10.2  |          -5.73 | 100.0%           |                9,982 |
| Always short | enter at t (same close)                           | 9.7%         | 27.4%     |     0.35 |      0.39 | -158.1%        | -100.8%       | -146.0%     |       -10.14 |          -5.72 | 100.0%           |                9,982 |
| Conditional (spread > 0) | cost 0.5 vol pt                       | 14.7%        | 23.9%     |     0.62 |      0.67 | -142.5%        | -98.9%        | -138.9%     |       -11.34 |          -6.74 | 98.9%            |                8,874 |
| Conditional (spread > 0) | enter at t (same close)               | 10.0%        | 24.2%     |     0.41 |      0.45 | -153.1%        | -100.1%       | -140.8%     |       -10.84 |          -6.69 | 98.9%            |                8,874 |
| Sized by spread | cost 0.5 vol pt                                | 13.9%        | 27.2%     |     0.51 |      0.56 | -178.6%        | -115.6%       | -161.8%     |       -13.82 |          -7.57 | 94.5%            |                7,782 |
| Sized by spread | enter at t (same close)                        | 10.1%        | 27.3%     |     0.37 |      0.41 | -184.4%        | -116.2%       | -162.5%     |       -12.88 |          -7.54 | 94.5%            |                7,783 |
| Always short, vol-targeted | cost 0.5 vol pt                     | 9.1%         | 16.3%     |     0.55 |      0.61 | -98.6%         | -61.6%        | -89.4%      |        -8.06 |          -5.62 | 100.0%           |                6,851 |
| Always short, vol-targeted | enter at t (same close)             | 5.3%         | 16.5%     |     0.32 |      0.35 | -104.2%        | -60.2%        | -87.8%      |        -7.66 |          -5.36 | 100.0%           |                6,851 |
| Conditional (spread > 0), vol-targeted | cost 0.5 vol pt         | 9.0%         | 15.4%     |     0.58 |      0.64 | -99.8%         | -61.4%        | -88.1%      |        -8.65 |          -6.17 | 98.9%            |                6,368 |
| Conditional (spread > 0), vol-targeted | enter at t (same close) | 5.6%         | 15.5%     |     0.36 |      0.4  | -103.5%        | -59.8%        | -86.3%      |        -8.16 |          -5.9  | 98.9%            |                6,368 |
| Always short, flat in backwardation | enter at t (same close)    | 10.1%        | 9.2%      |     1.1  |      1.3  | -24.9%         | -16.1%        | -24.5%      |        -5.39 |          -0.16 | 55.6%            |                6,272 |
| Always short (same sample) | enter at t (same close)             | 8.3%         | 28.7%     |     0.29 |      0.31 | -158.1%        | -100.8%       | -146.0%     |        -9.82 |          -5.51 | 100.0%           |               10,000 |

## Cost multiples (staggered)

The VIX-scaled haircut was fixed before running: 1 vol pt x max(1, VIX / 20), so 3 vol pts at VIX 60.

|                                                        | ann_return   | ann_vol   |   sharpe |   sortino | max_drawdown   | worst_month   | worst_21d   |   skew_daily |   skew_monthly | time_in_market   |   avg_vega_in_market |
|:-------------------------------------------------------|:-------------|:----------|---------:|----------:|:---------------|:--------------|:------------|-------------:|---------------:|:-----------------|---------------------:|
| Always short | 0 vol pt                                | 21.0%        | 26.3%     |     0.8  |      0.88 | -140.1%        | -95.7%        | -139.1%     |       -10.25 |          -5.73 | 100.0%           |                9,982 |
| Always short | 1 vol pt (base)                         | 9.7%         | 27.4%     |     0.35 |      0.39 | -158.1%        | -100.8%       | -146.0%     |       -10.14 |          -5.72 | 100.0%           |                9,982 |
| Always short | 2 vol pt                                | -2.2%        | 28.6%     |    -0.08 |     -0.08 | -196.5%        | -106.5%       | -153.5%     |       -10.02 |          -5.71 | 100.0%           |                9,982 |
| Always short | 1 vol pt x max(1, VIX/20)               | 7.5%         | 27.8%     |     0.27 |      0.29 | -162.8%        | -103.9%       | -148.6%     |       -10.25 |          -5.8  | 100.0%           |                9,982 |
| Conditional (spread > 0) | 0 vol pt                    | 19.6%        | 23.4%     |     0.84 |      0.92 | -136.8%        | -96.5%        | -135.6%     |       -11.41 |          -6.72 | 98.9%            |                8,874 |
| Conditional (spread > 0) | 1 vol pt (base)             | 9.7%         | 24.4%     |     0.4  |      0.43 | -156.4%        | -101.3%       | -142.3%     |       -11.27 |          -6.75 | 98.9%            |                8,874 |
| Conditional (spread > 0) | 2 vol pt                    | -0.7%        | 25.6%     |    -0.03 |     -0.03 | -190.9%        | -106.7%       | -149.6%     |       -11.12 |          -6.77 | 98.9%            |                8,874 |
| Conditional (spread > 0) | 1 vol pt x max(1, VIX/20)   | 7.9%         | 24.8%     |     0.32 |      0.35 | -160.1%        | -103.8%       | -144.7%     |       -11.37 |          -6.82 | 98.9%            |                8,874 |
| Always short, vol-targeted | 0 vol pt                  | 12.9%        | 15.9%     |     0.81 |      0.89 | -89.3%         | -60.1%        | -87.1%      |        -8.09 |          -5.58 | 100.0%           |                6,851 |
| Always short, vol-targeted | 1 vol pt (base)           | 5.1%         | 16.8%     |     0.31 |      0.33 | -108.3%        | -63.2%        | -91.8%      |        -8.03 |          -5.65 | 100.0%           |                6,851 |
| Always short, vol-targeted | 2 vol pt                  | -3.1%        | 17.7%     |    -0.17 |     -0.19 | -138.6%        | -66.6%        | -96.9%      |        -7.97 |          -5.67 | 100.0%           |                6,851 |
| Always short, vol-targeted | 1 vol pt x max(1, VIX/20) | 4.3%         | 16.9%     |     0.25 |      0.28 | -109.8%        | -63.8%        | -92.5%      |        -8.06 |          -5.65 | 100.0%           |                6,851 |

## P&L by year, % of capital (staggered)

|   Date | Always short   | Conditional (spread > 0)   | Conditional minus always short   |
|-------:|:---------------|:---------------------------|:---------------------------------|
|   2004 | 30.3%          | 30.3%                      | 0.0%                             |
|   2005 | 25.7%          | 25.7%                      | 0.0%                             |
|   2006 | 14.8%          | 14.7%                      | -0.1%                            |
|   2007 | 15.7%          | 15.8%                      | 0.2%                             |
|   2008 | -53.6%         | -44.4%                     | 9.2%                             |
|   2009 | 78.1%          | 77.9%                      | -0.2%                            |
|   2010 | 34.5%          | 32.2%                      | -2.3%                            |
|   2011 | 4.8%           | 4.5%                       | -0.2%                            |
|   2012 | 33.9%          | 31.3%                      | -2.6%                            |
|   2013 | 21.6%          | 20.5%                      | -1.2%                            |
|   2014 | 11.6%          | 6.8%                       | -4.9%                            |
|   2015 | -9.5%          | -11.1%                     | -1.6%                            |
|   2016 | 17.7%          | 14.4%                      | -3.3%                            |
|   2017 | 28.3%          | 27.6%                      | -0.7%                            |
|   2018 | -40.5%         | -34.6%                     | 5.9%                             |
|   2019 | 28.7%          | 20.9%                      | -7.8%                            |
|   2020 | -69.2%         | -74.2%                     | -5.0%                            |
|   2021 | 58.0%          | 57.9%                      | -0.0%                            |
|   2022 | -23.6%         | -22.9%                     | 0.6%                             |
|   2023 | 36.3%          | 27.2%                      | -9.1%                            |
|   2024 | 1.0%           | -3.7%                      | -4.7%                            |
|   2025 | -18.9%         | 11.2%                      | 30.1%                            |
|   2026 | -6.2%          | -8.7%                      | -2.5%                            |

Conditional beats always short in 5 of 23 years.

## Rolling 12-month Sharpe of always short, by thirds of the sample

|                    |   mean rolling 12m Sharpe |   share of days < 0 |
|:-------------------|--------------------------:|--------------------:|
| 2005-04 to 2012-06 |                      1.38 |                0.14 |
| 2012-06 to 2019-09 |                      0.95 |                0.3  |
| 2019-09 to 2026-11 |                      0.75 |                0.42 |

## Vol-targeted size on the first day of each stress window (target 10%, 63-day trailing vol, cap 2)

The rule sizes from the last 63 days. Before the sharp crashes (2008, 2011, 2018, 2020) those were calm, so it entered at a normal size or larger (1.8x into Feb 2018, after the calm of 2017) and only cut after the first shock. The realized P&L vol overshoots the 10% target because a few crash days dominate the full-sample standard deviation.

|                       |   size_at_start |   vix_at_start |
|:----------------------|----------------:|---------------:|
| 1998 LTCM / Russia    |          nan    |         nan    |
| 2008 GFC              |            0.54 |          24.02 |
| Aug 2011 US downgrade |            0.72 |          20.95 |
| Feb 2018 Volmageddon  |            0.97 |          16.29 |
| Mar 2020 Covid        |            0.84 |          18.58 |
| 2022 bear market      |            0.61 |          21.2  |

## P&L in stress windows and calm years, % of capital (staggered)

|                       | Always short | staggered   | Conditional (spread > 0) | staggered   | Sized by spread | staggered   | Always short, vol-targeted | staggered   | Conditional (spread > 0), vol-targeted | staggered   | Always short, constant size at the same average risk (hindsight scale) | staggered   | Always short | staggered (from 2006)   | Always short, flat in backwardation | staggered (from 2006)   |
|:----------------------|:---------------------------|:---------------------------------------|:------------------------------|:-----------------------------------------|:-----------------------------------------------------|:-------------------------------------------------------------------------------------|:---------------------------------------|:--------------------------------------------------------------|
| 1998 LTCM / Russia    | 0.0%                       | 0.0%                                   | 0.0%                          | 0.0%                                     | 0.0%                                                 | 0.0%                                                                                 | 0.0%                                   | 0.0%                                                          |
| 2008 GFC              | -48.8%                     | -37.8%                                 | -9.7%                         | -27.5%                                   | -22.2%                                               | -29.9%                                                                               | -48.8%                                 | 13.2%                                                         |
| Aug 2011 US downgrade | -18.5%                     | -18.2%                                 | -9.2%                         | -20.1%                                   | -20.0%                                               | -11.3%                                                                               | -18.5%                                 | -2.7%                                                         |
| Feb 2018 Volmageddon  | -11.9%                     | -12.1%                                 | -18.2%                        | -14.1%                                   | -14.2%                                               | -7.3%                                                                                | -11.9%                                 | 0.0%                                                          |
| Mar 2020 Covid        | -123.0%                    | -125.3%                                | -140.7%                       | -87.1%                                   | -86.3%                                               | -75.3%                                                                               | -123.0%                                | 1.0%                                                          |
| 2022 bear market      | -23.6%                     | -22.9%                                 | -15.6%                        | -11.8%                                   | -11.1%                                               | -14.4%                                                                               | -23.6%                                 | -3.2%                                                         |
| Calm: 2005-2006       | 40.5%                      | 40.4%                                  | 26.3%                         | 38.2%                                    | 38.1%                                                | 24.8%                                                                                | 19.4%                                  | 0.0%                                                          |
| Calm: 2017            | 28.3%                      | 27.6%                                  | 20.4%                         | 28.3%                                    | 27.6%                                                | 17.3%                                                                                | 28.3%                                  | 15.0%                                                         |

## Tradable proxies (compounded daily returns; SVXY leverage changed on 2018-02-28)


