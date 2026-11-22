# Cross-asset comparison: SPY, TLT, GLD

Same purged walk-forward engine for every asset; asset-specific costs and lagged macro features.

## Model and strategy summary

|                | SPY        | TLT        | GLD        |
|:---------------|:-----------|:-----------|:-----------|
| asset_class    | equity     | rates      | gold       |
| oos_start      | 2004-01-08 | 2006-07-31 | 2008-11-19 |
| oos_end        | 2026-11-20 | 2026-11-20 | 2026-11-20 |
| oos_days       | 5755       | 5111       | 4529       |
| cost_bps       | 1.50       | 2.00       | 3.00       |
| n_features     | 18         | 25         | 26         |
| vol_r2_ridge   | 0.707      | 0.568      | 0.537      |
| vol_r2_har     | 0.651      | 0.550      | 0.518      |
| vol_dm_t       | -9.98      | -2.51      | -3.44      |
| ret_ic_5d      | 0.087      | -0.128     | 0.016      |
| ret_ic_t       | 1.74       | -1.60      | 0.22       |
| ret_view_share | 35.0%      | 15.2%      | 23.2%      |
| ret_r2_oos     | 0.001      | -0.001     | -0.002     |
| vt_sharpe      | 0.57       | 0.19       | 0.50       |
| vt_max_dd      | -31.1%     | -43.0%     | -41.0%     |
| vt_turnover    | 8.75       | 4.61       | 3.74       |
| vt_vol         | 12.5%      | 13.3%      | 12.8%      |
| vt_cagr        | 8.4%       | 3.3%       | 7.2%       |
| bh_sharpe      | 0.52       | 0.16       | 0.49       |
| bh_max_dd      | -55.2%     | -48.4%     | -45.6%     |
| bh_vol         | 18.6%      | 14.9%      | 17.3%      |
| bh_cagr        | 10.2%      | 3.0%       | 8.7%       |

`vol_dm_t` < 0: Ridge beats HAR-OLS. `ret_ic_5d`: rank IC of the 5-day return tilt on days the model has a view, t-stat uses n/5 effective observations.

## Correlation of vol-targeted strategy returns (daily, common window)

|     |   SPY |   TLT |   GLD |
|:----|------:|------:|------:|
| SPY |  1    | -0.24 |  0.08 |
| TLT | -0.24 |  1    |  0.23 |
| GLD |  0.08 |  0.23 |  1    |

Buy & hold, same window, for reference:

|     |   SPY |   TLT |   GLD |
|:----|------:|------:|------:|
| SPY |  1    | -0.3  |  0.09 |
| TLT | -0.3  |  1    |  0.19 |
| GLD |  0.09 |  0.19 |  1    |

## Equal-weight book of the vol-targeted sleeves (2008-11-19 to 2026-11-20, 18.0 years)

|                             | ann_return   | ann_vol   |   sharpe |   sortino | max_drawdown   |   calmar |
|:----------------------------|:-------------|:----------|---------:|----------:|:---------------|---------:|
| SPY                         | 10.7%        | 12.5%     |     0.77 |      1.05 | -18.9%         |     0.57 |
| TLT                         | 2.3%         | 13.4%     |     0.13 |      0.19 | -43.0%         |     0.05 |
| GLD                         | 7.2%         | 12.8%     |     0.5  |      0.7  | -41.0%         |     0.18 |
| Equal-weight (vol-targeted) | 7.3%         | 7.6%      |     0.78 |      1.1  | -18.7%         |     0.39 |

Average pairwise correlation 0.02; diversification ratio (avg sleeve vol / book vol) 1.69.

## Regime breakdown per asset

|                                                                        |   sharpe |   sharpe_gross | ann_return   | max_drawdown   | ann_turnover   |
|:-----------------------------------------------------------------------|---------:|---------------:|:-------------|:---------------|:---------------|
| ('SPY', '2004-2007 pre-GFC', 'Vol target + signal')                    |     0.31 |           0.32 | 6.7%         | -9.0%          | 8.2x           |
| ('SPY', '2004-2007 pre-GFC', 'Vol target + signal (long-short)')       |     0.31 |           0.32 | 6.7%         | -9.0%          | 8.5x           |
| ('SPY', '2004-2007 pre-GFC', 'Vol target only')                        |     0.31 |           0.32 | 6.7%         | -9.0%          | 8.1x           |
| ('SPY', '2004-2007 pre-GFC', 'Signal only')                            |     0.46 |           0.46 | 8.6%         | -9.9%          | 0.3x           |
| ('SPY', '2004-2007 pre-GFC', 'Buy & hold')                             |     0.46 |           0.46 | 8.6%         | -9.9%          | 0.0x           |
| ('SPY', '2008-2009 GFC', 'Vol target + signal')                        |    -0.38 |          -0.38 | -4.7%        | -25.7%         | 3.7x           |
| ('SPY', '2008-2009 GFC', 'Vol target + signal (long-short)')           |    -0.38 |          -0.38 | -4.7%        | -25.7%         | 3.7x           |
| ('SPY', '2008-2009 GFC', 'Vol target only')                            |    -0.38 |          -0.38 | -4.7%        | -25.7%         | 3.7x           |
| ('SPY', '2008-2009 GFC', 'Signal only')                                |    -0.17 |          -0.17 | -10.6%       | -51.9%         | 0.0x           |
| ('SPY', '2008-2009 GFC', 'Buy & hold')                                 |    -0.17 |          -0.17 | -10.6%       | -51.9%         | 0.0x           |
| ('SPY', '2010-2019 post-GFC', 'Vol target + signal')                   |     0.89 |           0.9  | 11.4%        | -15.9%         | 8.8x           |
| ('SPY', '2010-2019 post-GFC', 'Vol target + signal (long-short)')      |     0.89 |           0.9  | 11.4%        | -15.9%         | 8.8x           |
| ('SPY', '2010-2019 post-GFC', 'Vol target only')                       |     0.89 |           0.9  | 11.4%        | -15.9%         | 8.8x           |
| ('SPY', '2010-2019 post-GFC', 'Signal only')                           |     0.9  |           0.9  | 13.5%        | -19.3%         | 0.0x           |
| ('SPY', '2010-2019 post-GFC', 'Buy & hold')                            |     0.9  |           0.9  | 13.5%        | -19.3%         | 0.0x           |
| ('SPY', '2020-2026 Covid & after', 'Vol target + signal')              |     0.53 |           0.54 | 9.2%         | -18.9%         | 10.4x          |
| ('SPY', '2020-2026 Covid & after', 'Vol target + signal (long-short)') |     0.53 |           0.54 | 9.2%         | -18.9%         | 10.4x          |
| ('SPY', '2020-2026 Covid & after', 'Vol target only')                  |     0.53 |           0.54 | 9.2%         | -18.9%         | 10.4x          |
| ('SPY', '2020-2026 Covid & after', 'Signal only')                      |     0.58 |           0.58 | 13.3%        | -33.7%         | 0.0x           |
| ('SPY', '2020-2026 Covid & after', 'Buy & hold')                       |     0.58 |           0.58 | 13.3%        | -33.7%         | 0.0x           |
| ('TLT', '2004-2007 pre-GFC', 'Vol target + signal')                    |     0.68 |           0.68 | 12.9%        | -12.9%         | 1.3x           |
| ('TLT', '2004-2007 pre-GFC', 'Vol target + signal (long-short)')       |     0.68 |           0.68 | 12.9%        | -12.9%         | 1.3x           |
| ('TLT', '2004-2007 pre-GFC', 'Vol target only')                        |     0.68 |           0.68 | 12.9%        | -12.9%         | 1.3x           |
| ('TLT', '2004-2007 pre-GFC', 'Signal only')                            |     0.72 |           0.73 | 11.2%        | -8.0%          | 0.0x           |
| ('TLT', '2004-2007 pre-GFC', 'Buy & hold')                             |     0.72 |           0.73 | 11.2%        | -8.0%          | 0.0x           |
| ('TLT', '2008-2009 GFC', 'Vol target + signal')                        |     0.06 |           0.06 | 0.6%         | -19.7%         | 2.0x           |
| ('TLT', '2008-2009 GFC', 'Vol target + signal (long-short)')           |     0.06 |           0.06 | 0.6%         | -19.7%         | 2.0x           |
| ('TLT', '2008-2009 GFC', 'Vol target only')                            |     0.06 |           0.06 | 0.6%         | -19.7%         | 2.0x           |
| ('TLT', '2008-2009 GFC', 'Signal only')                                |     0.18 |           0.18 | 2.3%         | -26.6%         | 0.0x           |
| ('TLT', '2008-2009 GFC', 'Buy & hold')                                 |     0.18 |           0.18 | 2.3%         | -26.6%         | 0.0x           |
| ('TLT', '2010-2019 post-GFC', 'Vol target + signal')                   |     0.59 |           0.6  | 7.8%         | -20.6%         | 4.7x           |
| ('TLT', '2010-2019 post-GFC', 'Vol target + signal (long-short)')      |     0.59 |           0.6  | 7.8%         | -20.6%         | 4.7x           |
| ('TLT', '2010-2019 post-GFC', 'Vol target only')                       |     0.59 |           0.6  | 7.8%         | -20.6%         | 4.7x           |
| ('TLT', '2010-2019 post-GFC', 'Signal only')                           |     0.54 |           0.54 | 7.2%         | -20.7%         | 0.0x           |
| ('TLT', '2010-2019 post-GFC', 'Buy & hold')                            |     0.54 |           0.54 | 7.2%         | -20.7%         | 0.0x           |
| ('TLT', '2020-2026 Covid & after', 'Vol target + signal')              |    -0.44 |          -0.42 | -2.9%        | -39.5%         | 11.0x          |
| ('TLT', '2020-2026 Covid & after', 'Vol target + signal (long-short)') |    -0.33 |          -0.3  | -2.5%        | -37.4%         | 18.7x          |
| ('TLT', '2020-2026 Covid & after', 'Vol target only')                  |    -0.43 |          -0.42 | -3.8%        | -43.0%         | 5.9x           |
| ('TLT', '2020-2026 Covid & after', 'Signal only')                      |    -0.41 |          -0.4  | -3.8%        | -43.3%         | 8.1x           |
| ('TLT', '2020-2026 Covid & after', 'Buy & hold')                       |    -0.36 |          -0.36 | -4.3%        | -48.4%         | 0.0x           |
| ('GLD', '2008-2009 GFC', 'Vol target + signal')                        |     0.99 |           1.03 | 8.4%         | -6.4%          | 11.4x          |
| ('GLD', '2008-2009 GFC', 'Vol target + signal (long-short)')           |    -0.36 |          -0.3  | -4.6%        | -11.5%         | 22.5x          |
| ('GLD', '2008-2009 GFC', 'Vol target only')                            |     1.76 |           1.76 | 21.6%        | -6.6%          | 1.6x           |
| ('GLD', '2008-2009 GFC', 'Signal only')                                |     0.61 |           0.64 | 9.4%         | -14.9%         | 17.1x          |
| ('GLD', '2008-2009 GFC', 'Buy & hold')                                 |     1.66 |           1.66 | 42.5%        | -12.9%         | 0.0x           |
| ('GLD', '2010-2019 post-GFC', 'Vol target + signal')                   |     0.14 |           0.15 | 1.5%         | -39.8%         | 4.9x           |
| ('GLD', '2010-2019 post-GFC', 'Vol target + signal (long-short)')      |     0.09 |           0.1  | 0.9%         | -42.5%         | 5.9x           |
| ('GLD', '2010-2019 post-GFC', 'Vol target only')                       |     0.19 |           0.2  | 2.1%         | -41.0%         | 4.3x           |
| ('GLD', '2010-2019 post-GFC', 'Signal only')                           |     0.18 |           0.18 | 2.2%         | -42.8%         | 1.0x           |
| ('GLD', '2010-2019 post-GFC', 'Buy & hold')                            |     0.23 |           0.23 | 2.9%         | -45.6%         | 0.0x           |
| ('GLD', '2020-2026 Covid & after', 'Vol target + signal')              |     0.75 |           0.76 | 12.8%        | -19.7%         | 3.2x           |
| ('GLD', '2020-2026 Covid & after', 'Vol target + signal (long-short)') |     0.75 |           0.76 | 12.8%        | -19.7%         | 3.2x           |
| ('GLD', '2020-2026 Covid & after', 'Vol target only')                  |     0.75 |           0.76 | 12.8%        | -19.7%         | 3.2x           |
| ('GLD', '2020-2026 Covid & after', 'Signal only')                      |     0.57 |           0.57 | 12.6%        | -34.9%         | 0.0x           |
| ('GLD', '2020-2026 Covid & after', 'Buy & hold')                       |     0.57 |           0.57 | 12.6%        | -34.9%         | 0.0x           |
