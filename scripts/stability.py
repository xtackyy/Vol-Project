r"""Edge stability: is the vol-targeting Sharpe edge spread over many years or one crisis?

    python scripts\stability.py          # -> reports\stability\

Reads the saved out-of-sample weights in reports\<TICKER>\oos_predictions.csv (run the pipeline
first), backtests them with the headline settings (next-open fills, net of costs) and reports the
Sharpe gap to buy and hold by year and with 2008-09 (and 2020) removed.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402

from volcast.assets import build_config  # noqa: E402
from volcast.backtest import backtest, buy_and_hold_market  # noqa: E402
from volcast.data import load_market_data  # noqa: E402
from volcast.metrics import edge_by_year, sharpe  # noqa: E402

TICKERS = ("SPY", "TLT", "GLD")
OUT = Path("reports/stability")


def one(ticker: str) -> tuple[dict, pd.Series]:
    cfg = build_config(ticker)
    w = pd.read_csv(cfg.output_dir / "oos_predictions.csv", index_col=0, parse_dates=True)["w_vol_target_only"]
    mkt = load_market_data(cfg.data)
    vt = backtest(w, mkt, cfg.strategy).net
    bh = buy_and_hold_market(w.index, mkt, cfg.strategy).net
    e = edge_by_year(vt, bh, mkt["rf"])
    row = {"ticker": ticker, "vt_sharpe": sharpe(vt, mkt["rf"]), "bh_sharpe": sharpe(bh, mkt["rf"]), **e["summary"]}
    return row, e["yearly_gap"].rename(ticker)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows, gaps = zip(*(one(t) for t in TICKERS), strict=True)
    table = pd.DataFrame(rows).set_index("ticker")
    yearly = pd.concat(gaps, axis=1)
    table.to_csv(OUT / "summary.csv")
    yearly.index.name = "year"
    yearly.to_csv(OUT / "sharpe_gap_by_year.csv")
    view = table.copy().astype(object)
    for c in table.columns:
        if table[c].dtype.kind == "f":
            view[c] = table[c].map(lambda v: f"{v:.3f}")
    lines = ["# Edge stability: vol target only vs buy and hold", "",
             "Next-open fills, net of costs, Sharpe on excess returns. Saved out-of-sample weights.", "",
             view.to_markdown(), "", "## Sharpe gap (vol target minus buy and hold) by calendar year", "",
             yearly.round(2).to_markdown(), ""]
    (OUT / "results.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
