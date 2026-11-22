"""Publication-quality figures (matplotlib + seaborn), one function per chart."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter

# Colour-blind-validated categorical slots, fixed order; benchmark is neutral grey.
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
GREY, INK, INK_2, GRID, SURFACE = "#8a8984", "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"

STRATEGY_COLORS = {
    "Vol target + signal": BLUE,
    "Vol target only": AQUA,
    "Signal only": ORANGE,
    "Vol target + signal (long-short)": YELLOW,
    "Buy & hold": GREY,
}


def set_style() -> None:
    sns.set_theme(style="whitegrid", context="paper")
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": GRID, "grid.color": GRID, "grid.linewidth": 0.6,
        "axes.labelcolor": INK_2, "xtick.color": INK_2, "ytick.color": INK_2,
        "text.color": INK, "axes.titleweight": "bold", "axes.titlesize": 12,
        "axes.titlelocation": "left", "font.size": 10, "legend.frameon": False,
        "lines.linewidth": 1.4, "figure.dpi": 110, "savefig.dpi": 200,
        "axes.spines.top": False, "axes.spines.right": False,
    })


def _plain_log_axis(axis) -> None:
    """Log scale with plain tick labels (5, 10, 20 ... instead of 2x10^1)."""
    axis.set_major_locator(LogLocator(base=10, subs=(1.0, 2.0, 3.0, 5.0)))
    axis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    axis.set_minor_formatter(NullFormatter())


def _save(fig: plt.Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_vol_forecast(actual: pd.Series, ridge: pd.Series, har: pd.Series, path: Path,
                      horizon: int) -> Path:
    """(1) Predicted vs actual forward realized vol: time series + calibration scatter."""
    set_style()
    df = pd.concat({"actual": actual, "ridge": ridge, "har": har}, axis=1).dropna()
    vol = np.exp(df) * 100  # log annualised vol -> annualised %
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.6), gridspec_kw={"width_ratios": [2.6, 1]})

    ax1.plot(vol.index, vol["actual"], color=GREY, lw=0.8, alpha=0.8, label="Realized")
    ax1.plot(vol.index, vol["har"], color=ORANGE, lw=1.1, label="HAR-RV (OLS)")
    ax1.plot(vol.index, vol["ridge"], color=BLUE, lw=1.1, label="Ridge-HAR")
    ax1.set_yscale("log")
    _plain_log_axis(ax1.yaxis)
    ax1.set_ylabel("Annualised vol, % (log scale)")
    ax1.set_title(f"Out-of-sample {horizon}-day forward realized volatility")
    ax1.legend(loc="upper left", ncols=3)

    ax2.scatter(vol["ridge"], vol["actual"], s=8, color=BLUE, alpha=0.35, edgecolors="none")
    lo, hi = vol[["ridge", "actual"]].min().min(), vol[["ridge", "actual"]].max().max()
    ax2.plot([lo, hi], [lo, hi], color=INK_2, lw=1, ls="--")
    ax2.set_xscale("log"), ax2.set_yscale("log")
    _plain_log_axis(ax2.xaxis), _plain_log_axis(ax2.yaxis)
    ax2.set_xlabel("Ridge forecast, %"), ax2.set_ylabel("Realized, %")
    ax2.set_title("Calibration (45° line = unbiased)")
    fig.tight_layout()
    return _save(fig, path)


def plot_equity(curves: dict[str, pd.Series], path: Path, cost_bps: float) -> Path:
    """(2) Cumulative equity curves, net of costs, log scale."""
    set_style()
    fig, ax = plt.subplots(figsize=(12, 5))
    finals = {}
    for name, net in curves.items():
        eq = (1 + net).cumprod()
        ax.plot(eq.index, eq, color=STRATEGY_COLORS.get(name, INK), lw=1.6 if name != "Buy & hold" else 1.3,
                label=name)
        finals[name] = (eq.index[-1], float(eq.iloc[-1]))
    # End-of-line value labels, pushed apart in log space so they never collide.
    placed: list[float] = []
    for _name, (x, y) in sorted(finals.items(), key=lambda kv: kv[1][1]):
        ly = np.log(y)
        if placed and ly - placed[-1] < 0.05:
            ly = placed[-1] + 0.05
        placed.append(ly)
        ax.annotate(f"{y:.2f}x", (x, np.exp(ly)), xytext=(4, 0), textcoords="offset points",
                    va="center", fontsize=9, color=INK_2)
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    ax.yaxis.set_minor_formatter(FuncFormatter(lambda v, _: f"{v:g}" if round(v * 10) % 5 == 0 else ""))
    ax.set_ylabel("Growth of $1 (log scale)")
    ax.set_title(f"Out-of-sample equity curve, net of {cost_bps:.1f} bps per unit traded")
    ax.legend(loc="upper left")
    fig.tight_layout()
    return _save(fig, path)


def plot_rolling_risk(rolling_sharpes: dict[str, pd.Series], drawdowns: dict[str, pd.Series],
                      path: Path) -> Path:
    """(3) Rolling 1y Sharpe ratio and drawdown, stacked on a shared time axis."""
    set_style()
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), sharex=True,
                                   gridspec_kw={"height_ratios": [1.2, 1]})
    for name, s in rolling_sharpes.items():
        ax1.plot(s.index, s, color=STRATEGY_COLORS.get(name, INK), lw=1.3, label=name)
    ax1.axhline(0, color=INK_2, lw=0.8)
    ax1.set_ylabel("Sharpe (252d rolling)")
    ax1.set_title("Rolling Sharpe ratio")
    ax1.legend(loc="upper left", ncols=len(rolling_sharpes))

    for name, dd in drawdowns.items():
        color = STRATEGY_COLORS.get(name, INK)
        ax2.plot(dd.index, dd * 100, color=color, lw=1.1, label=name)
        if name != "Buy & hold":
            ax2.fill_between(dd.index, dd * 100, 0, color=color, alpha=0.12, lw=0)
    ax2.set_ylabel("Drawdown, %")
    ax2.set_title("Drawdown from peak")
    fig.tight_layout()
    return _save(fig, path)


def plot_feature_selection(coefs: pd.DataFrame, path: Path, title: str) -> Path:
    """(4) How often Lasso keeps each feature across refits, and its mean sign."""
    set_style()
    freq = (coefs.abs() > 1e-12).mean().sort_values()
    mean_coef = coefs.mean().reindex(freq.index)
    fig, ax = plt.subplots(figsize=(8, 0.32 * len(freq) + 1.4))
    colors = [BLUE if c >= 0 else ORANGE for c in mean_coef]
    ax.barh(freq.index, freq * 100, color=colors, height=0.6)
    for y, (f, c) in enumerate(zip(freq, mean_coef, strict=True)):
        label = "never selected" if f == 0 else f"{f:.0%}  ({'+' if c >= 0 else '−'})"
        ax.text(f * 100 + 1, y, label, va="center",
                fontsize=8, color=INK_2)
    ax.set_xlim(0, 112)
    ax.set_xlabel("Share of walk-forward refits with non-zero coefficient, %")
    ax.set_title(title)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    return _save(fig, path)


ASSET_COLORS = {"SPY": BLUE, "TLT": ORANGE, "GLD": YELLOW, "Equal-weight (vol-targeted)": AQUA}


def plot_multi_asset_equity(curves: dict[str, pd.Series], path: Path, title: str) -> Path:
    """Growth of $1 for each asset's vol-targeted strategy plus the combined book (log scale)."""
    set_style()
    fig, ax = plt.subplots(figsize=(12, 5))
    finals = {}
    for name, net in curves.items():
        eq = (1 + net).cumprod()
        combo = name.startswith("Equal")
        ax.plot(eq.index, eq, color=ASSET_COLORS.get(name, GREY), lw=2.2 if combo else 1.4, label=name)
        finals[name] = (eq.index[-1], float(eq.iloc[-1]))
    placed: list[float] = []
    for _name, (x, y) in sorted(finals.items(), key=lambda kv: kv[1][1]):
        ly = np.log(y)
        if placed and ly - placed[-1] < 0.05:
            ly = placed[-1] + 0.05
        placed.append(ly)
        ax.annotate(f"{y:.2f}x", (x, np.exp(ly)), xytext=(4, 0), textcoords="offset points",
                    va="center", fontsize=9, color=INK_2)
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    ax.yaxis.set_minor_formatter(FuncFormatter(lambda v, _: f"{v:g}" if round(v * 10) % 5 == 0 else ""))
    ax.set_ylabel("Growth of $1 (log scale)")
    ax.set_title(title)
    ax.legend(loc="upper left")
    fig.tight_layout()
    return _save(fig, path)


def plot_rolling_correlations(pairs: dict[str, pd.Series], path: Path) -> Path:
    """Rolling 1-year correlation of the vol-targeted strategy returns, per asset pair."""
    set_style()
    fig, ax = plt.subplots(figsize=(12, 4.2))
    colors = [BLUE, ORANGE, AQUA, YELLOW]
    for (name, s), c in zip(pairs.items(), colors, strict=False):
        ax.plot(s.index, s, color=c, lw=1.4, label=name)
    ax.axhline(0, color=INK_2, lw=0.8)
    ax.set_ylim(-1, 1)
    ax.set_ylabel("Correlation (252d)")
    ax.set_title("Rolling 1-year correlation of vol-targeted strategy returns")
    ax.legend(loc="lower left", ncols=len(pairs))
    fig.tight_layout()
    return _save(fig, path)
