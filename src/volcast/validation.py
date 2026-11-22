"""Purged walk-forward splits.

At each refit date `s` the model is trained only on rows whose *labels* were fully
observed before `s`. A label at row i covers days i+1..i+h, so it is known after the
close of day i+h; requiring i + h < s ("purging") removes the overlap that otherwise
leaks the test period into training whenever the target horizon exceeds one day.
"""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Fold:
    train_idx: np.ndarray  # positional indices used to fit
    test_idx: np.ndarray   # positional indices forecast with that fit

    @property
    def fit_position(self) -> int:
        return int(self.test_idx[0])


def walk_forward_splits(
    n_obs: int,
    min_train: int,
    refit_every: int,
    horizon: int,
    rolling_window: int | None = None,
) -> Iterator[Fold]:
    """Yield expanding (or rolling) purged folds covering [min_train, n_obs)."""
    if min_train <= horizon:
        raise ValueError("min_train must exceed the label horizon")
    for start in range(min_train, n_obs, refit_every):
        train_end = start - horizon  # exclusive: rows i <= start - horizon - 1
        train_start = 0 if rolling_window is None else max(0, train_end - rolling_window)
        test_end = min(start + refit_every, n_obs)
        yield Fold(np.arange(train_start, train_end), np.arange(start, test_end))
