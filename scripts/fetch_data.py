"""Deterministic, provenance-recording fetch of real public TESS SPOC
2-minute cadence light curve FITS files.

Queries MAST directly (no fabricated metadata) via astroquery.mast.Observations,
the same access pattern verified in hst-acs-two-axis-cte-audit and
hst-wfc3ir-ramp-linearity-audit. Sector 40 is used (not Sector 1) because the
Straylight2 (bit 13, value 4096) scattered-light-exclude flag did not exist
in Sector 1's early SPOC pipeline version -- see IMPLEMENTATION_PLAN.md
Section 1 for the verified literature basis.

This script performs real network downloads and must only be invoked with
explicit user authorization for the session.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from tess_scattered_light_quality_audit.exceptions import ArchiveAccessError
from tess_scattered_light_quality_audit.logging_utils import get_logger
from tess_scattered_light_quality_audit.provenance import ManifestRow, append_manifest_row, sha256_file

LOGGER = get_logger(__name__)

SECTOR = 40
SOURCE_URL = "https://mast.stsci.edu"
LICENCE_TERMS = (
    "STScI/MAST public TESS archive data (dataRights=PUBLIC), no proprietary period; "
    "standard STScI archive usage terms apply, https://archive.stsci.edu/copyright.html"
)


def _select_observations(n_targets: int):
    try:
        from astroquery.mast import Observations
    except ImportError as exc:  # pragma: no cover - environment guard
        raise ArchiveAccessError("astroquery is not installed in this environment") from exc

    try:
        obs = Observations.query_criteria(
            obs_collection="TESS",
            dataproduct_type="timeseries",
            sequence_number=SECTOR,
            calib_level=3,
        )
    except Exception as exc:  # noqa: BLE001
        raise ArchiveAccessError(f"MAST query failed: {exc}") from exc

    if len(obs) == 0:
        raise ArchiveAccessError(f"MAST query for TESS Sector {SECTOR} timeseries returned zero observations")

    obs.sort("target_name")
    selected = obs[:n_targets]
    for row in selected:
        if str(row["dataRights"]) != "PUBLIC":
            raise ArchiveAccessError(
                f"observation {row['target_name']} is not PUBLIC (dataRights={row['dataRights']!r}); refusing to download"
            )
    return selected


def _download_lc(observations, out_dir: Path) -> list[Path]:
    from astroquery.mast import Observations

    out_dir.mkdir(parents=True, exist_ok=True)
    downloaded: list[Path] = []
    for row in observations:
        try:
            products = Observations.get_product_list(observations[observations["target_name"] == row["target_name"]])
        except Exception as exc:  # noqa: BLE001
            raise ArchiveAccessError(f"failed to list products for {row['target_name']}: {exc}") from exc

        subset = products[
            (products["productSubGroupDescription"] == "LC")
            & (products["dataRights"] == "PUBLIC")
        ]
        if len(subset) == 0:
            LOGGER.warning("no PUBLIC LC product found for %s; skipping", row["target_name"])
            continue

        download_manifest = Observations.download_products(subset, download_dir=str(out_dir))
        for local_path_str in download_manifest["Local Path"]:
            downloaded.append(Path(local_path_str))
    return downloaded


def _flatten(paths: list[Path], out_dir: Path) -> list[Path]:
    import shutil

    flat_paths = []
    for path in paths:
        flat_path = out_dir / path.name
        if path != flat_path:
            shutil.move(str(path), str(flat_path))
        flat_paths.append(flat_path)
    mast_download_dir = out_dir / "mastDownload"
    if mast_download_dir.is_dir():
        shutil.rmtree(mast_download_dir, ignore_errors=True)
    return flat_paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n-targets", type=int, default=3)
    parser.add_argument("--out-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--manifest", type=Path, default=Path("data/manifest.csv"))
    parser.add_argument(
        "--i-have-authorization",
        action="store_true",
        help=(
            "Required flag confirming the operator has explicitly authorized this "
            "real network download in the current session."
        ),
    )
    args = parser.parse_args()

    if not args.i_have_authorization:
        raise SystemExit(
            "Refusing to download real archive data without --i-have-authorization. "
            "This flag exists so the download only runs after the operator has "
            "explicitly confirmed it in the current session."
        )

    selected = _select_observations(args.n_targets)
    LOGGER.info("Selected %d observations", len(selected))

    downloaded = _download_lc(selected, args.out_dir)
    if not downloaded:
        raise ArchiveAccessError("no PUBLIC LC products were successfully identified for download")
    downloaded = _flatten(downloaded, args.out_dir)
    retrieved_utc = datetime.now(timezone.utc).isoformat()

    for local_path in downloaded:
        if not local_path.is_file():
            raise ArchiveAccessError(f"expected downloaded file missing: {local_path}")
        digest = sha256_file(local_path)
        size = local_path.stat().st_size
        row = ManifestRow(
            product_id=local_path.stem,
            source="MAST/TESS",
            source_url=SOURCE_URL,
            retrieved_utc=retrieved_utc,
            sha256=digest,
            file_size_bytes=size,
            selection_reason=(
                f"deterministic first-{args.n_targets} public TESS Sector {SECTOR} "
                "SPOC 2-minute LC target sample, sorted by target_name"
            ),
            licence_or_terms=LICENCE_TERMS,
        )
        append_manifest_row(args.manifest, row)
        LOGGER.info("Recorded manifest row for %s (%d bytes)", local_path.name, size)

    print(f"Downloaded and recorded {len(downloaded)} LC files under {args.out_dir}")


if __name__ == "__main__":
    main()
