"""Generate the 5 required figures (docs/FIGURE_AND_UI_SPEC.md) as SVG + 300 dpi
PNG, each with a sidecar JSON recording git commit, config hash, sample size
and units.

--demo builds figures from the synthetic, clearly-labelled data model in
tess_scattered_light_quality_audit.synthetic. The real-data path reads
data/manifest.csv + data/raw/ and must only be run after
scripts/run_analysis.py (real mode) has produced validated results.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scienceplots  # noqa: F401

from tess_scattered_light_quality_audit import __version__
from tess_scattered_light_quality_audit.config import load_config
from tess_scattered_light_quality_audit.core import demo_series, run_pipeline
from tess_scattered_light_quality_audit.lightcurve_metrics import normalized_flux
from tess_scattered_light_quality_audit.mast_fetch import load_lightcurve
from tess_scattered_light_quality_audit.plotting import plot_demo
from tess_scattered_light_quality_audit.provenance import get_git_commit, read_manifest, sha256_config
from tess_scattered_light_quality_audit.quality_flags import (
    MASK_POLICIES,
    SCATTERED_LIGHT_BIT,
    apply_mask_policy,
    is_flagged,
)
from tess_scattered_light_quality_audit.synthetic import SyntheticLightCurveSpec, make_synthetic_lightcurve

plt.style.use(["science", "no-latex"])


def _sidecar(path: Path, *, data_kind: str, sample_size: int, units: str, config_path: Path, extra: dict | None = None) -> None:
    payload = {
        "figure": path.stem,
        "data_kind": data_kind,
        "sample_size": sample_size,
        "units": units,
        "git_commit": get_git_commit(Path(__file__).resolve().parents[1]),
        "config_sha256": sha256_config(config_path) if config_path.is_file() else None,
        "package_version": __version__,
    }
    if extra:
        payload.update(extra)
    path.with_suffix(".json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _save(fig, out_dir: Path, name: str) -> Path:
    svg_path = out_dir / f"{name}.svg"
    png_path = out_dir / f"{name}.png"
    fig.savefig(svg_path)
    fig.savefig(png_path, dpi=300)
    plt.close(fig)
    return png_path


def _fig_raw_masked(out_dir, config_path, data_kind, time, flux, quality, tag):
    keep = apply_mask_policy(quality, "default")
    flagged = is_flagged(quality, SCATTERED_LIGHT_BIT)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(time, flux, ".", color="lightgray", label="all cadences", ms=3)
    ax.plot(time[keep], flux[keep], ".", color="tab:blue", label="kept (default mask)", ms=3)
    ax.plot(time[flagged], flux[flagged], "x", color="tab:red", label="Straylight2 flagged", ms=5)
    ax.set_xlabel("Time (BTJD)")
    ax.set_ylabel("PDCSAP flux (e-/s)")
    ax.set_title(f"Raw vs. masked light curve - {tag} (n={time.size})")
    ax.legend(fontsize=8)
    path = _save(fig, out_dir, "fig01_raw_masked_lightcurve")
    _sidecar(path, data_kind=data_kind, sample_size=time.size, units="flux vs BTJD", config_path=config_path)


def _fig_quality_timeline(out_dir, config_path, data_kind, time, quality, tag):
    flagged = is_flagged(quality, SCATTERED_LIGHT_BIT)
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.fill_between(time, 0, flagged.astype(int), step="mid", color="tab:red", alpha=0.6)
    ax.set_xlabel("Time (BTJD)")
    ax.set_ylabel("Straylight2 flag")
    ax.set_yticks([0, 1])
    ax.set_title(f"Quality-bit timeline - {tag} (n={time.size})")
    path = _save(fig, out_dir, "fig02_quality_bit_timeline")
    _sidecar(path, data_kind=data_kind, sample_size=time.size, units="boolean vs BTJD", config_path=config_path)


def _fig_scatter_comparison(out_dir, config_path, data_kind, ratios_by_policy, tag):
    fig, ax = plt.subplots(figsize=(6, 4.5))
    policies = list(ratios_by_policy.keys())
    values = [ratios_by_policy[p] for p in policies]
    ax.bar(policies, values, color=["tab:blue", "tab:orange", "tab:green"][: len(policies)])
    ax.axhline(1.0, color="black", lw=0.8, ls="--")
    ax.set_ylabel("Scatter ratio (RMS all / RMS kept)")
    ax.set_title(f"Scatter comparison by mask policy - {tag}")
    path = _save(fig, out_dir, "fig03_scatter_comparison")
    _sidecar(path, data_kind=data_kind, sample_size=len(policies), units="dimensionless", config_path=config_path)


def _fig_bootstrap_rms(out_dir, config_path, data_kind, rms_all, rms_kept, tag):
    fig, ax = plt.subplots(figsize=(5, 4.5))
    ax.bar(["all cadences", "kept (default)"], [rms_all, rms_kept], color=["lightgray", "tab:blue"])
    ax.set_ylabel("Normalized flux RMS")
    ax.set_title(f"Flux scatter before/after masking - {tag}")
    path = _save(fig, out_dir, "fig04_bootstrap_rms")
    _sidecar(path, data_kind=data_kind, sample_size=2, units="dimensionless", config_path=config_path)


def _fig_background_diagnostic(out_dir, config_path, data_kind, background, flagged, tag):
    fig, ax = plt.subplots(figsize=(6, 4.5))
    finite = np.isfinite(background)
    unflagged_values = background[~flagged & finite]
    flagged_values = background[flagged & finite]
    if unflagged_values.size:
        ax.hist(
            unflagged_values,
            bins=30,
            alpha=0.6,
            label="unflagged",
            color="tab:blue",
            density=True,
        )
    if flagged_values.size:
        ax.hist(
            flagged_values,
            bins=30,
            alpha=0.6,
            label="Straylight2 flagged",
            color="tab:red",
            density=True,
        )
    else:
        ax.text(
            0.98,
            0.95,
            "No finite Straylight2-flagged background samples",
            ha="right",
            va="top",
            transform=ax.transAxes,
            fontsize=8,
        )
    ax.set_xlabel("SAP background flux")
    ax.set_ylabel("Density")
    ax.set_title(f"Background diagnostic - {tag}")
    if unflagged_values.size or flagged_values.size:
        ax.legend(fontsize=8)
    path = _save(fig, out_dir, "fig05_background_diagnostic")
    _sidecar(path, data_kind=data_kind, sample_size=int(finite.sum()), units="flux histogram", config_path=config_path)


def make_demo_figures(out_dir: Path, config_path: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    data_kind = "synthetic_demo"
    spec = SyntheticLightCurveSpec()
    lc = make_synthetic_lightcurve(spec, seed=2000)
    tag = "SYNTHETIC DEMO"

    _fig_raw_masked(out_dir, config_path, data_kind, lc.time, lc.flux, lc.quality, tag)
    _fig_quality_timeline(out_dir, config_path, data_kind, lc.time, lc.quality, tag)

    ratios = {}
    for policy in MASK_POLICIES:
        keep = apply_mask_policy(lc.quality, policy)
        norm = normalized_flux(lc.flux)
        rms_all = float(np.sqrt(np.mean((norm - np.mean(norm)) ** 2)))
        kept = norm[keep]
        rms_kept = float(np.sqrt(np.mean((kept - np.mean(kept)) ** 2))) if kept.size > 1 else float("nan")
        ratios[policy] = rms_all / rms_kept if rms_kept > 0 else float("nan")
    _fig_scatter_comparison(out_dir, config_path, data_kind, ratios, tag)

    keep_default = apply_mask_policy(lc.quality, "default")
    norm = normalized_flux(lc.flux)
    rms_all = float(np.sqrt(np.mean((norm - np.mean(norm)) ** 2)))
    kept = norm[keep_default]
    rms_kept = float(np.sqrt(np.mean((kept - np.mean(kept)) ** 2)))
    _fig_bootstrap_rms(out_dir, config_path, data_kind, rms_all, rms_kept, tag)

    flagged = is_flagged(lc.quality, SCATTERED_LIGHT_BIT)
    _fig_background_diagnostic(out_dir, config_path, data_kind, lc.background, flagged, tag)

    print(f"Wrote 5 demo figures (SVG+PNG+JSON) to {out_dir}")


def make_real_figures(out_dir: Path, config_path: Path, manifest_path: Path, raw_dir: Path) -> None:
    config = load_config(config_path)
    manifest_rows = read_manifest(manifest_path)
    if not manifest_rows:
        raise SystemExit(
            "data/manifest.csv has no rows. Run scripts/fetch_data.py (with explicit "
            "operator authorization) and scripts/run_analysis.py before generating real figures."
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    data_kind = config.input.data_mode

    result = run_pipeline(manifest_rows, raw_dir, config)
    if not result.targets:
        raise SystemExit("Real-data pipeline produced zero usable targets; cannot generate real figures.")

    first_product_id = manifest_rows[0]["product_id"]
    lc = load_lightcurve(raw_dir / f"{first_product_id}.fits")
    tag = f"{first_product_id}"

    _fig_raw_masked(out_dir, config_path, data_kind, lc.time, lc.flux, lc.quality, tag)
    _fig_quality_timeline(out_dir, config_path, data_kind, lc.time, lc.quality, tag)

    first_result = result.targets[0]
    ratios = {p: first_result.scatter_by_policy[p].scatter_ratio_rms for p in MASK_POLICIES if p in first_result.scatter_by_policy}
    _fig_scatter_comparison(out_dir, config_path, data_kind, ratios, tag)

    default_cmp = first_result.scatter_by_policy["default"]
    _fig_bootstrap_rms(out_dir, config_path, data_kind, default_cmp.rms_all, default_cmp.rms_kept, tag)

    flagged = is_flagged(lc.quality, SCATTERED_LIGHT_BIT)
    _fig_background_diagnostic(out_dir, config_path, data_kind, lc.background, flagged, tag)

    print(f"Wrote 5 real-data figures (SVG+PNG+JSON) to {out_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--out-dir", type=Path, default=Path("figures"))
    parser.add_argument("--config", type=Path, default=Path("config/analysis.yml"))
    parser.add_argument("--manifest", type=Path, default=Path("data/manifest.csv"))
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    args = parser.parse_args()

    if args.demo:
        plot_demo(demo_series(), args.out_dir / "fig00_smoke_test.png")
        make_demo_figures(args.out_dir, args.config)
        return

    make_real_figures(args.out_dir, args.config, args.manifest, args.raw_dir)


if __name__ == "__main__":
    main()
