from __future__ import annotations

import numpy as np
import pytest
from astropy.io import fits

from tess_scattered_light_quality_audit.exceptions import DataSchemaError
from tess_scattered_light_quality_audit.mast_fetch import load_lightcurve
from tess_scattered_light_quality_audit.synthetic import SyntheticLightCurveSpec, make_synthetic_lightcurve


def _write_synthetic_fits(path, lc, ticid=12345, sector=40, camera=1, ccd=1):
    primary = fits.PrimaryHDU()
    primary.header["TICID"] = ticid
    primary.header["SECTOR"] = sector
    primary.header["CAMERA"] = camera
    primary.header["CCD"] = ccd
    cols = [
        fits.Column(name="TIME", array=lc.time, format="D"),
        fits.Column(name="PDCSAP_FLUX", array=lc.flux, format="D"),
        fits.Column(name="PDCSAP_FLUX_ERR", array=lc.flux_err, format="D"),
        fits.Column(name="QUALITY", array=lc.quality, format="J"),
        fits.Column(name="SAP_BKG", array=lc.background, format="D"),
    ]
    table_hdu = fits.BinTableHDU.from_columns(cols)
    fits.HDUList([primary, table_hdu]).writeto(path, overwrite=True)


def test_load_lightcurve_reads_synthetic_fits_correctly(tmp_path):
    lc = make_synthetic_lightcurve(SyntheticLightCurveSpec(), seed=5)
    path = tmp_path / "synth_lc.fits"
    _write_synthetic_fits(path, lc, ticid=99, sector=40)

    loaded = load_lightcurve(path)
    assert loaded.tic_id == "99"
    assert loaded.sector == 40
    assert loaded.time.size == lc.time.size
    np.testing.assert_allclose(loaded.flux, lc.flux)
    np.testing.assert_array_equal(loaded.quality, lc.quality)


def test_load_lightcurve_missing_file_raises():
    with pytest.raises(DataSchemaError):
        load_lightcurve("does_not_exist.fits")


def test_load_lightcurve_missing_column_raises(tmp_path):
    primary = fits.PrimaryHDU()
    cols = [fits.Column(name="TIME", array=np.arange(10, dtype=float), format="D")]
    table_hdu = fits.BinTableHDU.from_columns(cols)
    path = tmp_path / "malformed.fits"
    fits.HDUList([primary, table_hdu]).writeto(path, overwrite=True)

    with pytest.raises(DataSchemaError):
        load_lightcurve(path)
