"""Flux-scatter and background metrics used to compare TESS quality-mask policies.

All statistics operate on normalized flux (flux / median(flux)) so RMS/MAD
are dimensionless and comparable across targets of different brightness.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from tess_scattered_light_quality_audit.exceptions import InsufficientDataError


def normalized_flux(flux: np.ndarray) -> np.ndarray:
    arr = np.asarray(flux, dtype=float)
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        raise InsufficientDataError("normalized_flux: no finite flux values")
    median = np.median(finite)
    if median == 0:
        raise InsufficientDataError("normalized_flux: median flux is zero, cannot normalize")
    return arr / median


def rms(values: np.ndarray) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        raise InsufficientDataError("rms: no finite values")
    return float(np.sqrt(np.mean((arr - np.mean(arr)) ** 2)))


def mad(values: np.ndarray) -> float:
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        raise InsufficientDataError("mad: no finite values")
    med = np.median(arr)
    return float(np.median(np.abs(arr - med)))


@dataclass(frozen=True)
class ScatterComparison:
    n_all: int
    n_kept: int
    n_excluded: int
    rms_all: float
    rms_kept: float
    mad_all: float
    mad_kept: float
    scatter_ratio_rms: float
    scatter_ratio_mad: float


def scatter_comparison(flux: np.ndarray, keep_mask: np.ndarray) -> ScatterComparison:
    """Compare flux scatter before/after applying a quality-mask keep-mask.

    scatter_ratio > 1 means the flagged (excluded) cadences were
    contributing excess scatter relative to the kept cadences.
    """
    norm = normalized_flux(flux)
    keep_mask = np.asarray(keep_mask, dtype=bool)
    if keep_mask.shape != norm.shape:
        raise InsufficientDataError("scatter_comparison: keep_mask shape does not match flux shape")

    kept = norm[keep_mask & np.isfinite(norm)]
    if kept.size < 2:
        raise InsufficientDataError("scatter_comparison: fewer than 2 cadences survive the mask policy")

    rms_all = rms(norm)
    rms_kept = rms(kept)
    mad_all = mad(norm)
    mad_kept = mad(kept)

    return ScatterComparison(
        n_all=int(norm.size),
        n_kept=int(kept.size),
        n_excluded=int(norm.size - kept.size),
        rms_all=rms_all,
        rms_kept=rms_kept,
        mad_all=mad_all,
        mad_kept=mad_kept,
        scatter_ratio_rms=rms_all / rms_kept if rms_kept > 0 else float("nan"),
        scatter_ratio_mad=mad_all / mad_kept if mad_kept > 0 else float("nan"),
    )


def background_flux_correlation(background: np.ndarray, flux: np.ndarray, flagged: np.ndarray) -> dict[str, float]:
    """Median background level for flagged vs. unflagged cadences.

    A positive elevation (flagged median > unflagged median) is consistent
    with scattered-light-flagged cadences coinciding with elevated
    background flux, the physical mechanism the quality bit is meant to
    capture.
    """
    background = np.asarray(background, dtype=float)
    flagged = np.asarray(flagged, dtype=bool)
    finite = np.isfinite(background)

    flagged_vals = background[flagged & finite]
    unflagged_vals = background[~flagged & finite]
    if flagged_vals.size == 0 or unflagged_vals.size == 0:
        raise InsufficientDataError(
            "background_flux_correlation: need at least one finite background value in both flagged and unflagged groups"
        )

    med_flagged = float(np.median(flagged_vals))
    med_unflagged = float(np.median(unflagged_vals))
    return {
        "median_background_flagged": med_flagged,
        "median_background_unflagged": med_unflagged,
        "background_elevation_ratio": med_flagged / med_unflagged if med_unflagged != 0 else float("nan"),
        "n_flagged": float(flagged_vals.size),
        "n_unflagged": float(unflagged_vals.size),
    }
