# Exposure-window sensitivity (2026-11-23)

Author: Biswajit Jana. Python implementation prepared with AI coding assistance; review and execution required.

## Scope and assumptions
Duty cycle is the union length of clipped exposure intervals divided by an externally supplied fixed observation window. Overlapping cadences are not double counted. This is a time-coverage diagnostic, not the TESS QUALITY policy or target observability. Exposure-weighted inverse-variance flux mean uses weights t/sigma²; its reported standard error uses the independent heteroscedastic measurement-error model, not a correlated-noise or astrophysical-variability estimate. It is **not** 1/sqrt(sum weights) when exposure weights are used. The mask is supplied explicitly; no quality bits are interpreted here.

## Reproduce
From this directory: `python -m pytest -q test_cadence_exposure.py`. Requires numpy and pytest. Synthetic cases only; no MAST or real TESS files were read. Published Sector 40 null result remains unchanged.

## Next validation
Test edge cases with real cadence exposure start/end columns and compare duty cycle across quality policies using the same fixed observation window. Issue #6.
