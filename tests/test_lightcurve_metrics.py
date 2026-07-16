from __future__ import annotations

import numpy as np
import pytest

from tess_scattered_light_quality_audit.exceptions import InsufficientDataError
from tess_scattered_light_quality_audit.lightcurve_metrics import (
    background_flux_correlation,
    mad,
    normalized_flux,
    rms,
    scatter_comparison,
)


def test_normalized_flux_median_is_one():
    flux = np.array([9.0, 10.0, 11.0])
    norm = normalized_flux(flux)
    assert np.median(norm) == pytest.approx(1.0)


def test_normalized_flux_rejects_all_nan():
    with pytest.raises(InsufficientDataError):
        normalized_flux(np.array([np.nan, np.nan]))


def test_rms_and_mad_zero_for_constant_series():
    values = np.full(10, 5.0)
    assert rms(values) == pytest.approx(0.0)
    assert mad(values) == pytest.approx(0.0)


def test_scatter_comparison_detects_injected_excess_scatter(synthetic_lc):
    from tess_scattered_light_quality_audit.quality_flags import apply_mask_policy

    # Real finding, not a bug: lightkurve's "default" mask policy does NOT
    # include the Straylight2 bit (only "hard"/"hardest" do) -- verified
    # directly: DEFAULT_BITMASK & Straylight2 == 0. This is exactly the
    # kind of mask-policy difference this project's scientific question
    # is about, so the injection-recovery gate uses "hard" here.
    keep = apply_mask_policy(synthetic_lc.quality, "hard")
    cmp = scatter_comparison(synthetic_lc.flux, keep)
    # Injected segment has much higher noise; excluding it should reduce RMS.
    assert cmp.scatter_ratio_rms > 1.0
    assert cmp.n_excluded == (synthetic_lc.injected_end - synthetic_lc.injected_start)


def test_scatter_comparison_rejects_too_few_kept_cadences():
    flux = np.array([1.0, 2.0, 3.0])
    keep_mask = np.array([True, False, False])
    with pytest.raises(InsufficientDataError):
        scatter_comparison(flux, keep_mask)


def test_background_flux_correlation_detects_injected_elevation(synthetic_lc):
    from tess_scattered_light_quality_audit.quality_flags import SCATTERED_LIGHT_BIT, is_flagged

    flagged = is_flagged(synthetic_lc.quality, SCATTERED_LIGHT_BIT)
    result = background_flux_correlation(synthetic_lc.background, synthetic_lc.flux, flagged)
    assert result["background_elevation_ratio"] > 1.0


def test_background_flux_correlation_rejects_empty_group():
    background = np.array([1.0, 2.0, 3.0])
    flux = np.array([1.0, 2.0, 3.0])
    flagged = np.array([False, False, False])
    with pytest.raises(InsufficientDataError):
        background_flux_correlation(background, flux, flagged)
