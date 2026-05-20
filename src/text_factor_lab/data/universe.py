from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from text_factor_lab.schemas.config import ExperimentConfig
from text_factor_lab.schemas.universe import UniverseQualityReport, UniverseRecord


def load_universe_manifest(path: str | Path) -> list[UniverseRecord]:
    universe_path = Path(path)
    with universe_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return [UniverseRecord.model_validate(row) for row in reader]


def find_duplicates(values: list[str]) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def build_universe_quality_report(
    *,
    records: list[UniverseRecord],
    config: ExperimentConfig,
    source_path: str | Path,
) -> UniverseQualityReport:
    entity_ids = [record.entity_id for record in records]
    tickers = [record.ticker for record in records]

    placeholder_rows = sum(
        1 for record in records if record.mapping_source.strip().lower() == "placeholder"
    )
    missing_market_cap_rows = sum(
        1 for record in records if record.market_cap_at_selection is None
    )
    delisted_rows = sum(1 for record in records if record.delisting_date is not None)
    selection_after_sample_rows = sum(
        1 for record in records if record.selection_date > config.sample.start_date
    )
    mapping_after_selection_rows = sum(
        1
        for record in records
        if record.mapping_available_time_utc.date() > record.selection_date
    )

    warnings: list[str] = []
    if placeholder_rows:
        warnings.append(
            "Universe contains placeholder mapping_source rows; replace before research-grade runs."
        )
    if missing_market_cap_rows:
        warnings.append("Universe contains rows without market_cap_at_selection.")
    if delisted_rows == 0 and config.universe.allow_delisted_firms:
        warnings.append(
            "No delisted firms are present; residual survivorship-bias risk should be disclosed."
        )
    if selection_after_sample_rows:
        warnings.append("Some universe rows have selection_date after sample.start_date.")
    if mapping_after_selection_rows:
        warnings.append("Some mappings were not available by their selection_date.")

    invalid_rows = selection_after_sample_rows
    coverage = 0.0 if not records else (len(records) - invalid_rows) / len(records)
    formal_run_blockers: list[str] = []
    if placeholder_rows:
        formal_run_blockers.append("placeholder_mapping_source")
    if missing_market_cap_rows:
        formal_run_blockers.append("missing_market_cap_at_selection")
    if len(records) < 100 and "large_cap" in config.universe.name:
        formal_run_blockers.append("large_cap_universe_too_small")
    if config.universe.historical_ticker_mapping and mapping_after_selection_rows:
        formal_run_blockers.append("mapping_not_available_by_selection_date")
    if config.universe.allow_delisted_firms and delisted_rows == 0:
        formal_run_blockers.append("no_delisted_firms_for_survivorship_control")

    return UniverseQualityReport(
        universe_name=config.universe.name,
        source_path=str(source_path),
        rows_total=len(records),
        unique_entities=len(set(entity_ids)),
        unique_tickers=len(set(tickers)),
        duplicate_entity_ids=find_duplicates(entity_ids),
        duplicate_tickers=find_duplicates(tickers),
        placeholder_mapping_rows=placeholder_rows,
        missing_market_cap_rows=missing_market_cap_rows,
        delisted_rows=delisted_rows,
        selection_date_after_sample_start_rows=selection_after_sample_rows,
        mapping_available_after_selection_rows=mapping_after_selection_rows,
        coverage=coverage,
        warnings=warnings,
        formal_run_blockers=formal_run_blockers,
        is_research_grade=not formal_run_blockers,
    )


def load_and_report_universe(
    config: ExperimentConfig,
) -> tuple[list[UniverseRecord], UniverseQualityReport]:
    records = load_universe_manifest(config.universe.tickers_file)
    report = build_universe_quality_report(
        records=records,
        config=config,
        source_path=config.universe.tickers_file,
    )
    return records, report
