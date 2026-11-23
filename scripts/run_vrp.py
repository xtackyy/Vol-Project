r"""Variance risk premium extension: one command runs every milestone built so far.

    python scripts\run_vrp.py        # -> reports\vrp\ and reports\figures\vrp\

Milestone 1: data, implied / realized variance, VRP descriptive statistics, first two plots.
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
from vrp.evaluate import describe_vrp, hac_mean_test, vrp_by_period, vrp_by_year, worst_blocks  # noqa: E402
from vrp.targets import build_vrp, non_overlapping  # noqa: E402


def _md(df: pd.DataFrame, digits: int = 2) -> str:
    return df.round(digits).to_markdown()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    cfg = VRPConfig()
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    cfg.figure_dir.mkdir(parents=True, exist_ok=True)
    h = cfg.horizon

    data = load_vrp_data(cfg)
    vrp = build_vrp(data, h)
    blocks = non_overlapping(vrp, h)

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

    summary.to_csv(cfg.output_dir / "vrp_summary.csv", header=["value"])
    hac.to_csv(cfg.output_dir / "vrp_mean_hac.csv")
    worst.to_csv(cfg.output_dir / "vrp_worst_blocks.csv")
    periods.to_csv(cfg.output_dir / "vrp_by_period.csv")
    years.to_csv(cfg.output_dir / "vrp_by_year.csv")
    blocks.to_csv(cfg.output_dir / "vrp_blocks.csv")
    range_vs_cc.to_csv(cfg.output_dir / "rv_close_vs_range.csv", header=["value"])

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
    (cfg.output_dir / "results.md").write_text("\n".join(lines), encoding="utf-8")

    pd.set_option("display.width", 200)
    print(summary.to_string())
    print(hac.round(3).to_string())
    print(worst.round(1).to_string())
    print(periods.round(2).to_string())
    print(range_vs_cc.round(3).to_string())
    print(f"Files: {cfg.output_dir}, {cfg.figure_dir}")


if __name__ == "__main__":
    main()
