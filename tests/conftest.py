from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from tess_scattered_light_quality_audit.synthetic import SyntheticLightCurveSpec, make_synthetic_lightcurve


@pytest.fixture
def synthetic_lc():
    return make_synthetic_lightcurve(SyntheticLightCurveSpec(), seed=2000)
