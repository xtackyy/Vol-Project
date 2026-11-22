"""Cross-asset features: strict one-day lag, holiday-safe alignment, profiles and IC."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from volcast.assets import PROFILES, build_config, get_profile
from volcast.data import add_synthetic_aux, align_to, simulate_market
from volcast.features import build_features
from volcast.metrics import information_coefficient

CLASSES = {"SPY": "equity", "TLT": "rates", "GLD": "gold"}


def market_for(ticker: str, n: int = 900) -> pd.DataFrame:
    return add_synthetic_aux(simulate_market(n, seed=3), tuple(PROFILES[ticker].aux))


def macro_cols(df: pd.DataFrame, asset_class: str) -> list[str]:
    base = build_features(df.drop(columns=[c for c in df if c.startswith("x_") or c == "vix"]), "equity")
    return [c for c in build_features(df, asset_class).columns if c not in base.columns]


@pytest.mark.parametrize("ticker", ["SPY", "TLT", "GLD"])
def test_same_day_cross_asset_close_is_not_used(ticker):
    """Shocking every outside series *on day t only* must not move features at t (lag = 1)
    but must move them at t+1 (the input is actually used)."""
    df = market_for(ticker)
    cls = CLASSES[ticker]
    cut = 600
    moved = df.copy()
    for c in [c for c in df if c.startswith("x_") or c == "vix"]:
        moved.iloc[cut, moved.columns.get_loc(c)] *= 1.5
    a, b = build_features(df, cls), build_features(moved, cls)
    cols = macro_cols(df, cls)
    assert cols, "expected a cross-asset block"
    pd.testing.assert_frame_equal(a.iloc[: cut + 1], b.iloc[: cut + 1])
    assert not np.allclose(a[cols].iloc[cut + 1].fillna(0), b[cols].iloc[cut + 1].fillna(0))


@pytest.mark.parametrize("ticker", ["SPY", "TLT", "GLD"])
def test_cross_asset_features_ignore_the_future(ticker):
    df = market_for(ticker)
    cls = CLASSES[ticker]
    cut = 650
    moved = df.copy()
    rng = np.random.default_rng(1)
    for c in [c for c in df if c.startswith("x_") or c == "vix"]:
        moved.iloc[cut + 1:, moved.columns.get_loc(c)] *= np.exp(rng.normal(0, 0.3, len(df) - cut - 1))
    pd.testing.assert_frame_equal(build_features(df, cls).iloc[: cut + 1],
                                  build_features(moved, cls).iloc[: cut + 1])


def test_feature_sets_differ_by_asset_class():
    assert set(macro_cols(market_for("SPY"), "equity")) == {"log_vix", "vrp"}
    rates = set(macro_cols(market_for("TLT"), "rates"))
    assert {"curve_slope", "slope_chg_5", "eq_bond_corr_21", "vix_chg_5"} <= rates
    gold = set(macro_cols(market_for("GLD"), "gold"))
    assert {"dxy_ret_21", "real_rate_proxy_21", "breakeven_chg_21", "vix_stress"} <= gold


def test_missing_cross_asset_series_is_skipped():
    df = market_for("GLD").drop(columns=["x_dxy"])
    cols = macro_cols(df, "gold")
    assert not any(c.startswith("dxy") for c in cols) and "real_rate_proxy_21" in cols


def test_align_to_is_as_of_and_never_forward():
    # Outside series trades on a day the ETF is closed (Jan 3) and is missing on Jan 5.
    s = pd.Series([1.0, 2.0, 3.0, 4.0],
                  index=pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04", "2024-01-08"]))
    target = pd.to_datetime(["2024-01-02", "2024-01-04", "2024-01-05", "2024-01-09"])
    out = align_to(s, pd.DatetimeIndex(target))
    # Jan 5: last known value is Jan 4's (3.0), never Jan 8's (4.0).
    assert out.tolist() == [1.0, 3.0, 3.0, 4.0]


def test_align_to_marks_dead_feeds():
    s = pd.Series([1.0], index=pd.to_datetime(["2024-01-02"]))
    target = pd.bdate_range("2024-01-02", periods=10)
    out = align_to(s, target, max_stale_days=3)
    assert out.iloc[:4].notna().all() and out.iloc[4:].isna().all()


def test_profiles_set_costs_and_overrides_win():
    assert get_profile("SPY").cost_bps == pytest.approx(1.5)
    assert get_profile("tlt").cost_bps == pytest.approx(2.0)
    assert get_profile("GLD").cost_bps == pytest.approx(3.0)
    cfg = build_config("TLT")
    assert cfg.strategy.cost_per_unit_traded == pytest.approx(2.0e-4)
    assert cfg.data.asset_class == "rates" and "tnx" in cfg.data.aux_tickers
    cfg = build_config("GLD", strategy_overrides={"slippage_bps": 10.0})
    assert cfg.strategy.cost_per_unit_traded == pytest.approx(10.5e-4)
    assert get_profile("XLE").asset_class == "equity"  # unknown ticker -> equity defaults


def test_information_coefficient():
    idx = pd.bdate_range("2020-01-01", periods=500)
    rng = np.random.default_rng(0)
    bench = pd.Series(0.001, index=idx)
    y = pd.Series(rng.normal(0, 0.01, 500), index=idx)
    perfect = information_coefficient(y, bench + (y - bench), bench, horizon=1)
    assert perfect["ic"] == pytest.approx(1.0) and perfect["view_share"] == pytest.approx(1.0)
    none = information_coefficient(y, bench.copy(), bench, horizon=5)
    assert none["view_share"] == 0 and np.isnan(none["ic"])
    noise = information_coefficient(y, bench + rng.normal(0, 0.01, 500), bench, horizon=5)
    assert abs(noise["ic_t"]) < 3
