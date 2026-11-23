r"""Variance risk premium extension: one command runs every milestone built so far.

    python scripts\run_vrp.py        # -> reports\vrp\ and reports\figures\vrp\

1. Data, implied / realized variance, VRP descriptive statistics, first two plots.
2. 21-day HAR walk-forward forecasts vs VIX: accuracy, Mincer-Zarnowitz, encompassing.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402

from vrp import plots  # noqa: E402
from vrp.config import CRISES, REGIMES, VRPConfig  # noqa: E402
from vrp.data import load_vrp_data  # noqa: E402
from vrp.evaluate import (  # noqa: E402
    describe_vrp,
    encompassing,
    forecast_accuracy,
    hac_mean_test,
    mz_table,
    ols_hac,
    vrp_by_period,
    vrp_by_year,
    worst_blocks,
)
from vrp.forecast import har_forecasts  # noqa: E402
from vrp.targets import build_vrp, non_overlapping  # noqa: E402

log = logging.getLogger("run_vrp")


def _md(df: pd.DataFrame, digits: int = 2) -> str:
    return df.round(digits).to_markdown()


def _reg_md(table: pd.DataFrame) -> str:
    return f"{_md(table, 3)}\n\nR² = {table.attrs['r2']:.3f}, n = {table.attrs['n']:,}"


def milestone1(cfg: VRPConfig, data: pd.DataFrame, vrp: pd.DataFrame, blocks: pd.DataFrame) -> None:
    h = cfg.horizon
    summary = describe_vrp(blocks)
    daily = vrp.dropna(subset=["vrp_vol"])
    hac = pd.DataFrame({"vrp_vol": hac_mean_test(daily["vrp_vol"], h - 1),
                        "vrp_varpts": hac_mean_test(daily["vrp_varpts"], h - 1)}).T
    worst = worst_blocks(blocks)
    periods = vrp_by_period(vrp, REGIMES)
    years = vrp_by_year(blocks)
    range_vs_cc = pd.Series({
        "mean_rv_close_to_close": blocks["rv_vol"].mean(),
        "mean_rv_range_based": blocks["rv_range_vol"].mean(),
        "corr": blocks[["rv_vol", "rv_range_vol"]].corr().iloc[0, 1],
    })
    out = cfg.output_dir
    summary.to_csv(out / "vrp_summary.csv", header=["value"])
    hac.to_csv(out / "vrp_mean_hac.csv")
    worst.to_csv(out / "vrp_worst_blocks.csv")
    periods.to_csv(out / "vrp_by_period.csv")
    years.to_csv(out / "vrp_by_year.csv")
    blocks.to_csv(out / "vrp_blocks.csv")
    range_vs_cc.to_csv(out / "rv_close_vs_range.csv", header=["value"])

    plots.implied_vs_realized(vrp, {k: REGIMES[k] for k in CRISES}, cfg.figure_dir / "1_implied_vs_realized.png")
    plots.vrp_histogram(blocks, cfg.figure_dir / "2_vrp_histogram.png")

    lines = [
        "# Variance risk premium: SPY, VIX-implied vs realized", "",
        f"Daily data {data.index[0]:%Y-%m-%d} to {data.index[-1]:%Y-%m-%d}. Horizon {h} trading days. "
        f"Non-overlapping blocks: every {h}th day from {summary['first_entry']} ({int(summary['blocks'])} blocks).",
        "VRP in vol points = VIX at t minus realized vol over t+1..t+21; variance points = vol points squared.", "",
        "## Summary (non-overlapping blocks)", "", summary.to_frame("value").to_markdown(), "",
        f"## Mean VRP on all daily (overlapping) windows, Newey-West t-stat ({h - 1} lags)", "", _md(hac), "",
        "## Worst 10 blocks", "", _md(worst, 1), "",
        "## By stress window / calm period (every daily entry date in the window, overlapping)", "", _md(periods), "",
        "## By year", "", _md(years), "",
        "## Realized vol: close-to-close vs range-based (Garman-Klass + overnight)", "",
        range_vs_cc.to_frame("value").round(3).to_markdown(), "",
    ]
    (out / "results.md").write_text("\n".join(lines), encoding="utf-8")
    print(summary.to_string())
    print(periods.round(2).to_string())


def milestone2(cfg: VRPConfig, data: pd.DataFrame, vrp: pd.DataFrame) -> pd.DataFrame:
    """HAR forecasts vs VIX. Main inference: all daily (overlapping) dates with Newey-West errors,
    h-1 lags. Check: the same regressions on non-overlapping blocks."""
    h, lags, out = cfg.horizon, cfg.horizon - 1, cfg.output_dir
    har = har_forecasts(data, h)
    fc = pd.concat([vrp[["iv_vol", "rv_vol", "vrp_vol"]], har], axis=1).dropna(subset=["har_ridge", "iv_vol"])
    fc["spread"] = fc["iv_vol"] - fc["har_ridge"]      # the signal: VIX minus HAR forecast, vol points
    fc.to_csv(out / "forecasts.csv")
    scored = fc.dropna(subset=["rv_vol"])
    blocks = scored.iloc[::h]

    named = {"VIX": scored["iv_vol"], "HAR-Ridge": scored["har_ridge"], "HAR-OLS": scored["har_ols"],
             "HAR-Ridge, no Jensen correction": scored["har_ridge_median"]}
    acc = forecast_accuracy(scored["rv_vol"], named, h)
    mz = mz_table(scored["rv_vol"], named, lags)
    mz_blocks = mz_table(blocks["rv_vol"], {k: v.reindex(blocks.index) for k, v in named.items()}, 1)
    enc = encompassing(scored["rv_vol"], scored["iv_vol"].rename("VIX"), scored["har_ridge"].rename("HAR-Ridge"), lags)
    enc_ols = encompassing(scored["rv_vol"], scored["iv_vol"].rename("VIX"), scored["har_ols"].rename("HAR-OLS"), lags)
    enc_blocks = encompassing(blocks["rv_vol"], blocks["iv_vol"].rename("VIX"),
                              blocks["har_ridge"].rename("HAR-Ridge"), 1)

    # First look at the signal: does a richer spread come before a bigger premium?
    sig_spread = ols_hac(scored["vrp_vol"], scored[["spread"]], lags)
    sig_vix = ols_hac(scored["vrp_vol"], scored[["iv_vol"]].rename(columns={"iv_vol": "VIX"}), lags)
    sig_both = ols_hac(scored["vrp_vol"], scored[["iv_vol", "spread"]].rename(columns={"iv_vol": "VIX"}), lags)
    spread_stats = scored["spread"].describe().to_frame("spread").T
    spread_stats["share_positive"] = float((scored["spread"] > 0).mean())

    acc.to_csv(out / "forecast_accuracy.csv")
    mz.to_csv(out / "mincer_zarnowitz.csv")
    mz_blocks.to_csv(out / "mincer_zarnowitz_blocks.csv")
    for name, t in {"encompassing_vix_ridge": enc, "encompassing_vix_ols": enc_ols,
                    "encompassing_blocks": enc_blocks, "signal_vrp_on_spread": sig_spread,
                    "signal_vrp_on_vix": sig_vix, "signal_vrp_on_vix_and_spread": sig_both}.items():
        t.assign(r2=t.attrs["r2"], n=t.attrs["n"]).to_csv(out / f"{name}.csv")

    lines = [
        "# HAR-RV vs VIX: forecasting SPY realized vol over the next 21 trading days", "",
        f"Out-of-sample dates {scored.index[0]:%Y-%m-%d} to {scored.index[-1]:%Y-%m-%d} "
        f"({len(scored):,} days; {len(blocks)} non-overlapping blocks). Forecasts in vol points. HAR models are "
        "walk-forward (expanding window, monthly refits, purged), without VIX inputs, Jensen-corrected so the "
        "squared forecast targets the mean variance; the uncorrected row forecasts the median.",
        f"Inference on daily overlapping data uses Newey-West errors with {lags} lags; "
        "the block versions use non-overlapping 21-day windows.", "",
        "## Accuracy (DM t < 0: lower loss than VIX)", "", _md(acc, 3), "",
        "## Mincer-Zarnowitz: realized = a + b * forecast (daily, HAC)", "", _md(mz, 3), "",
        "## Mincer-Zarnowitz on non-overlapping blocks", "", _md(mz_blocks, 3), "",
        "## Encompassing: realized = c + b1 * VIX + b2 * HAR (daily, HAC)", "", _reg_md(enc), "",
        _reg_md(enc_ols), "",
        "## Encompassing on non-overlapping blocks", "", _reg_md(enc_blocks), "",
        "## Signal preview: VRP_t (vol points) on spread_t = VIX_t - HAR-Ridge_t (daily, HAC)", "",
        _md(spread_stats, 3), "", "VRP on spread:", "", _reg_md(sig_spread), "",
        "VRP on VIX level:", "", _reg_md(sig_vix), "", "VRP on both:", "", _reg_md(sig_both), "",
    ]
    (out / "results_forecast.md").write_text("\n".join(lines), encoding="utf-8")
    print(acc.round(3).to_string())
    print(mz.round(3).to_string())
    print(mz_blocks.round(3).to_string())
    for name, t in {"encompassing (Ridge)": enc, "encompassing (OLS)": enc_ols, "encompassing blocks": enc_blocks,
                    "VRP~spread": sig_spread, "VRP~VIX": sig_vix, "VRP~both": sig_both}.items():
        print(f"--- {name}  R2={t.attrs['r2']:.3f} n={t.attrs['n']}")
        print(t.round(3).to_string())
    print(spread_stats.round(2).to_string())
    return fc


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    cfg = VRPConfig()
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    cfg.figure_dir.mkdir(parents=True, exist_ok=True)
    pd.set_option("display.width", 200)

    data = load_vrp_data(cfg)
    vrp = build_vrp(data, cfg.horizon)
    milestone1(cfg, data, vrp, non_overlapping(vrp, cfg.horizon))
    milestone2(cfg, data, vrp)
    print(f"Files: {cfg.output_dir}, {cfg.figure_dir}")


if __name__ == "__main__":
    main()
