"""Prediction-distribution contracts for component forecasts."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import poisson

PROJECTION_DISTRIBUTION_VERSION = "m10-projection-distribution-v1"


@dataclass(frozen=True)
class ProjectionDistribution:
    """Point forecast plus explicitly labelled uncertainty intervals."""

    expected: pd.DataFrame
    lower: pd.DataFrame
    upper: pd.DataFrame
    coverage: float
    interval_method: str
    data_cutoff: str
    model_version: str
    version: str = PROJECTION_DISTRIBUTION_VERSION

    def to_frame(self) -> pd.DataFrame:
        """Flatten the distribution for persistence or audit output."""

        result = self.expected.copy()
        for column in self.expected.columns:
            result[f"{column}_lower"] = self.lower[column]
            result[f"{column}_upper"] = self.upper[column]
        return result


def build_poisson_component_distribution(
    expected: pd.DataFrame,
    *,
    coverage: float = 0.8,
    data_cutoff: str = "unknown",
    model_version: str = "unknown",
) -> ProjectionDistribution:
    """Build central Poisson intervals for non-negative event components."""

    _validate_coverage(coverage)
    means = expected.apply(pd.to_numeric, errors="coerce").fillna(0.0).clip(lower=0.0)
    alpha = (1.0 - coverage) / 2.0
    lower = pd.DataFrame(
        {column: poisson.ppf(alpha, means[column].to_numpy()) for column in means.columns},
        index=means.index,
    )
    upper = pd.DataFrame(
        {column: poisson.ppf(1.0 - alpha, means[column].to_numpy()) for column in means.columns},
        index=means.index,
    )
    return ProjectionDistribution(
        expected=means,
        lower=lower.astype(float),
        upper=upper.astype(float),
        coverage=coverage,
        interval_method="poisson_central_interval_unadjusted",
        data_cutoff=data_cutoff,
        model_version=model_version,
    )


def build_empirical_component_distribution(
    expected: pd.DataFrame,
    actual: pd.DataFrame,
    *,
    coverage: float = 0.8,
    data_cutoff: str = "unknown",
    model_version: str = "unknown",
) -> ProjectionDistribution:
    """Build intervals from a declared calibration sample.

    The caller must provide a held-out or otherwise pre-declared calibration
    sample. This function does not infer that the sample is out-of-sample.
    """

    _validate_coverage(coverage)
    if list(expected.columns) != list(actual.columns) or len(expected) != len(actual):
        raise ValueError("expected and actual must have identical columns and row counts")
    means = expected.apply(pd.to_numeric, errors="coerce").fillna(0.0).clip(lower=0.0)
    observed = actual.apply(pd.to_numeric, errors="coerce")
    alpha = (1.0 - coverage) / 2.0
    lower_widths: dict[str, float] = {}
    upper_widths: dict[str, float] = {}
    for column in means.columns:
        residuals = (observed[column] - means[column]).dropna().to_numpy(dtype=float)
        if not len(residuals):
            lower_widths[column] = 0.0
            upper_widths[column] = 0.0
        else:
            lower_widths[column] = float(np.quantile(residuals, alpha))
            upper_widths[column] = float(np.quantile(residuals, 1.0 - alpha))
    lower = pd.DataFrame(
        {column: np.maximum(means[column] + lower_widths[column], 0.0) for column in means.columns},
        index=means.index,
    )
    upper = pd.DataFrame(
        {
            column: np.maximum(means[column] + upper_widths[column], lower[column])
            for column in means.columns
        },
        index=means.index,
    )
    return ProjectionDistribution(
        expected=means,
        lower=lower,
        upper=upper,
        coverage=coverage,
        interval_method="empirical_residual_interval",
        data_cutoff=data_cutoff,
        model_version=model_version,
    )


def _validate_coverage(coverage: float) -> None:
    if not 0.0 < coverage < 1.0:
        raise ValueError("coverage must be strictly between 0 and 1")
