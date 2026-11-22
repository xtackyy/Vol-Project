"""Cross-asset comparison: SPY (equities), TLT (rates) and GLD (gold) through the same engine.

Each asset gets its own profile (costs, return prior, macro features) but the identical
purged walk-forward validation, models and strategy rules. Outputs one comparison table,
the correlation of the vol-targeted strategies' returns and an equal-weight combination.

    python scripts/run_multi_asset.py                    # download (first run) + full study
    python scripts/run_multi_asset.py --download-only    # just fetch & cache the data
    python scripts/run_multi_asset.py --synthetic        # offline smoke test
"""
from __future__ import annotations

import argparse
import logging
import sys
from concurrent.futures import ProcessPoolExecutor
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from volcast import plotting  # noqa: E402
from volcast.assets import build_config  # noqa: E402
from volcast.config import TRADING_DAYS  # noqa: E402
from volcast.data import load_market_data  # noqa: E402
from volcast.metrics import drawdown, performance  # noqa: E402
from volcast.pipeline import _fmt_perf, evaluate_strategy, fit_forecasts, write_markdown_report  # noqa: E402

VT, BH = "Vol target only", "Buy & hold"
COMBO = "Equal-weight (vol-targeted)"


def _config(ticker: str, args: argparse.Namespace, i: int):
    kw = {"start": args.start, "synthetic": args.synthetic, "seed": 7 + 11 * i}
    return build_config(ticker, output_dir=args.output.parent / ticker, **kw)


def _run_one(job: tuple[str, argparse.Namespace, int]) -> dict:
    ticker, args, i = job
    # Workers are spawned on Windows and don't inherit main()'s logging config; without this,
    # warnings such as "cross-asset dxy unavailable" are silently dropped.
    logging.basicConfig(level=logging.INFO, format=f"%(asctime)s [{ticker}] %(message)s",
                        datefmt="%H:%M:%S", force=True)
    cfg = _config(ticker, args, i)
    fc = fit_forecasts(cfg)
    sr = evaluate_strategy(fc, cfg.strategy)
    out = Path(cfg.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    write_markdown_report(out / "results.md", cfg, fc.market, sr.weights.index, fc.vol_metrics,
                          fc.ret_metrics, sr.performance, fc.har_inference, sr.regimes)
    sr.performance.to_csv(out / "strategy_performance.csv")
    sr.regimes.to_csv(out / "regime_breakdown.csv")
    fc.ret_metrics.to_csv(out / "return_model_metrics.csv")
    fc.vol_metrics.to_csv(out / "vol_model_metrics.csv")

    vm, rm, p = fc.vol_metrics, fc.ret_metrics.iloc[0], sr.performance
    oos = sr.weights.index
    row = {
        "asset_class": cfg.data.asset_class,
        "oos_start": oos[0].date(), "oos_end": oos[-1].date(), "oos_days": len(oos),
        "cost_bps": cfg.strategy.cost_per_unit_traded * 1e4,
        "n_features": fc.features.shape[1],
        "vol_r2_ridge": vm.loc["Ridge-HAR (Model A)", "r2_oos_vs_mean"],
        "vol_r2_har": vm.loc["HAR-RV OLS (baseline)", "r2_oos_vs_mean"],
        "vol_dm_t": vm.loc["Ridge-HAR (Model A)", "dm_stat"],
        "ret_ic_5d": rm["ic"], "ret_ic_t": rm["ic_t"], "ret_view_share": rm["view_share"],
        "ret_r2_oos": rm["r2_oos_vs_mean"],
        "vt_sharpe": p.loc[VT, "sharpe"], "vt_max_dd": p.loc[VT, "max_drawdown"],
        "vt_turnover": p.loc[VT, "ann_turnover"], "vt_vol": p.loc[VT, "ann_vol"], "vt_cagr": p.loc[VT, "ann_return"],
        "bh_sharpe": p.loc[BH, "sharpe"], "bh_max_dd": p.loc[BH, "max_drawdown"],
        "bh_vol": p.loc[BH, "ann_vol"], "bh_cagr": p.loc[BH, "ann_return"],
    }
    return {"ticker": ticker, "row": row, "vt": sr.backtests[VT].net, "bh": sr.backtests[BH].net,
            "rf": fc.market["rf"], "regimes": sr.regimes}


def _corr_table(rets: dict[str, pd.Series]) -> pd.DataFrame:
    return pd.concat(rets, axis=1).dropna().corr()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tickers", nargs="+", default=["SPY", "TLT", "GLD"])
    ap.add_argument("--start", default="2000-01-01")
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--download-only", action="store_true")
    ap.add_argument("--output", type=Path, default=Path("reports/multi_asset"))
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    tickers = [t.upper() for t in args.tickers]

    if args.download_only:
        for i, t in enumerate(tickers):
            df = load_market_data(_config(t, args, i).data)
            cols = ", ".join(c for c in df.columns if c.startswith("x_") or c in ("vix", "rf"))
            print(f"{t}: {df.index[0].date()} -> {df.index[-1].date()} ({len(df)} days); aligned: {cols}")
        print("Cached in data/. Run again without --download-only for the study.")
        return

    with ProcessPoolExecutor(len(tickers)) as ex:
        results = {r["ticker"]: r for r in ex.map(_run_one, [(t, args, i) for i, t in enumerate(tickers)])}

    out = args.output
    (out / "figures").mkdir(parents=True, exist_ok=True)
    comp = pd.DataFrame({t: r["row"] for t, r in results.items()}).T
    comp.index.name = "ticker"
    regimes = pd.concat({t: r["regimes"] for t, r in results.items()}, names=["ticker"])

    # ---- Diversification: correlations and an equal-weight book on the common window.
    vt = {t: r["vt"] for t, r in results.items()}
    bh = {t: r["bh"] for t, r in results.items()}
    corr_vt, corr_bh = _corr_table(vt), _corr_table(bh)
    common = pd.concat(vt, axis=1).dropna()
    rf = results[tickers[0]]["rf"]
    # Each sleeve already targets the same vol, so equal weights are ~equal risk. Daily
    # rebalancing between sleeves is assumed free here (sleeve costs are already included).
    combo = common.mean(axis=1)
    book = {**{t: common[t] for t in tickers}, COMBO: combo}
    book_perf = pd.DataFrame({k: performance(v, rf) for k, v in book.items()}).T
    years = len(common) / TRADING_DAYS
    avg_corr = corr_vt.where(~np.eye(len(tickers), dtype=bool)).stack().mean()
    div_ratio = float(common.std().mean() / combo.std())

    comp.to_csv(out / "comparison.csv")
    corr_vt.to_csv(out / "correlation_vol_targeted.csv")
    corr_bh.to_csv(out / "correlation_buy_and_hold.csv")
    book_perf.to_csv(out / "equal_weight_book.csv")
    regimes.to_csv(out / "regimes_all_assets.csv")

    rolling = {f"{a}-{b}": common[a].rolling(TRADING_DAYS).corr(common[b]).dropna()
               for a, b in combinations(tickers, 2)}
    plotting.plot_multi_asset_equity(book, out / "figures" / "1_vol_targeted_equity.png",
                                     f"Vol-targeted strategies, common window {common.index[0].year}-"
                                     f"{common.index[-1].year}, net of costs")
    plotting.plot_rolling_correlations(rolling, out / "figures" / "2_rolling_correlations.png")
    dd = {k: drawdown(v) for k, v in book.items()}

    # ---- Report.
    show = comp.copy()
    pct = ["vt_max_dd", "bh_max_dd", "vt_vol", "bh_vol", "vt_cagr", "bh_cagr", "ret_view_share"]
    for c in show.columns:
        if c in pct:
            show[c] = show[c].map(lambda v: f"{v:.1%}")
        elif c in ("vol_r2_ridge", "vol_r2_har", "ret_ic_5d", "ret_r2_oos"):
            show[c] = show[c].map(lambda v: f"{v:.3f}")
        elif c in ("vt_sharpe", "bh_sharpe", "vol_dm_t", "ret_ic_t", "vt_turnover", "cost_bps"):
            show[c] = show[c].map(lambda v: f"{v:.2f}")
    src = "SYNTHETIC data (offline smoke test)" if args.synthetic else ", ".join(tickers)
    lines = [
        f"# Cross-asset comparison: {src}",
        "",
        "Same purged walk-forward engine for every asset; asset-specific costs and lagged macro features.",
        "",
        "## Model and strategy summary",
        "",
        show.T.to_markdown(),
        "",
        "`vol_dm_t` < 0: Ridge beats HAR-OLS. `ret_ic_5d`: rank IC of the 5-day return tilt on days the "
        "model has a view, t-stat uses n/5 effective observations.",
        "",
        "## Correlation of vol-targeted strategy returns (daily, common window)",
        "",
        corr_vt.map(lambda v: f"{v:.2f}").to_markdown(),
        "",
        "Buy & hold, same window, for reference:",
        "",
        corr_bh.map(lambda v: f"{v:.2f}").to_markdown(),
        "",
        f"## Equal-weight book of the vol-targeted sleeves ({common.index[0].date()} to "
        f"{common.index[-1].date()}, {years:.1f} years)",
        "",
        _fmt_perf(book_perf[["ann_return", "ann_vol", "sharpe", "sortino", "max_drawdown", "calmar"]]).to_markdown(),
        "",
        f"Average pairwise correlation {avg_corr:.2f}; diversification ratio (avg sleeve vol / book vol) "
        f"{div_ratio:.2f}.",
        "",
        "## Regime breakdown per asset",
        "",
        _fmt_perf(regimes).to_markdown(),
        "",
    ]
    (out / "results.md").write_text("\n".join(lines), encoding="utf-8")

    pd.set_option("display.width", 200, "display.max_columns", 30)
    print("\n=== Cross-asset summary ===")
    print(show.T.to_string())
    print("\n=== Correlation of vol-targeted strategy returns ===")
    print(corr_vt.round(2).to_string())
    print(f"\n=== Equal-weight vol-targeted book, {common.index[0].date()} -> {common.index[-1].date()} ===")
    print(_fmt_perf(book_perf[["ann_return", "ann_vol", "sharpe", "max_drawdown"]]).to_string())
    worst = min(d.min() for k, d in dd.items() if k != COMBO)
    print(f"avg pairwise corr {avg_corr:.2f} | diversification ratio {div_ratio:.2f} | "
          f"worst sleeve drawdown {worst:.1%} vs book {dd[COMBO].min():.1%}")
    print(f"\nReport: {out / 'results.md'}  Per-asset reports: {out.parent}/<TICKER>/")


if __name__ == "__main__":
    main()
