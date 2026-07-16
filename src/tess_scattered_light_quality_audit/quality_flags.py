"""TESS SPOC QUALITY bitmask constants and mask-policy helpers.

Bit values verified against lightkurve.utils.TessQualityFlags (which cites
SDPDD EXP-TESS-ARC-ICD-TM-0014 Table 28), cross-checked against real TESS
Sector 1 and Sector 40 Data Release Notes (see IMPLEMENTATION_PLAN.md
Section 1 for source URLs). Key finding: bit 12/Straylight (predicted,
FFI-only) is disabled for 2-minute/20-second products; bit 13/Straylight2
("Scattered Light Exclude", value 4096) is the SPOC-pipeline empirical
per-target flag actually active in 2-minute light curves and is the primary
scattered-light indicator used throughout this project.
"""
from __future__ import annotations

import numpy as np

AttitudeTweak = 1
SafeMode = 2
CoarsePoint = 4
EarthPoint = 8
Argabrightening = 16
Desat = 32
ApertureCosmic = 64
ManualExclude = 128
Discontinuity = 256
ImpulsiveOutlier = 512
CollateralCosmic = 1024
Straylight = 2048
Straylight2 = 4096
PlanetSearchExclude = 8192
BadCalibrationExclude = 16384
InsufficientTargets = 32768

BIT_NAMES: dict[int, str] = {
    AttitudeTweak: "AttitudeTweak",
    SafeMode: "SafeMode",
    CoarsePoint: "CoarsePoint",
    EarthPoint: "EarthPoint",
    Argabrightening: "Argabrightening",
    Desat: "Desat",
    ApertureCosmic: "ApertureCosmic",
    ManualExclude: "ManualExclude",
    Discontinuity: "Discontinuity",
    ImpulsiveOutlier: "ImpulsiveOutlier",
    CollateralCosmic: "CollateralCosmic",
    Straylight: "Straylight",
    Straylight2: "Straylight2",
    PlanetSearchExclude: "PlanetSearchExclude",
    BadCalibrationExclude: "BadCalibrationExclude",
    InsufficientTargets: "InsufficientTargets",
}

# The three named mask policies from Lightkurve, used as the "quality-mask
# policies" compared in this audit's central scientific question.
DEFAULT_BITMASK = 17087
HARD_BITMASK = 24319
HARDEST_BITMASK = 65535

MASK_POLICIES: dict[str, int] = {
    "default": DEFAULT_BITMASK,
    "hard": HARD_BITMASK,
    "hardest": HARDEST_BITMASK,
}

# The primary scattered-light-specific bit used for the audit's headline
# comparison, per the real Sector 40 DRN (see module docstring).
SCATTERED_LIGHT_BIT = Straylight2


def decode_flags(quality: int) -> list[str]:
    """Return the sorted list of bit names set in a single QUALITY value."""
    return [name for bit, name in sorted(BIT_NAMES.items()) if quality & bit]


def is_flagged(quality: np.ndarray, bitmask: int) -> np.ndarray:
    """Boolean array: True where a cadence's QUALITY value intersects bitmask."""
    quality = np.asarray(quality, dtype=np.int64)
    return (quality & np.int64(bitmask)) != 0


def apply_mask_policy(quality: np.ndarray, policy: str) -> np.ndarray:
    """Boolean 'keep' mask (True = cadence retained) for a named mask policy."""
    if policy not in MASK_POLICIES:
        raise ValueError(f"unknown mask policy '{policy}', expected one of {list(MASK_POLICIES)}")
    return ~is_flagged(quality, MASK_POLICIES[policy])
