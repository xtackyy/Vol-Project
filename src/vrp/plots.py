"""Figures for the VRP extension (saved to reports/figures/vrp/)."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams.update({"figure.dpi": 120, "axes.grid": True, "grid.alpha": 0.3,
                     "axes.spines.top": False, "axes.spines.right": False})


def _shade(ax, crises: dict[str, tuple[str, str]]) -> None:
    for i, (a, b) in enumerate(crises.values()):
        ax.axvspan(pd.Timestamp(a), pd.Timestamp(b), color="red", alpha=0.12, lw=0,
                   label="Stress windows" if i == 0 else None)


def implied_vs_realized(vrp: pd.DataFrame, crises: dict[str, tuple[str, str]], path: Path) -> None:
    d = vrp.dropna(subset=["iv_vol", "rv_vol"])
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 7), sharex=True, height_ratios=[3, 2])
    a1.plot(d.index, d["iv_vol"], lw=0.7, label="VIX close at t (implied vol, next 30 days)")
    a1.plot(d.index, d["rv_vol"], lw=0.7, alpha=0.8, label="SPY realized vol over t+1..t+21")
    _shade(a1, crises)
    a1.set(ylabel="Vol points (annualised %)", title="Implied vs subsequently realized SPY volatility")
    a1.legend(loc="upper left", fontsize=8)
    a2.fill_between(d.index, d["vrp_vol"], 0, where=d["vrp_vol"] >= 0, color="tab:green", lw=0,
                    label="Implied > realized (seller paid)")
    a2.fill_between(d.index, d["vrp_vol"], 0, where=d["vrp_vol"] < 0, color="tab:red", lw=0,
                    label="Realized > implied (seller lost)")
    a2.axhline(0, color="black", lw=0.7)
    a2.set(ylabel="VRP, vol points", title="Variance risk premium: implied minus realized vol (daily, overlapping)")
    a2.legend(loc="lower left", fontsize=8)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def vrp_histogram(blocks: pd.DataFrame, path: Path, n_labels: int = 4) -> None:
    v = blocks["vrp_vol"]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(v, bins=60, color="tab:blue", alpha=0.8)
    ax.axvline(v.mean(), color="black", lw=1.5, label=f"Mean {v.mean():.1f}")
    ax.axvline(v.median(), color="black", lw=1.5, ls="--", label=f"Median {v.median():.1f}")
    ax.axvline(v.quantile(0.05), color="tab:red", lw=1.2, ls=":", label=f"5th percentile {v.quantile(0.05):.1f}")
    for i, (date, val) in enumerate(v.nsmallest(n_labels).items()):  # staggered so labels don't collide
        ax.annotate(f"{date:%b %Y}: {val:.0f}", (val, 0.5), xytext=(val, 10 + 9 * i),
                    ha="center", fontsize=8, arrowprops={"arrowstyle": "-", "lw": 0.6})
    ax.set(xlabel="VRP per non-overlapping 21-day block: implied minus realized vol, vol points",
           ylabel="Number of blocks",
           title=f"Distribution of the SPY variance risk premium ({len(v)} non-overlapping blocks): "
                 "small gains, rare large losses")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
