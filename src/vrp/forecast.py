"""21-day HAR-RV forecasts of SPY realized vol, walk-forward, built only from SPY's own history.

Everything is volcast's code with the horizon set to 21:
  * features  volcast.features.build_features (HAR d/w/m/q on range-based RV, leverage, vol-of-vol, ...)
  * models    Ridge with alpha tuned by GridSearchCV over TimeSeriesSplit(gap=21), scaler inside the
              Pipeline (volcast.models.penalised_regression); classic HAR-OLS as a benchmark
  * engine    volcast.models.walk_forward: expanding window, monthly refits, purged so a training
              label never overlaps the test period
  * Jensen    exp(forecast of log vol) is a median; volcast.strategy.forecast_bias_correction scales
              it by sqrt(mean exp(2 e)) over matured past errors, so its square forecasts the mean variance

Two choices specific to the VRP study:
  * Target = log annualised *close-to-close* realized vol over t+1..t+21, the quantity VIX is
    judged against, so no proxy-to-close conversion is needed afterwards.
  * VIX-based features (log_vix, vrp) are dropped. "Does HAR add information beyond VIX?" is only
    a fair question if the HAR forecast contains no VIX.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from volcast.config import ModelConfig
from volcast.features import HAR_FEATURES, build_features, vol_feature_columns
from volcast.models import HAROLS, penalised_regression, walk_forward
from volcast.strategy import forecast_bias_correction

from .targets import forward_realized_variance, vol_points

log = logging.getLogger(__name__)

VIX_FEATURES = ("log_vix", "vrp")


def har_features(data: pd.DataFrame) -> pd.DataFrame:
    """HAR feature matrix without any VIX input; every column known at the SPY close of t."""
    feats = build_features(data, asset_class="equity")
    cols = [c for c in vol_feature_columns(feats) if c not in VIX_FEATURES]
    return feats[cols].dropna()


def log_vol_target(data: pd.DataFrame, horizon: int) -> pd.Series:
    """log(annualised close-to-close realized vol over t+1..t+h), as a decimal (0.15 -> log 0.15)."""
    return np.log(vol_points(forward_realized_variance(data["close"], horizon), horizon) / 100)


def har_forecasts(data: pd.DataFrame, horizon: int, model: ModelConfig | None = None) -> pd.DataFrame:
    """Out-of-sample 21-day vol forecasts in vol points: 'har_ridge' and 'har_ols'.

    Rows start once the walk-forward burn-in and the Jensen correction's 252 matured errors exist.
    """
    m = model or ModelConfig()
    X = har_features(data)
    y = log_vol_target(data, horizon).reindex(X.index)
    wf = dict(min_train=m.min_train_days, refit_every=m.refit_every, horizon=horizon)
    fits = {
        "har_ridge": walk_forward(X, y, penalised_regression("ridge", m.vol_alphas, m.cv_splits, gap=horizon), **wf),
        "har_ols": walk_forward(X[HAR_FEATURES], y, HAROLS, **wf),
    }
    out = {}
    for name, res in fits.items():
        bias = forecast_bias_correction(y, res.predictions, horizon)
        out[name] = 100 * np.exp(res.predictions) * bias
        out[f"{name}_median"] = 100 * np.exp(res.predictions)   # before the Jensen correction
        log.info("%s: %d forecasts, %d refits", name, res.predictions.notna().sum(), len(res.alphas))
    return pd.DataFrame(out).dropna()
