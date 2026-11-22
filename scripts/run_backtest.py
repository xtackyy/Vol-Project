"""CLI entry point.

Examples
--------
    python scripts/run_backtest.py --ticker SPY
    python scripts/run_backtest.py --ticker TLT          # rates: curve slope, equity-bond corr, VIX
    python scripts/run_backtest.py --ticker GLD          # gold: dollar, real-rate proxy, VIX stress
    python scripts/run_backtest.py --synthetic          # offline, no network needed

Costs, the return prior and the cross-asset inputs come from the asset profile
(src/volcast/assets.py); any flag you pass explicitly overrides the profile.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

from volcast.assets import build_config, get_profile
from volcast.config import ModelConfig
from volcast.pipeline import _fmt_perf, run


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--ticker", default="SPY")
    p.add_argument("--start", default="2000-01-01")
    p.add_argument("--end", default=None)
    p.add_argument("--no-vix", action="store_true", help="drop implied-vol features")
    p.add_argument("--synthetic", action="store_true", help="simulated market, no download")
    p.add_argument("--horizon", type=int, default=5, help="vol forecast horizon in days")
    p.add_argument("--refit-every", type=int, default=21)
    p.add_argument("--min-train", type=int, default=756)
    p.add_argument("--rolling-window", type=int, default=None)
    p.add_argument("--return-model", choices=["lasso", "ridge"], default="lasso")
    p.add_argument("--ret-horizon", type=int, default=5, help="Model B target horizon in days")
    p.add_argument("--ema", type=int, default=5, help="EMA span on the return signal (0 = off)")
    p.add_argument("--hold", type=int, default=1, help="refresh the return signal every k days")
    p.add_argument("--short-fee-bps", type=float, default=25.0)
    p.add_argument("--target-vol", type=float, default=0.12)
    p.add_argument("--max-leverage", type=float, default=1.5)
    p.add_argument("--prior-premium", type=float, default=None,
                   help="annual return prior for the long/flat signal (default: asset profile); "
                        "negative = use raw forecast")
    p.add_argument("--band", type=float, default=0.10, help="no-trade band in weight units")
    p.add_argument("--commission-bps", type=float, default=None, help="default: asset profile")
    p.add_argument("--slippage-bps", type=float, default=None, help="default: asset profile")
    p.add_argument("--output", type=Path, default=None, help="default: reports/<TICKER>")
    return p.parse_args()


def main() -> None:
    a = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
    overrides = dict(target_vol=a.target_vol, max_leverage=a.max_leverage, rebalance_band=a.band,
                     signal_ema_span=a.ema or None, signal_hold=a.hold, short_fee_bps=a.short_fee_bps)
    if a.commission_bps is not None:
        overrides["commission_bps"] = a.commission_bps
    if a.slippage_bps is not None:
        overrides["slippage_bps"] = a.slippage_bps
    if a.prior_premium is not None:
        overrides["prior_premium"] = None if a.prior_premium < 0 else a.prior_premium
    cfg = build_config(
        a.ticker,
        model=ModelConfig(vol_horizon=a.horizon, refit_every=a.refit_every, min_train_days=a.min_train,
                          rolling_window=a.rolling_window, return_model=a.return_model,
                          ret_horizon=a.ret_horizon),
        strategy_overrides=overrides,
        output_dir=a.output,
        start=a.start, end=a.end, synthetic=a.synthetic, vix_ticker=None if a.no_vix else "^VIX",
    )
    prof = get_profile(a.ticker)
    logging.info("%s profile: %s, costs %.1f bps, prior %s, cross-asset inputs: %s", prof.ticker,
                 prof.asset_class, cfg.strategy.cost_per_unit_traded * 1e4, cfg.strategy.prior_premium,
                 ", ".join(prof.aux) or "VIX only")
    res = run(cfg)
    pd.set_option("display.width", 160, "display.max_columns", 20)
    print("\n=== Model A: volatility forecast (out-of-sample) ===")
    print(res.vol_metrics.round(4).to_string())
    print(f"\n=== Model B: {a.ret_horizon}-day return forecast (out-of-sample) ===")
    print(res.ret_metrics.round(5).to_string())
    print("\n=== Strategy performance, net of costs ===")
    print(_fmt_perf(res.performance).to_string())
    print("\n=== Regime breakdown, net of costs ===")
    print(_fmt_perf(res.regimes).to_string())
    print(f"\nReport: {cfg.output_dir / 'results.md'}   Figures: {cfg.output_dir / 'figures'}")


if __name__ == "__main__":
    main()
