import numpy as np
import pytest
from tess_scattered_light_quality_audit.robustness import (
    policy_attribution, block_bootstrap_scatter_ratio, circular_shift_background_test,
)
from tess_scattered_light_quality_audit.synthetic import make_synthetic_lightcurve


def test_policy_incremental_exclusion_accounting():
    q = np.array([0, 1, 4096, 8192, 65535, 0], dtype=np.int64)
    result = policy_attribution(q)
    counts = result['excluded']
    assert counts['default'] <= counts['hard'] <= counts['hardest']
    assert result['hard_only'] == counts['hard'] - counts['default']
    assert result['hardest_only'] == counts['hardest'] - counts['hard']
    assert result['flagged_by_bit']['Straylight2'] == 2


def test_policy_null_flag_sample():
    result = policy_attribution(np.array([0, 32, 128, 512], dtype=np.int64))
    assert result['flagged_by_bit']['Straylight2'] == 0


def test_block_bootstrap_reproducible_and_injection_detected():
    s = make_synthetic_lightcurve(seed=17)
    a = block_bootstrap_scatter_ratio(s.flux, s.quality, policy='hard', n_resamples=100, seed=7)
    b = block_bootstrap_scatter_ratio(s.flux, s.quality, policy='hard', n_resamples=100, seed=7)
    assert a == b
    assert a['estimate'] > 1.1
    default = block_bootstrap_scatter_ratio(s.flux, s.quality, n_resamples=100)
    assert default['estimate'] == 1.0  # Default does not mask Straylight2
    assert a['ci_low'] > 1.0


def test_block_length_sensitivity_and_constant_flux_guard():
    s = make_synthetic_lightcurve(seed=17)
    a = block_bootstrap_scatter_ratio(s.flux, s.quality, policy='hard', block_length=5, n_resamples=100)
    b = block_bootstrap_scatter_ratio(s.flux, s.quality, policy='hard', block_length=30, n_resamples=100)
    assert a['estimate'] == b['estimate']
    assert (a['ci_low'], a['ci_high']) != (b['ci_low'], b['ci_high'])
    with pytest.raises(ValueError):
        block_bootstrap_scatter_ratio(np.ones(40), np.zeros(40, dtype=int))


def test_circular_shift_injected_alignment_and_null():
    s = make_synthetic_lightcurve(seed=17)
    result = circular_shift_background_test(s.background, s.quality)
    assert result['background_median_difference'] > 400
    assert result['two_sided_shift_p'] < .1
    assert result['null_count'] == len(s.flux) - 1


def test_circular_shift_requires_both_classes():
    with pytest.raises(ValueError, match='Both flagged'):
        circular_shift_background_test(np.arange(40.), np.zeros(40, dtype=int))


def test_invalid_inputs_fail():
    with pytest.raises(ValueError):
        policy_attribution(np.array([-1]))
    with pytest.raises(ValueError):
        block_bootstrap_scatter_ratio(np.ones(20), np.zeros(20, dtype=int), block_length=30)
    with pytest.raises(ValueError):
        circular_shift_background_test(np.arange(20.), np.ones(20, dtype=int), bit=3)
