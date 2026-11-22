"""Turn the two forecasts into target portfolio weights.

    vol_scale_t = min(target_vol / sigma_hat_t, max_leverage)
    mu_t        = smoothed expected daily excess return (see below)
    long-only   : w_t = vol_scale_t * 1{mu_t > threshold}            in [0, max_leverage]
    long-short  : w_t = vol_scale_t * sign(mu_t - threshold)          in [-max_leverage, max_leverage]
                  (flat when mu_t == threshold exactly, i.e. the model has no view)

Weights are decided at close t and held over t+1 (see backtest.py). Two ablations are
produced alongside so each model's contribution is visible: vol-targeting only (always
long) and the return signal only (unit exposure when long).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import TRADING_DAYS, StrategyConfig


def expected_excess_return(pred_ret: pd.Series, prevailing_mean: pd.Series,
                           prior_premium: float | None, horizon: int = 1) -> pd.Series:
    """Expected *daily* excess return used for the position decision.

    `pred_ret` forecasts the excess return summed over the next `horizon` days, so it is
    divided by `horizon` to get a per-day rate. A penalised model's forecast is
    intercept (training-window mean, very noisy: after 2008 the expanding mean of SPY
    excess returns was negative for years) + feature tilt. With `prior_premium` set the
    noisy intercept is replaced by a fixed equity-premium prior, so the strategy goes
    flat only when the *features* forecast a shortfall larger than the premium.
    `None` uses the raw model forecast.
    """
    if prior_premium is None:
        return pred_ret / horizon
    tilt = (pred_ret - prevailing_mean.reindex(pred_ret.index)) / horizon
    return prior_premium / TRADING_DAYS + tilt


def forecast_bias_correction(y_log_vol: pd.Series, pred_log_vol: pd.Series, horizon: int,
                             min_obs: int = 252) -> pd.Series:
    """Point-in-time multiplier for exp(log-vol forecast): sqrt(mean of exp(2 e)), e = y - pred.

    exp(forecast of log vol) estimates the median, not the mean (Jensen's inequality), so it
    under-sizes risk. This smearing estimator (Duan, 1983) measures the gap on the model's own
    past out-of-sample errors, in variance terms because a vol target controls variance.
    The error of the forecast made at s is only known at the close of s + horizon (when its
    label window ends), so errors are shifted by `horizon` rows before use. Returns NaN until
    `min_obs` errors have matured; callers treat that as no correction.
    """
    err = y_log_vol.reindex(pred_log_vol.index) - pred_log_vol
    known = err.shift(horizon)
    second_moment = np.exp(2 * known).expanding(min_periods=min_obs).mean()
    return np.sqrt(second_moment).rename("vol_bias_correction")


def smooth_signal(mu: pd.Series, ema_span: int | None = None, hold: int = 1) -> pd.Series:
    """Causal smoothing of the expected-return signal.

    * ema_span: exponential moving average (adjust=False -> recursive, uses only <= t).
    * hold: refresh the signal only every `hold` days and carry it forward in between
      (hold=5 approximates a weekly rebalance of the signal leg).
    Both only ever look backwards, so smoothing cannot leak future information.
    """
    out = mu.astype(float)
    if ema_span and ema_span > 1:
        out = out.ewm(span=ema_span, adjust=False).mean()
    if hold > 1:
        out = out.iloc[::hold].reindex(out.index).ffill()
    return out


def target_weights(
    pred_log_vol: pd.Series,
    mu: pd.Series,
    cfg: StrategyConfig,
    vol_calibration: pd.Series | None = None,
) -> pd.DataFrame:
    """Target weights per strategy variant. `vol_calibration` must be point-in-time.

    `mu` is the expected daily excess return *before* smoothing; smoothing per `cfg`
    is applied here so every variant sees the same signal.
    """
    idx = pred_log_vol.index.intersection(mu.index)
    sigma_hat = np.exp(pred_log_vol.loc[idx])  # annualised vol forecast (proxy units)
    if vol_calibration is not None:
        sigma_hat = sigma_hat * vol_calibration.reindex(idx).ffill().fillna(1.0)
    vol_scale = (cfg.target_vol / sigma_hat).clip(upper=cfg.max_leverage)
    sig = smooth_signal(mu.loc[idx], cfg.signal_ema_span, cfg.signal_hold)
    long_flat = (sig > cfg.signal_threshold).astype(float)
    # sign(0) = 0: a forecast exactly at the threshold (e.g. Lasso with every coefficient
    # shrunk to zero and no prior) is "no view", which means flat rather than short.
    long_short = np.sign(sig - cfg.signal_threshold)
    return pd.DataFrame(
        {
            "vol_target_signal": vol_scale * long_flat,
            "vol_target_signal_ls": vol_scale * long_short,
            "vol_target_only": vol_scale,
            "signal_only": long_flat,
        },
        index=idx,
    )
