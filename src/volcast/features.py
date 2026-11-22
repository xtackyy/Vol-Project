"""Feature and target engineering.

Timing convention (used everywhere in the repo):
    Row t holds information available at the *close* of day t.
    * Features at row t use data from days <= t only (trailing windows, no centring).
    * Targets at row t are strictly in the future: days t+1 .. t+h.
A position decided from row t is held over day t+1 (see backtest.py).

`tests/test_no_lookahead.py` enforces this by perturbing future prices and checking
that past features do not move.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import TRADING_DAYS

HAR_FEATURES = ["har_d", "har_w", "har_m"]
_EPS = 1e-10


def daily_realized_variance(df: pd.DataFrame) -> pd.Series:
    """Range-based daily variance proxy: overnight gap^2 + Garman-Klass intraday term.

    With only daily bars this is the most efficient realized-variance proxy available
    (~7x more efficient than squared close-to-close returns), and it captures the
    overnight jump that the pure GK estimator ignores.
    """
    log_hl = np.log(df["high"] / df["low"])
    log_co = np.log(df["close"] / df["open"])
    overnight = np.log(df["open"] / df["close"].shift(1))
    gk = 0.5 * log_hl**2 - (2 * np.log(2) - 1) * log_co**2
    rv = overnight.fillna(0.0) ** 2 + gk.clip(lower=0.0)
    return rv.clip(lower=_EPS).rename("rv")


def _log_ann_vol(daily_var: pd.Series) -> pd.Series:
    return np.log(np.sqrt(TRADING_DAYS * daily_var.clip(lower=_EPS)))


def build_features(df: pd.DataFrame, asset_class: str = "equity") -> pd.DataFrame:
    """Engineer the full feature matrix. Every column is computable at the close of t."""
    close = df["close"]
    ret = np.log(close / close.shift(1))
    rv = daily_realized_variance(df)
    f = pd.DataFrame(index=df.index)

    # --- HAR-RV block (Corsi, 2009): daily / weekly / monthly vol components in logs.
    f["har_d"] = _log_ann_vol(rv)
    f["har_w"] = _log_ann_vol(rv.rolling(5).mean())
    f["har_m"] = _log_ann_vol(rv.rolling(22).mean())
    f["har_q"] = _log_ann_vol(rv.rolling(66).mean())

    # --- Leverage effect: negative returns raise future vol more than positive ones.
    f["neg_ret_d"] = ret.clip(upper=0.0)
    f["neg_ret_w"] = ret.rolling(5).sum().clip(upper=0.0)

    # --- Vol-of-vol and vol term structure (realized).
    f["vol_of_vol"] = f["har_d"].rolling(22).std()
    f["rv_slope"] = f["har_w"] - f["har_m"]


    # --- Return / signal features.
    f["ret_1d"] = ret
    f["ret_5d"] = ret.rolling(5).sum()
    f["ret_21d"] = ret.rolling(21).sum()
    f["mom_12_1"] = ret.shift(21).rolling(231).sum()  # 12m momentum skipping last month
    f["ma200_gap"] = np.log(close / close.rolling(200).mean())
    f["drawdown_252"] = np.log(close / close.rolling(252).max())
    f["ret_5d_z"] = f["ret_5d"] / (np.exp(f["har_m"]) * np.sqrt(5 / TRADING_DAYS))

    # --- Volume: abnormal activity relative to its own trailing quarter.
    log_vol = np.log(df["volume"].replace(0, np.nan))
    f["volume_z"] = (log_vol - log_vol.rolling(63).mean()) / log_vol.rolling(63).std()

    # --- Macro / cross-asset block for this asset class (all inputs lagged one day).
    f = f.join(cross_asset_features(df, asset_class, own_ret=ret, har_m=f["har_m"]))
    return f.replace([np.inf, -np.inf], np.nan)


def _lagged(df: pd.DataFrame, col: str) -> pd.Series | None:
    """Cross-asset input as known *strictly before* the close of t (value at t-1).

    Other markets settle at other times (VIX 16:15 ET, ICE dollar index 17:00 ET, Treasury
    yield indices mid-afternoon), so their same-day close is not reliably known at the
    traded ETF's 16:00 close. Lagging every outside series one day removes that risk.
    """
    if col not in df or df[col].notna().mean() < 0.5:
        return None
    return df[col].shift(1)


def cross_asset_features(df: pd.DataFrame, asset_class: str, own_ret: pd.Series,
                         har_m: pd.Series) -> pd.DataFrame:
    """Asset-class-specific macro features. Columns missing from `df` are skipped."""
    f = pd.DataFrame(index=df.index)

    # Implied equity vol (every asset): level plus an asset-specific transform.
    vix = _lagged(df, "vix")
    if vix is not None:
        lv = np.log(vix / 100)
        f["log_vix"] = lv
        if asset_class == "equity":
            f["vrp"] = lv - har_m            # implied (t-1) minus realised (to t): variance risk premium
        else:
            f["vix_chg_5"] = lv.diff(5)      # equity stress building up
        if asset_class == "gold":
            f["vix_stress"] = (vix > 25).astype(float).where(vix.notna())
            f["vix_z_252"] = (lv - lv.rolling(252).mean()) / lv.rolling(252).std()

    if asset_class == "rates":
        tnx, irx = _lagged(df, "x_tnx"), _lagged(df, "x_irx")
        if tnx is not None:
            f["tnx_chg_5"] = tnx.diff(5)     # 10y yield change, % points
            f["tnx_chg_21"] = tnx.diff(21)
            if irx is not None:
                slope = tnx - irx            # 10y minus 3m: curve slope, % points
                f["curve_slope"] = slope
                f["slope_chg_5"] = slope.diff(5)
                f["slope_chg_21"] = slope.diff(21)
        if "x_spy" in df and df["x_spy"].notna().mean() >= 0.5:
            spy_ret = np.log(df["x_spy"] / df["x_spy"].shift(1))
            # Pairs are matched on the same day, then the whole statistic is lagged.
            f["eq_bond_corr_21"] = spy_ret.rolling(21).corr(own_ret).shift(1)
            f["spy_ret_5"] = spy_ret.rolling(5).sum().shift(1)   # flight-to-quality pressure

    if asset_class == "gold":
        dxy = _lagged(df, "x_dxy")
        if dxy is not None:
            r = np.log(dxy / dxy.shift(1))
            f["dxy_ret_5"] = r.rolling(5).sum()
            f["dxy_ret_21"] = r.rolling(21).sum()
            f["dxy_mom_63"] = r.rolling(63).sum()
        tnx = _lagged(df, "x_tnx")
        if tnx is not None:
            f["tnx_chg_21"] = tnx.diff(21)
        tip, ief = _lagged(df, "x_tip"), _lagged(df, "x_ief")
        if tip is not None:
            tip_r21 = np.log(tip / tip.shift(21))
            f["real_rate_proxy_21"] = -tip_r21                 # TIPS down => real yields up
            if ief is not None:
                # TIPS beating same-duration nominals => breakevens (inflation expectations) up
                f["breakeven_chg_21"] = tip_r21 - np.log(ief / ief.shift(21))

    return f


VOL_FEATURES_EXCLUDE: tuple[str, ...] = ("ret_1d", "ret_21d", "mom_12_1", "ma200_gap", "ret_5d_z")


def vol_feature_columns(features: pd.DataFrame) -> list[str]:
    """Columns used by the volatility model: HAR block + leverage + vol-state features."""
    return [c for c in features.columns if c not in VOL_FEATURES_EXCLUDE]


def proxy_calibration(df: pd.DataFrame, window: int = 756) -> pd.Series:
    """Point-in-time ratio sqrt(sum r_cc^2 / sum rv_proxy) over a trailing window.

    The model forecasts the range-based proxy, but the portfolio's P&L variance is driven
    by close-to-close returns. Multiplying the vol forecast by this factor (estimated only
    from data up to t) converts proxy units to close-to-close units. Without it a 12% target
    typically realises ~14%. It does not correct the separate Jensen gap of exp(log forecast);
    see strategy.forecast_bias_correction.
    """
    r2 = np.log(df["close"] / df["close"].shift(1)) ** 2
    rv = daily_realized_variance(df)
    ratio = r2.rolling(window, min_periods=252).sum() / rv.rolling(window, min_periods=252).sum()
    return np.sqrt(ratio).rename("vol_calibration")


def build_targets(df: pd.DataFrame, horizon: int, ret_horizon: int = 1) -> pd.DataFrame:
    """Forward-looking targets. NaN in the last rows where the future is unknown.

    y_vol : log annualised realized vol over days t+1..t+horizon
    y_ret : summed simple excess return over days t+1..t+ret_horizon, in decimal
            (ret_horizon=1 is the next-day return). Overlapping for ret_horizon > 1,
            so the walk-forward purge and the inner-CV gap must equal ret_horizon.
    """
    rv = daily_realized_variance(df)
    fwd_var = rv.rolling(horizon).mean().shift(-horizon)  # mean of rv[t+1 .. t+h]
    excess = df["close"].pct_change() - df["rf"]
    fwd_ret = excess.rolling(ret_horizon).sum().shift(-ret_horizon)  # sum of excess[t+1 .. t+h]
    return pd.DataFrame(
        {"y_vol": _log_ann_vol(fwd_var).where(fwd_var.notna()), "y_ret": fwd_ret},
        index=df.index,
    )


def make_dataset(df: pd.DataFrame, horizon: int, ret_horizon: int = 1,
                 asset_class: str = "equity") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Features and targets aligned on rows where every feature is defined.

    Targets may be NaN at the tail (unknown future); the walk-forward engine never
    trains on those rows but still produces forecasts for them.
    """
    feats = build_features(df, asset_class).dropna()
    targets = build_targets(df, horizon, ret_horizon).reindex(feats.index)
    return feats, targets
