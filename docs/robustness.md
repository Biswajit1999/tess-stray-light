# TESS QUALITY mask attribution and time-aware sensitivity

Scope issue: #2. This addition preserves the original Sector 40 null result: none of the three retained real light curves contains the empirical `Straylight2` flag. The figure and significance demonstration here use the repository's **seeded synthetic injection**, not a new observational finding.

The three diagnostics in `src/tess_scattered_light_quality_audit/robustness.py` are:

1. `policy_attribution`: nested excluded-cadence counts and per-bit counts (which **overlap** for multi-bit QUALITY values). Importantly, `DEFAULT_BITMASK=17087` does **not** include `Straylight2=4096`; `HARD_BITMASK=24319` and `HARDEST_BITMASK=65535` do. Consequently, a synthetic light curve carrying only Straylight2 remains entirely unmasked under `default`, while hard/hardest exclude the injected interval.
2. `block_bootstrap_scatter_ratio`: paired circular-block resampling of flux and QUALITY, preserving within-block temporal structure and mask membership. Percentile intervals are conditional on approximate stationarity, chosen block length, seed, and sample size. If most resamples lose the retained population or have zero scatter, the routine fails rather than reporting false precision.
3. `circular_shift_background_test`: exact finite circular-shift alignment comparison between a quality bit and the median background contrast. The p-value uses all nonzero cyclic shifts plus the observed alignment; it is **not** valid for strongly trending backgrounds, changing pointing, or periodic/systematic nonstationarity. It requires both flagged and unflagged cadences and therefore cannot be applied to the current three-file real-data null sample.

Reproduce synthetic results with `python scripts/run_robustness.py --output data/processed/robustness`. Outputs are JSON and PNG. No archive credentials, restricted products, or real-data detection claims are introduced. The existing repository's `pytest` and Ruff CI checks should be run before merging.
