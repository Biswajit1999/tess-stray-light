import numpy as np
import pytest

from tess_scattered_light_quality_audit.policy_robustness import (
    policy_exclusion_audit, zero_flag_upper_sensitivity, paired_block_bootstrap,
)


def test_policy_additions_and_scattered_light_default_retention():
    q = np.array([0, 4096, 4096, 1, 8192, 32768], dtype=np.int64)
    d = policy_exclusion_audit(q)
    assert d["straylight2_flagged"] == 2
    assert d["straylight2_retained_by_default"] == 2
    assert d["newly_excluded_hard_vs_default"] >= 2
    assert d["excluded_by_policy"]["default"] <= d["excluded_by_policy"]["hard"]
    assert d["excluded_by_policy"]["hard"] <= d["excluded_by_policy"]["hardest"]


def test_zero_event_exact_n1_and_scaling():
    one = zero_flag_upper_sensitivity(1)[0]
    assert one["zero_event_upper_fraction"] == pytest.approx(.95)
    rows = zero_flag_upper_sensitivity(300, independent_block_lengths=(1, 10, 30))
    assert rows[0]["zero_event_upper_fraction"] < rows[1]["zero_event_upper_fraction"]
    assert rows[1]["zero_event_upper_fraction"] < rows[2]["zero_event_upper_fraction"]
    assert rows[2]["effective_trials"] == 10


def test_zero_event_validation():
    with pytest.raises(ValueError):
        zero_flag_upper_sensitivity(0)
    with pytest.raises(ValueError):
        zero_flag_upper_sensitivity(10, independent_block_lengths=(0,))


def synthetic():
    rng = np.random.default_rng(99)
    n = 400
    flux = 10000 + rng.normal(0, 10, n)
    quality = np.zeros(n, dtype=np.int64)
    quality[250:320] = 4096
    flux[250:320] = 10000 + rng.normal(0, 50, 70)
    return flux, quality


def test_paired_bootstrap_injected_effect_recovered():
    f, q = synthetic()
    d = paired_block_bootstrap(f, q, block_length=20, n_resamples=300, seed=42)
    assert d["hard_minus_default_ratio"] > .5
    assert d["bootstrap_p975"] > d["bootstrap_p025"]
    assert d["valid_resamples"] >= 240


def test_paired_bootstrap_seed_reproducible():
    f, q = synthetic()
    a = paired_block_bootstrap(f, q, n_resamples=100, seed=8)
    b = paired_block_bootstrap(f, q, n_resamples=100, seed=8)
    assert a == b


def test_identical_masks_null_contrast_exactly_zero():
    f, _ = synthetic()
    q = np.zeros(f.size, dtype=np.int64)
    d = paired_block_bootstrap(f, q, n_resamples=80)
    assert d["hard_minus_default_ratio"] == pytest.approx(0.0)
    assert d["bootstrap_p025"] == pytest.approx(0.0)


def test_invalid_inputs():
    f, q = synthetic()
    with pytest.raises(ValueError, match="flux"):
        paired_block_bootstrap(f[:-1], q)
    with pytest.raises(ValueError, match="block length"):
        paired_block_bootstrap(f, q, block_length=200)
    with pytest.raises(ValueError, match="QUALITY"):
        policy_exclusion_audit(np.array([-1, 0]))
