from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from text_factor_lab.data import (
    build_universe_quality_report,
    load_entity_link_history,
    load_security_master,
    load_universe_manifest,
    load_universe_membership,
)
from text_factor_lab.orchestration import RunManager
from text_factor_lab.schemas import (
    EntityLinkHistoryRecord,
    ExperimentConfig,
    SecurityMasterRecord,
    UniverseMembershipRecord,
    UniverseRecord,
)

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


def write_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    path.write_text(
        ",".join(header)
        + "\n"
        + "\n".join(",".join(str(value) for value in row) for row in rows)
        + "\n",
        encoding="utf-8",
    )


def write_research_grade_universe_files(tmp_path: Path) -> dict[str, Path]:
    tickers = tmp_path / "tickers.csv"
    security_master = tmp_path / "security_master.csv"
    membership = tmp_path / "membership.csv"
    links = tmp_path / "entity_link_history.csv"
    write_csv(
        tickers,
        [
            "entity_id",
            "ticker",
            "historical_ticker",
            "cik",
            "company_name",
            "sector",
            "industry",
            "selection_date",
            "market_cap_at_selection",
            "entry_date",
            "exit_date",
            "delisting_date",
            "mapping_source",
            "mapping_available_time_utc",
        ],
        [
            [
                "CIK0000320193",
                "aapl",
                "aapl",
                "320193",
                "Apple Inc.",
                "Information Technology",
                "Technology Hardware",
                "2010-01-01",
                "100000000",
                "2010-01-01",
                "2024-12-31",
                "",
                "research_grade_fixture",
                "2009-12-31T00:00:00Z",
            ],
            [
                "CIK0000012345",
                "old",
                "old",
                "12345",
                "Old Co.",
                "Industrials",
                "Machinery",
                "2010-01-01",
                "1000000",
                "2010-01-01",
                "2012-12-31",
                "2012-12-31",
                "research_grade_fixture",
                "2009-12-31T00:00:00Z",
            ],
        ],
    )
    write_csv(
        security_master,
        [
            "entity_id",
            "permno",
            "permco",
            "gvkey",
            "cik",
            "ticker",
            "historical_ticker",
            "company_name",
            "name_start_date",
            "name_end_date",
            "exchange",
            "share_class",
            "security_type",
            "sic",
            "naics",
            "gics_sector",
            "gics_industry",
            "source",
            "source_version",
            "available_time_utc",
        ],
        [
            [
                "CIK0000320193",
                "14593",
                "7",
                "001690",
                "320193",
                "AAPL",
                "AAPL",
                "Apple Inc.",
                "1980-12-12",
                "",
                "NASDAQ",
                "common",
                "equity",
                "3571",
                "334220",
                "Information Technology",
                "Technology Hardware",
                "fixture",
                "v1",
                "2009-12-31T00:00:00Z",
            ],
            [
                "CIK0000012345",
                "99999",
                "8",
                "009999",
                "12345",
                "OLD",
                "OLD",
                "Old Co.",
                "1990-01-01",
                "2012-12-31",
                "NYSE",
                "common",
                "equity",
                "3500",
                "333000",
                "Industrials",
                "Machinery",
                "fixture",
                "v1",
                "2009-12-31T00:00:00Z",
            ],
        ],
    )
    write_csv(
        membership,
        [
            "universe_id",
            "entity_id",
            "ticker",
            "selection_date",
            "entry_date",
            "exit_date",
            "delisting_date",
            "selection_rank",
            "market_cap_at_selection",
            "price_at_selection",
            "shares_outstanding_at_selection",
            "liquidity_filter_pass",
            "source",
            "source_version",
        ],
        [
            [
                "fixture_research_grade",
                "CIK0000320193",
                "AAPL",
                "2010-01-01",
                "2010-01-01",
                "2024-12-31",
                "",
                "1",
                "100000000",
                "30",
                "3333333",
                "true",
                "fixture",
                "v1",
            ],
            [
                "fixture_research_grade",
                "CIK0000012345",
                "OLD",
                "2010-01-01",
                "2010-01-01",
                "2012-12-31",
                "2012-12-31",
                "2",
                "1000000",
                "10",
                "100000",
                "true",
                "fixture",
                "v1",
            ],
        ],
    )
    write_csv(
        links,
        [
            "entity_id",
            "cik",
            "ticker",
            "permno",
            "gvkey",
            "link_start_date",
            "link_end_date",
            "link_type",
            "link_confidence",
            "source",
        ],
        [
            [
                "CIK0000320193",
                "320193",
                "AAPL",
                "14593",
                "001690",
                "1980-12-12",
                "",
                "primary",
                "1.0",
                "fixture",
            ],
            [
                "CIK0000012345",
                "12345",
                "OLD",
                "99999",
                "009999",
                "1990-01-01",
                "2012-12-31",
                "primary",
                "0.95",
                "fixture",
            ],
        ],
    )
    return {
        "tickers": tickers,
        "security_master": security_master,
        "membership": membership,
        "links": links,
    }


def research_grade_config(tmp_path: Path, paths: dict[str, Path]) -> ExperimentConfig:
    payload = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    payload["run"]["run_id"] = "research_grade_universe_test"
    payload["run"]["output_dir"] = str(tmp_path / "runs" / "research_grade_universe_test")
    payload["universe"]["name"] = "research_grade_fixture"
    payload["universe"]["universe_data_level"] = "research_grade"
    payload["universe"]["tickers_file"] = str(paths["tickers"])
    payload["universe"]["security_master_file"] = str(paths["security_master"])
    payload["universe"]["membership_file"] = str(paths["membership"])
    payload["universe"]["entity_link_history_file"] = str(paths["links"])
    return ExperimentConfig.model_validate(payload)


def test_research_grade_universe_tables_load_and_validate(tmp_path: Path) -> None:
    paths = write_research_grade_universe_files(tmp_path)

    security_master = load_security_master(paths["security_master"])
    membership = load_universe_membership(paths["membership"])
    links = load_entity_link_history(paths["links"])

    assert isinstance(security_master[0], SecurityMasterRecord)
    assert isinstance(membership[0], UniverseMembershipRecord)
    assert isinstance(links[0], EntityLinkHistoryRecord)
    assert security_master[0].ticker == "AAPL"
    assert membership[0].liquidity_filter_pass is True
    assert links[0].cik == "0000320193"


def test_research_grade_universe_quality_report_can_pass(tmp_path: Path) -> None:
    paths = write_research_grade_universe_files(tmp_path)
    config = research_grade_config(tmp_path, paths)
    records = load_universe_manifest(paths["tickers"])
    report = build_universe_quality_report(
        records=records,
        config=config,
        source_path=paths["tickers"],
        security_master=load_security_master(paths["security_master"]),
        membership=load_universe_membership(paths["membership"]),
        entity_links=load_entity_link_history(paths["links"]),
    )

    assert report.universe_data_level == "research_grade"
    assert report.security_master_rows == 2
    assert report.membership_rows == 2
    assert report.entity_link_rows == 2
    assert report.membership_without_security_master_rows == 0
    assert report.membership_without_entity_link_rows == 0
    assert report.membership_missing_market_cap_rows == 0
    assert report.membership_delisted_rows == 1
    assert report.formal_run_blockers == []
    assert report.is_research_grade is True


def test_research_grade_universe_quality_report_blocks_missing_tables(
    tmp_path: Path,
) -> None:
    paths = write_research_grade_universe_files(tmp_path)
    config = research_grade_config(
        tmp_path,
        {
            **paths,
            "security_master": tmp_path / "missing_security_master.csv",
            "membership": tmp_path / "missing_membership.csv",
            "links": tmp_path / "missing_links.csv",
        },
    )
    records = load_universe_manifest(paths["tickers"])
    report = build_universe_quality_report(
        records=records,
        config=config,
        source_path=paths["tickers"],
    )

    assert "missing_security_master" in report.formal_run_blockers
    assert "missing_universe_membership" in report.formal_run_blockers
    assert "missing_entity_link_history" in report.formal_run_blockers
    assert report.is_research_grade is False
