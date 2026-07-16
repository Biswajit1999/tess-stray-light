"""Observational (bootstrap) vs numerical (fit convergence) uncertainty.

Kept strictly separate per the project's non-negotiable rules: bootstrap
resampling estimates observational uncertainty on a statistic; fit
convergence checks assess numerical reliability of a model fit. Never
conflate the two.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from tess_scattered_light_quality_audit.exceptions import ConvergenceError, InsufficientDataError


@dataclass(frozen=True)
class BootstrapResult:
    estimate: float
    ci_low: float
    ci_high: float
    n_resamples: int


def bootstrap_statistic(
    values: np.ndarray,
    statistic=np.median,
    n_resamples: int = 1000,
    confidence: float = 0.95,
    seed: int = 20260713,
) -> BootstrapResult:
    """Bootstrap confidence interval for a statistic of `values`."""
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size < 2:
        raise InsufficientDataError("bootstrap_statistic requires at least 2 finite values")

    rng = np.random.default_rng(seed)
    point_estimate = float(statistic(arr))
    resample_stats = np.empty(n_resamples, dtype=float)
    for i in range(n_resamples):
        sample = rng.choice(arr, size=arr.size, replace=True)
        resample_stats[i] = statistic(sample)

    alpha = 1.0 - confidence
    lo = float(np.quantile(resample_stats, alpha / 2.0))
    hi = float(np.quantile(resample_stats, 1.0 - alpha / 2.0))
    return BootstrapResult(estimate=point_estimate, ci_low=lo, ci_high=hi, n_resamples=n_resamples)


@dataclass(frozen=True)
class ConvergenceCheck:
    converged: bool
    condition_number: float
    reduced_chi_square: float | None


def check_fit_convergence(
    covariance: np.ndarray,
    residuals: np.ndarray | None = None,
    dof: int | None = None,
    max_condition_number: float = 1e10,
) -> ConvergenceCheck:
    """Assess numerical convergence of a fit via covariance conditioning
    and (optionally) reduced chi-square.

    Raises `ConvergenceError` if the covariance is non-finite or its
    condition number exceeds `max_condition_number`.
    """
    cov = np.asarray(covariance, dtype=float)
    if not np.all(np.isfinite(cov)):
        raise ConvergenceError("fit covariance matrix contains non-finite values")

    try:
        condition_number = float(np.linalg.cond(cov))
    except np.linalg.LinAlgError as exc:
        raise ConvergenceError(f"fit covariance matrix is singular: {exc}") from exc

    reduced_chi_square = None
    if residuals is not None and dof is not None and dof > 0:
        reduced_chi_square = float(np.sum(np.asarray(residuals, dtype=float) ** 2) / dof)

    if condition_number > max_condition_number:
        raise ConvergenceError(
            f"fit covariance condition number {condition_number:.3e} exceeds threshold {max_condition_number:.3e}"
        )

    return ConvergenceCheck(converged=True, condition_number=condition_number, reduced_chi_square=reduced_chi_square)
