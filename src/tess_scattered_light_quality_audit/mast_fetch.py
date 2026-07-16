"""Loading SPOC 2-minute cadence TESS light curve FITS files.

Shared by scripts/fetch_data.py (post-download validation) and core.py (the
real-data pipeline), isolating the FITS structure so it is testable without
a real network call.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from astropy.io import fits

from tess_scattered_light_quality_audit.exceptions import DataSchemaError

REQUIRED_COLUMNS = ("TIME", "PDCSAP_FLUX", "PDCSAP_FLUX_ERR", "QUALITY", "SAP_BKG")


@dataclass(frozen=True)
class LightCurve:
    tic_id: str
    sector: int
    camera: int
    ccd: int
    time: np.ndarray
    flux: np.ndarray
    flux_err: np.ndarray
    quality: np.ndarray
    background: np.ndarray


def load_lightcurve(path: str | Path) -> LightCurve:
    """Load a SPOC 2-minute light curve FITS file into a `LightCurve`.

    Raises `DataSchemaError` for a missing file or missing/malformed
    required columns, rather than silently returning partial data.
    """
    fits_path = Path(path)
    if not fits_path.is_file():
        raise DataSchemaError(f"light curve file not found: {fits_path}")

    try:
        with fits.open(fits_path) as hdul:
            if len(hdul) < 2:
                raise DataSchemaError(f"{fits_path}: expected a LIGHTCURVE extension, found {len(hdul)} HDUs")
            header0 = hdul[0].header
            data = hdul[1].data
            colnames = set(data.columns.names) if data is not None else set()
            missing = [c for c in REQUIRED_COLUMNS if c not in colnames]
            if missing:
                raise DataSchemaError(f"{fits_path}: missing required columns: {missing}")

            tic_id = str(header0.get("TICID", header0.get("OBJECT", "UNKNOWN")))
            sector = int(header0.get("SECTOR", -1))
            camera = int(header0.get("CAMERA", -1))
            ccd = int(header0.get("CCD", -1))

            time = np.asarray(data["TIME"], dtype=float)
            flux = np.asarray(data["PDCSAP_FLUX"], dtype=float)
            flux_err = np.asarray(data["PDCSAP_FLUX_ERR"], dtype=float)
            quality = np.asarray(data["QUALITY"], dtype=np.int64)
            background = np.asarray(data["SAP_BKG"], dtype=float)
    except OSError as exc:
        raise DataSchemaError(f"{fits_path}: could not be opened as FITS: {exc}") from exc

    if time.size == 0:
        raise DataSchemaError(f"{fits_path}: light curve has zero cadences")

    return LightCurve(
        tic_id=tic_id, sector=sector, camera=camera, ccd=ccd,
        time=time, flux=flux, flux_err=flux_err, quality=quality, background=background,
    )
