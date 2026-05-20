from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from text_factor_lab.data import build_universe_quality_report, load_universe_manifest
from text_factor_lab.orchestration import RunManager
from text_factor_lab.schemas import ExperimentConfig, UniverseRecord

UNIVERSE_PATH = Path("configs/universe/us_large_cap_2010.csv")
CONFIG_PATH = Path("configs/text_factor_lab/mvp_v0.yaml")


def load_config() -> ExperimentConfig:
    payload = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    return ExperimentConfig.model_validate(payload)


def test_load_universe_manifest_normalizes_ticker_and_cik() -> None:
    records = load_universe_manifest(UNIVERSE_PATH)

    assert len(records) == 3
    assert records[0].ticker == "AAPL"
    assert records[0].cik == "0000320193"
    assert records[0].mapping_available_time_utc.tzinfo is not None


def test_universe_record_rejects_non_digit_cik() -> None:
    payload = {
        "entity_id": "bad",
        "ticker": "bad",
        "historical_ticker": "bad",
        "cik": "not-a-cik",
        "company_name": "Bad Co",
        "sector": "Unknown",
        "industry": "Unknown",
        "selection_date": "2010-01-01",
        "market_cap_at_selection": "",
        "entry_date": "",
        "exit_date": "",
        "delisting_date": "",
        "mapping_source": "test",
        "mapping_available_time_utc": "2010-01-01T00:00:00Z",
    }

    try:
        UniverseRecord.model_validate(payload)
    except ValidationError as exc:
        assert "cik" in str(exc)
    else:
        raise AssertionError("Expected invalid CIK to fail validation")


def test_universe_quality_report_flags_placeholder_and_missing_market_cap() -> None:
    config = load_config()
    records = load_universe_manifest(UNIVERSE_PATH)
    report = build_universe_quality_report(
        records=records,
        config=config,
        source_path=UNIVERSE_PATH,
    )

    assert report.rows_total == 3
    assert report.unique_entities == 3
    assert report.duplicate_entity_ids == []
    assert report.placeholder_mapping_rows == 3
    assert report.missing_market_cap_rows == 3
    assert report.coverage == 1.0
    assert "placeholder_mapping_source" in report.formal_run_blockers
    assert "missing_market_cap_at_selection" in report.formal_run_blockers
    assert report.is_research_grade is False
    assert report.warnings


def test_run_initialization_writes_universe_quality_report(tmp_path: Path) -> None:
    payload = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    payload["run"]["run_id"] = "test_universe_run"
    payload["run"]["output_dir"] = str(tmp_path / "runs" / "test_universe_run")
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    manager = RunManager.from_config_path(config_path)
    manager.initialize_run()

    assert manager.universe_quality_report_path.exists()
    report_text = manager.universe_quality_report_path.read_text(encoding="utf-8")
    assert "placeholder_mapping_rows" in report_text
