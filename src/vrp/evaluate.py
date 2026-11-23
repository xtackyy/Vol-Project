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

from volcast.metrics import diebold_mariano, mincer_zarnowitz, qlike


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


def _qlike_t(rv_vol: pd.Series, f_vol: pd.Series) -> pd.Series:
    """Per-day QLIKE loss on variances (vol points squared; the scale cancels in the ratio)."""
    ratio = rv_vol**2 / f_vol**2
    return ratio - np.log(ratio) - 1


def forecast_accuracy(rv_vol: pd.Series, forecasts: dict[str, pd.Series], horizon: int,
                      reference: str = "VIX") -> pd.DataFrame:
    """MAE / RMSE in vol points and QLIKE on variance, on the dates every forecast covers.

    DM t-stats compare each forecast with `reference` (negative = lower loss than VIX):
    on squared vol errors (volcast's DM, HLN-corrected) and on QLIKE (HAC mean of the loss
    difference, h-1 lags).
    """
    df = pd.concat({"rv": rv_vol, **forecasts}, axis=1).dropna()
    rows = {}
    for name in forecasts:
        e = df["rv"] - df[name]
        row = {"n_days": len(df), "mean_forecast": df[name].mean(), "mean_realized": df["rv"].mean(),
               "mean_error": e.mean(), "mae": e.abs().mean(), "rmse": float(np.sqrt((e**2).mean())),
               "qlike": qlike((df["rv"] / 100) ** 2, (df[name] / 100) ** 2)}
        if name != reference:
            e_ref = df["rv"] - df[reference]
            row["dm_t_sq_err_vs_vix"] = diebold_mariano(e, e_ref, horizon)["dm_stat"]
            d = _qlike_t(df["rv"], df[name]) - _qlike_t(df["rv"], df[reference])
            row["dm_t_qlike_vs_vix"] = hac_mean_test(d, horizon - 1)["t_hac"]
        rows[name] = row
    return pd.DataFrame(rows).T


def mz_table(rv_vol: pd.Series, forecasts: dict[str, pd.Series], lags: int) -> pd.DataFrame:
    """Mincer-Zarnowitz: realized = a + b * forecast; unbiased means a = 0, b = 1 (HAC errors)."""
    df = pd.concat({"rv": rv_vol, **forecasts}, axis=1).dropna()
    return pd.DataFrame({k: mincer_zarnowitz(df["rv"], df[k], lags) for k in forecasts}).T


def ols_hac(y: pd.Series, X: pd.DataFrame, lags: int) -> pd.DataFrame:
    """OLS with a constant and Newey-West errors; coefficient table with R^2 and n in .attrs."""
    df = pd.concat([y.rename("y"), X], axis=1).dropna()
    fit = sm.OLS(df["y"], sm.add_constant(df[X.columns])).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    out = pd.DataFrame({"coef": fit.params, "t_hac": fit.tvalues})
    out.attrs.update(r2=float(fit.rsquared), n=int(fit.nobs))
    return out


def encompassing(rv_vol: pd.Series, a: pd.Series, b: pd.Series, lags: int) -> pd.DataFrame:
    """realized = c + b1 * a + b2 * b. If b2 is significant, forecast b adds information beyond a."""
    return ols_hac(rv_vol, pd.concat({a.name: a, b.name: b}, axis=1), lags)


def strategy_stats(bt: pd.DataFrame, capital: float) -> dict[str, float]:
    """Risk and return of a daily $ P&L series, as % of a fixed capital (no compounding).

    Sharpe = mean / std of daily P&L x sqrt(252): a swap is unfunded, so the capital (margin)
    would earn the risk-free rate on top and the P&L itself is already an excess return.
    """
    pnl = bt["pnl"]
    downside = np.sqrt((pnl.clip(upper=0) ** 2).mean())
    cum = pnl.cumsum()
    monthly = pnl.resample("ME").sum()
    return {
        "ann_return": pnl.mean() * 252 / capital,
        "ann_vol": pnl.std() * np.sqrt(252) / capital,
        "sharpe": pnl.mean() / pnl.std() * np.sqrt(252),
        "sortino": pnl.mean() / downside * np.sqrt(252),
        "max_drawdown": (cum - cum.cummax()).min() / capital,
        "worst_month": monthly.min() / capital,
        "worst_21d": pnl.rolling(21).sum().min() / capital,
        "skew_daily": float(pnl.skew()),
        "skew_monthly": float(monthly.skew()),
        "time_in_market": float((bt["vega"] > 0).mean()),
        "avg_vega_in_market": float(bt.loc[bt["vega"] > 0, "vega"].mean()),
    }


def period_pnl(pnl: pd.Series, periods: dict[str, tuple[str, str]], capital: float) -> pd.Series:
    """Total P&L inside each window, % of capital."""
    return pd.Series({k: pnl.loc[a:b].sum() / capital for k, (a, b) in periods.items()})


def etp_stats(ret: pd.Series) -> dict[str, float]:
    """Compounded stats of a daily return series (the tradable-proxy check)."""
    ret = ret.dropna()
    eq = (1 + ret).cumprod()
    years = len(ret) / 252
    return {"start": ret.index[0].date(), "ann_return": eq.iloc[-1] ** (1 / years) - 1,
            "ann_vol": ret.std() * np.sqrt(252), "sharpe": ret.mean() / ret.std() * np.sqrt(252),
            "max_drawdown": (eq / eq.cummax() - 1).min(),
            "worst_month": (1 + ret).resample("ME").prod().min() - 1,
            "time_in_market": float((ret != 0).mean())}


def vrp_by_year(blocks: pd.DataFrame) -> pd.DataFrame:
    g = blocks.groupby(blocks.index.year)
    return pd.DataFrame({"blocks": g.size(), "mean_implied_vol": g["iv_vol"].mean(),
                         "mean_realized_vol": g["rv_vol"].mean(), "mean_vrp_vol": g["vrp_vol"].mean(),
                         "worst_vrp_vol": g["vrp_vol"].min(),
                         "share_positive": g["vrp_vol"].apply(lambda s: float((s > 0).mean()))})
