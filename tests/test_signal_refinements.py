"""Leakage and accounting tests for the multi-day return target, signal smoothing and long-short."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from test_no_lookahead import scramble_after

from volcast.backtest import run_backtest
from volcast.config import StrategyConfig
from volcast.data import simulate_market
from volcast.features import build_features, build_targets
from volcast.metrics import regime_table
from volcast.models import penalised_regression, walk_forward
from volcast.strategy import expected_excess_return, smooth_signal, target_weights

RET_H = 5


@pytest.fixture(scope="module")
def market() -> pd.DataFrame:
    return simulate_market(1100, seed=4)


def test_multiday_return_target_is_strictly_future(market):
    cut = 700
    a = build_targets(market, 5, RET_H)["y_ret"]
    b = build_targets(scramble_after(market, cut), 5, RET_H)["y_ret"]
    # Labels whose 5-day window ends at or before `cut` are untouched...
    pd.testing.assert_series_equal(a.iloc[: cut - RET_H + 1], b.iloc[: cut - RET_H + 1])
    # ...and the label at `cut` changes, because its window starts at cut+1.
    assert not np.isclose(a.iloc[cut], b.iloc[cut])
    assert a.iloc[-RET_H:].isna().all()


def test_multiday_target_equals_sum_of_next_returns(market):
    y = build_targets(market, 5, RET_H)["y_ret"]
    excess = market["close"].pct_change() - market["rf"]
    t = 400
    assert y.iloc[t] == pytest.approx(excess.iloc[t + 1: t + 1 + RET_H].sum())


def test_smoothing_is_causal():
    rng = np.random.default_rng(0)
    idx = pd.bdate_range("2020-01-01", periods=300)
    mu = pd.Series(rng.normal(size=300), index=idx)
    moved = mu.copy()
    moved.iloc[200:] += 50.0
    for ema, hold in [(10, 1), (None, 5), (20, 5)]:
        a, b = smooth_signal(mu, ema, hold), smooth_signal(moved, ema, hold)
        pd.testing.assert_series_equal(a.iloc[:200], b.iloc[:200])


def test_hold_refreshes_every_k_days():
    mu = pd.Series(np.arange(12, dtype=float), index=pd.bdate_range("2020-01-01", periods=12))
    held = smooth_signal(mu, None, 5)
    assert held.tolist() == [0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 10, 10]


def test_expected_return_is_per_day():
    idx = pd.bdate_range("2020-01-01", periods=3)
    pred = pd.Series([0.010, 0.005, -0.005], index=idx)   # 5-day forecasts
    bench = pd.Series(0.005, index=idx)                    # training mean of 5-day returns
    mu = expected_excess_return(pred, bench, prior_premium=0.0, horizon=5)
    np.testing.assert_allclose(mu, [0.001, 0.0, -0.002])
    np.testing.assert_allclose(expected_excess_return(pred, bench, None, 5), pred / 5)


def test_long_short_weights_and_bounds():
    idx = pd.bdate_range("2020-01-01", periods=4)
    log_vol = pd.Series(np.log([0.10, 0.20, 0.05, 0.10]), index=idx)
    mu = pd.Series([1e-4, -1e-4, -1e-4, 1e-4], index=idx)
    cfg = StrategyConfig(target_vol=0.10, max_leverage=1.5, signal_ema_span=None)
    w = target_weights(log_vol, mu, cfg)
    np.testing.assert_allclose(w["vol_target_signal"], [1.0, 0.0, 0.0, 1.0])
    np.testing.assert_allclose(w["vol_target_signal_ls"], [1.0, -0.5, -1.5, 1.0])
    assert w["vol_target_signal"].between(0, cfg.max_leverage).all()
    assert w["vol_target_signal_ls"].abs().le(cfg.max_leverage).all()


def test_short_position_accounting():
    """Short 1x: earn -r on the asset, 2x rf on cash (proceeds + capital), pay the borrow fee."""
    idx = pd.bdate_range("2020-01-01", periods=10)
    r = pd.Series(0.01, index=idx)
    rf = pd.Series(0.0001, index=idx)
    cfg = StrategyConfig(commission_bps=0, slippage_bps=0, rebalance_band=0, short_fee_bps=252)
    res = run_backtest(pd.Series(-1.0, index=idx), r, rf, cfg)
    assert res.gross.iloc[1] == pytest.approx(-0.01 + 2 * 0.0001 - 0.0001)


def test_gross_minus_net_is_cost(market):
    idx = market.index[300:600]
    w = pd.Series(np.tile([1.0, 0.0], len(idx) // 2), index=idx)
    res = run_backtest(w, market["close"].pct_change(), market["rf"], StrategyConfig(rebalance_band=0))
    np.testing.assert_allclose(res.net, (1 + res.gross) * (1 - res.costs) - 1)
    assert (res.gross >= res.net).all()


def test_regime_table_slices_by_date(market):
    idx = market.index[300:]
    res = run_backtest(pd.Series(1.0, index=idx), market["close"].pct_change(), market["rf"], StrategyConfig())
    first, last = str(idx[0].year), str(idx[-1].year)
    tab = regime_table({"bh": res}, market["rf"], {"a": (first, first), "b": (last, last)})
    assert set(tab.index.get_level_values(0)) <= {"a", "b"}
    assert (tab["max_drawdown"] <= 0).all()


def test_five_day_return_model_ignores_the_future(market):
    """End-to-end: Lasso on 5-day targets with purge=5 and CV gap=5 is point-in-time."""
    cut = 850

    def predict(df: pd.DataFrame) -> pd.Series:
        f = build_features(df).dropna()
        y = build_targets(df, 5, RET_H).reindex(f.index)["y_ret"]
        return walk_forward(f, y, penalised_regression("lasso", np.logspace(-6, -3, 4), 3, RET_H),
                            min_train=300, refit_every=21, horizon=RET_H).predictions

    base, moved = predict(market), predict(scramble_after(market, cut))
    past = base.index[base.index <= market.index[cut]]
    assert len(past) > 200
    pd.testing.assert_series_equal(base.loc[past], moved.loc[past])
