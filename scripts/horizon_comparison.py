r"""Forecast horizon study: 5-day vs 21-day vol and return forecasts on SPY, TLT and GLD.

For each asset the same purged walk-forward is run twice, once with 5-day and once with
21-day targets (purge gap, inner-CV gap, Diebold-Mariano lag and IC effective sample all
follow the horizon). One strategy variant is added, decided before looking at results:
"vol target only" sized on the 21-day vol forecast instead of the 5-day one, everything
else identical, both scored on the same dates.

    python scripts\horizon_comparison.py              # ~5-10 min, runs the 6 fits in parallel
    python scripts\horizon_comparison.py --synthetic  # offline smoke test
"""
from __future__ import annotations

import argparse
import logging
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

from volcast.assets import build_config
from volcast.metrics import performance
from volcast.pipeline import _fmt_perf, evaluate_strategy, fit_forecasts

HORIZONS = (5, 21)
VT, BH = "Vol target only", "Buy & hold"
RIDGE, HAR = "Ridge-HAR (Model A)", "HAR-RV OLS (baseline)"


def _fit(job: tuple[str, int, int, argparse.Namespace]) -> dict:
    ticker, h, i, a = job
    logging.basicConfig(level=logging.INFO, format=f"%(asctime)s [{ticker} h={h}] %(message)s",
                        datefmt="%H:%M:%S", force=True)
    cfg = build_config(ticker, start=a.start, synthetic=a.synthetic, seed=7 + 11 * i)
    cfg = replace(cfg, model=replace(cfg.model, vol_horizon=h, ret_horizon=h))
    fc = fit_forecasts(cfg)
    vm, rm = fc.vol_metrics, fc.ret_metrics.iloc[0]
    vol_row = {"ridge_r2": vm.loc[RIDGE, "r2_oos_vs_mean"], "har_r2": vm.loc[HAR, "r2_oos_vs_mean"],
               "dm_t": vm.loc[RIDGE, "dm_stat"], "ridge_qlike": vm.loc[RIDGE, "qlike"],
               "har_qlike": vm.loc[HAR, "qlike"], "n_oos": vm.loc[RIDGE, "n_oos"],
               "n_eff": vm.loc[RIDGE, "n_oos"] / h}
    ret_row = {"ic": rm["ic"], "ic_t": rm["ic_t"], "view_share": rm["view_share"],
               "n_view": rm["n_view"], "n_eff": rm["n_view"] / h, "r2_oos": rm["r2_oos_vs_mean"]}
    res = evaluate_strategy(fc, cfg.strategy)
    return {"ticker": ticker, "h": h, "vol": vol_row, "ret": ret_row,
            "vt": res.backtests[VT], "bh": res.backtests[BH], "rf": fc.market["rf"]}


def _perf(bt, rf: pd.Series, idx: pd.DatetimeIndex) -> dict:
    return performance(bt.net.loc[idx], rf, bt.turnover.loc[idx], bt.weight.loc[idx],
                       bt.gross.loc[idx], bt.costs.loc[idx])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", nargs="+", default=["SPY", "TLT", "GLD"])
    ap.add_argument("--start", default="2000-01-01")
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--output", type=Path, default=Path("reports/horizons"))
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    tickers = [t.upper() for t in a.tickers]
    jobs = [(t, h, i, a) for i, t in enumerate(tickers) for h in HORIZONS]
    with ProcessPoolExecutor(min(len(jobs), 6)) as ex:
        res = {(r["ticker"], r["h"]): r for r in ex.map(_fit, jobs)}

    vol = pd.DataFrame({k: r["vol"] for k, r in res.items()}).T.rename_axis(["ticker", "horizon"])
    ret = pd.DataFrame({k: r["ret"] for k, r in res.items()}).T.rename_axis(["ticker", "horizon"])

    # Strategy: 5-day vs 21-day vol sizing, scored on the dates both have.
    rows, windows = {}, {}
    for t in tickers:
        r5, r21 = res[(t, 5)], res[(t, 21)]
        idx = r5["vt"].net.index.intersection(r21["vt"].net.index)
        windows[t] = (idx[0].date(), idx[-1].date())
        rows[(t, "Vol target, 5-day vol")] = _perf(r5["vt"], r5["rf"], idx)
        rows[(t, "Vol target, 21-day vol")] = _perf(r21["vt"], r21["rf"], idx)
        rows[(t, "Buy & hold")] = _perf(r5["bh"], r5["rf"], idx)
    strat = pd.DataFrame(rows).T.rename_axis(["ticker", "strategy"])
    cols = ["ann_return", "ann_vol", "sharpe", "sharpe_gross", "max_drawdown", "ann_turnover", "cost_drag_bps"]
    strat = strat[cols]

    out = a.output
    out.mkdir(parents=True, exist_ok=True)
    vol.to_csv(out / "vol_by_horizon.csv")
    ret.to_csv(out / "returns_by_horizon.csv")
    strat.to_csv(out / "strategy_5d_vs_21d_vol.csv")

    src = "SYNTHETIC data (offline smoke test)" if a.synthetic else ", ".join(tickers)
    win = "; ".join(f"{t} {s} to {e}" for t, (s, e) in windows.items())
    lines = [
        f"# Forecast horizon: 5 vs 21 days ({src})",
        "",
        "## Vol forecast",
        "",
        vol.round(3).to_markdown(),
        "",
        "`n_eff` = OOS days / horizon (overlapping labels). DM t < 0: Ridge beats HAR-OLS.",
        "",
        "## Return forecast (rank IC of the tilt, t-stat on n_view / horizon)",
        "",
        ret.round(3).to_markdown(),
        "",
        "## Strategy: vol target sized on 5-day vs 21-day vol forecast (common dates)",
        "",
        f"Windows: {win}.",
        "",
        _fmt_perf(strat).to_markdown(),
        "",
    ]
    (out / "results.md").write_text("\n".join(lines), encoding="utf-8")
    pd.set_option("display.width", 200, "display.max_columns", 20)
    print("\n=== Vol forecast ===\n" + vol.round(3).to_string())
    print("\n=== Return forecast ===\n" + ret.round(3).to_string())
    print(f"\n=== Strategy ({win}) ===\n" + _fmt_perf(strat).to_string())
    print(f"\nReport: {out / 'results.md'}")


if __name__ == "__main__":
    main()
