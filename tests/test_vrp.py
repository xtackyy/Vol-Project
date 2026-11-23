"""VRP extension: variance scaling, label timing (strictly t+1..t+h) and signs."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from volcast.config import ModelConfig
from volcast.data import simulate_market
from vrp.backtest import (
    SwapConfig,
    conditional,
    short_variance_pnl,
    sized,
    staggered,
    vol_target_size,
)
from vrp.forecast import VIX_FEATURES, har_features, har_forecasts
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


FAST = ModelConfig(min_train_days=300, refit_every=21, cv_splits=3, vol_alphas=tuple(np.logspace(-2, 3, 6)))


@pytest.fixture(scope="module")
def long_market() -> pd.DataFrame:
    df = simulate_market(1300, seed=5)
    df["vix"] = 20.0 + 5 * np.sin(np.arange(len(df)) / 40)
    return df


def test_har_forecast_ignores_the_future(long_market):
    """Scrambling every price after `cut` must leave every forecast made at or before `cut` unchanged
    (features, scaler, CV, Ridge, refits and the Jensen correction together)."""
    cut = 1050
    base = har_forecasts(long_market, H, FAST)
    moved_mkt = long_market.copy()
    shock = np.exp(np.random.default_rng(1).normal(0, 0.05, len(moved_mkt) - cut - 1)).cumprod()
    for c in ["open", "high", "low", "close"]:
        moved_mkt.iloc[cut + 1:, moved_mkt.columns.get_loc(c)] *= shock * 2
    moved = har_forecasts(moved_mkt, H, FAST)
    past = base.index[base.index <= long_market.index[cut]]
    assert len(past) > 50
    pd.testing.assert_frame_equal(base.loc[past], moved.loc[past])
    later = base.index[base.index > long_market.index[cut + H]]
    assert not np.allclose(base.loc[later], moved.loc[later])


def test_har_forecast_contains_no_vix(long_market):
    assert not set(VIX_FEATURES) & set(har_features(long_market).columns)
    other = long_market.assign(vix=long_market["vix"] * 3)
    pd.testing.assert_frame_equal(har_forecasts(long_market, H, FAST), har_forecasts(other, H, FAST))


def _one_swap(market, entry: int, cost: float = 1.0, lag: int = 0):
    size = pd.Series(0.0, index=market.index)
    size.iloc[entry] = 1.0
    cfg = SwapConfig(horizon=H, cost_vol_pts=cost)
    return short_variance_pnl(market["vix"], market["close"], size, cfg, entry_lag=lag), cfg


def test_swap_held_to_maturity_pays_strike_minus_realized(market):
    e = 300
    bt, cfg = _one_swap(market, e)
    K = market["vix"].iloc[e] - cfg.cost_vol_pts
    N = cfg.vega_notional / (2 * K)
    rv_pts = vol_points(forward_realized_variance(market["close"], H), H).iloc[e] ** 2   # independent code path
    assert bt["pnl"].sum() == pytest.approx(N * (K**2 - rv_pts))
    assert bt["pnl"].iloc[e] == pytest.approx(N * (K**2 - market["vix"].iloc[e] ** 2))  # cost booked on entry
    assert bt["pnl"].iloc[e] < 0
    assert (bt["pnl"].iloc[:e] == 0).all() and (bt["pnl"].iloc[e + H + 1:] == 0).all()
    assert (bt["vega"].iloc[e + 1: e + H + 1] == cfg.vega_notional).all() and bt["vega"].iloc[e] == 0


def test_swap_ignores_the_entry_days_own_return(market):
    """The realized leg starts the day after entry: a shock to the entry day's return is irrelevant."""
    e = 300
    shocked = market.copy()
    shocked.iloc[e:, shocked.columns.get_loc("close")] *= 1.2      # jump on day e only
    base, _ = _one_swap(market, e)
    moved, _ = _one_swap(shocked, e)
    assert moved["pnl"].sum() == pytest.approx(base["pnl"].sum())
    # Entering a day later (strike VIX at e+1) makes day e+1's return the first one that counts.
    lagged, _ = _one_swap(market, e, lag=1)
    assert lagged["pnl"].iloc[e] == 0 and lagged["pnl"].iloc[e + 1] != 0


def test_vix_scaled_cost_widens_only_above_the_reference_level():
    idx = pd.bdate_range("2020-01-01", periods=60)
    for vix, expected_cost in ((15.0, 1.0), (20.0, 1.0), (60.0, 3.0)):
        flat = pd.DataFrame({"close": 100.0, "vix": vix}, index=idx)
        size = pd.Series(0.0, index=idx)
        size.iloc[5] = 1.0
        cfg = SwapConfig(horizon=H, cost_vol_pts=1.0, cost_ref_vix=20.0)
        bt = short_variance_pnl(flat["vix"], flat["close"], size, cfg)
        K = vix - expected_cost
        assert bt["pnl"].iloc[5] == pytest.approx(cfg.vega_notional / (2 * K) * (K**2 - vix**2))


def test_short_variance_earns_when_nothing_moves():
    idx = pd.bdate_range("2020-01-01", periods=60)
    flat = pd.DataFrame({"close": 100.0, "vix": 20.0}, index=idx)
    bt, cfg = _one_swap(flat, 5, cost=0.0)
    N = cfg.vega_notional / (2 * 20.0)
    assert bt["pnl"].sum() == pytest.approx(N * 20.0**2)   # realized variance 0: keeps the whole strike
    assert (bt["pnl"].iloc[6:5 + H + 1] > 0).all()          # and accrues it day by day


def test_sizes_at_t_ignore_later_spreads():
    rng = np.random.default_rng(2)
    idx = pd.bdate_range("2000-01-01", periods=800)
    spread = pd.Series(rng.normal(2, 3, len(idx)), index=idx)
    later = spread.copy()
    later.iloc[600:] += 50
    for rule in (lambda s: conditional(s, 0.0), sized):
        pd.testing.assert_series_equal(rule(spread).iloc[:600], rule(later).iloc[:600])


def test_vol_target_size_uses_only_past_pnl():
    rng = np.random.default_rng(4)
    idx = pd.bdate_range("2000-01-01", periods=400)
    pnl = pd.Series(rng.normal(0, 2_000, len(idx)), index=idx)
    later = pnl.copy()
    later.iloc[300:] *= 20                                  # a crash after day 299
    a = vol_target_size(pnl, 1e6, 0.10, 63, 2.0)
    b = vol_target_size(later, 1e6, 0.10, 63, 2.0)
    pd.testing.assert_series_equal(a.iloc[:300], b.iloc[:300])
    assert b.iloc[300] < a.iloc[300]                        # the day-300 loss itself is known at t=300
    assert (a.iloc[:62] == 0).all() and (a <= 2.0).all()    # no size before 63 days of history; capped
    # Scale: daily std 2,000 -> annual ~31.7k = 3.2% of 1m, so a 10% target wants ~3.2x, capped at 2.
    assert a.iloc[100] == 2.0
    assert vol_target_size(pnl * 10, 1e6, 0.10, 63, 2.0).iloc[100] == pytest.approx(
        0.10 * 1e6 / (pnl.iloc[38:101].std() * 10 * np.sqrt(252)))


def test_staggered_tranches_build_to_constant_exposure(market):
    cfg = SwapConfig(horizon=H)
    bt = short_variance_pnl(market["vix"], market["close"], staggered(market.index, H), cfg)
    first = market["vix"].first_valid_index()          # tranches start once VIX exists
    full = bt["vega"].loc[first:].iloc[H + 1: -1]
    np.testing.assert_allclose(full, cfg.vega_notional)


def test_blocks_do_not_overlap(market):
    v = build_vrp(market, H)
    b = non_overlapping(v, H)
    pos = v.index.get_indexer(b.index)
    assert (np.diff(pos) == H).all()        # each block starts where the previous window ended
    assert b[["iv_var", "rv_var"]].notna().all().all()
