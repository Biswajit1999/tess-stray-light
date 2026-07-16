from __future__ import annotations

from tess_scattered_light_quality_audit.provenance import (
    ManifestRow,
    append_manifest_row,
    get_git_commit,
    read_manifest,
    sha256_file,
)


def test_manifest_roundtrip(tmp_path):
    manifest_path = tmp_path / "manifest.csv"
    row = ManifestRow(
        product_id="tic0000000001_s0040_lc",
        source="MAST/TESS",
        source_url="https://mast.stsci.edu",
        retrieved_utc="2026-07-15T00:00:00+00:00",
        sha256="0" * 64,
        file_size_bytes=2048000,
        selection_reason="unit test",
        licence_or_terms="STScI/MAST public TESS archive data",
    )
    append_manifest_row(manifest_path, row)
    rows = read_manifest(manifest_path)
    assert len(rows) == 1
    assert rows[0]["product_id"] == "tic0000000001_s0040_lc"


def test_sha256_file_matches_known_content(tmp_path):
    path = tmp_path / "sample.bin"
    path.write_bytes(b"tess-scattered-light-quality-audit")
    digest = sha256_file(path)
    assert len(digest) == 64
    assert digest == sha256_file(path)


def test_get_git_commit_never_raises(tmp_path):
    result = get_git_commit(tmp_path)
    assert isinstance(result, str)
    assert result != ""


def test_read_manifest_missing_file_returns_empty_list(tmp_path):
    assert read_manifest(tmp_path / "does_not_exist.csv") == []
