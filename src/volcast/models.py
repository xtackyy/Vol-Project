"""Model definitions and the walk-forward fit/forecast engine.

* Model A  - Ridge on an extended HAR feature set -> log forward realized vol.
* Baseline - classic HAR-RV (OLS on daily/weekly/monthly log vol), via statsmodels.
* Model B  - Lasso (or Ridge) on all features -> next-day excess return.

Scaling and the regularisation strength are chosen *inside* each training window:
the StandardScaler lives in the Pipeline, and alpha is tuned by GridSearchCV over a
TimeSeriesSplit with a purge gap, so neither ever sees out-of-sample data.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.linear_model import Lasso, Ridge
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .validation import walk_forward_splits

EstimatorFactory = Callable[[], BaseEstimator]


def penalised_regression(
    kind: str, alphas: Sequence[float], cv_splits: int, gap: int
) -> EstimatorFactory:
    """Factory for scaler -> Ridge/Lasso with time-series CV over alpha."""

    def factory() -> GridSearchCV:
        model = Ridge() if kind == "ridge" else Lasso(max_iter=20_000, tol=1e-6)
        pipe = Pipeline([("scaler", StandardScaler()), ("model", model)])
        return GridSearchCV(
            pipe,
            {"model__alpha": list(alphas)},
            cv=TimeSeriesSplit(n_splits=cv_splits, gap=gap),
            scoring="neg_mean_squared_error",
            n_jobs=None,
        )

    return factory


class HAROLS(BaseEstimator, RegressorMixin):
    """Classic HAR-RV: y = b0 + b_d RV_d + b_w RV_w + b_m RV_m, fitted by OLS (statsmodels)."""

    def fit(self, X: pd.DataFrame | np.ndarray, y: np.ndarray) -> HAROLS:
        self.result_ = sm.OLS(np.asarray(y), sm.add_constant(np.asarray(X), has_constant="add")).fit()
        return self

    def predict(self, X: pd.DataFrame | np.ndarray) -> np.ndarray:
        return self.result_.predict(sm.add_constant(np.asarray(X), has_constant="add"))


def har_inference_table(X: pd.DataFrame, y: pd.Series, horizon: int) -> pd.DataFrame:
    """Full-sample HAR regression with Newey-West (HAC) errors.

    In-sample by design: this is the *inference* view (are the HAR loadings significant
    once overlapping-label autocorrelation is accounted for?), not a forecast.
    """
    res = sm.OLS(y, sm.add_constant(X)).fit(cov_type="HAC", cov_kwds={"maxlags": max(horizon, 5)})
    return pd.DataFrame({"coef": res.params, "hac_t": res.tvalues, "p_value": res.pvalues})


@dataclass
class WalkForwardResult:
    predictions: pd.Series        # out-of-sample forecasts, indexed by date
    coefficients: pd.DataFrame    # standardised coefficients per refit (penalised models)
    alphas: pd.Series             # chosen regularisation per refit
    benchmark: pd.Series          # prevailing-mean forecast (training-window mean of y)


def walk_forward(
    X: pd.DataFrame,
    y: pd.Series,
    factory: EstimatorFactory,
    *,
    min_train: int,
    refit_every: int,
    horizon: int,
    rolling_window: int | None = None,
) -> WalkForwardResult:
    """Refit on purged past data every `refit_every` rows and forecast the next block."""
    Xv, yv = X.to_numpy(), y.to_numpy()
    preds = np.full(len(X), np.nan)
    bench = np.full(len(X), np.nan)
    coefs, alphas, fit_dates = [], [], []

    for fold in walk_forward_splits(len(X), min_train, refit_every, horizon, rolling_window):
        tr = fold.train_idx[~np.isnan(yv[fold.train_idx])]
        est = factory().fit(Xv[tr], yv[tr])
        preds[fold.test_idx] = est.predict(Xv[fold.test_idx])
        bench[fold.test_idx] = yv[tr].mean()

        fit_dates.append(X.index[fold.fit_position])
        best = getattr(est, "best_estimator_", None)
        if best is not None:
            coefs.append(best.named_steps["model"].coef_.copy())
            alphas.append(est.best_params_["model__alpha"])
        else:
            coefs.append(np.asarray(est.result_.params[1:]))
            alphas.append(np.nan)

    return WalkForwardResult(
        predictions=pd.Series(preds, index=X.index, name="pred").dropna(),
        coefficients=pd.DataFrame(coefs, index=pd.DatetimeIndex(fit_dates), columns=X.columns),
        alphas=pd.Series(alphas, index=pd.DatetimeIndex(fit_dates), name="alpha"),
        benchmark=pd.Series(bench, index=X.index, name="bench").dropna(),
    )
