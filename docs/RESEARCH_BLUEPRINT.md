# Research Blueprint

## Technical title

TESS Scattered-Light Quality-Flag Audit

## Category

Photometric instrumentation data science

## Bounded scientific question

How do TESS quality-mask policies alter flux scatter and background behaviour near scattered-light-affected cadences?

## Gap statement

A focused audit layer; not a replacement for Lightkurve, SPOC, QLP or MAST.

## First-release scope

The first release must be completable as a focused 4–6 hour implementation pass after data access is working. It must deliver one reproducible analysis pipeline, one deterministic example/smoke dataset, tests, 4–6 figures, a concise TeX report and a deployable research webpage.

## Validation and uncertainty

- bit decoder tests
- RMS/MAD before-after
- bootstrap scatter
- mask policy sensitivity
- background-flux relation

## Required figures

1. raw/masked light curve
2. quality-bit timeline
3. scatter comparison
4. bootstrap RMS
5. background diagnostic

## Reusable scientific modules

- `mast_fetch.py`
- `quality_flags.py`
- `lightcurve_metrics.py`
- `uncertainty.py`
- `plotting.py`
- `report.py`

## Explicit exclusions

- No novelty claim beyond the bounded dataset/question/method combination.
- No causal claim from descriptive catalogue correlations.
- No hidden manual data editing.
- No unsupported precision beyond the input uncertainties.
- No production-pipeline replacement claim.
