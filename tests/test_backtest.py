"""Backtest engine correctness: timing, costs, financing and metric sanity."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from volcast.backtest import buy_and_hold, run_backtest
from volcast.config import StrategyConfig
from volcast.metrics import drawdown, performance

IDX = pd.bdate_range("2020-01-01", periods=300)


@pytest.fixture
def rets() -> pd.Series:
    return pd.Series(np.random.default_rng(3).normal(0.0004, 0.01, len(IDX)), index=IDX)


def test_weights_are_applied_with_one_day_lag(rets):
    """An oracle weight w_t = 1{r_t > 0} must NOT capture r_t: it only trades on t+1."""
    cfg = StrategyConfig(commission_bps=0, slippage_bps=0, rebalance_band=0)
    oracle = (rets > 0).astype(float)
    res = run_backtest(oracle, rets, pd.Series(0.0, index=IDX), cfg)
    expected = oracle.shift(1).fillna(0) * rets
    expected.iloc[0] = 0.0
    np.testing.assert_allclose(res.gross, expected, atol=1e-12)
    assert res.net.mean() < oracle.mul(rets).mean()  # far from the impossible oracle P&L


def test_buy_and_hold_equals_asset_minus_entry_cost(rets):
    cfg = StrategyConfig(commission_bps=1, slippage_bps=1)
    bh = buy_and_hold(IDX, rets, pd.Series(0.0, index=IDX), cfg)
    assert bh.turnover.iloc[0] == pytest.approx(1.0)
    assert bh.turnover.iloc[1:].abs().max() < 1e-12
    np.testing.assert_allclose(bh.net.iloc[1:], rets.iloc[1:], atol=1e-12)
    assert bh.net.iloc[0] == pytest.approx(-2e-4)


def test_costs_scale_with_turnover(rets):
    flip = pd.Series(np.tile([1.0, 0.0], len(IDX) // 2), index=IDX)
    cheap = run_backtest(flip, rets, pd.Series(0.0, index=IDX), StrategyConfig(slippage_bps=0, commission_bps=0))
    dear = run_backtest(flip, rets, pd.Series(0.0, index=IDX), StrategyConfig(slippage_bps=10, commission_bps=0))
    assert dear.costs.sum() == pytest.approx(dear.turnover.sum() * 10e-4)
    assert dear.equity.iloc[-1] < cheap.equity.iloc[-1]


def test_no_trade_band_reduces_turnover(rets):
    noisy = pd.Series(0.8 + np.random.default_rng(5).normal(0, 0.05, len(IDX)), index=IDX)
    tight = run_backtest(noisy, rets, pd.Series(0.0, index=IDX), StrategyConfig(rebalance_band=0.0))
    wide = run_backtest(noisy, rets, pd.Series(0.0, index=IDX), StrategyConfig(rebalance_band=0.1))
    assert wide.turnover.iloc[1:].sum() < 0.6 * tight.turnover.iloc[1:].sum()


def test_leverage_pays_rf_plus_spread():
    cfg = StrategyConfig(commission_bps=0, slippage_bps=0, borrow_spread_bps=100, rebalance_band=0)
    flat = pd.Series(0.0, index=IDX)
    rf = pd.Series(0.0002, index=IDX)
    res = run_backtest(pd.Series(2.0, index=IDX), flat, rf, cfg)
    # 2x levered on a zero-return asset: pay rf on the borrowed unit plus the spread.
    assert res.gross.iloc[5] == pytest.approx(-0.0002 - 0.01 / 252, rel=1e-6)


def test_performance_metrics_sanity(rets):
    rf = pd.Series(0.0, index=IDX)
    perf = performance(rets, rf)
    assert perf["max_drawdown"] == pytest.approx(drawdown(rets).min())
    assert perf["sharpe"] == pytest.approx(rets.mean() / rets.std() * np.sqrt(252))
    assert perf["sortino"] > perf["sharpe"] * 0.5
