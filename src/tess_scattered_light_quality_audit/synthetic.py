"""Synthetic TESS-like light curve generator with a known injected
excess-scatter / elevated-background segment, flagged by a synthetic
QUALITY column subset carrying the Straylight2 bit.

Shared by pytest fixtures (conftest.py) and any `--demo` CLI path so there
is one source of truth for the injected ground truth.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from tess_scattered_light_quality_audit.quality_flags import Straylight2


@dataclass(frozen=True)
class SyntheticLightCurveSpec:
    n_cadences: int = 400
    baseline_flux: float = 10000.0
    baseline_noise_frac: float = 0.001
    injected_start: int = 250
    injected_end: int = 320
    scatter_multiplier: float = 5.0
    background_offset: float = 500.0
    baseline_background: float = 100.0


@dataclass(frozen=True)
class SyntheticLightCurve:
    time: np.ndarray
    flux: np.ndarray
    flux_err: np.ndarray
    quality: np.ndarray
    background: np.ndarray
    injected_start: int
    injected_end: int
    truth_scatter_multiplier: float
    truth_background_offset: float


def make_synthetic_lightcurve(spec: SyntheticLightCurveSpec = SyntheticLightCurveSpec(), seed: int = 20260713) -> SyntheticLightCurve:
    """Build a synthetic light curve with a known injected excess-scatter,
    elevated-background segment, flagged Straylight2 over exactly that
    segment.
    """
    if spec.n_cadences < 8:
        raise ValueError("n_cadences must be at least 8")
    if not (0 <= spec.injected_start < spec.injected_end <= spec.n_cadences):
        raise ValueError("injected_start/injected_end must define a valid sub-range of n_cadences")

    rng = np.random.default_rng(seed)
    time = np.arange(spec.n_cadences, dtype=float) * (2.0 / 60.0 / 24.0)  # 2-minute cadence in days

    noise_sigma = np.full(spec.n_cadences, spec.baseline_flux * spec.baseline_noise_frac)
    noise_sigma[spec.injected_start:spec.injected_end] *= spec.scatter_multiplier

    flux = spec.baseline_flux + rng.normal(0.0, noise_sigma)
    flux_err = noise_sigma.copy()

    background = np.full(spec.n_cadences, spec.baseline_background)
    background[spec.injected_start:spec.injected_end] += spec.background_offset
    background += rng.normal(0.0, spec.baseline_background * 0.01, size=spec.n_cadences)

    quality = np.zeros(spec.n_cadences, dtype=np.int64)
    quality[spec.injected_start:spec.injected_end] |= Straylight2

    return SyntheticLightCurve(
        time=time, flux=flux, flux_err=flux_err, quality=quality, background=background,
        injected_start=spec.injected_start, injected_end=spec.injected_end,
        truth_scatter_multiplier=spec.scatter_multiplier, truth_background_offset=spec.background_offset,
    )
