from __future__ import annotations

import pytest

from tess_scattered_light_quality_audit.quality_flags import Straylight2, is_flagged
from tess_scattered_light_quality_audit.synthetic import SyntheticLightCurveSpec, make_synthetic_lightcurve


def test_synthetic_lightcurve_flags_exactly_injected_segment():
    spec = SyntheticLightCurveSpec(n_cadences=200, injected_start=50, injected_end=80)
    lc = make_synthetic_lightcurve(spec, seed=1)
    flagged = is_flagged(lc.quality, Straylight2)
    assert flagged[50:80].all()
    assert not flagged[:50].any()
    assert not flagged[80:].any()


def test_synthetic_lightcurve_is_deterministic_for_fixed_seed():
    spec = SyntheticLightCurveSpec()
    lc1 = make_synthetic_lightcurve(spec, seed=42)
    lc2 = make_synthetic_lightcurve(spec, seed=42)
    assert (lc1.flux == lc2.flux).all()


def test_synthetic_lightcurve_rejects_invalid_injection_range():
    with pytest.raises(ValueError):
        make_synthetic_lightcurve(SyntheticLightCurveSpec(injected_start=300, injected_end=100))


def test_synthetic_lightcurve_rejects_too_few_cadences():
    with pytest.raises(ValueError):
        make_synthetic_lightcurve(SyntheticLightCurveSpec(n_cadences=4, injected_start=0, injected_end=2))
