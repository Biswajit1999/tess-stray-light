"""Run the TESS scattered-light quality-flag audit: either the synthetic
--demo smoke path, or the real-data pipeline over data/manifest.csv +
data/raw/.

Peak memory is measured with the stdlib `tracemalloc` (Python-level
allocations) rather than a full process-RSS profiler such as psutil, which
is not part of this project's pinned dependency set.
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
import tracemalloc
from pathlib import Path

import numpy as np

from tess_scattered_light_quality_audit import __version__
from tess_scattered_light_quality_audit.config import load_config
from tess_scattered_light_quality_audit.core import demo_series, robust_summary, run_pipeline
from tess_scattered_light_quality_audit.exceptions import ProjectError
from tess_scattered_light_quality_audit.logging_utils import get_logger
from tess_scattered_light_quality_audit.provenance import get_git_commit, read_manifest, sha256_config
from tess_scattered_light_quality_audit.results_io import Metric, write_summary

LOGGER = get_logger(__name__)


def _write_benchmark(path: Path, label: str, wall_time_s: float, peak_memory_mib: float, dataset_size: int) -> None:
    payload = {
        "label": label,
        "wall_time_seconds": wall_time_s,
        "peak_memory_mib": peak_memory_mib,
        "peak_memory_method": "tracemalloc (Python-level allocations, not full process RSS)",
        "dataset_size": dataset_size,
        "python_version": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "package_version": __version__,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else []
    existing.append(payload)
    path.write_text(json.dumps(existing, indent=2), encoding="utf-8")


def run_demo() -> None:
    tracemalloc.start()
    start = time.perf_counter()

    values = demo_series()
    summary = robust_summary(values)

    elapsed = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    out = Path("results")
    out.mkdir(exist_ok=True)
    metrics = [
        Metric(name="median", estimate=summary.median, units="dimensionless", sample_size=summary.count),
        Metric(name="median_absolute_deviation", estimate=summary.mad, units="dimensionless", sample_size=summary.count),
    ]
    payload = write_summary(
        out / "summary.json",
        project="TESS Scattered-Light Quality-Flag Audit (demo smoke test)",
        data_kind="synthetic_smoke_test",
        metrics=metrics,
        provenance={
            "config_sha256": None,
            "git_commit": get_git_commit(Path(__file__).resolve().parents[1]),
            "package_version": __version__,
        },
        warnings=[],
    )
    print(json.dumps(payload, indent=2))
    _write_benchmark(out / "benchmarks.json", "demo", elapsed, peak / (1024 * 1024), values.size)


def run_real_data(config_path: Path, manifest_path: Path, raw_dir: Path, results_dir: Path) -> None:
    config = load_config(config_path)
    try:
        manifest_rows = read_manifest(manifest_path)
    except ProjectError as exc:
        raise SystemExit(
            f"Cannot run the real-data pipeline: {exc}. Run scripts/fetch_data.py "
            "(with explicit operator authorization) first."
        ) from exc

    if not manifest_rows:
        raise SystemExit(
            "data/manifest.csv has no rows. Run scripts/fetch_data.py "
            "(with explicit operator authorization) before running the real-data pipeline."
        )

    tracemalloc.start()
    start = time.perf_counter()

    result = run_pipeline(manifest_rows, raw_dir, config)

    elapsed = time.perf_counter() - start
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    if not result.targets:
        raise SystemExit(
            f"Real-data pipeline produced zero usable targets ({len(result.warnings)} warnings). "
            "Check data/raw/ contains the files listed in data/manifest.csv."
        )

    straylight2_fractions = [t.straylight2_fraction for t in result.targets]
    metrics = [
        Metric(
            name="median_straylight2_fraction",
            estimate=float(np.median(straylight2_fractions)),
            units="dimensionless",
            sample_size=len(straylight2_fractions),
        ),
    ]
    for policy in ("default", "hard", "hardest"):
        ratios_rms = [
            t.scatter_by_policy[policy].scatter_ratio_rms
            for t in result.targets
            if policy in t.scatter_by_policy and np.isfinite(t.scatter_by_policy[policy].scatter_ratio_rms)
        ]
        if ratios_rms:
            metrics.append(
                Metric(
                    name=f"median_scatter_ratio_rms_{policy}",
                    estimate=float(np.median(ratios_rms)),
                    units="dimensionless",
                    sample_size=len(ratios_rms),
                )
            )
        n_excluded = [
            t.scatter_by_policy[policy].n_excluded for t in result.targets if policy in t.scatter_by_policy
        ]
        if n_excluded:
            metrics.append(
                Metric(
                    name=f"mean_n_excluded_{policy}",
                    estimate=float(np.mean(n_excluded)),
                    units="cadences",
                    sample_size=len(n_excluded),
                )
            )

    elevation_ratios = [
        t.background_correlation["background_elevation_ratio"]
        for t in result.targets
        if t.background_correlation is not None and np.isfinite(t.background_correlation["background_elevation_ratio"])
    ]
    if elevation_ratios:
        metrics.append(
            Metric(
                name="median_background_elevation_ratio_flagged_vs_unflagged",
                estimate=float(np.median(elevation_ratios)),
                units="dimensionless",
                sample_size=len(elevation_ratios),
            )
        )

    for policy in ("default", "hard", "hardest"):
        if len(result.targets) < config.validation.minimum_sample_size:
            result.warnings.append(
                f"policy '{policy}': n_targets={len(result.targets)} below minimum_sample_size="
                f"{config.validation.minimum_sample_size}"
            )

    provenance = {
        "config_sha256": sha256_config(config_path),
        "git_commit": get_git_commit(Path(__file__).resolve().parents[1]),
        "package_version": __version__,
        "n_targets_attempted": len(manifest_rows),
        "n_targets_processed": len(result.targets),
    }

    results_dir.mkdir(exist_ok=True)
    write_summary(
        results_dir / "summary.json",
        project=config.project.title,
        data_kind=config.input.data_mode,
        metrics=metrics,
        provenance=provenance,
        warnings=result.warnings,
    )
    (results_dir / "warnings.json").write_text(json.dumps(result.warnings, indent=2), encoding="utf-8")
    _write_benchmark(results_dir / "benchmarks.json", "real_data", elapsed, peak / (1024 * 1024), len(manifest_rows))
    print(f"Wrote {results_dir / 'summary.json'} ({len(metrics)} metrics, {len(result.warnings)} warnings)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="Run synthetic smoke data only")
    parser.add_argument("--config", type=Path, default=Path("config/analysis.yml"))
    parser.add_argument("--manifest", type=Path, default=Path("data/manifest.csv"))
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    args = parser.parse_args()

    if args.demo:
        run_demo()
        return

    run_real_data(args.config, args.manifest, args.raw_dir, args.results_dir)


if __name__ == "__main__":
    main()
