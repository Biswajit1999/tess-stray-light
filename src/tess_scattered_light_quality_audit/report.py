"""Helpers that read results/summary.json into a lookup usable when writing
reports/report.tex, so numbers quoted in the report are never hand-typed
independently of the actual pipeline output.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tess_scattered_light_quality_audit.exceptions import DataSchemaError


def load_metric_lookup(summary_path: str | Path) -> dict[str, dict[str, Any]]:
    """Return {metric_name: metric_dict} from a results/summary.json file."""
    path = Path(summary_path)
    if not path.is_file():
        raise DataSchemaError(f"summary file not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "metrics" not in payload:
        raise DataSchemaError(f"{path} has no 'metrics' key")
    return {m["name"]: m for m in payload["metrics"]}


def format_metric(metric: dict[str, Any], precision: int = 4) -> str:
    """Format a metric dict as 'estimate [ci_low, ci_high] units'."""
    estimate = metric["estimate"]
    text = f"{estimate:.{precision}g}"
    if metric.get("uncertainty_low") is not None and metric.get("uncertainty_high") is not None:
        text += f" [{metric['uncertainty_low']:.{precision}g}, {metric['uncertainty_high']:.{precision}g}]"
    units = metric.get("units")
    if units and units != "dimensionless":
        text += f" {units}"
    return text
