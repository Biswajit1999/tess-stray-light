from __future__ import annotations

import numpy as np

from tess_scattered_light_quality_audit.quality_flags import (
    DEFAULT_BITMASK,
    HARD_BITMASK,
    HARDEST_BITMASK,
    Straylight2,
    apply_mask_policy,
    decode_flags,
    is_flagged,
)


def test_decode_flags_single_bit():
    assert decode_flags(Straylight2) == ["Straylight2"]


def test_decode_flags_combined_bits():
    combined = 1 | 4096
    assert decode_flags(combined) == ["AttitudeTweak", "Straylight2"]


def test_decode_flags_zero_is_empty():
    assert decode_flags(0) == []


def test_is_flagged_vectorized():
    quality = np.array([0, 4096, 1, 4097])
    flagged = is_flagged(quality, Straylight2)
    np.testing.assert_array_equal(flagged, [False, True, False, True])


def test_mask_policy_bitmask_values_match_verified_literature():
    # Values verified against lightkurve.utils.TessQualityFlags in
    # IMPLEMENTATION_PLAN.md Section 1.
    assert DEFAULT_BITMASK == 17087
    assert HARD_BITMASK == 24319
    assert HARDEST_BITMASK == 65535


def test_apply_mask_policy_hardest_excludes_more_than_default():
    quality = np.array([0, 4096, 128, 8192])
    keep_default = apply_mask_policy(quality, "default")
    keep_hardest = apply_mask_policy(quality, "hardest")
    assert keep_default.sum() >= keep_hardest.sum()


def test_apply_mask_policy_unknown_raises():
    import pytest

    with pytest.raises(ValueError):
        apply_mask_policy(np.array([0]), "not_a_policy")
