"""Next-open execution and multiple-testing (deflated Sharpe) checks."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from volcast.backtest import run_backtest, run_backtest_next_open
from volcast.config import StrategyConfig
from volcast.metrics import deflated_sharpe, expected_max_sharpe, probabilistic_sharpe


def _market(n: int = 400, seed: int = 0):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2015-01-01", periods=n)
    ret = pd.Series(rng.normal(0.0004, 0.01, n), index=idx)
    target = pd.Series(rng.uniform(0.2, 1.0, n), index=idx)  # unlevered, so no borrow cost
    return idx, ret, target


def test_next_open_with_no_overnight_gap_matches_close_execution():
    """With no overnight move and no costs or rf, trading at t+1's open earns exactly t+1's return,
    which is what close execution earns, so the two engines must agree."""
    idx, ret, target = _market()
    zero = pd.Series(0.0, index=idx)
    cfg = StrategyConfig(commission_bps=0.0, slippage_bps=0.0)
    close = run_backtest(target, ret, zero, cfg, band=0.0)
    nxt = run_backtest_next_open(target, zero, ret, zero, cfg, band=0.0)
    np.testing.assert_allclose(nxt.net.iloc[1:], close.net.iloc[1:], atol=1e-14)


def test_next_open_books_the_same_trades_one_day_later():
    idx, ret, target = _market(seed=1)
    zero = pd.Series(0.0, index=idx)
    cfg = StrategyConfig()
    close = run_backtest(target, ret, zero, cfg, band=0.0)
    nxt = run_backtest_next_open(target, zero, ret, zero, cfg, band=0.0)
    np.testing.assert_allclose(nxt.turnover.iloc[1:].to_numpy(), close.turnover.iloc[:-1].to_numpy(), atol=1e-12)


def test_next_open_target_does_not_earn_the_overnight_gap():
    """A target decided at the close of t-1 is traded at t's open, after the overnight gap.
    Changing it must leave the overnight P&L of day t untouched."""
    idx, ret, target = _market(seed=2)
    zero = pd.Series(0.0, index=idx)
    cfg = StrategyConfig(commission_bps=0.0, slippage_bps=0.0)
    k = 200
    moved = target.copy()
    moved.iloc[k - 1] = 0.0 if target.iloc[k - 1] > 0.5 else 1.0
    a = run_backtest_next_open(target, ret, zero, zero, cfg, band=0.0)  # all return is overnight
    b = run_backtest_next_open(moved, ret, zero, zero, cfg, band=0.0)
    pd.testing.assert_series_equal(a.net.iloc[: k + 1], b.net.iloc[: k + 1])
    assert not np.isclose(a.net.iloc[k + 1], b.net.iloc[k + 1])


def test_expected_max_sharpe_matches_simulation():
    rng = np.random.default_rng(0)
    n, sd = 50, 0.3
    simulated = rng.normal(0, sd, size=(20000, n)).max(axis=1).mean()
    assert expected_max_sharpe(sd ** 2, n) == pytest.approx(simulated, rel=0.03)
    assert expected_max_sharpe(sd ** 2, 1) == 0.0


def test_probabilistic_sharpe_is_one_half_at_its_own_sharpe():
    rng = np.random.default_rng(3)
    x = pd.Series(rng.standard_t(5, 3000) * 0.01 + 0.0005)
    sr = x.mean() / x.std(ddof=1)
    assert probabilistic_sharpe(x, sr) == pytest.approx(0.5)
    assert probabilistic_sharpe(x, 0.0) > probabilistic_sharpe(x, sr / 2) > 0.5


def test_deflated_sharpe_penalises_more_trials():
    rng = np.random.default_rng(4)
    best = pd.Series(rng.normal(0.0006, 0.01, 4000))
    trials = rng.normal(0.0, 0.02, 100)
    one = deflated_sharpe(best, trials, n_trials=1)
    many = deflated_sharpe(best, trials)
    assert one["deflated_sharpe"] == pytest.approx(one["psr_vs_zero"])
    assert many["deflated_sharpe"] < one["deflated_sharpe"]
    assert many["n_trials"] == 100
