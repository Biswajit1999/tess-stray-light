# Implementation Plan — TESS Scattered-Light Quality-Flag Audit

Author: Biswajit Jana. Local Claude Code implementation pass, project from the
30-project portfolio pack (`BUILD_FIRST`, priority 9.0/10). No git operations.

## 1. Literature verification (done before any code)

| Seed citation | Verification method | Result |
|---|---|---|
| Ricker et al. 2015, TESS mission, DOI:10.1117/1.JATIS.1.1.014003 | CrossRef API (`api.crossref.org/works/...`) + arXiv abstract page (1406.0151) | VERIFIED — title/authors/journal/year match exactly. |
| Jenkins et al. 2016, SPOC, DOI:10.1117/12.2233418 | CrossRef API | VERIFIED — "The TESS science processing operations center", SPIE Proceedings, 2016. |
| MAST TESS archive documentation | `archive.stsci.edu/missions-and-data/tess` (Documentation section) | VERIFIED — links to TESS Science Data Products Description Document (SDPDD) and TESS Archive Manual. |
| TESS quality-flag documentation (bit meanings incl. scattered light) | `outerspace.stsci.edu/display/TESS/2.0+-+Data+Product+Overview` (official STScI TESS archive wiki) + Lightkurve `src/lightkurve/utils.py` (`TessQualityFlags`, cites SDPDD EXP-TESS-ARC-ICD-TM-0014 Table 28) + real Sector 1 and Sector 40 Data Release Notes PDFs (`archive.stsci.edu/missions/tess/doc/tess_drn/`) | VERIFIED against two independent primary sources plus real sector DRNs (see below). |
| Lightkurve documentation/software paper | ASCL entry `ascl:1812.013` | VERIFIED — "Lightkurve: Kepler and TESS time series analysis in Python", Lightkurve Collaboration, 2018. |

### Key real finding from primary sources (not assumed from memory)

TESS `QUALITY` bitmask (from `lightkurve.utils.TessQualityFlags`, sourced from the
official SDPDD Table 28, cross-checked against real Sector 1 and Sector 40 DRNs):

- Bit 12, value **2048** = `Straylight` — a **predicted, FFI-only** flag (mission
  planning geometry). Confirmed via the real Sector 40 DRN: "The predicted stray
  light flag (bit 12) is **disabled for the 2-minute and 20-second data
  products**." Not usable for light-curve-level analysis.
- Bit 13, value **4096** = `Straylight2` ("Scattered Light Exclude") — the
  **SPOC-pipeline, per-target, empirical** flag, confirmed active for 2-minute
  light curve products from the Sector 40 DRN: "The scattered light exclude flag
  (bit 13, value 4096) identifies cadences at which individual targets are
  affected by scattered light." This is the bit this project's `quality_flags.py`
  and `run_analysis.py` treat as the primary scattered-light indicator.
- The Sector 1 DRN (the sector most people associate with "TESS scattered light")
  explicitly states bit 12/`Straylight` was **not used at all** in Sector 1's
  QUALITY column, and bit 13/`Straylight2` did not exist yet at that early SPOC
  pipeline version — so Sector 1 alone would give an empty scattered-light-bit
  gate. **Decision: use a later sector (Sector ~40, SPOC pipeline >= 4.0.5) for
  the real-data sample**, documented in `docs/DATASET_PLAN.md` and
  `scripts/fetch_data.py`, so the mask-policy comparison has genuine flagged
  cadences to compare against.
- `DEFAULT_BITMASK = 17087`, `HARD_BITMASK = 24319` (adds `ApertureCosmic`,
  `CollateralCosmic`, `Straylight`, `Straylight2`), `HARDEST_BITMASK = 65535`
  (Lightkurve's three named mask policies) — used directly as the three
  "quality-mask policies" compared in this audit's central question.

All of the above is recorded with source URLs in `docs/LITERATURE_SEEDS.md`
updates and `references.bib`. No citation needed `TODO_VERIFY`.

## 2. Real-data access plan (verified live against MAST)

- `astroquery.mast.Observations.query_criteria(obs_collection="TESS", ...)` —
  same package/pattern (`astroquery==0.4.7`) used successfully in
  `hst-acs-two-axis-cte-audit` and `hst-wfc3ir-ramp-linearity-audit`.
- Product: SPOC 2-minute cadence light curve FITS (`*_lc.fits`, `productSubGroupDescription="LC"`),
  which carries the `QUALITY` column (bit 4096 verified active, see above).
- Deterministic sample: a fixed, sorted-by-`target_name` set of TIC IDs with
  public Sector 40 SPOC 2-minute light curves. All rows verified
  `dataRights=PUBLIC` before download, exactly mirroring
  `hst-wfc3ir-ramp-linearity-audit/scripts/fetch_data.py`'s `_select_observations`
  pattern.
- `data/manifest.csv` records product_id/source/source_url/retrieved_utc/sha256/
  file_size_bytes/selection_reason/licence_or_terms per file; raw FITS never
  committed (`data/raw/` gitignored).

## 3. File-level task list

### Foundation (ported near-verbatim from `hst-wfc3ir-ramp-linearity-audit`, package renamed)
- `src/tess_scattered_light_quality_audit/config.py` — typed `AnalysisConfig` loader for `config/analysis.yml`.
- `src/tess_scattered_light_quality_audit/exceptions.py` — add `ArchiveAccessError`, `ConvergenceError`, `InsufficientDataError` to existing `ProjectError`/`DataSchemaError`/`ProvenanceError`.
- `src/tess_scattered_light_quality_audit/logging_utils.py` — `configure_logging`/`get_logger` from `config/logging.yml`.
- `src/tess_scattered_light_quality_audit/provenance.py` — extend existing `sha256_file` with `ManifestRow`, `append_manifest_row`, `read_manifest`, `sha256_bytes`, `sha256_config`, `get_git_commit`.
- `src/tess_scattered_light_quality_audit/results_io.py` (new) — `Metric` dataclass + `write_summary`/`validate_summary` matching `results/summary.schema.json`.

### Data layer
- `src/tess_scattered_light_quality_audit/synthetic.py` (new) — synthetic TESS-like light curve generator with an injected excess-scatter/background-elevated segment (known ground truth: injected start/end cadence indices, injected scatter multiplier, injected background offset) and a matching synthetic `QUALITY` column with a subset of cadences flagged `Straylight2`.
- `scripts/fetch_data.py` — real MAST fetch, gated behind `--i-have-authorization`, flattens `mastDownload/`, checksums, manifest rows.
- `data/INPUT_SCHEMA.md` mapping: `source_or_trigger_id`->TIC ID, `time`->TIME (BTJD), `measurement`->PDCSAP_FLUX, `uncertainty`->PDCSAP_FLUX_ERR, `quality_flags`->QUALITY, `background_or_auxiliary_series`->SAP_BKG, `instrument_or_channel`->CAMERA/CCD.

### Scientific modules (`docs/RESEARCH_BLUEPRINT.md` §"Reusable scientific modules")
- `mast_fetch.py` — thin, testable wrapper around the FITS-loading logic shared by `fetch_data.py` and `core.py` (load `_lc.fits`, extract TIME/PDCSAP_FLUX/PDCSAP_FLUX_ERR/QUALITY/SAP_BKG/CAMERA/CCD/TICID; raise `DataSchemaError` on missing columns).
- `quality_flags.py` — verified `TessQualityFlags`-equivalent bit constants (`Straylight=2048`, `Straylight2=4096`, plus full bit table), `DEFAULT_BITMASK`/`HARD_BITMASK`/`HARDEST_BITMASK`, `is_flagged`, `decode_flags` (bit -> name list), mask-policy application function.
- `lightcurve_metrics.py` — RMS/MAD (raw vs masked), scatter ratio, background-flux vs scatter relation, per-mask-policy summary statistics, cadence binning near flagged segments.
- `uncertainty.py` — `bootstrap_statistic` (1000 resamples, seed 20260713) and `check_fit_convergence` (covariance condition number + reduced chi-square), kept strictly separate per CLAUDE_TASK.md.
- `plotting.py` — extend existing `plot_demo` with the 5 required figure-building blocks (called from `scripts/make_figures.py`, not re-implemented there).
- `report.py` — helper(s) that assemble the machine-readable numbers used verbatim in `reports/report.tex` (avoids hand-typed numbers drifting from `results/summary.json`).
- `core.py` — extend existing `Summary`/`validate_numeric`/`robust_summary`/`demo_series` with `run_pipeline(manifest_rows, raw_dir, config)` orchestrating per-target processing, catching `InsufficientDataError`/`ConvergenceError`/`DataSchemaError` per target as warnings (never aborting the whole run), raising `InsufficientDataError` immediately on empty input.

### Validation/QA
- `tests/conftest.py` — synthetic fixtures.
- `tests/test_quality_flags.py` — bit decoder tests (each bit round-trips; combined masks decode to the right name set; verified constants match the literature table).
- `tests/test_lightcurve_metrics.py` — RMS/MAD before/after masking on synthetic data with known injected excess scatter; background-flux relation.
- `tests/test_uncertainty.py` — bootstrap CI coverage sanity + convergence-error raising on ill-conditioned covariance.
- `tests/test_core_pipeline.py` — injection-recovery gate (known injected excess-scatter segment recovered within tolerance), null control (zero-injection synthetic recovers near-baseline scatter ratio), failure-mode tests (empty manifest, missing columns, all-NaN flux).
- `tests/test_synthetic.py`, `tests/test_provenance.py`, `tests/test_results_io.py`, `tests/test_config.py` — supporting coverage mirroring the sibling projects' test layout.
- Benchmarks via `tracemalloc` + `time.perf_counter()` in `scripts/run_analysis.py`.

### Figures + report
- `scripts/make_figures.py` — `make_demo_figures`/`make_real_figures` for the 5 required figures (raw/masked light curve; quality-bit timeline; scatter comparison; bootstrap RMS; background diagnostic), SVG+PNG(300dpi)+sidecar JSON.
- `reports/report.tex` + `reports/references.bib` — full sections, real numbers only after real pipeline run.

### React dashboard
- `web-react/eslint.config.js` — add `react/jsx-uses-vars`/`react/jsx-uses-react`.
- `web-react/package.json` — remove `recharts`.
- `web-react/src/App.jsx` — replace stub using `hst-wfc3ir-ramp-linearity-audit/web-react/src/App.jsx` as template.
- `web-react/public/project.json` — rewrite with real fields.
- `scripts/sync_web_assets.py` (new) — copy results/figures/manifest into `web-react/public/`.

### Final
- `LOCAL_COMPLETION_REPORT.md`, `_PROJECT_LOG.md` — filled in after real-data run.

## 4. Environment

Dedicated conda env `tess-scattered-light-quality-audit`, Python 3.11, installed
from this project's own `pyproject.toml` (already pinned: numpy 1.26.4, scipy
1.13.1, pandas 2.2.2, matplotlib 3.9.0, pyyaml 6.0.1, astropy 6.1.0, astroquery
0.4.7, lightkurve 2.5.0; dev: pytest 8.2.2, pytest-cov 5.0.0, ruff 0.5.5, mypy
1.10.1). `photutils` is not required (no aperture photometry in this project —
SPOC light curves are already extracted); `types-PyYAML` added for mypy.

## 5. Stop conditions encountered

None yet identified as hard blockers. Sector 1 bit-availability caveat above
was resolved by switching the real-sample sector, not by stopping.
