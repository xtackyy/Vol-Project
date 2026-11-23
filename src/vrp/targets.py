"""Implied variance, realized variance and the variance risk premium over h trading days.

Row t uses the VIX close at t and the SPY returns of days t+1 .. t+h, so every quantity here
is a *label* (future), never a feature.

    implied variance  IV_t = (VIX_t / 100)^2 * h / 252
                      VIX is a 30-calendar-day annualised vol in %; 21 trading days ~ 30 days.
    realized variance RV_t = sum of squared daily SPY log returns, days t+1 .. t+h
    VRP_t             = IV_t - RV_t   (positive: the variance seller was paid)

Readable units: vol points = 100 * sqrt(variance * 252 / h); variance points = vol points^2.
The VRP in vol points is defined as implied vol minus realized vol (a difference of vols,
which can be negative), not the square root of the variance VRP.
SPY stands in for SPX, on whose options VIX is computed.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from volcast.config import TRADING_DAYS
from volcast.features import daily_realized_variance


def implied_variance(vix: pd.Series, horizon: int) -> pd.Series:
    return (vix / 100) ** 2 * horizon / TRADING_DAYS


def forward_realized_variance(close: pd.Series, horizon: int) -> pd.Series:
    """Sum of squared close-to-close log returns over t+1 .. t+h (NaN for the last h rows)."""
    r2 = np.log(close / close.shift(1)) ** 2
    return r2.rolling(horizon).sum().shift(-horizon)


def forward_range_variance(ohlc: pd.DataFrame, horizon: int) -> pd.Series:
    """Same window with volcast's range-based daily variance (overnight gap^2 + Garman-Klass)."""
    return daily_realized_variance(ohlc).rolling(horizon).sum().shift(-horizon)


def vol_points(variance: pd.Series, horizon: int) -> pd.Series:
    return 100 * np.sqrt(variance * TRADING_DAYS / horizon)


def build_vrp(data: pd.DataFrame, horizon: int) -> pd.DataFrame:
    iv = implied_variance(data["vix"], horizon)
    rv = forward_realized_variance(data["close"], horizon)
    rv_range = forward_range_variance(data, horizon)
    out = pd.DataFrame({"iv_var": iv, "rv_var": rv, "rv_range_var": rv_range, "vrp_var": iv - rv},
                       index=data.index)
    out["iv_vol"] = vol_points(iv, horizon)       # equals the VIX close
    out["rv_vol"] = vol_points(rv, horizon)
    out["rv_range_vol"] = vol_points(rv_range, horizon)
    out["vrp_vol"] = out["iv_vol"] - out["rv_vol"]
    out["vrp_varpts"] = out["iv_vol"] ** 2 - out["rv_vol"] ** 2   # annualised variance points
    return out


def non_overlapping(frame: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Every h-th complete row: back-to-back h-day windows with no shared days ('months')."""
    done = frame.dropna(subset=["iv_var", "rv_var"])
    return done.iloc[::horizon]
