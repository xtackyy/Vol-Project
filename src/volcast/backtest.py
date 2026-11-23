"""Daily event-driven backtest with drift, a no-trade band, costs and financing.

For each day t (all quantities as fractions of NAV):
    1. The weight held from before earns the market until the trade:
       gross = w r + (1 - w) rf - max(w - 1, 0) * borrow_spread - max(-w, 0) * short_fee
       (financing per day / 252; "gross" = before trading costs), and drifts:
       w_drift = w (1 + r) / (1 + gross).
    2. Trade to the target only if |target - w_drift| > band; pay costs on |trade|.

Two fill times share one engine (`_simulate`):
    next open (headline)  the target decided at the close of t trades at the open of t+1;
                          the overnight gap is earned by the old weight.
    close (comparison)    the target trades at the same close it was computed from.
Either way a forecast never trades on the return it was made with.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import TRADING_DAYS, StrategyConfig


@dataclass
class BacktestResult:
    net: pd.Series        # daily net returns
    gross: pd.Series      # daily returns before trading costs
    costs: pd.Series      # daily cost drag
    weight: pd.Series     # end-of-day held weight (post trade)
    turnover: pd.Series   # |trade| per day, fraction of NAV

    @property
    def equity(self) -> pd.Series:
        return (1 + self.net).cumprod()


def _simulate(goals: np.ndarray, r_pre: np.ndarray, r_post: np.ndarray, rf: np.ndarray,
              frac_pre: float, cfg: StrategyConfig, band: float, idx: pd.Index) -> BacktestResult:
    """The one engine behind both fill times. Each day t has three steps:

        1. the weight held from the previous day earns the pre-trade segment (return r_pre[t]),
        2. the book trades to goals[t] if it is outside the no-trade band (NaN = no trade),
        3. the new weight earns the post-trade segment (return r_post[t]).

    Financing (rf, borrow spread, short fee) accrues `frac_pre` of a day before the trade and
    the rest after it. Costs are paid on |trade| between the two segments.
    """
    borrow = cfg.borrow_spread_bps / 1e4 / TRADING_DAYS
    short_fee = cfg.short_fee_bps / 1e4 / TRADING_DAYS
    cost_rate = cfg.cost_per_unit_traded

    def segment(w: float, r: float, rf_: float, frac: float) -> tuple[float, float]:
        if frac == 0.0 and r == 0.0:
            return 0.0, w
        g = (w * r + (1 - w) * rf_ * frac - max(w - 1.0, 0.0) * borrow * frac
             - max(-w, 0.0) * short_fee * frac)
        return g, (w * (1 + r) / (1 + g) if (1 + g) != 0 else w)

    n = len(idx)
    net, gross, costs, held, trades = (np.zeros(n) for _ in range(5))
    w = 0.0  # start flat
    for t in range(n):
        g1, w = segment(w, r_pre[t], rf[t], frac_pre)
        goal, c, trade = goals[t], 0.0, 0.0
        if not np.isnan(goal):
            w_new = goal if abs(goal - w) > band or (goal == 0.0 and w != 0.0) else w
            trade = abs(w_new - w)
            c = trade * cost_rate
            w = w_new
        held[t] = w
        g2, w = segment(w, r_post[t], rf[t], 1.0 - frac_pre)
        gross[t] = (1 + g1) * (1 + g2) - 1
        net[t] = (1 + g1) * (1 - c) * (1 + g2) - 1
        costs[t], trades[t] = c, trade

    def s(a: np.ndarray, name: str) -> pd.Series:
        return pd.Series(a, index=idx, name=name)

    return BacktestResult(s(net, "net"), s(gross, "gross"), s(costs, "costs"),
                          s(held, "weight"), s(trades, "turnover"))


def run_backtest(
    target: pd.Series,
    asset_ret: pd.Series,
    rf: pd.Series,
    cfg: StrategyConfig,
    band: float | None = None,
) -> BacktestResult:
    """Fill at the close: a target decided at the close of t is traded at that same close.

    This needs the signal before the closing print, which the day's own high / low / close
    can't provide, so it is the comparison case; the headline uses `run_backtest_next_open`.
    """
    band = cfg.rebalance_band if band is None else band
    idx = target.index
    r = asset_ret.reindex(idx).fillna(0.0).to_numpy(dtype=float, copy=True)
    rf_ = rf.reindex(idx).fillna(0.0).to_numpy(dtype=float, copy=True)
    r[0], rf_[0] = 0.0, 0.0  # nothing is held before the first close
    return _simulate(target.to_numpy(dtype=float), r, np.zeros(len(idx)), rf_, 1.0, cfg, band, idx)


def run_backtest_next_open(
    target: pd.Series,
    overnight_ret: pd.Series,
    intraday_ret: pd.Series,
    rf: pd.Series,
    cfg: StrategyConfig,
    band: float | None = None,
) -> BacktestResult:
    """Fill at the next open: a target decided at the close of t is traded at the open of t+1.

    Day t is split at the open: the weight carried from the previous close earns the
    overnight gap (close t-1 -> open t), then the book trades to target[t-1] and earns the
    intraday return (open t -> close t). So the overnight gap after a signal is never
    earned by the new position. Financing accrues half a day per segment. Costs per unit
    traded are unchanged, although opening-auction spreads can be wider than at the close.
    """
    band = cfg.rebalance_band if band is None else band
    idx = target.index
    r_on = overnight_ret.reindex(idx).fillna(0.0).to_numpy(dtype=float, copy=True)
    r_id = intraday_ret.reindex(idx).fillna(0.0).to_numpy(dtype=float, copy=True)
    rf_ = rf.reindex(idx).fillna(0.0).to_numpy(dtype=float, copy=True)
    r_on[0], r_id[0], rf_[0] = 0.0, 0.0, 0.0  # first signal is at the close of day 0
    goals = np.r_[np.nan, target.to_numpy(dtype=float)[:-1]]
    return _simulate(goals, r_on, r_id, rf_, 0.5, cfg, band, idx)


def backtest(target: pd.Series, market: pd.DataFrame, cfg: StrategyConfig,
             band: float | None = None) -> BacktestResult:
    """Backtest with the fill time set in `cfg.execution` ("next_open" or "close")."""
    if cfg.execution == "close":
        return run_backtest(target, market["close"].pct_change(), market["rf"], cfg, band)
    if cfg.execution != "next_open":
        raise ValueError(f"unknown execution {cfg.execution!r}")
    overnight = market["open"] / market["close"].shift(1) - 1
    intraday = market["close"] / market["open"] - 1
    return run_backtest_next_open(target, overnight, intraday, market["rf"], cfg, band)


def buy_and_hold(index: pd.Index, asset_ret: pd.Series, rf: pd.Series, cfg: StrategyConfig) -> BacktestResult:
    """Benchmark: fully invested from the first out-of-sample close, same cost model."""
    return run_backtest(pd.Series(1.0, index=index), asset_ret, rf, cfg, band=0.0)


def buy_and_hold_market(index: pd.Index, market: pd.DataFrame, cfg: StrategyConfig) -> BacktestResult:
    """Buy & hold with the same fill time as the strategies (`cfg.execution`)."""
    return backtest(pd.Series(1.0, index=index), market, cfg, band=0.0)
