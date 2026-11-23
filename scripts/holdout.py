r"""Holdout: the frozen pipeline on assets it has never been run on (see HOLDOUT.md).

    python scripts\holdout.py            # -> reports\holdout\<TICKER>\ and reports\holdout\results.md

Nothing here may be tuned after the run: same model, strategy settings and costs as fixed in
HOLDOUT.md. The table is reported as it comes out.
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
from volcast.data import load_market_data  # noqa: E402
from volcast.metrics import edge_by_year  # noqa: E402
from volcast.pipeline import run  # noqa: E402

TICKERS = ("IWM", "EFA", "EEM", "IEF")
OUT = Path("reports/holdout")


def _one(ticker: str) -> dict:
    logging.basicConfig(level=logging.INFO, format=f"%(asctime)s [{ticker}] %(message)s", datefmt="%H:%M:%S",
                        force=True)
    cfg = build_config(ticker, output_dir=OUT / ticker)
    res = run(cfg, make_plots=False)
    perf, vol = res.performance, res.vol_metrics
    rf = load_market_data(cfg.data)["rf"]
    vt, bh = res.backtests["Vol target only"].net, res.backtests["Buy & hold"].net
    edge = edge_by_year(vt, bh, rf)["summary"]
    return {
        "ticker": ticker, "oos_start": str(vt.index[0].date()), "oos_end": str(vt.index[-1].date()),
        "cost_bps": cfg.strategy.cost_per_unit_traded * 1e4,
        "vol_r2_oos_ridge": vol.loc["Ridge-HAR (Model A)", "r2_oos_vs_mean"],
        "vol_r2_oos_har": vol.loc["HAR-RV OLS (baseline)", "r2_oos_vs_mean"],
        "dm_t_ridge_vs_har": vol.loc["Ridge-HAR (Model A)", "dm_stat"],
        "vt_sharpe": perf.loc["Vol target only", "sharpe"], "bh_sharpe": perf.loc["Buy & hold", "sharpe"],
        "vt_max_dd": perf.loc["Vol target only", "max_drawdown"], "bh_max_dd": perf.loc["Buy & hold", "max_drawdown"],
        "vt_ann_vol": perf.loc["Vol target only", "ann_vol"],
        "vt_turnover": perf.loc["Vol target only", "ann_turnover"],
        "sharpe_gap_ex_2008_09": edge["sharpe_gap_ex_2008_2009"],
        "years_vt_beats_bh": edge["years_strat_beats_bench"],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    with ProcessPoolExecutor(len(TICKERS)) as ex:
        rows = list(ex.map(_one, TICKERS))
    table = pd.DataFrame(rows).set_index("ticker")
    table.to_csv(OUT / "summary.csv")
    pct = {"vt_max_dd", "bh_max_dd", "vt_ann_vol"}
    view = table.copy().astype(object)
    for c in table.columns:
        if c in pct:
            view[c] = table[c].map(lambda v: f"{v:.1%}")
        elif table[c].dtype.kind == "f":
            view[c] = table[c].map(lambda v: f"{v:.3f}")
    lines = ["# Holdout: frozen pipeline on assets it had never been run on", "",
             "Settings frozen in HOLDOUT.md before this run; nothing was changed after it. Next-open fills, "
             "net of costs. Sharpe on excess returns.", "", view.T.to_markdown(), ""]
    (OUT / "results.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
