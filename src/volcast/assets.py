"""Per-asset settings: trading costs, return prior and the cross-asset data each asset needs.

One `--ticker` flag selects a profile; `build_config` turns it into a full `Config`, so
SPY, TLT and GLD run through exactly the same validation engine with asset-specific inputs.

Cost assumptions are per unit of notional traded (commission + half-spread/impact) for a
liquid ETF executed at the close:
    SPY  1.5 bps   deepest ETF market, 1-cent spread on a ~$500+ price
    TLT  2.0 bps   very liquid, slightly wider relative spread
    GLD  3.0 bps   liquid but wider spread / more close-auction impact
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Literal

from .config import Config, DataConfig, ModelConfig, StrategyConfig

log = logging.getLogger(__name__)

AssetClass = Literal["equity", "rates", "gold"]


@dataclass(frozen=True)
class AssetProfile:
    ticker: str
    asset_class: AssetClass
    commission_bps: float
    slippage_bps: float
    prior_premium: float  # annual excess-return prior used by the long/flat signal
    # Cross-asset inputs: feature key -> Yahoo tickers to try in order (first success wins).
    aux: dict[str, tuple[str, ...]] = field(default_factory=dict)

    @property
    def cost_bps(self) -> float:
        return self.commission_bps + self.slippage_bps


PROFILES: dict[str, AssetProfile] = {
    "SPY": AssetProfile("SPY", "equity", 0.5, 1.0, 0.04),
    "QQQ": AssetProfile("QQQ", "equity", 0.5, 1.0, 0.04),
    "TLT": AssetProfile(
        "TLT", "rates", 0.5, 1.5, 0.01,
        aux={"tnx": ("^TNX",), "irx": ("^IRX",), "spy": ("SPY",)},
    ),
    "GLD": AssetProfile(
        "GLD", "gold", 0.5, 2.5, 0.02,
        # DX-Y.NYB (ICE dollar index) has history back to the 1970s; UUP is the ETF fallback.
        aux={"dxy": ("DX-Y.NYB", "UUP"), "tnx": ("^TNX",), "tip": ("TIP",), "ief": ("IEF",)},
    ),
}


def get_profile(ticker: str) -> AssetProfile:
    t = ticker.upper()
    if t in PROFILES:
        return PROFILES[t]
    log.warning("no profile for %s: using equity defaults (1.5 bps, no cross-asset features)", t)
    return replace(PROFILES["SPY"], ticker=t)


def build_config(
    ticker: str,
    *,
    model: ModelConfig | None = None,
    strategy_overrides: dict | None = None,
    output_dir: Path | None = None,
    **data_kwargs,
) -> Config:
    """Full config for `ticker`: profile costs, prior and cross-asset inputs, then overrides.

    `strategy_overrides` are StrategyConfig fields that win over the profile (e.g. a CLI
    `--commission-bps`); `data_kwargs` go to DataConfig (start, end, synthetic, ...).
    """
    p = get_profile(ticker)
    strategy = StrategyConfig(commission_bps=p.commission_bps, slippage_bps=p.slippage_bps,
                              prior_premium=p.prior_premium)
    if strategy_overrides:
        strategy = replace(strategy, **strategy_overrides)
    data = DataConfig(ticker=p.ticker, asset_class=p.asset_class, aux_tickers=dict(p.aux), **data_kwargs)
    return Config(data=data, model=model or ModelConfig(), strategy=strategy,
                  output_dir=output_dir or Path("reports") / p.ticker)
