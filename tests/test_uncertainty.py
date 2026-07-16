from __future__ import annotations

import numpy as np
import pytest

from tess_scattered_light_quality_audit.exceptions import ConvergenceError, InsufficientDataError
from tess_scattered_light_quality_audit.uncertainty import bootstrap_statistic, check_fit_convergence


def test_bootstrap_statistic_ci_contains_true_median():
    rng = np.random.default_rng(1)
    values = rng.normal(loc=5.0, scale=1.0, size=200)
    result = bootstrap_statistic(values, seed=20260713)
    assert result.ci_low < 5.0 < result.ci_high


def test_bootstrap_statistic_rejects_too_few_values():
    with pytest.raises(InsufficientDataError):
        bootstrap_statistic(np.array([1.0]))


def test_check_fit_convergence_accepts_well_conditioned_covariance():
    cov = np.eye(2) * 0.01
    result = check_fit_convergence(cov)
    assert result.converged


def test_check_fit_convergence_rejects_ill_conditioned_covariance():
    cov = np.array([[1e-20, 0.0], [0.0, 1e20]])
    with pytest.raises(ConvergenceError):
        check_fit_convergence(cov, max_condition_number=1e10)


def test_check_fit_convergence_rejects_nonfinite_covariance():
    cov = np.array([[np.nan, 0.0], [0.0, 1.0]])
    with pytest.raises(ConvergenceError):
        check_fit_convergence(cov)
