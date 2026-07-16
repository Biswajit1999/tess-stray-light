from __future__ import annotations

import pytest
from astropy.io import fits

from tess_scattered_light_quality_audit.config import load_config
from tess_scattered_light_quality_audit.core import run_pipeline
from tess_scattered_light_quality_audit.exceptions import InsufficientDataError
from tess_scattered_light_quality_audit.synthetic import SyntheticLightCurveSpec, make_synthetic_lightcurve


def _write_synthetic_fits(path, lc, ticid=1):
    primary = fits.PrimaryHDU()
    primary.header["TICID"] = ticid
    primary.header["SECTOR"] = 40
    cols = [
        fits.Column(name="TIME", array=lc.time, format="D"),
        fits.Column(name="PDCSAP_FLUX", array=lc.flux, format="D"),
        fits.Column(name="PDCSAP_FLUX_ERR", array=lc.flux_err, format="D"),
        fits.Column(name="QUALITY", array=lc.quality, format="J"),
        fits.Column(name="SAP_BKG", array=lc.background, format="D"),
    ]
    table_hdu = fits.BinTableHDU.from_columns(cols)
    fits.HDUList([primary, table_hdu]).writeto(path, overwrite=True)


def test_run_pipeline_injection_recovery_detects_known_excess_scatter(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    config = load_config("config/analysis.yml")

    lc = make_synthetic_lightcurve(SyntheticLightCurveSpec(scatter_multiplier=5.0), seed=10)
    _write_synthetic_fits(raw_dir / "synth1.fits", lc)

    manifest_rows = [{"product_id": "synth1"}]
    result = run_pipeline(manifest_rows, raw_dir, config)

    assert len(result.targets) == 1
    # lightkurve's "default" mask does not include Straylight2 (verified:
    # DEFAULT_BITMASK & Straylight2 == 0); use "hard", which does.
    hard_cmp = result.targets[0].scatter_by_policy["hard"]
    # The injected excess-scatter segment is flagged and excluded by the
    # hard mask; excluding it should reduce scatter relative to all cadences.
    assert hard_cmp.scatter_ratio_rms > 1.0


def test_run_pipeline_null_control_zero_injection_recovers_near_baseline(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    config = load_config("config/analysis.yml")

    lc = make_synthetic_lightcurve(SyntheticLightCurveSpec(scatter_multiplier=1.0, background_offset=0.0), seed=11)
    _write_synthetic_fits(raw_dir / "synth1.fits", lc)

    manifest_rows = [{"product_id": "synth1"}]
    result = run_pipeline(manifest_rows, raw_dir, config)

    hard_cmp = result.targets[0].scatter_by_policy["hard"]
    # With no real injected excess scatter, the ratio should be close to 1.
    assert abs(hard_cmp.scatter_ratio_rms - 1.0) < 0.3


def test_run_pipeline_raises_on_empty_manifest(tmp_path):
    config = load_config("config/analysis.yml")
    with pytest.raises(InsufficientDataError):
        run_pipeline([], tmp_path, config)


def test_run_pipeline_warns_not_crashes_on_missing_file(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    config = load_config("config/analysis.yml")
    manifest_rows = [{"product_id": "missing_target"}]
    result = run_pipeline(manifest_rows, raw_dir, config)
    assert len(result.targets) == 0
    assert any("missing_target" in w for w in result.warnings)
