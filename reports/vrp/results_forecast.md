# HAR-RV vs VIX: forecasting SPY realized vol over the next 21 trading days

Out-of-sample dates 1998-02-23 to 2026-10-22 (7,212 days; 344 non-overlapping blocks). Forecasts in vol points. HAR models are walk-forward (expanding window, monthly refits, purged), without VIX inputs, Jensen-corrected so the squared forecast targets the mean variance; the uncorrected row forecasts the median.
Inference on daily overlapping data uses Newey-West errors with 20 lags; the block versions use non-overlapping 21-day windows.

## Accuracy (DM t < 0: lower loss than VIX)

|                                 |   n_days |   mean_forecast |   mean_realized |   mean_error |   mae |   rmse |   qlike |   dm_t_sq_err_vs_vix |   dm_t_qlike_vs_vix |
|:--------------------------------|---------:|----------------:|----------------:|-------------:|------:|-------:|--------:|---------------------:|--------------------:|
| VIX                             |     7212 |          20.137 |          16.427 |       -3.711 | 6.055 |  8.132 |   0.317 |              nan     |             nan     |
| HAR-Ridge                       |     7212 |          18.281 |          16.427 |       -1.855 | 5.202 |  7.811 |   0.318 |               -1.977 |               0.043 |
| HAR-OLS                         |     7212 |          18.495 |          16.427 |       -2.068 | 5.265 |  7.689 |   0.305 |               -3.64  |              -0.961 |
| HAR-Ridge, no Jensen correction |     7212 |          15.687 |          16.427 |        0.739 | 4.334 |  7.368 |   0.354 |               -3.048 |               0.906 |

## Mincer-Zarnowitz: realized = a + b * forecast (daily, HAC)

|                                 |   mz_alpha |   mz_beta |   mz_r2 |   mz_wald_p |
|:--------------------------------|-----------:|----------:|--------:|------------:|
| VIX                             |     -1.386 |     0.885 |   0.507 |       0     |
| HAR-Ridge                       |      1.622 |     0.81  |   0.474 |       0     |
| HAR-OLS                         |      0.317 |     0.871 |   0.485 |       0     |
| HAR-Ridge, no Jensen correction |      1.098 |     0.977 |   0.485 |       0.023 |

## Mincer-Zarnowitz on non-overlapping blocks

|                                 |   mz_alpha |   mz_beta |   mz_r2 |   mz_wald_p |
|:--------------------------------|-----------:|----------:|--------:|------------:|
| VIX                             |     -2.669 |     0.951 |   0.528 |       0     |
| HAR-Ridge                       |      0.897 |     0.857 |   0.468 |       0     |
| HAR-OLS                         |      0.575 |     0.859 |   0.468 |       0     |
| HAR-Ridge, no Jensen correction |      0.323 |     1.036 |   0.479 |       0.068 |

## Encompassing: realized = c + b1 * VIX + b2 * HAR (daily, HAC)

|           |   coef |   t_hac |
|:----------|-------:|--------:|
| const     | -1.037 |  -0.941 |
| VIX       |  0.665 |   6.484 |
| HAR-Ridge |  0.223 |   2.601 |

R² = 0.511, n = 7,212

|         |   coef |   t_hac |
|:--------|-------:|--------:|
| const   | -1.347 |  -1.234 |
| VIX     |  0.593 |   7.321 |
| HAR-OLS |  0.316 |   3.002 |

R² = 0.515, n = 7,212

## Encompassing on non-overlapping blocks

|           |   coef |   t_hac |
|:----------|-------:|--------:|
| const     | -2.543 |  -1.465 |
| VIX       |  0.856 |   3.203 |
| HAR-Ridge |  0.098 |   0.447 |

R² = 0.529, n = 344

## Signal preview: VRP_t (vol points) on spread_t = VIX_t - HAR-Ridge_t (daily, HAC)

|        |   count |   mean |   std |     min |   25% |   50% |   75% |    max |   share_positive |
|:-------|--------:|-------:|------:|--------:|------:|------:|------:|-------:|-----------------:|
| spread |    7212 |  1.856 | 3.129 | -30.982 | 0.329 | 1.782 | 3.415 | 21.611 |            0.787 |

VRP on spread:

|        |   coef |   t_hac |
|:-------|-------:|--------:|
| const  |  3.277 |   9.66  |
| spread |  0.234 |   2.629 |

R² = 0.010, n = 7,212

VRP on VIX level:

|       |   coef |   t_hac |
|:------|-------:|--------:|
| const |  1.386 |   1.234 |
| VIX   |  0.115 |   1.83  |

R² = 0.017, n = 7,212

VRP on both:

|        |   coef |   t_hac |
|:-------|-------:|--------:|
| const  |  1.037 |   0.941 |
| VIX    |  0.112 |   1.807 |
| spread |  0.223 |   2.601 |

R² = 0.026, n = 7,212
