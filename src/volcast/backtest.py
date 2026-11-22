"""Daily event-driven backtest with drift, a no-trade band, costs and financing.

For each day t (all quantities as fractions of NAV):
    1. Enter the day holding weight w_{t-1} (set at the close of t-1).
    2. Gross P&L: w r_t + (1 - w) rf_t - max(w - 1, 0) * borrow_spread / 252
                  - max(-w, 0) * short_fee / 252        ("gross" = before trading costs)
    3. The weight drifts with the market: w_drift = w (1 + r_t) / (1 + gross).
    4. At the close, trade to the new target only if |target - w_drift| > band.
    5. Pay costs on |trade| (commission + slippage per unit notional).

The weight used on day t was decided at t-1, so a forecast can never trade on the
return it was made with.
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


def run_backtest(
    target: pd.Series,
    asset_ret: pd.Series,
    rf: pd.Series,
    cfg: StrategyConfig,
    band: float | None = None,
) -> BacktestResult:
    """Simulate `target` weights (decided at each close) against simple asset returns."""
    band = cfg.rebalance_band if band is None else band
    idx = target.index
    r = asset_ret.reindex(idx).fillna(0.0).to_numpy()
    rf_ = rf.reindex(idx).fillna(0.0).to_numpy()
    tgt = target.to_numpy()
    borrow = cfg.borrow_spread_bps / 1e4 / TRADING_DAYS
    short_fee = cfg.short_fee_bps / 1e4 / TRADING_DAYS
    cost_rate = cfg.cost_per_unit_traded

    n = len(idx)
    net, gross, costs, held, trades = (np.zeros(n) for _ in range(5))
    w = 0.0  # start flat; the first close is the first trade
    for t in range(n):
        # Short proceeds sit in cash (earning rf via the (1 - w) term); shorts pay a borrow fee.
        g = 0.0 if t == 0 else (w * r[t] + (1 - w) * rf_[t] - max(w - 1.0, 0.0) * borrow
                                - max(-w, 0.0) * short_fee)
        w_drift = w * (1 + r[t]) / (1 + g) if t > 0 and (1 + g) != 0 else w
        w_new = tgt[t] if abs(tgt[t] - w_drift) > band or (tgt[t] == 0.0 and w_drift != 0.0) else w_drift
        trade = abs(w_new - w_drift)
        c = trade * cost_rate
        gross[t], costs[t], trades[t], held[t] = g, c, trade, w_new
        net[t] = (1 + g) * (1 - c) - 1
        w = w_new

    def s(a: np.ndarray, name: str) -> pd.Series:
        return pd.Series(a, index=idx, name=name)

    return BacktestResult(s(net, "net"), s(gross, "gross"), s(costs, "costs"),
                          s(held, "weight"), s(trades, "turnover"))


def buy_and_hold(index: pd.Index, asset_ret: pd.Series, rf: pd.Series, cfg: StrategyConfig) -> BacktestResult:
    """Benchmark: fully invested from the first out-of-sample close, same cost model."""
    return run_backtest(pd.Series(1.0, index=index), asset_ret, rf, cfg, band=0.0)
