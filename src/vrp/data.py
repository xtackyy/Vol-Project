"""SPY plus the VIX family and vol ETPs, cached as CSV in data/raw/.

Downloads and caching go through volcast.data.cached_history (CSV, like the rest of the repo;
parquet would need pyarrow, a new dependency) and calendars are joined with volcast.data.align_to
(last value on or before each SPY date, never a later one), so nothing here is new logic.

Columns on the SPY trading calendar:
    open, high, low, close, volume   SPY, dividend/split adjusted
    vix, vix9d, vix3m                CBOE indices, % annualised (vix9d from 2011, vix3m from 2006)
    svxy, vxx                        ETP closes (svxy from 2011; the current vxx only from 2018)

Timing: VIX closes at 16:15 ET, 15 minutes after SPY. A VIX close at t is used as the strike of
a position opened at t, whose realized leg starts with the SPY return of t+1.
"""
from __future__ import annotations

import logging

import pandas as pd

from volcast.data import align_to, cached_history

from .config import VRPConfig

log = logging.getLogger(__name__)

SPY = "SPY"
SERIES = {"vix": "^VIX", "vix9d": "^VIX9D", "vix3m": "^VIX3M", "svxy": "SVXY", "vxx": "VXX"}
REQUIRED = ("vix",)


def load_raw(ticker: str, cfg: VRPConfig) -> pd.DataFrame:
    """Daily OHLCV for one ticker: downloaded once, then read from data/raw/."""
    return cached_history(ticker, cfg.start, cfg.end, cfg.raw_dir)


def load_vrp_data(cfg: VRPConfig) -> pd.DataFrame:
    """Underlying OHLCV (SPY by default) plus the implied-vol index as `vix` and the VIX family."""
    px = load_raw(cfg.underlying, cfg)[["open", "high", "low", "close", "volume"]]
    out = px[(px[["open", "high", "low", "close"]] > 0).all(axis=1)].copy()
    for col, ticker in (SERIES | {"vix": cfg.vol_index}).items():
        try:
            out[col] = align_to(load_raw(ticker, cfg)["close"], out.index)
        except Exception as exc:  # pragma: no cover - network dependent
            if col in REQUIRED:
                raise
            log.warning("%s (%s) unavailable: %s", col, ticker, exc)
            out[col] = float("nan")
    return out
