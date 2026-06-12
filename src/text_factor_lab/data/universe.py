from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from text_factor_lab.schemas.config import ExperimentConfig
from text_factor_lab.schemas.universe import (
    EntityLinkHistoryRecord,
    SecurityMasterRecord,
    UniverseMembershipRecord,
    UniverseQualityReport,
    UniverseRecord,
)


def load_universe_manifest(path: str | Path) -> list[UniverseRecord]:
    universe_path = Path(path)
    with universe_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return [UniverseRecord.model_validate(row) for row in reader]


def load_security_master(path: str | Path) -> list[SecurityMasterRecord]:
    return _load_csv_records(path, SecurityMasterRecord)


def load_universe_membership(path: str | Path) -> list[UniverseMembershipRecord]:
    return _load_csv_records(path, UniverseMembershipRecord)


def load_entity_link_history(path: str | Path) -> list[EntityLinkHistoryRecord]:
    return _load_csv_records(path, EntityLinkHistoryRecord)


def _load_csv_records(path: str | Path, model):
    input_path = Path(path)
    with input_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return [model.model_validate(row) for row in reader]


def find_duplicates(values: list[str]) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if count > 1)


def build_universe_quality_report(
    *,
    records: list[UniverseRecord],
    config: ExperimentConfig,
    source_path: str | Path,
    security_master: list[SecurityMasterRecord] | None = None,
    membership: list[UniverseMembershipRecord] | None = None,
    entity_links: list[EntityLinkHistoryRecord] | None = None,
) -> UniverseQualityReport:
    security_master = security_master or []
    membership = membership or []
    entity_links = entity_links or []
    entity_ids = [record.entity_id for record in records]
    tickers = [record.ticker for record in records]
    security_master_entity_ids = {record.entity_id for record in security_master}
    link_entity_ids = {record.entity_id for record in entity_links}

    placeholder_rows = sum(
        1 for record in records if record.mapping_source.strip().lower() == "placeholder"
    )
    missing_market_cap_rows = sum(
        1 for record in records if record.market_cap_at_selection is None
    )
    estimated_market_cap_rows = sum(
        1
        for record in records
        if _market_cap_is_applied_estimate(record.market_cap_quality_flag)
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
    membership_without_security_master_rows = sum(
        1 for record in membership if record.entity_id not in security_master_entity_ids
    )
    membership_without_entity_link_rows = sum(
        1 for record in membership if record.entity_id not in link_entity_ids
    )
    low_confidence_link_rows = sum(1 for record in entity_links if record.link_confidence < 0.8)
    membership_selection_after_sample_start_rows = sum(
        1 for record in membership if record.selection_date > config.sample.start_date
    )
    membership_missing_market_cap_rows = sum(
        1 for record in membership if record.market_cap_at_selection is None
    )
    membership_estimated_market_cap_rows = sum(
        1
        for record in membership
        if _market_cap_is_applied_estimate(record.market_cap_quality_flag)
    )
    membership_delisted_rows = sum(
        1 for record in membership if record.delisting_date is not None
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
    if config.universe.universe_data_level == "research_grade" and not security_master:
        warnings.append("Research-grade universe requires a populated security master.")
    if config.universe.universe_data_level == "research_grade" and not membership:
        warnings.append("Research-grade universe requires dated membership intervals.")
    if config.universe.universe_data_level == "research_grade" and not entity_links:
        warnings.append("Research-grade universe requires entity link history.")
    if membership_without_security_master_rows:
        warnings.append("Some membership rows are missing from security master.")
    if membership_without_entity_link_rows:
        warnings.append("Some membership rows are missing entity link history.")
    if low_confidence_link_rows:
        warnings.append("Some entity links have link_confidence below 0.8.")
    if membership_selection_after_sample_start_rows:
        warnings.append("Some membership rows have selection_date after sample.start_date.")
    if membership_missing_market_cap_rows:
        warnings.append("Some membership rows are missing market_cap_at_selection.")
    if estimated_market_cap_rows or membership_estimated_market_cap_rows:
        warnings.append(
            "Market-cap selection metadata includes applied-grade estimates; do not "
            "treat these as CRSP/WRDS research-grade market caps."
        )

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
    if config.universe.universe_data_level == "research_grade":
        if not security_master:
            formal_run_blockers.append("missing_security_master")
        if not membership:
            formal_run_blockers.append("missing_universe_membership")
        if not entity_links:
            formal_run_blockers.append("missing_entity_link_history")
        if membership_without_security_master_rows:
            formal_run_blockers.append("membership_entity_missing_security_master")
        if membership_without_entity_link_rows:
            formal_run_blockers.append("membership_entity_missing_link_history")
        if membership_selection_after_sample_start_rows:
            formal_run_blockers.append("membership_selection_after_sample_start")
        if membership_missing_market_cap_rows:
            formal_run_blockers.append("membership_missing_market_cap_at_selection")
        if config.universe.allow_delisted_firms and membership_delisted_rows == 0:
            formal_run_blockers.append("membership_no_delisted_firms")

    is_research_grade = (
        config.universe.universe_data_level == "research_grade"
        and not formal_run_blockers
        and estimated_market_cap_rows == 0
        and membership_estimated_market_cap_rows == 0
    )

    return UniverseQualityReport(
        universe_name=config.universe.name,
        universe_data_level=config.universe.universe_data_level,
        source_path=str(source_path),
        security_master_path=(
            str(config.universe.security_master_file)
            if config.universe.security_master_file is not None
            else None
        ),
        membership_path=(
            str(config.universe.membership_file)
            if config.universe.membership_file is not None
            else None
        ),
        entity_link_history_path=(
            str(config.universe.entity_link_history_file)
            if config.universe.entity_link_history_file is not None
            else None
        ),
        rows_total=len(records),
        security_master_rows=len(security_master),
        membership_rows=len(membership),
        entity_link_rows=len(entity_links),
        unique_entities=len(set(entity_ids)),
        unique_tickers=len(set(tickers)),
        duplicate_entity_ids=find_duplicates(entity_ids),
        duplicate_tickers=find_duplicates(tickers),
        placeholder_mapping_rows=placeholder_rows,
        missing_market_cap_rows=missing_market_cap_rows,
        estimated_market_cap_rows=estimated_market_cap_rows,
        delisted_rows=delisted_rows,
        selection_date_after_sample_start_rows=selection_after_sample_rows,
        mapping_available_after_selection_rows=mapping_after_selection_rows,
        membership_without_security_master_rows=membership_without_security_master_rows,
        membership_without_entity_link_rows=membership_without_entity_link_rows,
        low_confidence_link_rows=low_confidence_link_rows,
        membership_selection_after_sample_start_rows=(
            membership_selection_after_sample_start_rows
        ),
        membership_missing_market_cap_rows=membership_missing_market_cap_rows,
        membership_estimated_market_cap_rows=membership_estimated_market_cap_rows,
        membership_delisted_rows=membership_delisted_rows,
        coverage=coverage,
        warnings=warnings,
        formal_run_blockers=formal_run_blockers,
        is_research_grade=is_research_grade,
    )


def load_and_report_universe(
    config: ExperimentConfig,
) -> tuple[list[UniverseRecord], UniverseQualityReport]:
    records = load_universe_manifest(config.universe.tickers_file)
    security_master = (
        load_security_master(config.universe.security_master_file)
        if config.universe.security_master_file is not None
        else []
    )
    membership = (
        load_universe_membership(config.universe.membership_file)
        if config.universe.membership_file is not None
        else []
    )
    entity_links = (
        load_entity_link_history(config.universe.entity_link_history_file)
        if config.universe.entity_link_history_file is not None
        else []
    )
    report = build_universe_quality_report(
        records=records,
        config=config,
        source_path=config.universe.tickers_file,
        security_master=security_master,
        membership=membership,
        entity_links=entity_links,
    )
    return records, report


def _market_cap_is_applied_estimate(flag: str | None) -> bool:
    normalized = (flag or "").lower()
    return "not_crsp" in normalized or "estimate" in normalized or "proxy" in normalized
