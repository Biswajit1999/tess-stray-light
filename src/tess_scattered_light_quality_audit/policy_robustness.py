"""Independent TESS quality-mask diagnostics; no changes to production masking.

All numerical examples are synthetic. A zero-flag binomial calculation assumes
independent trials and is only a sensitivity scenario, not a population bound
for the repository's deterministically selected three Sector 40 targets.
"""
from __future__ import annotations

import numpy as np

from tess_scattered_light_quality_audit.quality_flags import (
    MASK_POLICIES, SCATTERED_LIGHT_BIT, apply_mask_policy,
)


def _quality(quality: np.ndarray) -> np.ndarray:
    q = np.asarray(quality)
    if q.ndim != 1 or q.size == 0 or not np.issubdtype(q.dtype, np.integer):
        raise ValueError("QUALITY must be a nonempty one-dimensional integer array")
    if np.any(q < 0):
        raise ValueError("QUALITY values must be nonnegative")
    return q.astype(np.int64)


def policy_exclusion_audit(quality: np.ndarray) -> dict:
    """Count exclusions and exclusive additions between nested mask policies."""
    q = _quality(quality)
    excluded = {name: ~apply_mask_policy(q, name) for name in MASK_POLICIES}
    names = ("default", "hard", "hardest")
    if any(np.any(excluded[a] & ~excluded[b]) for a, b in zip(names[:-1], names[1:])):
        raise ValueError("configured mask policies are not nested")
    return {
        "n_cadences": int(q.size),
        "straylight2_flagged": int(np.count_nonzero(q & SCATTERED_LIGHT_BIT)),
        "excluded_by_policy": {k: int(np.count_nonzero(v)) for k, v in excluded.items()},
        "newly_excluded_hard_vs_default": int(np.count_nonzero(excluded["hard"] & ~excluded["default"])),
        "newly_excluded_hardest_vs_hard": int(np.count_nonzero(excluded["hardest"] & ~excluded["hard"])),
        "straylight2_retained_by_default": int(np.count_nonzero(
            (q & SCATTERED_LIGHT_BIT != 0) & ~excluded["default"])),
    }


def zero_flag_upper_sensitivity(n_cadences: int, confidence: float = 0.95,
                                independent_block_lengths=(1, 10, 30)) -> list[dict]:
    """Exact zero-event upper bound under hypothetical independent blocks.

    P(X=0|p)=(1-p)^n, hence p_upper=1-(1-confidence)^(1/n).
    A block length is NOT an estimated correlation length; these are only
    alternative effective-sample-size assumptions for zero observed events.
    """
    if not isinstance(n_cadences, int) or n_cadences < 1 or not (0 < confidence < 1):
        raise ValueError("n_cadences positive integer; confidence in (0,1)")
    rows = []
    for length in independent_block_lengths:
        if not isinstance(length, int) or length < 1:
            raise ValueError("block lengths must be positive integers")
        effective = int(np.ceil(n_cadences / length))
        upper = -np.expm1(np.log1p(-confidence) / effective)
        rows.append({"hypothetical_block_length": length, "effective_trials": effective,
                     "zero_event_upper_fraction": float(upper)})
    return rows


def _scatter_ratio(flux: np.ndarray, keep: np.ndarray) -> float:
    finite = np.isfinite(flux)
    all_flux = flux[finite]
    kept_flux = flux[finite & keep]
    if all_flux.size < 3 or kept_flux.size < 3:
        raise ValueError("at least three finite cadences must survive each mask")
    std_all = float(np.std(all_flux))
    std_keep = float(np.std(kept_flux))
    if std_keep <= 0 or not np.isfinite(std_keep):
        raise ValueError("retained flux has zero or nonfinite scatter")
    return std_all / std_keep


def paired_block_bootstrap(
    flux: np.ndarray, quality: np.ndarray, block_length: int = 20,
    n_resamples: int = 600, seed: int = 20261029,
) -> dict:
    """Circular moving-block bootstrap of hard-minus-default scatter ratios.

    The same sampled indices are used for both masks. No confidence-interval
    coverage is asserted when flagged intervals are rare or nonstationary.
    """
    q = _quality(quality)
    f = np.asarray(flux, dtype=float)
    if f.shape != q.shape or not np.all(np.isfinite(f)):
        raise ValueError("flux must be finite and have QUALITY's shape")
    if not isinstance(block_length, int) or not (1 <= block_length <= q.size // 3):
        raise ValueError("block length must be between 1 and n/3")
    if n_resamples < 30:
        raise ValueError("at least 30 resamples required")

    def contrast(x: np.ndarray, flags: np.ndarray) -> float:
        return _scatter_ratio(x, apply_mask_policy(flags, "hard")) - _scatter_ratio(
            x, apply_mask_policy(flags, "default"))

    point = contrast(f, q)
    rng = np.random.default_rng(seed)
    results = []
    n_blocks = int(np.ceil(q.size / block_length))
    for _ in range(n_resamples):
        starts = rng.integers(0, q.size, size=n_blocks)
        idx = ((starts[:, None] + np.arange(block_length)) % q.size).ravel()[:q.size]
        try:
            results.append(contrast(f[idx], q[idx]))
        except ValueError:
            # Degenerate resamples are counted, never replaced with zero.
            pass
    if len(results) < int(0.8 * n_resamples):
        raise ValueError("too many degenerate block resamples for reliable diagnostics")
    return {
        "hard_minus_default_ratio": float(point),
        "bootstrap_p025": float(np.quantile(results, 0.025)),
        "bootstrap_p975": float(np.quantile(results, 0.975)),
        "valid_resamples": len(results), "attempted_resamples": int(n_resamples),
        "block_length_cadences": int(block_length),
    }
