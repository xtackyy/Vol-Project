"""Central, immutable configuration for the whole pipeline.

Every tunable number lives here so a run is fully described by one object
(which is also serialised next to the results for reproducibility).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

import numpy as np

TRADING_DAYS: int = 252


@dataclass(frozen=True)
class DataConfig:
    """Where the data comes from."""

    ticker: str = "SPY"
    asset_class: str = "equity"      # equity | rates | gold: selects the cross-asset feature block
    start: str = "2000-01-01"
    end: str | None = None
    vix_ticker: str | None = "^VIX"  # implied-vol feature (set None to disable)
    rf_ticker: str | None = "^IRX"   # 13-week T-bill yield, % p.a. -> daily risk-free
    # Cross-asset inputs: feature key -> Yahoo tickers to try in order (see assets.py).
    aux_tickers: dict[str, tuple[str, ...]] = field(default_factory=dict)
    cache_dir: Path = Path("data")
    synthetic: bool = False          # offline mode: simulated GARCH market
    synthetic_days: int = 5000
    seed: int = 7


@dataclass(frozen=True)
class ModelConfig:
    """Walk-forward and model hyper-parameters."""

    vol_horizon: int = 5             # forecast horizon (days) for forward realized vol
    min_train_days: int = 756        # 3y burn-in before the first out-of-sample forecast
    refit_every: int = 21            # refit monthly; predictions in between use the last fit
    rolling_window: int | None = None  # None = expanding window, else rolling length (days)
    cv_splits: int = 5               # inner TimeSeriesSplit folds for alpha selection
    return_model: Literal["lasso", "ridge"] = "lasso"
    ret_horizon: int = 5             # Model B target: summed excess return over t+1..t+h
    vol_alphas: tuple[float, ...] = tuple(np.logspace(-3, 4, 22))
    ret_ridge_alphas: tuple[float, ...] = tuple(np.logspace(0, 6, 19))
    # Wide enough that CV never picks the top edge (the old 1e-2.5 cap was hit in 69% of SPY
    # 5-day refits, forcing features in). At the top end every coefficient is zero: "no signal".
    ret_lasso_alphas: tuple[float, ...] = tuple(np.logspace(-6, 0, 25))


@dataclass(frozen=True)
class StrategyConfig:
    """Position sizing and execution-cost assumptions."""

    target_vol: float = 0.12         # annualised portfolio vol target
    max_leverage: float = 1.5        # hard cap on gross exposure
    signal_threshold: float = 0.0    # go long only if E[daily excess return] > threshold
    signal_ema_span: int | None = 5  # causal EMA on the expected-return signal (None = raw)
    signal_hold: int = 1             # refresh the signal only every k days (5 = weekly)
    prior_premium: float | None = 0.04  # annual equity-premium prior replacing the noisy
                                        # sample-mean intercept; None = raw model forecast
    rebalance_band: float = 0.10     # no-trade band in weight units (cuts turnover)
    commission_bps: float = 0.5      # per unit of notional traded
    slippage_bps: float = 1.0        # half-spread + impact, per unit traded
    borrow_spread_bps: float = 50.0  # annual spread over rf paid on leverage > 1
    short_fee_bps: float = 25.0      # annual stock-borrow fee on short notional (long-short variant)
    # Fill time. "next_open": a target decided at the close of t trades at the open of t+1 (the
    # headline, since the signal uses day t's own high, low and close). "close": same-close fills.
    execution: str = "next_open"
    vol_bias_correction: bool = True  # scale exp(log-vol forecast) by a point-in-time smearing
                                      # factor from past errors (Jensen: exp(E[log s]) < E[s])

    @property
    def cost_per_unit_traded(self) -> float:
        return (self.commission_bps + self.slippage_bps) / 1e4


# Sub-periods for the regime breakdown (out-of-sample data starts Jan 2004 after the burn-in).
REGIMES: dict[str, tuple[str, str]] = {
    "2004-2007 pre-GFC": ("2004-01-01", "2007-12-31"),
    "2008-2009 GFC": ("2008-01-01", "2009-12-31"),
    "2010-2019 post-GFC": ("2010-01-01", "2019-12-31"),
    "2020-2026 Covid & after": ("2020-01-01", "2026-12-31"),
}


@dataclass(frozen=True)
class Config:
    data: DataConfig = field(default_factory=DataConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    output_dir: Path = Path("reports")

    def to_dict(self) -> dict:
        def clean(obj):
            if isinstance(obj, dict):
                return {k: clean(v) for k, v in obj.items()}
            if isinstance(obj, (tuple, list)):
                return [clean(v) for v in obj]
            if isinstance(obj, Path):
                return str(obj)
            if isinstance(obj, np.floating):
                return float(obj)
            return obj

        return clean(asdict(self))
