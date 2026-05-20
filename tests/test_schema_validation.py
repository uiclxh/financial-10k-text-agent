from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from pydantic import ValidationError

from text_factor_lab.schemas import (
    DocumentManifestRecord,
    FeatureManifestRecord,
    FeatureRecord,
    LabelRecord,
    ParsedSectionRecord,
    PredictionRecord,
    RunStatusRecord,
)


def utc(year: int, month: int, day: int, hour: int = 0) -> datetime:
    return datetime(year, month, day, hour, tzinfo=UTC)


def test_document_manifest_requires_timezone_aware_datetimes() -> None:
    with pytest.raises(ValidationError, match="timezone-aware"):
        DocumentManifestRecord(
            document_id="doc-1",
            entity_id="CIK0000320193",
            ticker="AAPL",
            cik="0000320193",
            company_name="Apple Inc.",
            document_type="10-K",
            fiscal_year=2020,
            fiscal_period="FY",
            source_id="SEC_EDGAR",
            source_url_or_path="https://www.sec.gov/example",
            retrieval_time_utc=datetime(2020, 1, 2),
            available_time_utc=utc(2020, 1, 2),
            event_time_utc=utc(2020, 1, 1),
            event_date=date(2020, 1, 2),
            timezone="America/New_York",
            hash_sha256="a" * 64,
            license_note="public SEC filing",
            parser_version="parser-v0",
        )


def test_feature_record_rejects_lookahead() -> None:
    with pytest.raises(ValidationError, match="feature_time_utc"):
        FeatureRecord(
            feature_id="feat-1",
            entity_id="CIK0000320193",
            ticker="AAPL",
            event_time_utc=utc(2020, 1, 1),
            prediction_time_utc=utc(2020, 1, 2),
            feature_time_utc=utc(2020, 1, 3),
            feature_family="tfidf",
            feature_name="risk_factor_tfidf",
            feature_value=0.1,
            feature_version="tfidf-v0",
            source_document_id="doc-1",
        )


def test_label_record_requires_prediction_before_label_start() -> None:
    with pytest.raises(ValidationError, match="prediction_time_utc"):
        LabelRecord(
            label_id="label-1",
            entity_id="CIK0000320193",
            ticker="AAPL",
            event_time_utc=utc(2020, 1, 1),
            prediction_time_utc=utc(2020, 1, 2),
            label_start_date=date(2020, 1, 2),
            label_end_date=date(2020, 1, 31),
            target_name="CAR_1_20",
            target_value=0.02,
            benchmark_method="SPY",
            return_type="log",
            adjustment_method="adj_close",
            label_version="labels-v0",
        )


def test_prediction_record_rejects_non_finite_values() -> None:
    with pytest.raises(ValidationError, match="finite"):
        PredictionRecord(
            run_id="run-1",
            model_id="ridge",
            split_id="2018_2019_2020",
            ticker="AAPL",
            event_date=date(2020, 1, 2),
            target_name="realized_volatility_1_20",
            prediction_value=float("nan"),
            factor_score=0.1,
            feature_version="features-v0",
            label_version="labels-v0",
            training_window="2010-2017",
            validation_window="2018",
            test_window="2019",
        )


def test_run_status_coverage_bounds() -> None:
    with pytest.raises(ValidationError):
        RunStatusRecord(
            run_id="run-1",
            run_type="formal_run",
            status="created",
            created_at_utc=utc(2020, 1, 1),
            updated_at_utc=utc(2020, 1, 1),
            config_path="configs/text_factor_lab/mvp_v0.yaml",
            failure_reason=None,
            audit_status="not_run",
            coverage=1.5,
        )


def test_feature_manifest_requires_method_metadata() -> None:
    with pytest.raises(ValidationError, match="dictionary"):
        FeatureManifestRecord(
            feature_version="dictionary-tone-v0",
            feature_method="dictionary_tone",
            dictionary_source=None,
            dictionary_version=None,
            dictionary_license_note=None,
            dictionary_term_count=None,
            tfidf_params=None,
            fit_scope="no_fit_dictionary_counts",
            split_id="split-1",
            text_scope="full",
            train_doc_count=10,
            validation_doc_count=2,
            test_doc_count=2,
            vocabulary_size=0,
            created_at_utc=utc(2020, 1, 1),
            input_hashes={"document_manifest": "a" * 64},
        )


def test_parsed_section_requires_failure_reason_when_missing() -> None:
    with pytest.raises(ValidationError, match="failure_reason"):
        ParsedSectionRecord(
            section_id="doc-1:item_3",
            document_id="doc-1",
            entity_id="CIK0000320193",
            ticker="AAPL",
            cik="0000320193",
            document_type="10-K",
            fiscal_year=2020,
            section_key="item_3",
            section_name="Legal Proceedings",
            parser_status="missing",
            char_start=None,
            char_end=None,
            text_length=0,
            text_hash_sha256=None,
            source_hash_sha256="a" * 64,
            artifact_path=None,
            parser_version="parser-v0",
            failure_reason=None,
            created_at_utc=utc(2020, 1, 2),
        )
