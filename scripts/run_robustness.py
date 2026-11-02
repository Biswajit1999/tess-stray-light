"""Reproducible synthetic QUALITY-mask robustness demonstration."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from tess_scattered_light_quality_audit.robustness import (
    policy_attribution, block_bootstrap_scatter_ratio, circular_shift_background_test,
)
from tess_scattered_light_quality_audit.synthetic import make_synthetic_lightcurve


def run(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    sample = make_synthetic_lightcurve(seed=17)
    policies = policy_attribution(sample.quality)
    bootstrap = {name: block_bootstrap_scatter_ratio(sample.flux, sample.quality,
                 policy=name, block_length=12, n_resamples=500, seed=17)
                 for name in ('default', 'hard', 'hardest')}
    block_sensitivity = {str(b): block_bootstrap_scatter_ratio(sample.flux, sample.quality,
                         policy='hard', block_length=b, n_resamples=500, seed=17)
                         for b in (5, 12, 30)}
    shift = circular_shift_background_test(sample.background, sample.quality)
    summary = {"data_kind": "Seeded synthetic TESS-like light curve; not Sector 40 observational evidence",
               "seed": 17, "injected_segment": [sample.injected_start, sample.injected_end],
               "quality_policy_attribution": policies, "policy_bootstrap": bootstrap,
               "block_length_sensitivity": block_sensitivity, "background_shift_test": shift,
               "limitations": "Circular block bootstrap and circular shifts require approximate stationarity; masks are not independent observations"}
    (output/'summary.json').write_text(json.dumps(summary, indent=2, allow_nan=False)+'\n')
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    x = range(len(sample.flux))
    axes[0].plot(x, sample.flux, lw=.7, color='black')
    axes[0].axvspan(sample.injected_start, sample.injected_end, color='grey', alpha=.2)
    axes[0].set(xlabel='Synthetic cadence', ylabel='Flux (arbitrary units)')
    names = list(bootstrap)
    means = [bootstrap[n]['estimate'] for n in names]
    errors = [[means[i]-bootstrap[n]['ci_low'] for i, n in enumerate(names)],
              [bootstrap[n]['ci_high']-means[i] for i, n in enumerate(names)]]
    axes[1].errorbar(names, means, yerr=errors, fmt='o', color='black', capsize=4)
    axes[1].axhline(1, ls='--', color='grey')
    axes[1].set(xlabel='TESS QUALITY mask policy', ylabel='All / kept flux RMS')
    fig.suptitle('Synthetic scattered-light flag injection and mask sensitivity')
    fig.tight_layout()
    fig.savefig(output/'tess_robustness.png', dpi=160)
    plt.close(fig)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='data/processed/robustness')
    print(json.dumps(run(parser.parse_args().output), indent=2))
