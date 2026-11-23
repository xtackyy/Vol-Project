"""Market data: yfinance download with local caching, plus an offline simulator.

Output schema (DatetimeIndex, one row per trading day):
    open, high, low, close   dividend/split-adjusted OHLC
    volume                   shares traded
    rf                       daily risk-free return earned over day t (known at t-1)
    vix                      implied vol index close at t (optional, NaN if absent)
    x_<key>                  cross-asset closes (e.g. x_tnx, x_dxy), aligned to the traded
                             asset's calendar. Raw, *un-lagged*: features.py applies shift(1).

Holiday alignment: other markets keep other calendars (bond market shut on Columbus and
Veterans Day while equities trade; the ICE dollar index trades on US holidays). Each series
is aligned with `align_to`, which takes the latest value observed *on or before* each
trading day of the traded asset (as-of join), never a later one.
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from .config import TRADING_DAYS, DataConfig

log = logging.getLogger(__name__)

OHLCV = ["open", "high", "low", "close", "volume"]


def _download(ticker: str, start: str, end: str | None) -> pd.DataFrame:
    import yfinance as yf  # imported lazily so tests run without network

    hist = yf.Ticker(ticker).history(start=start, end=end, auto_adjust=True, actions=False)
    if hist.empty:
        raise RuntimeError(f"yfinance returned no data for {ticker!r}")
    hist.index = pd.DatetimeIndex(hist.index).tz_localize(None).normalize()
    hist.columns = [c.lower() for c in hist.columns]
    return hist


def cached_history(ticker: str, start: str, end: str | None, cache_dir: Path) -> pd.DataFrame:
    cache_dir.mkdir(parents=True, exist_ok=True)
    safe = ticker.replace("^", "IDX_")
    path = cache_dir / f"{safe}_{start}_{end or 'latest'}.csv"
    if path.exists():
        return pd.read_csv(path, index_col=0, parse_dates=True)
    df = _download(ticker, start, end)
    df.to_csv(path)
    return df


def align_to(series: pd.Series, index: pd.DatetimeIndex, max_stale_days: int = 5) -> pd.Series:
    """As-of alignment of `series` onto `index`: last observation on or before each date.

    Values from dates the target calendar skips are carried into the next target date, and a
    gap is filled for at most `max_stale_days` rows so a dead feed shows up as NaN.
    """
    series = series[~series.index.duplicated(keep="last")].sort_index()
    union = series.index.union(index)
    return series.reindex(union).ffill(limit=max_stale_days).reindex(index)


def _load_close(tickers: tuple[str, ...] | str, cfg: DataConfig) -> tuple[pd.Series, str]:
    """Close series of the first ticker in `tickers` that downloads; raises if none do."""
    if isinstance(tickers, str):
        tickers = (tickers,)
    errors = []
    for t in tickers:
        try:
            return cached_history(t, cfg.start, cfg.end, cfg.cache_dir)["close"], t
        except Exception as exc:  # pragma: no cover - network dependent
            errors.append(f"{t}: {exc}")
    raise RuntimeError("; ".join(errors))


def load_market_data(cfg: DataConfig) -> pd.DataFrame:
    """Load the traded asset plus risk-free, VIX and cross-asset series, aligned on asset dates."""
    if cfg.synthetic:
        mkt = simulate_market(cfg.synthetic_days, seed=cfg.seed)
        return add_synthetic_aux(mkt, tuple(cfg.aux_tickers), seed=cfg.seed)

    px = cached_history(cfg.ticker, cfg.start, cfg.end, cfg.cache_dir)[OHLCV].copy()
    px = px[(px[["open", "high", "low", "close"]] > 0).all(axis=1)]

    # Risk-free: ^IRX is an annualised % yield observed at the close of t.
    # Holding cash from close t-1 to close t earns the yield known at t-1 -> shift(1).
    if cfg.rf_ticker:
        try:
            irx, _ = _load_close(cfg.rf_ticker, cfg)
            px["rf"] = (align_to(irx, px.index) / 100 / TRADING_DAYS).shift(1)
        except Exception as exc:  # pragma: no cover - network dependent
            log.warning("risk-free download failed (%s); using rf = 0", exc)
            px["rf"] = 0.0
    else:
        px["rf"] = 0.0
    px["rf"] = px["rf"].fillna(0.0)

    if cfg.vix_ticker:
        try:
            vix, _ = _load_close(cfg.vix_ticker, cfg)
            px["vix"] = align_to(vix, px.index)
        except Exception as exc:  # pragma: no cover
            log.warning("VIX download failed (%s); dropping VIX features", exc)
            px["vix"] = np.nan
    else:
        px["vix"] = np.nan

    for key, tickers in cfg.aux_tickers.items():
        try:
            s, used = _load_close(tuple(tickers), cfg)
            px[f"x_{key}"] = align_to(s, px.index)
            log.info("cross-asset %s <- %s", key, used)
        except Exception as exc:  # pragma: no cover
            log.warning("cross-asset %s unavailable (%s); its features are skipped", key, exc)
    return px


def add_synthetic_aux(df: pd.DataFrame, keys: tuple[str, ...], seed: int = 7) -> pd.DataFrame:
    """Offline stand-ins for cross-asset series: yields as bounded random walks (in %),
    prices as geometric random walks. They carry no information about the asset, so any
    'skill' a model finds from them in a test is a red flag for leakage."""
    rng = np.random.default_rng(seed + 1000)
    out = df.copy()
    n = len(df)
    for key in keys:
        if key in ("tnx", "irx"):
            level = 3.0 if key == "tnx" else 1.5
            out[f"x_{key}"] = np.clip(level + np.cumsum(rng.normal(0, 0.05, n)), 0.05, 12.0)
        else:
            out[f"x_{key}"] = 100 * np.exp(np.cumsum(rng.normal(0, 0.008, n)))
    return out


def simulate_market(n_days: int = 5000, seed: int = 7, intraday_steps: int = 39) -> pd.DataFrame:
    """Simulate an equity index with realistic volatility dynamics, for offline runs and tests.

    Daily variance follows a GJR-GARCH(1,1) (persistent, mean-reverting, leverage effect),
    so a HAR model has real structure to find. Intraday paths are simulated so that
    high/low/open are internally consistent with close. Expected returns are a small
    constant: by construction there is *no* return predictability, which makes this a
    useful null for the return model (Lasso should shrink to the mean).
    """
    rng = np.random.default_rng(seed)
    omega, alpha, gamma, beta = 1.5e-6, 0.03, 0.12, 0.89
    mu_daily = 0.07 / TRADING_DAYS
    var = np.empty(n_days)
    var[0] = omega / (1 - alpha - gamma / 2 - beta)
    z = rng.standard_t(df=6, size=n_days) / np.sqrt(6 / 4)
    rets = np.empty(n_days)
    for t in range(n_days):
        if t > 0:
            shock = rets[t - 1] - mu_daily
            var[t] = omega + (alpha + gamma * (shock < 0)) * shock**2 + beta * var[t - 1]
        rets[t] = mu_daily + np.sqrt(var[t]) * z[t]

    close = 100 * np.exp(np.cumsum(rets))
    prev_close = np.r_[100.0, close[:-1]]
    # ~15% of daily variance arrives overnight, the rest intraday as a Brownian path.
    gap = rets * 0.15 + rng.normal(0, 1e-4, n_days)
    open_ = prev_close * np.exp(gap)
    incr = rng.normal(size=(n_days, intraday_steps))
    paths = np.cumsum(incr, axis=1)
    paths = paths - np.linspace(0, 1, intraday_steps) * paths[:, [-1]]  # Brownian bridge
    scale = np.sqrt(var * 0.85 / intraday_steps)[:, None]
    drift = np.linspace(0, 1, intraday_steps)[None, :] * np.log(close / open_)[:, None]
    log_path = np.log(open_)[:, None] + drift + paths * scale
    high = np.maximum(np.exp(log_path.max(axis=1)), np.maximum(open_, close))
    low = np.minimum(np.exp(log_path.min(axis=1)), np.minimum(open_, close))
    volume = 8e7 * np.exp(0.5 * np.log(var / var.mean()) + rng.normal(0, 0.25, n_days))
    vix = 100 * np.sqrt(TRADING_DAYS * var) * 1.15 * np.exp(rng.normal(0, 0.06, n_days))

    idx = pd.bdate_range("2005-01-03", periods=n_days, name="date")
    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume,
         "rf": 0.02 / TRADING_DAYS, "vix": vix},
        index=idx,
    )
