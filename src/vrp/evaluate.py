"""Statistics for the VRP study.

Overlap: daily 21-day-ahead labels share 20 of 21 days with their neighbours, so a plain t-stat
on daily data overstates significance about 21-fold in sample size. Two fixes are used:
  * non-overlapping 21-day blocks ("months") for counts, skew, worst months and plain t-stats;
  * Newey-West (HAC) standard errors with h - 1 lags whenever daily overlapping data is used.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm


def hac_mean_test(x: pd.Series, lags: int) -> dict[str, float]:
    """Mean of `x` with a Newey-West t-stat (regression of x on a constant)."""
    x = x.dropna()
    fit = sm.OLS(x.to_numpy(), np.ones(len(x))).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return {"mean": float(fit.params[0]), "t_hac": float(fit.tvalues[0]), "n": len(x)}


def describe_vrp(blocks: pd.DataFrame) -> pd.Series:
    """Summary of the VRP over non-overlapping blocks, in vol points and variance points."""
    v, vp = blocks["vrp_vol"], blocks["vrp_varpts"]
    n = len(v)
    return pd.Series({
        "blocks": n,
        "first_entry": blocks.index[0].date(), "last_entry": blocks.index[-1].date(),
        "mean_implied_vol": blocks["iv_vol"].mean(), "mean_realized_vol": blocks["rv_vol"].mean(),
        "mean_vrp_vol": v.mean(), "median_vrp_vol": v.median(), "std_vrp_vol": v.std(),
        "t_vrp_vol": v.mean() / (v.std() / np.sqrt(n)),
        "share_positive": float((v > 0).mean()),
        "skew_vrp_vol": float(v.skew()), "skew_vrp_varpts": float(vp.skew()),
        "mean_vrp_varpts": vp.mean(), "median_vrp_varpts": vp.median(),
        "p5_vrp_vol": v.quantile(0.05), "p1_vrp_vol": v.quantile(0.01), "min_vrp_vol": v.min(),
    })


def worst_blocks(blocks: pd.DataFrame, k: int = 10) -> pd.DataFrame:
    cols = ["iv_vol", "rv_vol", "vrp_vol", "vrp_varpts"]
    return blocks.nsmallest(k, "vrp_vol")[cols]


def vrp_by_period(daily: pd.DataFrame, periods: dict[str, tuple[str, str]]) -> pd.DataFrame:
    """VRP for every daily entry date inside each window (overlapping windows).

    Daily entries, not the fixed block calendar: a short window like Feb 2018 can fall between
    two block entry dates and would then look harmless.
    """
    rows = {}
    for name, (a, b) in periods.items():
        x = daily.loc[a:b].dropna(subset=["vrp_vol"])
        if len(x):
            worst = x["vrp_vol"].idxmin()
            rows[name] = {"entry_days": len(x), "mean_implied_vol": x["iv_vol"].mean(),
                          "mean_realized_vol": x["rv_vol"].mean(), "mean_vrp_vol": x["vrp_vol"].mean(),
                          "worst_vrp_vol": x["vrp_vol"].min(), "worst_entry": worst.date(),
                          "share_positive": float((x["vrp_vol"] > 0).mean())}
    return pd.DataFrame.from_dict(rows, orient="index")


def vrp_by_year(blocks: pd.DataFrame) -> pd.DataFrame:
    g = blocks.groupby(blocks.index.year)
    return pd.DataFrame({"blocks": g.size(), "mean_implied_vol": g["iv_vol"].mean(),
                         "mean_realized_vol": g["rv_vol"].mean(), "mean_vrp_vol": g["vrp_vol"].mean(),
                         "worst_vrp_vol": g["vrp_vol"].min(),
                         "share_positive": g["vrp_vol"].apply(lambda s: float((s > 0).mean()))})
