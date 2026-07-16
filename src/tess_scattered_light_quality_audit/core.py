"""Pipeline orchestration: per-target processing for the real-data run, plus
the retained starter smoke-test functions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from tess_scattered_light_quality_audit.config import AnalysisConfig
from tess_scattered_light_quality_audit.exceptions import (
    ConvergenceError,
    DataSchemaError,
    InsufficientDataError,
)
from tess_scattered_light_quality_audit.lightcurve_metrics import (
    ScatterComparison,
    background_flux_correlation,
    scatter_comparison,
)
from tess_scattered_light_quality_audit.mast_fetch import load_lightcurve
from tess_scattered_light_quality_audit.quality_flags import (
    MASK_POLICIES,
    SCATTERED_LIGHT_BIT,
    apply_mask_policy,
    is_flagged,
)


@dataclass(frozen=True)
class Summary:
    count: int
    median: float
    mad: float


def validate_numeric(values: np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.ndim != 1:
        raise ValueError("values must be one-dimensional")
    if arr.size == 0:
        raise ValueError("values must not be empty")
    if not np.all(np.isfinite(arr)):
        raise ValueError("values contain non-finite entries")
    return arr


def robust_summary(values: np.ndarray) -> Summary:
    arr = validate_numeric(values)
    median = float(np.median(arr))
    mad = float(np.median(np.abs(arr - median)))
    return Summary(count=int(arr.size), median=median, mad=mad)


def demo_series(seed: int = 20260713, size: int = 128) -> np.ndarray:
    """Return deterministic synthetic data labelled only for smoke testing."""
    if size < 8:
        raise ValueError("size must be at least 8")
    rng = np.random.default_rng(seed)
    return rng.normal(loc=0.0, scale=1.0, size=size)


@dataclass
class TargetResult:
    tic_id: str
    scatter_by_policy: dict[str, ScatterComparison] = field(default_factory=dict)
    straylight2_fraction: float = 0.0
    background_correlation: dict[str, float] | None = None


@dataclass
class PipelineResult:
    targets: list[TargetResult]
    warnings: list[str] = field(default_factory=list)


def run_pipeline(manifest_rows: list[dict[str, str]], raw_dir: Path, config: AnalysisConfig) -> PipelineResult:
    """Run the real-data pipeline over every target listed in the manifest.

    Per-target failures (missing file, malformed FITS, insufficient
    cadences, ill-conditioned fit) are caught and converted to warnings;
    a single bad target never aborts the whole run. Raises
    `InsufficientDataError` immediately if the manifest is empty.
    """
    if not manifest_rows:
        raise InsufficientDataError("run_pipeline: manifest_rows is empty")

    targets: list[TargetResult] = []
    warnings: list[str] = []

    for row in manifest_rows:
        product_id = row.get("product_id", "UNKNOWN")
        lc_path = Path(raw_dir) / f"{product_id}.fits"
        try:
            lc = load_lightcurve(lc_path)

            result = TargetResult(tic_id=lc.tic_id)
            for policy_name in MASK_POLICIES:
                keep_mask = apply_mask_policy(lc.quality, policy_name)
                result.scatter_by_policy[policy_name] = scatter_comparison(lc.flux, keep_mask)

            flagged = is_flagged(lc.quality, SCATTERED_LIGHT_BIT)
            result.straylight2_fraction = float(np.mean(flagged))

            try:
                result.background_correlation = background_flux_correlation(lc.background, lc.flux, flagged)
            except InsufficientDataError as exc:
                warnings.append(f"{product_id}: background correlation skipped: {exc}")

            targets.append(result)
        except (InsufficientDataError, ConvergenceError, DataSchemaError) as exc:
            warnings.append(f"{product_id}: skipped: {exc}")
            continue

    return PipelineResult(targets=targets, warnings=warnings)
