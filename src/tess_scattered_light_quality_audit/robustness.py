"""Quality-mask attribution and time-aware synthetic TESS diagnostics.

Circular block resampling and circular shifts assume approximate stationarity;
these are sensitivity tools, not calibrated observational detection tests.
"""
from __future__ import annotations

import numpy as np
from tess_scattered_light_quality_audit.quality_flags import (
    BIT_NAMES, MASK_POLICIES, apply_mask_policy, SCATTERED_LIGHT_BIT,
)
from tess_scattered_light_quality_audit.lightcurve_metrics import scatter_comparison


def policy_attribution(quality):
    """Nested policy exclusion counts and per-bit membership (overlaps allowed)."""
    quality = np.asarray(quality)
    if quality.ndim != 1 or not np.issubdtype(quality.dtype, np.integer) or np.any(quality < 0):
        raise ValueError("QUALITY must be a nonnegative integer vector")
    masks = {name: ~apply_mask_policy(quality, name) for name in MASK_POLICIES}
    if not np.all(masks['default'] <= masks['hard']) or not np.all(masks['hard'] <= masks['hardest']):
        raise RuntimeError("Quality policies are not nested")
    return {"total": int(len(quality)),
            "excluded": {k: int(v.sum()) for k, v in masks.items()},
            "hard_only": int(np.sum(masks['hard'] & ~masks['default'])),
            "hardest_only": int(np.sum(masks['hardest'] & ~masks['hard'])),
            "flagged_by_bit": {name: int(np.sum((quality & bit) != 0)) for bit, name in BIT_NAMES.items()}}


def block_bootstrap_scatter_ratio(flux, quality, policy='default', block_length=12,
                                  n_resamples=500, seed=20261102):
    """Paired circular-block resampling of flux and QUALITY, including flagged fraction."""
    flux = np.asarray(flux, dtype=float)
    quality = np.asarray(quality)
    n = len(flux)
    if flux.ndim != 1 or quality.shape != flux.shape or n < 12 or not np.all(np.isfinite(flux)):
        raise ValueError("Aligned finite one-dimensional flux and quality required (n>=12)")
    if not np.issubdtype(quality.dtype, np.integer) or np.any(quality < 0):
        raise ValueError("QUALITY must be nonnegative integers")
    if not isinstance(block_length, int) or not 1 <= block_length <= n:
        raise ValueError("Invalid block length")
    if not isinstance(n_resamples, int) or n_resamples < 20:
        raise ValueError("At least 20 resamples required")
    keep = apply_mask_policy(quality, policy)
    if np.sum(keep) < 2:
        raise ValueError("Too few retained cadences")
    point = scatter_comparison(flux, keep).scatter_ratio_rms
    if not np.isfinite(point):
        raise ValueError("Zero scatter in retained data")
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(n_resamples):
        starts = rng.integers(0, n, size=(n + block_length - 1)//block_length)
        indices = ((starts[:, None] + np.arange(block_length)) % n).ravel()[:n]
        f, q = flux[indices], quality[indices]
        k = apply_mask_policy(q, policy)
        if k.sum() < 2:
            continue
        value = scatter_comparison(f, k).scatter_ratio_rms
        if np.isfinite(value):
            values.append(value)
    if len(values) < n_resamples * .8:
        raise ValueError("Too many degenerate bootstrap resamples")
    lo, hi = np.quantile(values, [.025, .975])
    return {"estimate": float(point), "ci_low": float(lo), "ci_high": float(hi),
            "valid_resamples": len(values), "requested_resamples": n_resamples}


def circular_shift_background_test(background, quality, bit=SCATTERED_LIGHT_BIT):
    """Exact cyclic-shift alignment test; not valid for nonstationary backgrounds."""
    background = np.asarray(background, dtype=float)
    quality = np.asarray(quality)
    if background.ndim != 1 or quality.shape != background.shape or len(background) < 8:
        raise ValueError("Aligned arrays with at least eight cadences required")
    if not np.all(np.isfinite(background)) or not np.issubdtype(quality.dtype, np.integer) or np.any(quality < 0):
        raise ValueError("Finite backgrounds and nonnegative integer quality required")
    if not isinstance(bit, int) or bit <= 0 or bit & (bit-1):
        raise ValueError("bit must be one positive power of two")
    flagged = (quality & bit) != 0
    if flagged.sum() == 0 or flagged.sum() == len(flagged):
        raise ValueError("Both flagged and unflagged cadences required")
    def contrast(mask):
        return float(np.median(background[mask]) - np.median(background[~mask]))
    observed = contrast(flagged)
    null = np.array([contrast(np.roll(flagged, shift)) for shift in range(1, len(flagged))])
    p = (1 + int(np.sum(np.abs(null) >= abs(observed) - 1e-12))) / len(flagged)
    return {"background_median_difference": observed, "two_sided_shift_p": float(p),
            "null_count": len(null), "null_95_abs": float(np.quantile(abs(null), .95))}
