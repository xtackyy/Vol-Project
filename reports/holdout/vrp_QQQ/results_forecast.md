# HAR-RV vs ^VXN: forecasting QQQ realized vol over the next 21 trading days

Out-of-sample dates 2004-04-12 to 2026-10-23 (5,671 days; 271 non-overlapping blocks). Forecasts in vol points. HAR models are walk-forward (expanding window, monthly refits, purged), without VIX inputs, Jensen-corrected so the squared forecast targets the mean variance; the uncorrected row forecasts the median.
Inference on daily overlapping data uses Newey-West errors with 20 lags; the block versions use non-overlapping 21-day windows.

## Accuracy (DM t < 0: lower loss than VIX)

|                                 |   n_days |   mean_forecast |   mean_realized |   mean_error |   mae |   rmse |   qlike |   dm_t_sq_err_vs_vix |   dm_t_qlike_vs_vix |
|:--------------------------------|---------:|----------------:|----------------:|-------------:|------:|-------:|--------:|---------------------:|--------------------:|
| VIX                             |     5671 |          22.144 |           18.96 |       -3.183 | 5.984 |  8.114 |   0.25  |              nan     |             nan     |
| HAR-Ridge                       |     5671 |          19.202 |           18.96 |       -0.242 | 4.983 |  7.705 |   0.273 |               -2.163 |               1.129 |
| HAR-OLS                         |     5671 |          19.647 |           18.96 |       -0.687 | 5.258 |  7.99  |   0.271 |               -0.568 |               1.338 |
| HAR-Ridge, no Jensen correction |     5671 |          17.802 |           18.96 |        1.158 | 4.712 |  7.678 |   0.309 |               -1.671 |               1.818 |

## Mincer-Zarnowitz: realized = a + b * forecast (daily, HAC)

|                                 |   mz_alpha |   mz_beta |   mz_r2 |   mz_wald_p |
|:--------------------------------|-----------:|----------:|--------:|------------:|
| VIX                             |     -0.433 |     0.876 |   0.476 |       0     |
| HAR-Ridge                       |      2.636 |     0.85  |   0.446 |       0.057 |
| HAR-OLS                         |      4.038 |     0.76  |   0.437 |       0.001 |
| HAR-Ridge, no Jensen correction |      1.834 |     0.962 |   0.449 |       0.001 |

## Mincer-Zarnowitz on non-overlapping blocks

|                                 |   mz_alpha |   mz_beta |   mz_r2 |   mz_wald_p |
|:--------------------------------|-----------:|----------:|--------:|------------:|
| VIX                             |      0.456 |     0.838 |   0.453 |       0     |
| HAR-Ridge                       |      3.619 |     0.801 |   0.411 |       0.128 |
| HAR-OLS                         |      5.025 |     0.709 |   0.406 |       0.008 |
| HAR-Ridge, no Jensen correction |      2.79  |     0.91  |   0.416 |       0.023 |

## Encompassing: realized = c + b1 * VIX + b2 * HAR (daily, HAC)

|           |   coef |   t_hac |
|:----------|-------:|--------:|
| const     | -0.105 |  -0.088 |
| VIX       |  0.657 |   6.145 |
| HAR-Ridge |  0.236 |   2.36  |

R² = 0.481, n = 5,671

|         |   coef |   t_hac |
|:--------|-------:|--------:|
| const   |  0.144 |   0.132 |
| VIX     |  0.645 |   7.821 |
| HAR-OLS |  0.231 |   2.738 |

R² = 0.484, n = 5,671

## Encompassing on non-overlapping blocks

|           |   coef |   t_hac |
|:----------|-------:|--------:|
| const     |  0.598 |   0.322 |
| VIX       |  0.751 |   4.266 |
| HAR-Ridge |  0.092 |   0.538 |

R² = 0.454, n = 271

## Signal preview: VRP_t (vol points) on spread_t = VIX_t - HAR-Ridge_t (daily, HAC)

|        |   count |   mean |   std |     min |   25% |   50% |   75% |    max |   share_positive |
|:-------|--------:|-------:|------:|--------:|------:|------:|------:|-------:|-----------------:|
| spread |    5671 |  2.942 | 2.947 | -20.805 | 1.282 | 2.923 |  4.66 | 18.108 |             0.88 |

VRP on spread:

|        |   coef |   t_hac |
|:-------|-------:|--------:|
| const  |  2.324 |   4.959 |
| spread |  0.292 |   2.919 |

R² = 0.013, n = 5,671

VRP on VIX level:

|       |   coef |   t_hac |
|:------|-------:|--------:|
| const |  0.433 |   0.368 |
| VIX   |  0.124 |   2.073 |

R² = 0.018, n = 5,671

VRP on both:

|        |   coef |   t_hac |
|:-------|-------:|--------:|
| const  |  0.105 |   0.088 |
| VIX    |  0.108 |   1.765 |
| spread |  0.236 |   2.36  |

R² = 0.026, n = 5,671
