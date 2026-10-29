"""Reproduce labelled synthetic TESS mask-policy sensitivity diagnostics."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tess_scattered_light_quality_audit.policy_robustness import (  # noqa: E402
    policy_exclusion_audit, zero_flag_upper_sensitivity, paired_block_bootstrap,
)
from tess_scattered_light_quality_audit.synthetic import (  # noqa: E402
    make_synthetic_lightcurve,
)


def main():
    curve = make_synthetic_lightcurve(seed=20261029)
    report = {
        "data_kind": "SYNTHETIC injection, not observational TESS result",
        "seed": 20261029,
        "policy_exclusions": policy_exclusion_audit(curve.quality),
        "zero_flag_independence_scenarios": zero_flag_upper_sensitivity(
            len(curve.quality), independent_block_lengths=(1, 10, 20, 40)),
        "paired_block_bootstrap": paired_block_bootstrap(
            curve.flux, curve.quality, block_length=20, seed=20261029),
        "limitations": "The zero-event calculation is a hypothetical independent-block "
        "scenario; the bootstrap assumes approximate block stationarity and does not "
        "validate the 3-target real Sector 40 null sample.",
    }
    out = ROOT / "reports/policy-robustness-synthetic.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    scenarios = report["zero_flag_independence_scenarios"]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot([r["hypothetical_block_length"] for r in scenarios],
            [r["zero_event_upper_fraction"] for r in scenarios], "o-")
    ax.set(xlabel="Hypothetical independent-block length (cadences)",
           ylabel="One-sided 95% zero-event upper fraction",
           title="Synthetic sample size: independence sensitivity")
    fig.tight_layout()
    fig.savefig(ROOT / "reports/policy-robustness-synthetic.png", dpi=150)
    plt.close(fig)
    print(f"Synthetic mask-policy audit: {len(curve.quality)} cadences; {out}")


if __name__ == "__main__":
    main()
