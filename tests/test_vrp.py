"""VRP extension: variance scaling, label timing (strictly t+1..t+h) and signs."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from volcast.data import simulate_market
from vrp.targets import (
    build_vrp,
    forward_realized_variance,
    implied_variance,
    non_overlapping,
    vol_points,
)

H = 21


@pytest.fixture(scope="module")
def market() -> pd.DataFrame:
    df = simulate_market(800, seed=3)
    df["vix"] = 100 * np.sqrt(252 * df["close"].pct_change().rolling(21).var()) + 3  # any positive series
    return df


def test_vix_20_scales_to_a_21_day_variance_and_back():
    iv = implied_variance(pd.Series([20.0]), H)
    assert iv.iloc[0] == pytest.approx(0.04 * 21 / 252)
    assert vol_points(iv, H).iloc[0] == pytest.approx(20.0)


def test_constant_returns_give_the_matching_vol():
    """Daily log returns of +-1% realize sqrt(252) * 1% = 15.87 vol points."""
    r = np.tile([0.01, -0.01], 50)
    close = pd.Series(100 * np.exp(np.cumsum(np.r_[0.0, r])))
    rv = forward_realized_variance(close, H)
    assert rv.iloc[0] == pytest.approx(21 * 0.01**2)
    assert vol_points(rv, H).iloc[0] == pytest.approx(100 * 0.01 * np.sqrt(252))


def test_realized_variance_uses_only_days_t_plus_1_to_t_plus_h(market):
    t = 400
    base = forward_realized_variance(market["close"], H)
    # A shock to the return of day t (close t-1 -> close t) is the past for row t ...
    past = market["close"].copy()
    past.iloc[t:] *= 1.10
    moved = forward_realized_variance(past, H)
    assert moved.iloc[t] == pytest.approx(base.iloc[t])
    assert not np.isclose(moved.iloc[t - 1], base.iloc[t - 1])
    # ... the return of day t+h is the last one row t sees, t+h+1 is outside its window.
    fut = market["close"].copy()
    fut.iloc[t + H + 1:] *= 1.10
    moved = forward_realized_variance(fut, H)
    assert moved.iloc[t] == pytest.approx(base.iloc[t])
    assert not np.isclose(moved.iloc[t + 1], base.iloc[t + 1])
    assert base.iloc[-H:].isna().all() and base.iloc[: -H].notna().iloc[1:].all()


def test_vrp_sign_and_units(market):
    v = build_vrp(market, H).dropna()
    np.testing.assert_allclose(v["vrp_var"], v["iv_var"] - v["rv_var"])
    np.testing.assert_allclose(v["iv_vol"], market["vix"].reindex(v.index))
    assert ((v["vrp_var"] > 0) == (v["vrp_vol"] > 0)).all()          # same sign in any units
    np.testing.assert_allclose(v["vrp_varpts"], v["iv_vol"] ** 2 - v["rv_vol"] ** 2)


def test_blocks_do_not_overlap(market):
    v = build_vrp(market, H)
    b = non_overlapping(v, H)
    pos = v.index.get_indexer(b.index)
    assert (np.diff(pos) == H).all()        # each block starts where the previous window ended
    assert b[["iv_var", "rv_var"]].notna().all().all()
