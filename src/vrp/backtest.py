"""Synthetic 21-day variance swaps on SPY: P&L engine and strategies. No options data needed.

One short variance swap opened at the close of day e (strike set from VIX at e):
    strike           K = VIX_e - cost                (vol points; the seller gives up `cost` as bid-ask)
    variance notional  N = size * vega_notional / (2 K)  (so a 1 vol point move near K is worth ~vega)
    payoff at e + T  N * (K^2 - RV),  RV = 252/T * sum of squared daily log returns e+1..e+T, x 10^4
Daily mark-to-market at e + k (k = 0..T), with VIX_t as the implied vol of the remaining days:
    value_k = N * (K^2 - [252/T * 10^4 * sum r^2 over e+1..e+k  +  (T-k)/T * VIX_{e+k}^2])
At k = 0 the value is N (K^2 - VIX_e^2) < 0: the cost is booked on entry. At k = T it is the payoff.
Daily P&L = change in value, summed over open swaps. A VIX spike shows up as a loss on the day it
happens, not three weeks later at expiry. No cap on realized variance; no margin modelling.

Timing: the size decided from information at t (VIX close at t, HAR forecast from SPY up to t) opens a
swap at t (entry_lag=0, strike VIX_t) or t+1 (entry_lag=1, strike VIX_{t+1}); its realized leg always
starts with the return of the day after entry.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from volcast.config import TRADING_DAYS


@dataclass(frozen=True)
class SwapConfig:
    horizon: int = 21
    vega_notional: float = 10_000.0   # $ per vol point
    cost_vol_pts: float = 1.0         # haircut on the strike: sell at VIX - cost
    capital: float = 1_000_000.0      # only used to express P&L as a % return


def short_variance_pnl(vix: pd.Series, close: pd.Series, size: pd.Series, cfg: SwapConfig,
                       entry_lag: int = 0) -> pd.DataFrame:
    """Daily P&L ($), vega exposure ($ per vol point) and entries for swaps opened per `size`.

    `size` is indexed by signal date; 0 or NaN = no new swap that day. Swaps run for `horizon`
    days; one still open at the end of the data is marked to market up to the last day.
    """
    idx = close.index
    T = cfg.horizon
    v = vix.reindex(idx).to_numpy(dtype=float)
    r2 = np.log(close / close.shift(1)).fillna(0.0).to_numpy() ** 2 * 1e4 * TRADING_DAYS / T
    s = size.reindex(idx).fillna(0.0).to_numpy(dtype=float)
    n = len(idx)
    pnl, exposure, entries = np.zeros(n), np.zeros(n), np.zeros(n)
    for sig in np.flatnonzero(s > 0):
        e = sig + entry_lag
        if e >= n or not np.isfinite(v[e]):
            continue
        K = v[e] - cfg.cost_vol_pts
        N = s[sig] * cfg.vega_notional / (2 * K)
        last = min(e + T, n - 1)
        k = np.arange(0, last - e + 1)
        realized = np.concatenate([[0.0], np.cumsum(r2[e + 1:last + 1])])
        value = N * (K**2 - (realized + (T - k) / T * v[e + k] ** 2))
        pnl[e:last + 1] += np.diff(np.concatenate([[0.0], value]))
        exposure[e + 1:last + 1] += s[sig] * cfg.vega_notional
        entries[e] += s[sig]
    return pd.DataFrame({"pnl": pnl, "vega": exposure, "entries": entries}, index=idx)


# ----------------------------------------------------------------------------- sizing rules
# Each returns a size per signal date (1 = one unit of vega notional), using only data up to t.

def roll_dates(index: pd.DatetimeIndex, horizon: int, offset: int = 0) -> pd.Series:
    """1 on every `horizon`-th date from `offset`: back-to-back monthly swaps."""
    out = pd.Series(0.0, index=index)
    out.iloc[offset::horizon] = 1.0
    return out


def staggered(index: pd.DatetimeIndex, horizon: int) -> pd.Series:
    """1/horizon every day: 21 overlapping tranches, one maturing each day (no roll-date luck)."""
    return pd.Series(1.0 / horizon, index=index)


def always(spread: pd.Series) -> pd.Series:
    return pd.Series(1.0, index=spread.index)


def conditional(spread: pd.Series, threshold: float) -> pd.Series:
    """Sell only when VIX is richer than the HAR forecast by more than `threshold` vol points."""
    return (spread > threshold).astype(float)


def sized(spread: pd.Series, cap: float = 2.0) -> pd.Series:
    """Size proportional to the spread, scaled by its average up to t (so ~1 on average), in [0, cap]."""
    scale = spread.expanding(min_periods=252).mean().clip(lower=0.25)
    return (spread / scale).clip(lower=0.0, upper=cap).fillna(0.0)


def not_backwardated(vix: pd.Series, vix3m: pd.Series) -> pd.Series:
    """1 when the VIX curve slopes up (VIX <= VIX3M) at t, 0 in backwardation, NaN before VIX3M exists."""
    return (vix <= vix3m).astype(float).where(vix3m.notna())


# ----------------------------------------------------------------------------- tradable proxy

def etp_pnl(close: pd.Series, position: pd.Series) -> pd.Series:
    """Daily return of holding `position` (decided at t's close) over t+1. Negative = short."""
    ret = close.pct_change()
    return (position.shift(1) * ret).rename("ret")
