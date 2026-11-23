r"""Variance risk premium extension: one command runs every milestone built so far.

    python scripts\run_vrp.py        # -> reports\vrp\ and reports\figures\vrp\

1. Data, implied / realized variance, VRP descriptive statistics, first two plots.
2. 21-day HAR walk-forward forecasts vs VIX: accuracy, Mincer-Zarnowitz, encompassing.
3. Synthetic variance-swap backtests of every strategy, with robustness checks.
4. Remaining figures, drawn from the files milestones 2 and 3 saved.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from volcast.metrics import deflated_sharpe  # noqa: E402
from vrp import plots  # noqa: E402
from vrp.backtest import (  # noqa: E402
    SwapConfig,
    always,
    conditional,
    etp_pnl,
    not_backwardated,
    roll_dates,
    short_variance_pnl,
    sized,
    staggered,
    vol_target_size,
)
from vrp.config import CRISES, REGIMES, VRPConfig  # noqa: E402
from vrp.data import load_vrp_data  # noqa: E402
from vrp.evaluate import (  # noqa: E402
    describe_vrp,
    encompassing,
    etp_stats,
    forecast_accuracy,
    hac_mean_test,
    mz_table,
    ols_hac,
    period_pnl,
    strategy_stats,
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


def _run(data: pd.DataFrame, size: pd.Series, swap: SwapConfig, start, entry_lag: int = 0) -> pd.DataFrame:
    return short_variance_pnl(data["vix"], data["close"], size, swap, entry_lag).loc[start:]


def _table(results: dict[str, pd.DataFrame], swap: SwapConfig) -> pd.DataFrame:
    return pd.DataFrame({k: strategy_stats(v, swap.capital) for k, v in results.items()}).T


def milestone3(cfg: VRPConfig, data: pd.DataFrame, fc: pd.DataFrame) -> None:
    """Variance-swap backtests. All sizes are decided from data up to the signal date."""
    h, out = cfg.horizon, cfg.output_dir
    swap = SwapConfig(horizon=h)
    spread = fc["spread"]
    start = spread.index[0]
    th0 = cfg.headline_threshold
    # Vol-targeted size from the trailing P&L vol of a 1-unit always-short book (data up to t).
    unit = short_variance_pnl(data["vix"], data["close"], staggered(data.index, h), swap)["pnl"]
    vt = vol_target_size(unit, swap.capital, cfg.vt_target_vol, cfg.vt_lookback, cfg.size_cap).reindex(spread.index)
    rules = {
        "Always short": always(spread),
        f"Conditional (spread > {th0:g})": conditional(spread, th0),
        "Sized by spread": sized(spread, cfg.size_cap),
        "Always short, vol-targeted": vt,
        f"Conditional (spread > {th0:g}), vol-targeted": conditional(spread, th0) * vt,
    }
    roll, stag = roll_dates(spread.index, h), staggered(spread.index, h)

    # 1. Headline: monthly roll and daily-staggered tranches, 1998+.
    main = {f"{k} | monthly": _run(data, roll * r, swap, start) for k, r in rules.items()}
    main |= {f"{k} | staggered": _run(data, stag * r, swap, start) for k, r in rules.items()}
    # Comparison only: constant-size always-short scaled (with hindsight) to the vol-targeted book's
    # average risk, so drawdowns are compared at equal risk. P&L is linear in size, costs included.
    plain, vt_book = main["Always short | staggered"], main["Always short, vol-targeted | staggered"]
    k_match = vt_book["pnl"].std() / plain["pnl"].std()
    main["Always short, constant size at the same average risk (hindsight scale) | staggered"] = plain.assign(
        pnl=plain["pnl"] * k_match, vega=plain["vega"] * k_match)
    headline = _table(main, swap)

    # 2. Threshold grid (monthly and staggered), every value shown.
    grid = {}
    for th in cfg.thresholds:
        for label, sched in (("monthly", roll), ("staggered", stag)):
            res = _run(data, sched * conditional(spread, th), swap, start)
            grid[(th, label)] = strategy_stats(res, swap.capital)
    grid = pd.DataFrame(grid).T
    grid.index.names = ["threshold", "roll"]

    # 3. Roll-date sensitivity: all 21 possible monthly roll dates.
    offsets = []
    for k, r in rules.items():
        for o in range(h):
            st = strategy_stats(_run(data, roll_dates(spread.index, h, o) * r, swap, start), swap.capital)
            offsets.append({"strategy": k, "offset": o, **st})
    offsets = pd.DataFrame(offsets)
    offset_summary = offsets.groupby("strategy", sort=False)[["sharpe", "max_drawdown", "worst_month"]].describe(
        percentiles=[0.5])[[(m, s) for m in ("sharpe", "max_drawdown", "worst_month") for s in ("min", "50%", "max")]]

    # 4. Flat in backwardation (VIX > VIX3M), from the first VIX3M date, against the same rules there.
    ok = not_backwardated(data["vix"], data["vix3m"]).reindex(spread.index)
    start_b = ok.first_valid_index()
    back = {}
    for k in ("Always short", f"Conditional (spread > {th0:g})"):
        for label, sched in (("monthly", roll), ("staggered", stag)):
            back[f"{k} | {label}"] = _run(data, sched * rules[k], swap, start_b)
            back[f"{k}, flat in backwardation | {label}"] = _run(data, sched * rules[k] * ok.fillna(0), swap, start_b)
    backwardation = _table(back, swap)

    # 5. Robustness: half the cost; entry one day after the signal.
    robust = {}
    cheap = SwapConfig(horizon=h, cost_vol_pts=cfg.cost_sensitivity_vol_pts)
    for k, r in rules.items():
        robust[f"{k} | cost {cfg.cost_sensitivity_vol_pts:g} vol pt"] = _run(data, stag * r, cheap, start)
        robust[f"{k} | enter at t+1"] = _run(data, stag * r, swap, start, entry_lag=1)
    # The backwardation filter gets the same checks: entry at t+1 and all 21 roll dates.
    flat_b = rules["Always short"] * ok.fillna(0)
    robust["Always short, flat in backwardation | enter at t+1"] = _run(data, stag * flat_b, swap, start_b, entry_lag=1)
    robust["Always short (same sample) | enter at t+1"] = _run(data, stag * rules["Always short"], swap, start_b,
                                                               entry_lag=1)
    robustness = _table(robust, swap)
    for name, r in (("Always short (from VIX3M start)", rules["Always short"]),
                    ("Always short, flat in backwardation", flat_b)):
        for o in range(h):
            st = strategy_stats(_run(data, roll_dates(spread.index, h, o) * r, swap, start_b), swap.capital)
            offsets = pd.concat([offsets, pd.DataFrame([{"strategy": name, "offset": o, **st}])], ignore_index=True)
    offset_summary = offsets.groupby("strategy", sort=False)[["sharpe", "max_drawdown", "worst_month"]].describe(
        percentiles=[0.5])[[(m, s) for m in ("sharpe", "max_drawdown", "worst_month") for s in ("min", "50%", "max")]]

    # Multiple testing: deflated Sharpe of the best threshold-grid configuration (volcast.metrics).
    trial_pnl = {}
    for th in cfg.thresholds:
        for label, sched in (("monthly", roll), ("staggered", stag)):
            trial_pnl[f"{th:g} {label}"] = _run(data, sched * conditional(spread, th), swap, start)["pnl"]
    trial_pnl = pd.DataFrame(trial_pnl)
    srs = (trial_pnl.mean() / trial_pnl.std()).to_numpy()
    best = trial_pnl.columns[srs.argmax()]
    # Against zero, and the more relevant test: P&L in excess of always-short on the same roll schedule.
    base = {"monthly": _run(data, roll * rules["Always short"], swap, start)["pnl"],
            "staggered": _run(data, stag * rules["Always short"], swap, start)["pnl"]}
    excess = pd.DataFrame({c: trial_pnl[c] - base[c.split()[1]] for c in trial_pnl})
    ex_srs = np.nan_to_num((excess.mean() / excess.std()).to_numpy())
    ex_best = excess.columns[ex_srs.argmax()]
    dsr = pd.DataFrame({
        "vs zero": {"best_config": best, **deflated_sharpe(trial_pnl[best], srs)},
        "excess over always short": {"best_config": ex_best, **deflated_sharpe(excess[ex_best], ex_srs)},
    })

    # 6. Crisis windows (% of capital), staggered versions.
    crisis = pd.DataFrame({k: period_pnl(v["pnl"], REGIMES, swap.capital)
                           for k, v in main.items() if k.endswith("staggered")})
    for k in ("Always short | staggered", "Always short, flat in backwardation | staggered"):
        crisis[f"{k} (from {start_b:%Y})"] = period_pnl(back[k]["pnl"], REGIMES, swap.capital)

    # 7. Tradable proxies: long SVXY / short VXX, always vs only when spread > threshold.
    pos = conditional(spread, th0).reindex(data.index)
    etp = {}
    for name, col, sign in (("SVXY long", "svxy", 1.0), ("VXX short", "vxx", -1.0)):
        px = data[col].dropna()
        if px.empty:
            continue
        for rule, p in (("always", pd.Series(1.0, index=data.index)), (f"spread > {th0:g}", pos)):
            r = etp_pnl(px, sign * p.reindex(px.index).fillna(0.0)).loc[start:]
            etp[f"{name}, {rule}"] = etp_stats(r)
            if col == "svxy":   # -1x until 27 Feb 2018, -0.5x after: report the two regimes too
                etp[f"{name}, {rule}, to 2018-02-27 (-1x)"] = etp_stats(r.loc[:"2018-02-27"])
                etp[f"{name}, {rule}, from 2018-02-28 (-0.5x)"] = etp_stats(r.loc["2018-02-28":])
    etp = pd.DataFrame(etp).T

    pnl_daily = pd.DataFrame({k: v["pnl"] for k, v in main.items()})
    pnl_daily.to_csv(out / "strategy_daily_pnl.csv")
    for name, t in {"strategy_headline": headline, "strategy_threshold_grid": grid,
                    "strategy_roll_offsets": offsets, "strategy_backwardation": backwardation,
                    "strategy_robustness": robustness, "strategy_crisis_pnl": crisis, "etp_check": etp,
                    "strategy_grid_deflated_sharpe": dsr}.items():
        t.to_csv(out / f"{name}.csv")

    pct = ["ann_return", "ann_vol", "max_drawdown", "worst_month", "worst_21d", "time_in_market"]

    def fmt(t: pd.DataFrame) -> str:
        t = t.copy()
        for c in t.columns:
            if c in pct:
                t[c] = t[c].map(lambda x: f"{x:.1%}")
            elif c == "avg_vega_in_market":
                t[c] = t[c].map(lambda x: f"{x:,.0f}")
            elif t[c].dtype.kind == "f":
                t[c] = t[c].map(lambda x: f"{x:.2f}")
        return t.to_markdown()

    # What the vol-targeted rule had on when each stress window began (size 1 = $10k vega).
    vt_entry = pd.DataFrame({k: {"size_at_start": vt.asof(pd.Timestamp(a)),
                                 "vix_at_start": data["vix"].asof(pd.Timestamp(a))}
                             for k, (a, _) in REGIMES.items() if k in CRISES}).T
    n_configs = len(main) + len(grid) + len(offsets) + len(back) + len(robust)
    lines = [
        "# Short-variance backtests: synthetic 21-day SPY variance swaps", "",
        f"Entries {start:%Y-%m-%d} to {data.index[-1]:%Y-%m-%d}. Vega notional ${swap.vega_notional:,.0f} per vol "
        f"point, strike = VIX - {swap.cost_vol_pts:g} vol pt, daily mark-to-market, no cap on realized variance. "
        f"Returns are P&L / ${swap.capital:,.0f} capital (not compounded). "
        f"Headline conditional threshold ({th0:g}) fixed before running; {len(cfg.thresholds)} thresholds shown. "
        f"{n_configs} backtest configurations in total in this file.", "",
        "## Headline", "", fmt(headline), "",
        "## Threshold grid (all values)", "", fmt(grid), "",
        "## Roll-date sensitivity: all 21 monthly roll dates (min / median / max)", "",
        offset_summary.round(3).to_markdown(), "",
        f"## Flat in backwardation (VIX > VIX3M), entries from {start_b:%Y-%m-%d}", "", fmt(backwardation), "",
        f"## Deflated Sharpe of the best of the {len(srs)} threshold-grid configurations (annualised Sharpe)", "",
        dsr.to_markdown(), "",
        "## Robustness (staggered)", "", fmt(robustness), "",
        f"## Vol-targeted size on the first day of each stress window (target {cfg.vt_target_vol:.0%}, "
        f"{cfg.vt_lookback}-day trailing vol, cap {cfg.size_cap:g})", "",
        "The rule sizes from the last 63 days. Before the sharp crashes (2008, 2011, 2018, 2020) "
        "those were calm, so it entered "
        "at a normal size or larger (1.8x into Feb 2018, after the calm of 2017) "
        "and only cut after the first shock. The realized P&L vol overshoots the 10% target "
        "because a few crash days dominate the full-sample standard deviation.", "",
        vt_entry.round(2).to_markdown(), "",
        "## P&L in stress windows and calm years, % of capital (staggered)", "",
        crisis.map(lambda x: f"{x:.1%}").to_markdown(), "",
        "## Tradable proxies (compounded daily returns; SVXY leverage changed on 2018-02-28)", "",
        fmt(etp), "",
    ]
    (out / "results_strategies.md").write_text("\n".join(lines), encoding="utf-8")
    cols = ["ann_return", "ann_vol", "sharpe", "sortino", "max_drawdown", "worst_month", "worst_21d",
            "skew_monthly", "time_in_market"]
    print(headline[cols].round(3).to_string())
    print(grid[["ann_return", "sharpe", "max_drawdown", "worst_month", "time_in_market"]].round(3).to_string())
    print(offset_summary.round(3).to_string())
    print(backwardation[cols].round(3).to_string())
    print(robustness[["ann_return", "sharpe", "max_drawdown", "worst_month"]].round(3).to_string())
    print(crisis.round(3).to_string())
    print(dsr.to_string())
    print(etp.round(3).to_string())


def milestone4(cfg: VRPConfig) -> None:
    swap = SwapConfig()
    out, figs = cfg.output_dir, cfg.figure_dir
    fc = pd.read_csv(out / "forecasts.csv", index_col=0, parse_dates=True)
    pnl = pd.read_csv(out / "strategy_daily_pnl.csv", index_col=0, parse_dates=True)
    coef = pd.read_csv(out / "signal_vrp_on_spread.csv", index_col=0)
    plots.forecasts_calm_vs_crisis(fc, {"Calm: 2017": ("2017-01-01", "2017-12-31"),
                                        "Crisis: 2020 Covid": ("2020-01-01", "2020-06-30")},
                                   figs / "3_forecasts_calm_vs_crisis.png")
    th0 = f"{cfg.headline_threshold:g}"
    cols = {"Always short | staggered": "Always short",
            f"Conditional (spread > {th0}) | staggered": f"Conditional (spread > {th0})",
            "Sized by spread | staggered": "Sized by spread",
            "Always short, vol-targeted | staggered": "Always short, vol-targeted"}
    plots.cumulative_pnl(pnl[list(cols)].rename(columns=cols), swap.capital,
                         {k: REGIMES[k] for k in CRISES}, figs / "4_cumulative_pnl.png")
    plots.spread_vs_vrp(fc, coef, figs / "5_spread_vs_vrp.png")


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
    fc = milestone2(cfg, data, vrp)
    milestone3(cfg, data, fc)
    milestone4(cfg)
    print(f"Files: {cfg.output_dir}, {cfg.figure_dir}")


if __name__ == "__main__":
    main()
