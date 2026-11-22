"""Leakage tests: the core guarantee of the project.

Strategy: change the *future* and assert the *past* does not move. If any feature,
scaler, alpha choice or model fit touched data after date T, outputs at or before T
would change when we scramble prices after T.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from volcast.data import simulate_market
from volcast.features import build_features, build_targets, proxy_calibration
from volcast.models import HAROLS, penalised_regression, walk_forward
from volcast.validation import walk_forward_splits

HORIZON = 5


@pytest.fixture(scope="module")
def market() -> pd.DataFrame:
    return simulate_market(1100, seed=1)


def scramble_after(df: pd.DataFrame, cut: int, seed: int = 99) -> pd.DataFrame:
    """Replace every row after position `cut` with very different, still-valid prices."""
    rng = np.random.default_rng(seed)
    out = df.copy()
    k = len(df) - cut - 1
    shock = np.exp(rng.normal(0, 0.05, k)).cumprod()
    for col in ["open", "high", "low", "close"]:
        out.iloc[cut + 1:, out.columns.get_loc(col)] = df[col].iloc[cut + 1:].to_numpy() * shock * 3
    out.iloc[cut + 1:, out.columns.get_loc("volume")] *= 10
    out.iloc[cut + 1:, out.columns.get_loc("vix")] *= 2
    return out


def test_features_ignore_the_future(market):
    cut = 700
    a = build_features(market).iloc[: cut + 1]
    b = build_features(scramble_after(market, cut)).iloc[: cut + 1]
    pd.testing.assert_frame_equal(a, b)


def test_calibration_is_point_in_time(market):
    cut = 700
    a = proxy_calibration(market).iloc[: cut + 1]
    b = proxy_calibration(scramble_after(market, cut)).iloc[: cut + 1]
    pd.testing.assert_series_equal(a, b)


def test_targets_are_strictly_future(market):
    """Changing day t+1.. must change the target at t, and nothing at t-h or earlier."""
    cut = 700
    a = build_targets(market, HORIZON)
    b = build_targets(scramble_after(market, cut), HORIZON)
    # Labels whose window ends at or before `cut` are unaffected...
    pd.testing.assert_series_equal(a["y_vol"].iloc[: cut - HORIZON + 1], b["y_vol"].iloc[: cut - HORIZON + 1])
    # ...and the label at `cut` depends only on what comes after it.
    assert not np.isclose(a["y_vol"].iloc[cut], b["y_vol"].iloc[cut])
    assert not np.isclose(a["y_ret"].iloc[cut], b["y_ret"].iloc[cut])
    assert a["y_vol"].iloc[-HORIZON:].isna().all() and np.isnan(a["y_ret"].iloc[-1])


@pytest.mark.parametrize("window", [None, 250])
def test_walk_forward_splits_are_purged(window):
    for fold in walk_forward_splits(2000, 500, 21, HORIZON, window):
        assert fold.train_idx.max() + HORIZON < fold.test_idx.min()
        if window is not None:
            assert len(fold.train_idx) <= window


def test_walk_forward_predictions_ignore_the_future(market):
    """End-to-end: scaler + GridSearchCV alpha + Ridge + forecasts are all point-in-time."""
    cut_date_pos = 850

    def predict(df: pd.DataFrame) -> pd.Series:
        f = build_features(df).dropna()
        t = build_targets(df, HORIZON).reindex(f.index)
        ridge = walk_forward(f, t["y_vol"], penalised_regression("ridge", np.logspace(-2, 3, 6), 3, HORIZON),
                             min_train=300, refit_every=21, horizon=HORIZON)
        return ridge.predictions

    base = predict(market)
    cut_date = market.index[cut_date_pos]
    moved = predict(scramble_after(market, cut_date_pos))
    past = base.index[base.index <= cut_date]
    assert len(past) > 200
    pd.testing.assert_series_equal(base.loc[past], moved.loc[past])
    # Sanity: the scramble really did change later forecasts.
    assert not np.allclose(base.loc[base.index > cut_date], moved.loc[moved.index > cut_date])


def test_har_ols_matches_closed_form():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(500, 3))
    y = 0.5 + X @ np.array([0.3, 0.4, 0.2]) + rng.normal(0, 0.01, 500)
    pred = HAROLS().fit(X, y).predict(X)
    beta = np.linalg.lstsq(np.c_[np.ones(500), X], y, rcond=None)[0]
    np.testing.assert_allclose(pred, np.c_[np.ones(500), X] @ beta, rtol=1e-8)
