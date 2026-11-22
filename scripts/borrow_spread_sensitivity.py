r"""How much can leverage cost before vol targeting stops beating buy & hold at matched risk?

At an 18.6% vol target (buy & hold's realized vol) the strategy is levered above 1x much of
the time, and every unit above 1x pays T-bills + a borrow spread. The forecasts are fitted
once; only the backtest is rerun for each spread, so rows differ only in financing cost.

    python scripts\borrow_spread_sensitivity.py
"""
from __future__ import annotations

import argparse
import logging
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

from volcast.assets import build_config
from volcast.pipeline import evaluate_strategy, fit_forecasts

SPREADS_BPS = (0, 50, 100, 150, 200, 250, 300, 400, 500)
VT, BH = "Vol target only", "Buy & hold"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", default="SPY")
    ap.add_argument("--target-vol", type=float, default=0.186)
    ap.add_argument("--output", type=Path, default=Path("reports/risk_matched_18.6"))
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")

    cfg = build_config(a.ticker, strategy_overrides={"target_vol": a.target_vol})
    fc = fit_forecasts(cfg)
    rows = {}
    for bps in SPREADS_BPS:
        res = evaluate_strategy(fc, replace(cfg.strategy, borrow_spread_bps=float(bps)))
        vt, bh = res.performance.loc[VT], res.performance.loc[BH]
        rows[bps] = {"vt_cagr": vt.ann_return, "bh_cagr": bh.ann_return,
                     "cagr_gap": vt.ann_return - bh.ann_return,
                     "vt_sharpe": vt.sharpe, "bh_sharpe": bh.sharpe,
                     "vt_max_dd": vt.max_drawdown, "bh_max_dd": bh.max_drawdown,
                     "vt_avg_exposure": vt.avg_exposure}
    table = pd.DataFrame.from_dict(rows, orient="index").rename_axis("borrow_spread_bps")
    a.output.mkdir(parents=True, exist_ok=True)
    table.to_csv(a.output / "borrow_spread_sensitivity.csv")
    print(table.round(4).to_string())


if __name__ == "__main__":
    main()
