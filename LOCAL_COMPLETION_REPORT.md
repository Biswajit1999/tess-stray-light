# Local Completion Report — TESS Scattered-Light Quality-Flag Audit

Author: Biswajit Jana. This report documents a local Claude Code implementation pass
(project 9 of the 30-project pack, `BUILD_FIRST` priority 9.0/10). No git operations
were performed. Nothing has been published.

## 1. Environment

- New dedicated conda env `tess-scattered-light-quality-audit` (Python 3.11),
  pinned to this project's own `pyproject.toml`: numpy==1.26.4, scipy==1.13.1,
  pandas==2.2.2, matplotlib==3.9.0, pyyaml==6.0.1, astropy==6.1.0,
  astroquery==0.4.7, lightkurve==2.5.0; dev: pytest==8.2.2, pytest-cov==5.0.0,
  ruff==0.5.5, mypy==1.10.1, types-PyYAML (added this session, along with a
  `[tool.mypy]` override block for astropy/astroquery/lightkurve/scipy).
- No local LaTeX toolchain.

## 2. Files created or changed

This project's entire `src/` layer was a raw stub scaffold (`NotImplementedError`
placeholders) at the start of this session, except a minimal `core.py` starter
and `provenance.py`'s `sha256_file`. Built this session: foundation
(`config.py`, `exceptions.py` (extended), `logging_utils.py`, `provenance.py`
(extended), `results_io.py`), data layer (`scripts/fetch_data.py`,
`synthetic.py`, `scripts/sync_web_assets.py`), scientific modules
(`quality_flags.py`, `mast_fetch.py`, `lightcurve_metrics.py`, `uncertainty.py`,
`report.py`, `core.py` (extended)), 9 test files (42 tests), figures/report
(`scripts/make_figures.py`, `reports/report.tex`, `reports/references.bib`),
and the web dashboard (`web-react/src/App.jsx` rewritten, `eslint.config.js`
fixed, `recharts` removed, `public/project.json` rewritten).

## 3. Exact commands run (in order)

```bash
python -m pip install -e ".[dev]"
pytest -q                                  # 42 passed
ruff check src tests scripts               # All checks passed
mypy src                                   # Success: no issues found in 14 source files
python scripts/run_analysis.py --demo
python scripts/make_figures.py --demo
# Real-data pipeline, run only after explicit operator authorization in chat:
python scripts/fetch_data.py --i-have-authorization --n-targets 3
python scripts/run_analysis.py
python scripts/make_figures.py
python scripts/sync_web_assets.py
cd web-react && npm install && npm run lint && npm run build
```

## 4. Test / lint / build results

- **pytest**: 42 tests passed, 0 failed.
- **ruff**: clean on `src tests scripts`.
- **mypy**: clean on `src` (0 errors, 14 source files).
- **web-react**: `npm run lint` and `npm run build` both clean.

### Bugs found and fixed during implementation

1. **Real finding, initially looked like a test bug**: two tests asserted
   that the "default" TESS mask policy excludes Straylight2-flagged
   cadences and reduces scatter. Both failed with `scatter_ratio_rms == 1.0`
   exactly (nothing excluded). Diagnosed by directly computing
   `DEFAULT_BITMASK & Straylight2` in Python: it is `0` —
   Lightkurve's real "default" bitmask (17087) does **not** include the
   Straylight2 bit (4096); only "hard" (24319) and "hardest" (65535) do.
   This is genuine, verified Lightkurve behaviour, not a bug in the ported
   bit constants. Fixed by updating the tests to use the "hard" policy
   (where the exclusion is real) rather than changing the constants —
   changing the constants would have been fabricating a result to make a
   test pass. This distinction (default policy doesn't touch scattered
   light) became a central, honestly-reported finding of the report itself.
2. `synthetic.py`'s dataclass import included an unused `field` import,
   removed for ruff cleanliness.

## 5. Real datasets accessed

`astroquery.mast.Observations` (obs_collection="TESS"), same pattern
verified in hst-acs-two-axis-cte-audit and hst-wfc3ir-ramp-linearity-audit.

- **Query**: TESS Sector 40 (not Sector 1 — the real Sector 1 DRN confirms
  bit 13/Straylight2 did not exist yet at that early SPOC pipeline version,
  which would give an empty scattered-light gate by construction),
  `dataproduct_type="timeseries"`, `calib_level=3`. Deterministic first-3
  selection sorted by `target_name`.
- **Products**: 3 real SPOC 2-minute cadence LC FITS files (`tess2021175071901-s0040-*_lc.fits`),
  ~2.06 MB each (6.19 MB total), all confirmed `dataRights=PUBLIC` before
  download. Retrieved 2026-07-16.
- **Licence/terms**: STScI/MAST public TESS archive data (dataRights=PUBLIC),
  no proprietary period.
- Full SHA-256 and provenance in `data/manifest.csv`. Raw FITS files are
  not committed.

## 6. Validation and uncertainty outcomes

- **Synthetic injection-recovery gate**: PASSED. A known excess-scatter
  (5x noise), elevated-background (+500) segment flagged Straylight2 is
  correctly recovered as a scatter ratio > 1.0 under the "hard" mask policy
  (verified as the correct policy to use, per the bug fix above).
- **Null control**: a synthetic light curve with no injected excess scatter
  recovers a scatter ratio within 30% of 1.0.
- **Failure-mode tests**: missing light curve file (recorded as a warning,
  pipeline continues), missing FITS columns, empty manifest — all raise
  the documented exceptions or are handled per-target.
- **Real-data result**: median Straylight2 fraction across the 3 real
  Sector 40 targets is 0.0 (n=3) — **directly confirmed** by inspecting the
  raw QUALITY column values in each downloaded file (only bits 8/32/128/512
  are ever set; bit 4096 never is). This is a genuine null result for this
  specific small deterministic sample, not every target in a sector shows
  scattered-light contamination via this bit. All three mask policies
  (default/hard/hardest) excluded an identical mean of 699.3 cadences per
  target from other, more common quality bits; median scatter ratio 1.0014
  for all three (consistent with the excluded cadences not being unusually
  noisy in this sample). Background-flux correlation could not be computed
  for any of the 3 targets (empty flagged group) — recorded as 3 explicit
  warnings, not silently dropped.

## 7. Remaining TODOs / unresolved risks

- `reports/report.tex` could not be compiled to PDF locally (no LaTeX
  toolchain); structural completeness was checked, not a rendered PDF.
- The real 3-target sample contains zero Straylight2-flagged cadences, so
  this project's central scattered-light-specific scatter/background
  comparison has only been exercised on synthetic data, not real data, in
  this release. A larger or scattered-light-targeted real sample is a
  natural next extension.
- Real-data sample is intentionally small (3 targets) and below the
  configured `minimum_sample_size=30`.

## 8. Claims safe for a public README

- "Implements a reproducible pipeline auditing how TESS SPOC quality-mask
  policies (default/hard/hardest) alter flux scatter and background
  behaviour, validated against a synthetic injection-recovery gate before
  use on real data."
- "A key verified finding from primary literature: Lightkurve's 'default'
  TESS quality mask does not exclude the scattered-light bit (Straylight2)
  — only the 'hard' and 'hardest' policies do — confirmed by direct bitwise
  computation, not assumed."
- "On a real sample of 3 public TESS Sector 40 SPOC 2-minute light curves,
  zero cadences were Straylight2-flagged — a genuine real finding about
  this specific small sample, reported honestly rather than replaced with a
  fabricated positive result."
- "42 automated tests including an injection-recovery validation gate, a
  null control, and failure-mode tests; ruff- and mypy-clean."
- "A focused audit layer; not a replacement for Lightkurve, SPOC, QLP or
  MAST."

## 9. Claims that must NOT be made

- Do not claim this demonstrates scattered-light effects on real data — the
  real 3-target sample has zero Straylight2-flagged cadences; the
  scattered-light-specific effect is only demonstrated on synthetic data.
- Do not claim the mask-policy scatter-ratio numbers (all ≈1.0) generalize
  to targets with real scattered-light contamination — they only reflect
  this specific null sample.
- Do not claim the TeX report PDF has been visually verified — only its
  source structure was checked.
- Do not claim this replaces or supersedes Lightkurve, SPOC, QLP, or MAST.

## 10. Manual review checklist for Biswajit

- [ ] Compile `reports/report.tex` locally/Overleaf and read the PDF end-to-end.
- [ ] Consider fetching a larger or scattered-light-targeted real sample
      (e.g. cameras/orbital phases known to have scattered light near
      Sector 40 Earth-limb crossings) to actually exercise the
      scattered-light-specific comparison on real data.
- [ ] Review `npm audit` output and decide whether to bump pinned frontend
      tooling.
- [ ] Follow `MANUAL_GITHUB_ONE_BY_ONE.md` for the actual repository creation
      and push — none of that was done in this session.
