# Independent TESS mask-policy robustness pilot (29 October 2026)

Run `python scripts/run_policy_robustness.py` after installing the pinned
project dependencies. The runner uses the repository's **synthetic**
Straylight2 injection generator and writes a labelled JSON report. No FITS
files, retained real data, or production quality-bit definitions are changed.

1. **Policy exclusion accounting:** audit the exact set differences between
   nested Lightkurve default/hard/hardest bitmasks, including Straylight2
   cadences *retained* by default.
2. **Zero-event sensitivity:** if zero flags occur in `n` independent trials,
   the one-sided confidence-level `C` upper probability is
   `1 - (1-C)**(1/n)`. Recalculate under hypothetical independent-block
   lengths. This is not a statistically calibrated bound for temporally
   correlated cadences or the non-randomly selected three real targets.
3. **Paired moving-block bootstrap:** sample contiguous circular blocks and
   compare hard-minus-default flux scatter ratios on identical resampled
   cadences, tracking degenerate replicates explicitly. Confidence interval
   coverage is not guaranteed under localized nonstationary contamination.

The original Sector 40 three-target real sample has **zero** Straylight2
flags. These synthetic analyses do not demonstrate a real scattered-light
signal or a mission-wide prevalence. The mask-policy differences are
algorithmic; scatter sensitivity is conditional on the injected model.
