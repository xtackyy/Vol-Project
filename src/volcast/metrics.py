"""Forecast-evaluation statistics and portfolio performance metrics."""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

from .config import TRADING_DAYS

# ----------------------------------------------------------------------------- forecasts


def r2_oos(y: pd.Series, pred: pd.Series, bench: pd.Series) -> float:
    """Campbell-Thompson out-of-sample R^2 relative to a benchmark forecast."""
    sse_model = float(((y - pred) ** 2).sum())
    sse_bench = float(((y - bench) ** 2).sum())
    return 1.0 - sse_model / sse_bench


def qlike(actual_var: pd.Series, forecast_var: pd.Series) -> float:
    """QLIKE loss (Patton, 2011): robust to noise in the realized-variance proxy."""
    ratio = actual_var / forecast_var
    return float((ratio - np.log(ratio) - 1).mean())


def mincer_zarnowitz(y: pd.Series, pred: pd.Series, hac_lags: int) -> dict[str, float]:
    """Regress realised on forecast; an unbiased forecast has a=0, b=1."""
    res = sm.OLS(y, sm.add_constant(pred.rename("pred"))).fit(
        cov_type="HAC", cov_kwds={"maxlags": hac_lags}
    )
    wald = res.wald_test("const = 0, pred = 1", scalar=True)
    return {"mz_alpha": float(res.params["const"]), "mz_beta": float(res.params["pred"]),
            "mz_r2": float(res.rsquared), "mz_wald_p": float(wald.pvalue)}


def diebold_mariano(e_model: pd.Series, e_bench: pd.Series, horizon: int) -> dict[str, float]:
    """DM test on squared errors with Newey-West variance and the HLN small-sample correction.

    Negative statistic => the model has lower loss than the benchmark.
    """
    d = (e_model**2 - e_bench**2).dropna().to_numpy()
    n = len(d)
    d_bar = d.mean()
    lag = max(horizon - 1, 0)
    gamma = [np.mean((d[k:] - d_bar) * (d[: n - k] - d_bar)) for k in range(lag + 1)]
    var = gamma[0] + 2 * sum((1 - k / (lag + 1)) * gamma[k] for k in range(1, lag + 1))
    dm = d_bar / np.sqrt(var / n)
    hln = np.sqrt((n + 1 - 2 * horizon + horizon * (horizon - 1) / n) / n)
    stat = dm * hln
    return {"dm_stat": float(stat), "dm_p_value": float(2 * stats.t.sf(abs(stat), df=n - 1))}


def regression_report(y: pd.Series, pred: pd.Series, bench: pd.Series) -> dict[str, float]:
    """Out-of-sample accuracy on the dates where truth, forecast and benchmark all exist."""
    idx = y.dropna().index.intersection(pred.index).intersection(bench.index)
    y, pred, bench = y.loc[idx], pred.loc[idx], bench.loc[idx]
    err = y - pred
    return {
        "n_oos": len(idx),
        "r2_oos_vs_mean": r2_oos(y, pred, bench),
        "rmse": float(np.sqrt((err**2).mean())),
        "mae": float(err.abs().mean()),
        "corr": float(np.corrcoef(y, pred)[0, 1]),
        "hit_rate_sign": float((np.sign(y) == np.sign(pred)).mean()),
    }


def information_coefficient(y: pd.Series, pred: pd.Series, bench: pd.Series, horizon: int) -> dict[str, float]:
    """Rank IC of the model's *tilt* (forecast minus training-window mean) vs realised
    return minus that mean, on days the model has a view (tilt != 0).

    Overlapping h-day labels are not independent, so the t-stat uses n_eff = n / h.
    """
    idx = y.dropna().index.intersection(pred.index).intersection(bench.index)
    tilt, real = pred.loc[idx] - bench.loc[idx], y.loc[idx] - bench.loc[idx]
    view = tilt.abs() > 1e-12
    n = int(view.sum())
    if n < 30:
        return {"ic": float("nan"), "ic_t": float("nan"), "view_share": n / max(len(idx), 1), "n_view": n}
    ic = float(stats.spearmanr(tilt[view], real[view])[0])
    n_eff = n / horizon
    t = ic * np.sqrt(max(n_eff - 2, 1) / max(1 - ic**2, 1e-12))
    return {"ic": ic, "ic_t": float(t), "view_share": n / len(idx), "n_view": n}


# ----------------------------------------------------------------------------- portfolios


def drawdown(net: pd.Series) -> pd.Series:
    equity = (1 + net).cumprod()
    return equity / equity.cummax() - 1


def sharpe(ret: pd.Series, rf: pd.Series) -> float:
    excess = ret - rf.reindex(ret.index).fillna(0.0)
    sd = excess.std()
    return float(excess.mean() / sd * np.sqrt(TRADING_DAYS)) if sd > 0 else float("nan")


def performance(net: pd.Series, rf: pd.Series, turnover: pd.Series | None = None,
                weight: pd.Series | None = None, gross: pd.Series | None = None,
                costs: pd.Series | None = None) -> dict[str, float]:
    """Annualised performance on daily simple returns. Sharpe/Sortino use excess returns.

    With `gross` (returns before trading costs) and `costs`, also reports the gross Sharpe
    and the annual cost drag in bps, so transaction-cost drag is explicit.
    """
    rf = rf.reindex(net.index).fillna(0.0)
    excess = net - rf
    years = len(net) / TRADING_DAYS
    equity = (1 + net).cumprod()
    downside = np.sqrt((excess.clip(upper=0) ** 2).mean())
    max_dd = float(drawdown(net).min())
    cagr = float(equity.iloc[-1] ** (1 / years) - 1)
    out = {
        "ann_return": cagr,
        "ann_vol": float(net.std() * np.sqrt(TRADING_DAYS)),
        "sharpe": float(excess.mean() / excess.std() * np.sqrt(TRADING_DAYS)),
        "sortino": float(excess.mean() / downside * np.sqrt(TRADING_DAYS)),
        "max_drawdown": max_dd,
        "calmar": cagr / abs(max_dd) if max_dd < 0 else np.nan,
        "skew": float(net.skew()),
    }
    if gross is not None:
        out["sharpe_gross"] = sharpe(gross, rf)
    if costs is not None:
        out["cost_drag_bps"] = float(costs.mean() * TRADING_DAYS * 1e4)
    if turnover is not None:
        out["ann_turnover"] = float(turnover.iloc[1:].mean() * TRADING_DAYS)  # ex initial buy
    if weight is not None:
        out["avg_exposure"] = float(weight.mean())
        out["pct_short"] = float((weight < 0).mean())
    return out


def regime_table(backtests: dict, rf: pd.Series, regimes: dict[str, tuple[str, str]]) -> pd.DataFrame:
    """Sharpe (net & gross), CAGR, max drawdown and turnover per strategy per sub-period.

    Drawdowns are measured from each sub-period's own start, so regimes are comparable.
    """
    rows = []
    for regime, (start, end) in regimes.items():
        for name, bt in backtests.items():
            sl = slice(start, end)
            net, gross = bt.net.loc[sl], bt.gross.loc[sl]
            turn = bt.turnover.iloc[1:].loc[sl]  # ex the initial entry trade
            if len(net) < 60:
                continue
            years = len(net) / TRADING_DAYS
            rows.append({
                "regime": regime, "strategy": name,
                "sharpe": sharpe(net, rf), "sharpe_gross": sharpe(gross, rf),
                "ann_return": float((1 + net).prod() ** (1 / years) - 1),
                "max_drawdown": float(drawdown(net).min()),
                "ann_turnover": float(turn.mean() * TRADING_DAYS),
            })
    return pd.DataFrame(rows).set_index(["regime", "strategy"])


def rolling_sharpe(net: pd.Series, rf: pd.Series, window: int = TRADING_DAYS) -> pd.Series:
    excess = net - rf.reindex(net.index).fillna(0.0)
    return excess.rolling(window).mean() / excess.rolling(window).std() * np.sqrt(TRADING_DAYS)
