from __future__ import annotations

from pathlib import Path

import yaml

from text_factor_lab.cli import main


def test_e2e_smoke_config_runs_full_pipeline(tmp_path: Path) -> None:
    payload = yaml.safe_load(
        Path("configs/text_factor_lab/e2e_smoke.yaml").read_text(encoding="utf-8")
    )
    payload["run"]["output_dir"] = str(tmp_path / "runs" / "tflab_e2e_smoke_001")
    config_path = tmp_path / "e2e_smoke.yaml"
    config_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    exit_code = main(["run", "--config", str(config_path), "--execute"])

    run_dir = Path(payload["run"]["output_dir"])
    assert exit_code == 0
    assert (run_dir / "orchestrator_report.json").exists()
    assert (run_dir / "parsed_sections.jsonl").exists()
    assert (run_dir / "features.jsonl").exists()
    assert (run_dir / "predictions.jsonl").exists()
    assert (run_dir / "portfolio_weights.jsonl").exists()
    assert (run_dir / "portfolio_returns.jsonl").exists()
    assert (run_dir / "portfolio_metrics.json").exists()
    assert (run_dir / "tested_specifications.jsonl").exists()
    assert (run_dir / "multiple_testing_report.json").exists()
    assert (run_dir / "audit_report.json").exists()
    assert (run_dir / "report.md").exists()
    assert (run_dir / "empirical_report.md").exists()
    assert (run_dir / "factor_card.md").exists()
    assert (run_dir / "appendix_tables.md").exists()
