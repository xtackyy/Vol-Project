"""Settings for the VRP extension, in the same frozen-dataclass style as volcast.config.

(A config.yaml would need pyyaml, a new dependency; a dataclass keeps everything in Python.)
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VRPConfig:
    start: str = "1993-01-01"        # SPY's first trading day is 1993-01-29
    end: str | None = None
    horizon: int = 21                # trading days, matching VIX's 30 calendar days
    raw_dir: Path = Path("data/raw")
    output_dir: Path = Path("reports/vrp")
    figure_dir: Path = Path("reports/figures/vrp")
    # Strategies. The headline threshold (0: sell whenever VIX is above the HAR forecast) was fixed
    # before any backtest was run; the whole grid is reported next to it.
    thresholds: tuple[float, ...] = (-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0)
    headline_threshold: float = 0.0
    size_cap: float = 2.0
    cost_sensitivity_vol_pts: float = 0.5   # alternative haircut (the base case is SwapConfig's 1.0)
    # Vol-targeted sizing, fixed before it was run: aim the P&L vol at 10% of capital using the
    # trailing 63-day vol of a 1-unit always-short book; at most 2 units ($20k vega).
    vt_target_vol: float = 0.10
    vt_lookback: int = 63


# Stress windows (named in the brief, plus two older ones the 1993+ sample covers) and calm years.
# A 21-day position is assigned to the window containing its entry date.
REGIMES: dict[str, tuple[str, str]] = {
    "1998 LTCM / Russia": ("1998-08-01", "1998-10-31"),
    "2008 GFC": ("2008-09-01", "2009-03-31"),
    "Aug 2011 US downgrade": ("2011-07-15", "2011-10-31"),
    "Feb 2018 Volmageddon": ("2018-01-22", "2018-03-09"),
    "Mar 2020 Covid": ("2020-02-19", "2020-04-30"),
    "2022 bear market": ("2022-01-01", "2022-12-31"),
    "Calm: 2005-2006": ("2005-01-01", "2006-12-31"),
    "Calm: 2017": ("2017-01-01", "2017-12-31"),
}
CRISES = [k for k in REGIMES if not k.startswith("Calm")]
