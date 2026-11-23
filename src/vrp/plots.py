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


# Fixed categorical order (validated: CVD separation >= 9 ΔE; the two lighter hues get direct labels).
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
INK = "#3a3a38"   # realized vol: the outcome, drawn in neutral ink rather than a series hue


def forecasts_calm_vs_crisis(fc: pd.DataFrame, windows: dict[str, tuple[str, str]], path: Path) -> None:
    """VIX and the HAR forecast made at t, against the vol SPY then realized over t+1..t+21."""
    fig, axes = plt.subplots(1, len(windows), figsize=(12, 4.6), sharey=False)
    for ax, (name, (a, b)) in zip(axes, windows.items(), strict=True):
        d = fc.loc[a:b]
        ax.plot(d.index, d["rv_vol"], color=INK, lw=2, label="Realized over the next 21 days")
        ax.plot(d.index, d["iv_vol"], color=SERIES[0], lw=2, label="VIX at t")
        ax.plot(d.index, d["har_ridge"], color=SERIES[1], lw=2, label="HAR-Ridge forecast at t")
        mae = {k: (d["rv_vol"] - d[k]).abs().mean() for k in ("iv_vol", "har_ridge")}
        ax.set(title=f"{name}   (MAE: VIX {mae['iv_vol']:.1f}, HAR {mae['har_ridge']:.1f} vol pts)",
               ylabel="Vol points (annualised %)")
        ax.tick_params(axis="x", labelrotation=30)
    axes[0].legend(loc="upper left", fontsize=8)
    fig.suptitle("21-day vol forecasts made at t vs what SPY then realized (plotted at the forecast date)")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def cumulative_pnl(pnl: pd.DataFrame, capital: float, crises: dict[str, tuple[str, str]], path: Path) -> None:
    """Cumulative P&L (% of capital, not compounded) per strategy, with each one's drawdown below."""
    cum = pnl.cumsum() / capital * 100
    dd = cum - cum.cummax()
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 7.5), sharex=True, height_ratios=[3, 2])
    for i, col in enumerate(cum.columns):
        a1.plot(cum.index, cum[col], color=SERIES[i], lw=1.5, label=col)
        a1.annotate(f"{cum[col].iloc[-1]:.0f}%", (cum.index[-1], cum[col].iloc[-1]), xytext=(4, 0),
                    textcoords="offset points", va="center", fontsize=8, color=INK)
        a2.plot(dd.index, dd[col], color=SERIES[i], lw=1.2,
                label=f"{col}: max {dd[col].min():.0f}% ({dd[col].idxmin():%b %Y})")
    for ax in (a1, a2):
        _shade(ax, crises)
    a1.axhline(0, color=INK, lw=0.7)
    a1.set(ylabel="Cumulative P&L, % of capital",
           title=r"Short 21-day SPY variance swaps, \$10k vega per \$1m capital, staggered daily entries")
    a1.legend(loc="upper left", fontsize=8)
    a2.set(ylabel="Drawdown, % of capital", title="Drawdown from the previous peak")
    a2.legend(loc="lower left", fontsize=8)
    a2.set_ylim(dd.min().min() * 1.15, 5)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def spread_vs_vrp(fc: pd.DataFrame, coef: pd.DataFrame, path: Path, bins: int = 10) -> None:
    """Does VIX minus the HAR forecast at t predict the VRP over t+1..t+21? Daily points + decile means."""
    d = fc.dropna(subset=["spread", "vrp_vol"])
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(d["spread"], d["vrp_vol"], s=6, alpha=0.15, color=SERIES[0], lw=0,
               label=f"Daily entries ({len(d):,}, overlapping 21-day windows)")
    g = d.groupby(pd.qcut(d["spread"], bins), observed=True)
    ax.plot(g["spread"].mean(), g["vrp_vol"].mean(), "o-", color=SERIES[1], ms=8, lw=2,
            mec="white", mew=2, label="Mean VRP per spread decile")
    a, b = coef.loc["const", "coef"], coef.loc["spread", "coef"]
    xs = pd.Series([d["spread"].quantile(0.005), d["spread"].quantile(0.995)])
    ax.plot(xs, a + b * xs, color=INK, lw=1.5, ls="--",
            label=f"OLS: slope {b:.2f} (Newey-West t {coef.loc['spread', 't_hac']:.1f}), R² {coef['r2'].iloc[0]:.3f}")
    ax.axhline(0, color=INK, lw=0.7)
    ax.axvline(0, color=INK, lw=0.7)
    ax.set(xlabel="Spread at t: VIX minus HAR-Ridge forecast, vol points",
           ylabel="VRP over t+1..t+21: VIX minus realized vol, vol points",
           title="A richer VIX (vs HAR) predicts a slightly larger premium, but explains 1% of it",
           xlim=(xs.iloc[0] - 2, xs.iloc[1] + 2), ylim=(d["vrp_vol"].quantile(0.002), d["vrp_vol"].quantile(0.999)))
    ax.legend(loc="lower left", fontsize=8)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
