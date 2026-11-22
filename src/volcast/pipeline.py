"""End-to-end orchestration: data -> features -> walk-forward models -> strategy -> report."""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from . import plotting
from .backtest import BacktestResult, buy_and_hold, run_backtest
from .config import REGIMES, Config, StrategyConfig
from .data import load_market_data
from .features import HAR_FEATURES, make_dataset, proxy_calibration, vol_feature_columns
from .metrics import (
    diebold_mariano,
    drawdown,
    information_coefficient,
    mincer_zarnowitz,
    performance,
    qlike,
    regime_table,
    regression_report,
    rolling_sharpe,
)
from .models import HAROLS, WalkForwardResult, har_inference_table, penalised_regression, walk_forward
from .strategy import expected_excess_return, target_weights

log = logging.getLogger(__name__)

STRATEGY_NAMES = {
    "vol_target_signal": "Vol target + signal",
    "vol_target_signal_ls": "Vol target + signal (long-short)",
    "vol_target_only": "Vol target only",
    "signal_only": "Signal only",
}


@dataclass
class Forecasts:
    """Everything that depends only on the models, not on the strategy settings."""

    market: pd.DataFrame
    features: pd.DataFrame
    targets: pd.DataFrame
    vol_ridge: WalkForwardResult
    vol_har: WalkForwardResult
    ret_model: WalkForwardResult
    vol_metrics: pd.DataFrame
    ret_metrics: pd.DataFrame
    har_inference: pd.DataFrame
    ret_horizon: int


@dataclass
class StrategyResult:
    weights: pd.DataFrame
    expected_ret: pd.Series
    backtests: dict[str, BacktestResult]
    performance: pd.DataFrame
    regimes: pd.DataFrame


@dataclass
class RunResult:
    vol_metrics: pd.DataFrame
    ret_metrics: pd.DataFrame
    performance: pd.DataFrame
    regimes: pd.DataFrame
    har_inference: pd.DataFrame
    vol_ridge: WalkForwardResult
    vol_har: WalkForwardResult
    ret_model: WalkForwardResult
    backtests: dict[str, BacktestResult]
    figures: list[Path]


def _vol_metrics(y: pd.Series, ridge: WalkForwardResult, har: WalkForwardResult, h: int) -> pd.DataFrame:
    idx = y.dropna().index.intersection(ridge.predictions.index).intersection(har.predictions.index)
    rows = {}
    for name, res in {"Ridge-HAR (Model A)": ridge, "HAR-RV OLS (baseline)": har}.items():
        pred = res.predictions.loc[idx]
        row = regression_report(y.loc[idx], pred, res.benchmark.loc[idx])
        vol_err = np.exp(y.loc[idx]) - np.exp(pred)
        row["rmse_vol_pts"] = float(np.sqrt((vol_err**2).mean()) * 100)  # in annualised vol points
        row["qlike"] = qlike(np.exp(2 * y.loc[idx]), np.exp(2 * pred))
        row.update(mincer_zarnowitz(y.loc[idx], pred, hac_lags=h))
        row.pop("hit_rate_sign")
        rows[name] = row
    dm = diebold_mariano(y.loc[idx] - ridge.predictions.loc[idx], y.loc[idx] - har.predictions.loc[idx], h)
    rows["Ridge-HAR (Model A)"].update(dm)
    return pd.DataFrame(rows).T


def fit_forecasts(cfg: Config, market: pd.DataFrame | None = None) -> Forecasts:
    """Walk-forward fit of Model A (vol), the HAR baseline and Model B (returns)."""
    m = cfg.model
    df = load_market_data(cfg.data) if market is None else market
    feats, targets = make_dataset(df, m.vol_horizon, m.ret_horizon, cfg.data.asset_class)
    log.info("dataset: %d rows x %d features, %s -> %s", *feats.shape, feats.index[0].date(),
             feats.index[-1].date())
    wf = dict(min_train=m.min_train_days, refit_every=m.refit_every, rolling_window=m.rolling_window)

    # ---- Model A: volatility (purge & CV gap = vol horizon).
    vol_cols = vol_feature_columns(feats)
    vol_ridge = walk_forward(
        feats[vol_cols], targets["y_vol"],
        penalised_regression("ridge", m.vol_alphas, m.cv_splits, gap=m.vol_horizon),
        horizon=m.vol_horizon, **wf)
    vol_har = walk_forward(feats[HAR_FEATURES], targets["y_vol"], HAROLS, horizon=m.vol_horizon, **wf)

    # ---- Model B: forward excess return over ret_horizon days (purge & CV gap = ret_horizon,
    # because overlapping h-day labels share returns with the following h-1 rows).
    ret_alphas = m.ret_lasso_alphas if m.return_model == "lasso" else m.ret_ridge_alphas
    ret_model = walk_forward(
        feats, targets["y_ret"],
        penalised_regression(m.return_model, ret_alphas, m.cv_splits, gap=m.ret_horizon),
        horizon=m.ret_horizon, **wf)

    vol_metrics = _vol_metrics(targets["y_vol"], vol_ridge, vol_har, m.vol_horizon)
    ret_row = regression_report(targets["y_ret"], ret_model.predictions, ret_model.benchmark)
    ret_row.update(information_coefficient(targets["y_ret"], ret_model.predictions, ret_model.benchmark,
                                           m.ret_horizon))
    ret_metrics = pd.DataFrame({f"{m.return_model.title()} (Model B, {m.ret_horizon}d)": ret_row}).T
    labelled = targets["y_vol"].notna()
    har_inf = har_inference_table(feats.loc[labelled, HAR_FEATURES], targets.loc[labelled, "y_vol"],
                                  m.vol_horizon)
    return Forecasts(df, feats, targets, vol_ridge, vol_har, ret_model, vol_metrics, ret_metrics,
                     har_inf, m.ret_horizon)


def evaluate_strategy(fc: Forecasts, s: StrategyConfig) -> StrategyResult:
    """Build weights from fitted forecasts and backtest every variant. Cheap: no refitting."""
    df = fc.market
    exp_ret = expected_excess_return(fc.ret_model.predictions, fc.ret_model.benchmark,
                                     s.prior_premium, fc.ret_horizon)
    weights = target_weights(fc.vol_ridge.predictions, exp_ret, s, vol_calibration=proxy_calibration(df))
    asset_ret = df["close"].pct_change()
    backtests = {STRATEGY_NAMES[c]: run_backtest(weights[c], asset_ret, df["rf"], s) for c in weights}
    backtests["Buy & hold"] = buy_and_hold(weights.index, asset_ret, df["rf"], s)
    perf = pd.DataFrame({k: performance(b.net, df["rf"], b.turnover, b.weight, b.gross, b.costs)
                         for k, b in backtests.items()}).T
    regimes = regime_table(backtests, df["rf"], REGIMES)
    return StrategyResult(weights, exp_ret, backtests, perf, regimes)


def run(cfg: Config, market: pd.DataFrame | None = None, make_plots: bool = True) -> RunResult:
    t0 = time.perf_counter()
    m, s = cfg.model, cfg.strategy
    out = Path(cfg.output_dir)
    (out / "figures").mkdir(parents=True, exist_ok=True)

    fc = fit_forecasts(cfg, market)
    sr = evaluate_strategy(fc, s)
    df, targets, weights, backtests = fc.market, fc.targets, sr.weights, sr.backtests

    figures: list[Path] = []
    if make_plots:
        figs = out / "figures"
        figures.append(plotting.plot_vol_forecast(targets["y_vol"], fc.vol_ridge.predictions,
                                                  fc.vol_har.predictions, figs / "1_vol_forecast.png",
                                                  m.vol_horizon))
        figures.append(plotting.plot_equity({k: b.net for k, b in backtests.items()},
                                            figs / "2_equity_curve.png",
                                            s.commission_bps + s.slippage_bps))
        keep = ["Vol target + signal", "Vol target only", "Buy & hold"]
        figures.append(plotting.plot_rolling_risk(
            {k: rolling_sharpe(backtests[k].net, df["rf"]) for k in keep},
            {k: drawdown(backtests[k].net) for k in keep}, figs / "3_rolling_sharpe_drawdown.png"))
        figures.append(plotting.plot_feature_selection(
            fc.ret_model.coefficients, figs / "4_return_feature_selection.png",
            f"Model B ({m.return_model}, {m.ret_horizon}d target): feature selection stability"))

    # ---- Persist everything needed to reproduce / inspect the run.
    fc.vol_metrics.to_csv(out / "vol_model_metrics.csv")
    fc.ret_metrics.to_csv(out / "return_model_metrics.csv")
    sr.performance.to_csv(out / "strategy_performance.csv")
    sr.regimes.to_csv(out / "regime_breakdown.csv")
    fc.har_inference.to_csv(out / "har_inference_hac.csv")
    pd.concat({"y_vol": targets["y_vol"], "pred_vol_ridge": fc.vol_ridge.predictions,
               "pred_vol_har": fc.vol_har.predictions, "y_ret": targets["y_ret"],
               "pred_ret": fc.ret_model.predictions, "expected_excess_ret": sr.expected_ret,
               **{f"w_{k}": v for k, v in weights.items()}}, axis=1).loc[weights.index].to_csv(
        out / "oos_predictions.csv")
    fc.ret_model.coefficients.to_csv(out / "return_model_coefficients.csv")
    (out / "run_config.json").write_text(json.dumps(cfg.to_dict(), indent=2), encoding="utf-8")
    write_markdown_report(out / "results.md", cfg, df, weights.index, fc.vol_metrics, fc.ret_metrics,
                          sr.performance, fc.har_inference, sr.regimes)
    log.info("finished in %.1fs", time.perf_counter() - t0)

    return RunResult(fc.vol_metrics, fc.ret_metrics, sr.performance, sr.regimes, fc.har_inference,
                     fc.vol_ridge, fc.vol_har, fc.ret_model, backtests, figures)


def _fmt_perf(perf: pd.DataFrame) -> pd.DataFrame:
    pct = ["ann_return", "ann_vol", "max_drawdown", "pct_short"]

    def f(v: float, c: str) -> str:
        if c in pct:
            return f"{v:.1%}"
        if c == "ann_turnover":
            return f"{v:.1f}x"
        if c == "cost_drag_bps":
            return f"{v:.0f}"
        return f"{v:.2f}"

    out = perf.copy().astype(object)
    for c in perf.columns:
        out[c] = perf[c].map(lambda v, c=c: f(v, c))
    return out


def write_markdown_report(path: Path, cfg: Config, df: pd.DataFrame, oos: pd.Index, vol: pd.DataFrame,
                          ret: pd.DataFrame, perf: pd.DataFrame, har_inf: pd.DataFrame,
                          regimes: pd.DataFrame | None = None) -> None:
    src = "SYNTHETIC GJR-GARCH market (offline demo)" if cfg.data.synthetic else cfg.data.ticker
    lines = [
        f"# Results: {src}",
        "",
        f"Out-of-sample window: **{oos[0].date()} → {oos[-1].date()}** ({len(oos):,} trading days). "
        f"Refit every {cfg.model.refit_every} days, {'expanding' if cfg.model.rolling_window is None else 'rolling'} "
        f"window, {cfg.model.min_train_days}-day burn-in. Costs: "
        f"{cfg.strategy.commission_bps + cfg.strategy.slippage_bps:.1f} bps per unit traded.",
        "",
        f"## Model A: {cfg.model.vol_horizon}-day forward realized volatility",
        "",
        vol.map(lambda v: f"{v:.3f}" if isinstance(v, float) else v).to_markdown(),
        "",
        "`r2_oos_vs_mean` is the Campbell-Thompson R² against the training-window mean; "
        "`dm_stat` < 0 means Ridge beats HAR-OLS on squared error.",
        "",
        f"## Model B: {cfg.model.ret_horizon}-day forward excess return",
        "",
        ret.map(lambda v: f"{v:.4f}" if isinstance(v, float) else v).to_markdown(),
        "",
        "## Strategy performance (net of costs)",
        "",
        _fmt_perf(perf).to_markdown(),
        "",
        "`sharpe` is net of trading costs, `sharpe_gross` before them; `cost_drag_bps` is the annual "
        "trading-cost drag. Signal settings: "
        f"EMA span={cfg.strategy.signal_ema_span}, hold={cfg.strategy.signal_hold}d, "
        f"no-trade band={cfg.strategy.rebalance_band}.",
        "",
        "## Regime breakdown (net of costs)",
        "",
        _fmt_perf(regimes).to_markdown() if regimes is not None else "",
        "",
        "## HAR loadings, full sample, Newey-West t-stats (in-sample inference only)",
        "",
        har_inf.map(lambda v: f"{v:.3f}").to_markdown(),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
