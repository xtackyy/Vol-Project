"""Execution timing: trade at the signal's own close (base case) vs the next morning's open.

Forecasts are fitted once per asset; the same target weights are then backtested twice. With
next-open execution the overnight gap right after each signal is earned by the old position,
so any edge that depends on trading at the close shows up as a gap between the two.

    python scripts/execution_sensitivity.py              # SPY, TLT, GLD (cached data)
    python scripts/execution_sensitivity.py --synthetic  # offline smoke test
"""
from __future__ import annotations

import argparse
import logging
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402

from volcast.assets import build_config  # noqa: E402
from volcast.backtest import run_backtest, run_backtest_next_open  # noqa: E402
from volcast.metrics import performance  # noqa: E402
from volcast.pipeline import evaluate_strategy, fit_forecasts  # noqa: E402

TICKERS = ("SPY", "TLT", "GLD")
STRATEGIES = {"Vol target only": "vol_target_only", "Vol target + signal": "vol_target_signal"}


def _run(args: tuple[str, bool]) -> pd.DataFrame:
    ticker, synthetic = args
    logging.basicConfig(level=logging.INFO, format=f"%(asctime)s [{ticker}] %(message)s",
                        datefmt="%H:%M:%S", force=True)
    cfg = build_config(ticker, synthetic=synthetic)
    fc = fit_forecasts(cfg)
    s = cfg.strategy
    res = evaluate_strategy(fc, s)
    df = fc.market
    rf = df["rf"]
    close_ret = df["close"].pct_change()
    overnight = df["open"] / df["close"].shift(1) - 1
    intraday = df["close"] / df["open"] - 1
    idx = res.weights.index

    rows = []
    targets = {name: res.weights[col] for name, col in STRATEGIES.items()}
    targets["Buy & hold"] = pd.Series(1.0, index=idx)
    for name, w in targets.items():
        band = 0.0 if name == "Buy & hold" else None
        for execution, bt in (("close", run_backtest(w, close_ret, rf, s, band=band)),
                              ("next open", run_backtest_next_open(w, overnight, intraday, rf, s, band=band))):
            # performance() drops day 0 as the initial buy; with next-open fills that buy is on day 1.
            turnover = bt.turnover if execution == "close" else bt.turnover.iloc[1:]
            p = performance(bt.net, rf, turnover, bt.weight, bt.gross, bt.costs)
            rows.append({"ticker": ticker, "strategy": name, "execution": execution,
                         "start": idx[0].date(), "end": idx[-1].date(), **p})
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--output", type=Path, default=Path("reports/execution"))
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")

    with ProcessPoolExecutor(len(TICKERS)) as ex:
        table = pd.concat(ex.map(_run, [(t, a.synthetic) for t in TICKERS]), ignore_index=True)
    a.output.mkdir(parents=True, exist_ok=True)
    table.to_csv(a.output / "close_vs_next_open.csv", index=False)

    cols = ["ann_return", "ann_vol", "sharpe", "max_drawdown", "ann_turnover", "cost_drag_bps"]
    view = table.set_index(["ticker", "strategy", "execution"])[cols]
    pd.set_option("display.width", 200)
    print(view.round(3).to_string())

    lines = ["# Execution timing: close vs next open", "",
             "Same forecasts and target weights; only the fill time changes. Costs per unit traded are "
             "unchanged (opening-auction spreads can be wider). Financing accrues half a day per segment.", "",
             "| Asset | Strategy | Sharpe (close) | Sharpe (next open) | CAGR (close) | CAGR (next open) "
             "| Max DD (close) | Max DD (next open) |",
             "|---|---|---|---|---|---|---|---|"]
    for (ticker, name), g in table.groupby(["ticker", "strategy"], sort=False):
        c, o = g.set_index("execution").loc["close"], g.set_index("execution").loc["next open"]
        lines.append(f"| {ticker} | {name} | {c.sharpe:.2f} | {o.sharpe:.2f} | {c.ann_return:.1%} | "
                     f"{o.ann_return:.1%} | {c.max_drawdown:.1%} | {o.max_drawdown:.1%} |")
    (a.output / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Files: {a.output}")


if __name__ == "__main__":
    main()
