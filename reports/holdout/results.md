# Holdout: frozen pipeline on assets it had never been run on

Settings frozen in HOLDOUT.md before this run; nothing was changed after it. Next-open fills, net of costs. Sharpe on excess returns.

|                       | IWM        | EFA        | EEM        | IEF        |
|:----------------------|:-----------|:-----------|:-----------|:-----------|
| oos_start             | 2004-06-03 | 2005-09-01 | 2007-04-17 | 2006-07-31 |
| oos_end               | 2026-11-23 | 2026-11-23 | 2026-11-23 | 2026-11-20 |
| cost_bps              | 2.000      | 2.500      | 3.000      | 2.000      |
| vol_r2_oos_ridge      | 0.662      | 0.608      | 0.599      | 0.533      |
| vol_r2_oos_har        | 0.618      | 0.548      | 0.562      | 0.513      |
| dm_t_ridge_vs_har     | -7.707     | -8.509     | -6.375     | -2.389     |
| vt_sharpe             | 0.310      | 0.211      | 0.137      | 0.233      |
| bh_sharpe             | 0.389      | 0.285      | 0.223      | 0.265      |
| vt_max_dd             | -25.8%     | -31.5%     | -29.0%     | -35.6%     |
| bh_max_dd             | -58.6%     | -61.0%     | -66.4%     | -23.9%     |
| vt_ann_vol            | 11.7%      | 11.4%      | 11.4%      | 9.5%       |
| vt_turnover           | 3.230      | 5.692      | 4.847      | 1.591      |
| sharpe_gap_ex_2008_09 | -0.105     | -0.106     | -0.108     | -0.022     |
| years_vt_beats_bh     | 2 of 23    | 3 of 22    | 3 of 20    | 4 of 21    |
