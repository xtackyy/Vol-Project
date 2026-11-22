"""Signal-refinement study: horizon x smoothing x no-trade band x long-only/long-short.

Models are fitted once per return horizon (the expensive part); every strategy setting is
then a cheap re-weighting + backtest of the *same* out-of-sample forecasts, so differences
between rows come only from the signal construction.

    python scripts/signal_experiments.py                 # SPY, cached data
    python scripts/signal_experiments.py --synthetic     # offline smoke test

Caveat printed with the results: this is a grid of many configurations evaluated on one
history. Picking the best row is in-sample selection, so treat the winner's Sharpe as
optimistic and prefer settings that are robust across neighbours and regimes.
"""
from __future__ import annotations

import argparse
import itertools
import logging
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402

from volcast.config import Config, DataConfig, ModelConfig, StrategyConfig  # noqa: E402
from volcast.pipeline import evaluate_strategy, fit_forecasts  # noqa: E402

HORIZONS = (1, 5)
EMA_SPANS = (None, 5, 10, 20)
HOLDS = (1, 5)
BANDS = (0.05, 0.10, 0.20)
# 0.04: noisy intercept replaced by a 4% equity-premium prior (the default strategy).
# 0.00: pure timing test - long (or short) only on whether the features forecast an above-
#       (below-) average return. This isolates whether the model has predictive content.
PRIORS = (0.04, 0.0)
VARIANTS = {"long-only": ("Vol target + signal", "vol_target_signal"),
            "long-short": ("Vol target + signal (long-short)", "vol_target_signal_ls")}
REFERENCE = ("Vol target only", "Buy & hold")


def _fit(args: tuple[Config, int]):
    cfg, h = args
    # Workers are spawned on Windows and don't inherit main()'s logging config.
    logging.basicConfig(level=logging.INFO, format=f"%(asctime)s [{cfg.data.ticker} h={h}] %(message)s",
                        datefmt="%H:%M:%S", force=True)
    cfg = replace(cfg, model=replace(cfg.model, ret_horizon=h))
    return h, fit_forecasts(cfg)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", default="SPY")
    ap.add_argument("--start", default="2000-01-01")
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--output", type=Path, default=Path("reports/experiments"))
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")

    base = Config(data=DataConfig(ticker=a.ticker, start=a.start, synthetic=a.synthetic),
                  model=ModelConfig(), strategy=StrategyConfig())
    with ProcessPoolExecutor(len(HORIZONS)) as ex:
        forecasts = dict(ex.map(_fit, [(base, h) for h in HORIZONS]))

    rows, regime_rows = [], []
    for h, prior, ema, hold, band in itertools.product(HORIZONS, PRIORS, EMA_SPANS, HOLDS, BANDS):
        s = replace(base.strategy, signal_ema_span=ema, signal_hold=hold, rebalance_band=band,
                    prior_premium=prior)
        res = evaluate_strategy(forecasts[h], s)
        cfg_cols = {"ret_horizon": h, "prior": prior, "ema": ema or 0, "hold": hold, "band": band}
        for variant, (name, col) in VARIANTS.items():
            p = res.performance.loc[name]
            rows.append({**cfg_cols, "variant": variant, "sharpe_net": p.sharpe, "sharpe_gross": p.sharpe_gross,
                         "cost_drag_bps": p.cost_drag_bps, "turnover": p.ann_turnover,
                         "ann_return": p.ann_return, "ann_vol": p.ann_vol, "max_dd": p.max_drawdown,
                         # share of days the signal is not long: flat (long-only) or short (long-short)
                         "pct_not_long": float((res.weights[col] <= 0).mean())})
        for ref in REFERENCE:
            p = res.performance.loc[ref]
            rows.append({**cfg_cols, "variant": ref, "sharpe_net": p.sharpe, "sharpe_gross": p.sharpe_gross,
                         "cost_drag_bps": p.cost_drag_bps, "turnover": p.ann_turnover,
                         "ann_return": p.ann_return, "ann_vol": p.ann_vol, "max_dd": p.max_drawdown,
                         "pct_not_long": 0.0})
        reg = res.regimes.reset_index()
        for k, v in cfg_cols.items():
            reg[k] = v
        regime_rows.append(reg)

    grid = pd.DataFrame(rows)
    regimes = pd.concat(regime_rows, ignore_index=True)
    a.output.mkdir(parents=True, exist_ok=True)
    grid.to_csv(a.output / "signal_grid.csv", index=False)
    regimes.to_csv(a.output / "signal_grid_regimes.csv", index=False)
    ret_quality = pd.concat({h: fc.ret_metrics.iloc[0] for h, fc in forecasts.items()}, axis=1).T
    ret_quality.index.name = "ret_horizon"
    ret_quality.to_csv(a.output / "return_model_by_horizon.csv")
    pd.concat({f"h{h}_{k}": v for h, fc in forecasts.items() for k, v in
               {"y": fc.targets["y_ret"], "pred": fc.ret_model.predictions,
                "bench": fc.ret_model.benchmark}.items()}, axis=1).dropna(how="all").to_csv(
        a.output / "return_forecasts.csv")

    pd.set_option("display.width", 200, "display.max_rows", 200)
    sig = grid[grid.variant.isin(VARIANTS)]
    print("\n=== Return model quality by horizon ===")
    print(ret_quality[["r2_oos_vs_mean", "corr", "hit_rate_sign"]].round(4).to_string())
    print("\n=== Top 10 signal configurations by net Sharpe ===")
    print(sig.sort_values("sharpe_net", ascending=False).head(10).round(3).to_string(index=False))
    ref = grid[(grid.variant == "Vol target only")].groupby("band")[["sharpe_net", "turnover"]].first()
    print("\n=== Reference: vol target only (by band) ===")
    print(ref.round(3).to_string())
    print(f"\n{len(sig)} signal configurations tested. The best row is selected in-sample: treat it as "
          "an upper bound, not an expected Sharpe.")
    print(f"Files: {a.output}")


if __name__ == "__main__":
    main()
