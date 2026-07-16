from __future__ import annotations

from tess_scattered_light_quality_audit.config import load_config


def test_load_config_reads_real_project_config():
    cfg = load_config("config/analysis.yml")
    assert cfg.project.repository == "tess-scattered-light-quality-audit"
    assert cfg.execution.seed == 20260713
    assert cfg.validation.bootstrap_resamples == 1000
