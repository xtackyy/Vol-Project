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
| ret_ic_5d      | 0.092      | -0.106     | nan        |
| ret_ic_t       | 1.74       | -1.30      | nan        |
| ret_view_share | 31.0%      | 14.8%      | 0.0%       |
| ret_r2_oos     | 0.001      | -0.001     | 0.000      |
| vt_sharpe      | 0.57       | 0.21       | 0.51       |
| vt_max_dd      | -28.9%     | -37.1%     | -40.1%     |
| vt_turnover    | 8.15       | 3.83       | 3.33       |
| vt_vol         | 11.8%      | 11.9%      | 12.3%      |
| vt_cagr        | 8.1%       | 3.5%       | 7.1%       |
| bh_sharpe      | 0.52       | 0.16       | 0.49       |
| bh_max_dd      | -55.2%     | -48.4%     | -45.6%     |
| bh_vol         | 18.6%      | 14.9%      | 17.3%      |
| bh_cagr        | 10.2%      | 3.0%       | 8.7%       |

`vol_dm_t` < 0: Ridge beats HAR-OLS. `ret_ic_5d`: rank IC of the 5-day return tilt on days the model has a view, t-stat uses n/5 effective observations.

## Correlation of vol-targeted strategy returns (daily, common window)

|     |   SPY |   TLT |   GLD |
|:----|------:|------:|------:|
| SPY |  1    | -0.24 |  0.08 |
| TLT | -0.24 |  1    |  0.22 |
| GLD |  0.08 |  0.22 |  1    |

Buy & hold, same window, for reference:

|     |   SPY |   TLT |   GLD |
|:----|------:|------:|------:|
| SPY |  1    | -0.3  |  0.09 |
| TLT | -0.3  |  1    |  0.19 |
| GLD |  0.09 |  0.19 |  1    |

## Equal-weight book of the vol-targeted sleeves (2008-11-19 to 2026-11-20, 18.0 years)

|                             | ann_return   | ann_vol   |   sharpe |   sortino | max_drawdown   |   calmar |
|:----------------------------|:-------------|:----------|---------:|----------:|:---------------|---------:|
| SPY                         | 10.2%        | 11.5%     |     0.78 |      1.07 | -17.1%         |     0.6  |
| TLT                         | 2.6%         | 11.9%     |     0.16 |      0.22 | -37.1%         |     0.07 |
| GLD                         | 7.1%         | 12.3%     |     0.51 |      0.71 | -40.1%         |     0.18 |
| Equal-weight (vol-targeted) | 7.1%         | 7.1%      |     0.8  |      1.14 | -16.9%         |     0.42 |

Average pairwise correlation 0.02; diversification ratio (avg sleeve vol / book vol) 1.69. The book is reset to equal weights daily; that rebalancing costs 2.0 bps/yr and is deducted.

## Regime breakdown per asset

|                                                                        |   sharpe |   sharpe_gross | ann_return   | max_drawdown   | ann_turnover   |
|:-----------------------------------------------------------------------|---------:|---------------:|:-------------|:---------------|:---------------|
| ('SPY', '2004-2007 pre-GFC', 'Vol target + signal')                    |     0.3  |           0.31 | 6.6%         | -8.9%          | 8.2x           |
| ('SPY', '2004-2007 pre-GFC', 'Vol target + signal (long-short)')       |     0.3  |           0.31 | 6.6%         | -8.9%          | 8.2x           |
| ('SPY', '2004-2007 pre-GFC', 'Vol target only')                        |     0.3  |           0.31 | 6.6%         | -8.9%          | 8.2x           |
| ('SPY', '2004-2007 pre-GFC', 'Signal only')                            |     0.46 |           0.46 | 8.6%         | -9.9%          | 0.0x           |
| ('SPY', '2004-2007 pre-GFC', 'Buy & hold')                             |     0.46 |           0.46 | 8.6%         | -9.9%          | 0.0x           |
| ('SPY', '2008-2009 GFC', 'Vol target + signal')                        |    -0.34 |          -0.34 | -3.9%        | -23.4%         | 3.0x           |
| ('SPY', '2008-2009 GFC', 'Vol target + signal (long-short)')           |    -0.34 |          -0.34 | -3.9%        | -23.4%         | 3.0x           |
| ('SPY', '2008-2009 GFC', 'Vol target only')                            |    -0.34 |          -0.34 | -3.9%        | -23.4%         | 3.0x           |
| ('SPY', '2008-2009 GFC', 'Signal only')                                |    -0.17 |          -0.17 | -10.6%       | -51.9%         | 0.0x           |
| ('SPY', '2008-2009 GFC', 'Buy & hold')                                 |    -0.17 |          -0.17 | -10.6%       | -51.9%         | 0.0x           |
| ('SPY', '2010-2019 post-GFC', 'Vol target + signal')                   |     0.9  |           0.91 | 10.8%        | -14.9%         | 8.6x           |
| ('SPY', '2010-2019 post-GFC', 'Vol target + signal (long-short)')      |     0.9  |           0.91 | 10.8%        | -14.9%         | 8.6x           |
| ('SPY', '2010-2019 post-GFC', 'Vol target only')                       |     0.9  |           0.91 | 10.8%        | -14.9%         | 8.6x           |
| ('SPY', '2010-2019 post-GFC', 'Signal only')                           |     0.9  |           0.9  | 13.5%        | -19.3%         | 0.0x           |
| ('SPY', '2010-2019 post-GFC', 'Buy & hold')                            |     0.9  |           0.9  | 13.5%        | -19.3%         | 0.0x           |
| ('SPY', '2020-2026 Covid & after', 'Vol target + signal')              |     0.54 |           0.55 | 8.9%         | -17.1%         | 9.0x           |
| ('SPY', '2020-2026 Covid & after', 'Vol target + signal (long-short)') |     0.54 |           0.55 | 8.9%         | -17.1%         | 9.0x           |
| ('SPY', '2020-2026 Covid & after', 'Vol target only')                  |     0.54 |           0.55 | 8.9%         | -17.1%         | 9.0x           |
| ('SPY', '2020-2026 Covid & after', 'Signal only')                      |     0.58 |           0.58 | 13.3%        | -33.7%         | 0.0x           |
| ('SPY', '2020-2026 Covid & after', 'Buy & hold')                       |     0.58 |           0.58 | 13.3%        | -33.7%         | 0.0x           |
| ('TLT', '2004-2007 pre-GFC', 'Vol target + signal')                    |     0.62 |           0.63 | 11.8%        | -12.9%         | 1.0x           |
| ('TLT', '2004-2007 pre-GFC', 'Vol target + signal (long-short)')       |     0.62 |           0.63 | 11.8%        | -12.9%         | 1.0x           |
| ('TLT', '2004-2007 pre-GFC', 'Vol target only')                        |     0.62 |           0.63 | 11.8%        | -12.9%         | 1.0x           |
| ('TLT', '2004-2007 pre-GFC', 'Signal only')                            |     0.72 |           0.73 | 11.2%        | -8.0%          | 0.0x           |
| ('TLT', '2004-2007 pre-GFC', 'Buy & hold')                             |     0.72 |           0.73 | 11.2%        | -8.0%          | 0.0x           |
| ('TLT', '2008-2009 GFC', 'Vol target + signal')                        |     0.15 |           0.15 | 1.8%         | -16.4%         | 1.3x           |
| ('TLT', '2008-2009 GFC', 'Vol target + signal (long-short)')           |     0.15 |           0.15 | 1.8%         | -16.4%         | 1.3x           |
| ('TLT', '2008-2009 GFC', 'Vol target only')                            |     0.15 |           0.15 | 1.8%         | -16.4%         | 1.3x           |
| ('TLT', '2008-2009 GFC', 'Signal only')                                |     0.18 |           0.18 | 2.3%         | -26.6%         | 0.0x           |
| ('TLT', '2008-2009 GFC', 'Buy & hold')                                 |     0.18 |           0.18 | 2.3%         | -26.6%         | 0.0x           |
| ('TLT', '2010-2019 post-GFC', 'Vol target + signal')                   |     0.6  |           0.61 | 7.2%         | -17.8%         | 4.3x           |
| ('TLT', '2010-2019 post-GFC', 'Vol target + signal (long-short)')      |     0.6  |           0.61 | 7.2%         | -17.8%         | 4.3x           |
| ('TLT', '2010-2019 post-GFC', 'Vol target only')                       |     0.6  |           0.61 | 7.2%         | -17.8%         | 4.3x           |
| ('TLT', '2010-2019 post-GFC', 'Signal only')                           |     0.54 |           0.54 | 7.2%         | -20.7%         | 0.0x           |
| ('TLT', '2010-2019 post-GFC', 'Buy & hold')                            |     0.54 |           0.54 | 7.2%         | -20.7%         | 0.0x           |
| ('TLT', '2020-2026 Covid & after', 'Vol target + signal')              |    -0.41 |          -0.39 | -1.9%        | -33.4%         | 9.3x           |
| ('TLT', '2020-2026 Covid & after', 'Vol target + signal (long-short)') |    -0.32 |          -0.29 | -1.7%        | -32.2%         | 16.1x          |
| ('TLT', '2020-2026 Covid & after', 'Vol target only')                  |    -0.4  |          -0.39 | -2.7%        | -37.1%         | 4.5x           |
| ('TLT', '2020-2026 Covid & after', 'Signal only')                      |    -0.41 |          -0.4  | -3.8%        | -43.3%         | 8.1x           |
| ('TLT', '2020-2026 Covid & after', 'Buy & hold')                       |    -0.36 |          -0.36 | -4.3%        | -48.4%         | 0.0x           |
| ('GLD', '2008-2009 GFC', 'Vol target + signal')                        |     1.77 |           1.78 | 21.8%        | -6.3%          | 1.6x           |
| ('GLD', '2008-2009 GFC', 'Vol target + signal (long-short)')           |     1.77 |           1.78 | 21.8%        | -6.3%          | 1.6x           |
| ('GLD', '2008-2009 GFC', 'Vol target only')                            |     1.77 |           1.78 | 21.8%        | -6.3%          | 1.6x           |
| ('GLD', '2008-2009 GFC', 'Signal only')                                |     1.66 |           1.66 | 42.5%        | -12.9%         | 0.0x           |
| ('GLD', '2008-2009 GFC', 'Buy & hold')                                 |     1.66 |           1.66 | 42.5%        | -12.9%         | 0.0x           |
| ('GLD', '2010-2019 post-GFC', 'Vol target + signal')                   |     0.21 |           0.22 | 2.4%         | -40.1%         | 3.9x           |
| ('GLD', '2010-2019 post-GFC', 'Vol target + signal (long-short)')      |     0.21 |           0.22 | 2.4%         | -40.1%         | 3.9x           |
| ('GLD', '2010-2019 post-GFC', 'Vol target only')                       |     0.21 |           0.22 | 2.4%         | -40.1%         | 3.9x           |
| ('GLD', '2010-2019 post-GFC', 'Signal only')                           |     0.23 |           0.23 | 2.9%         | -45.6%         | 0.0x           |
| ('GLD', '2010-2019 post-GFC', 'Buy & hold')                            |     0.23 |           0.23 | 2.9%         | -45.6%         | 0.0x           |
| ('GLD', '2020-2026 Covid & after', 'Vol target + signal')              |     0.75 |           0.75 | 12.2%        | -18.2%         | 2.8x           |
| ('GLD', '2020-2026 Covid & after', 'Vol target + signal (long-short)') |     0.75 |           0.75 | 12.2%        | -18.2%         | 2.8x           |
| ('GLD', '2020-2026 Covid & after', 'Vol target only')                  |     0.75 |           0.75 | 12.2%        | -18.2%         | 2.8x           |
| ('GLD', '2020-2026 Covid & after', 'Signal only')                      |     0.57 |           0.57 | 12.6%        | -34.9%         | 0.0x           |
| ('GLD', '2020-2026 Covid & after', 'Buy & hold')                       |     0.57 |           0.57 | 12.6%        | -34.9%         | 0.0x           |
