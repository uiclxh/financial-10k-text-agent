from __future__ import annotations

from datetime import UTC, date, datetime

from text_factor_lab.audit.coverage import build_coverage_diagnostics
from text_factor_lab.schemas import (
    LabelRecord,
    ModelManifestRecord,
    PredictionRecord,
    SplitAssignmentRecord,
)
from text_factor_lab.schemas import (
    TestedSpecificationRecord as SpecificationRecord,
)


def utc(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=UTC)


def label_record(label_id: str, target_name: str = "realized_volatility_1_20") -> LabelRecord:
    return LabelRecord(
        label_id=label_id,
        entity_id="CIK0000000001",
        ticker="AAA",
        event_time_utc=utc(2020, 1, 1),
        prediction_time_utc=utc(2020, 1, 1),
        label_start_date=date(2020, 1, 2),
        label_end_date=date(2020, 1, 31),
        target_name=target_name,
        target_value=0.05,
        benchmark_method="SPY",
        return_type="log",
        adjustment_method="adj_close",
        label_version="labels-v0",
    )


def assignment(label: LabelRecord, role: str, split_id: str = "split") -> SplitAssignmentRecord:
    return SplitAssignmentRecord(
        split_id=split_id,
        label_id=label.label_id,
        entity_id=label.entity_id,
        ticker=label.ticker,
        target_name=label.target_name,
        role=role,
        event_date=label.event_time_utc.date(),
        label_start_date=label.label_start_date,
        label_end_date=label.label_end_date,
        train_start_date=date(2010, 1, 1),
        train_end_date=date(2018, 12, 31),
        validation_start_date=date(2019, 1, 1),
        validation_end_date=date(2019, 12, 31),
        test_start_date=date(2020, 1, 1),
        test_end_date=date(2020, 12, 31),
        embargo_days=20,
        split_version="rolling-split-v0",
    )


def manifest(model_name: str, target_name: str = "realized_volatility_1_20") -> ModelManifestRecord:
    family = "baseline" if model_name in {"historical_mean", "industry_mean"} else "linear"
    return ModelManifestRecord(
        model_id=f"{model_name}::{target_name}::split",
        model_name=model_name,
        model_family=family,
        model_level=0,
        model_version="model-training-v0",
        hyperparameters={},
        random_seed=42,
        training_window="2010-01-01..2018-12-31",
        validation_window="2019-01-01..2019-12-31",
        test_window="2020-01-01..2020-12-31",
        feature_version="features-v0:split",
        label_version="labels-v0",
        train_observation_count=10,
        validation_observation_count=2,
        test_observation_count=1,
        feature_count=5,
        created_at_utc=utc(2020, 2, 1),
    )


def prediction(label: LabelRecord, model_name: str) -> PredictionRecord:
    return PredictionRecord(
        run_id="coverage_test_run",
        model_id=f"{model_name}::{label.target_name}::split",
        split_id="split",
        label_id=label.label_id,
        role="test",
        ticker=label.ticker,
        event_date=label.event_time_utc.date(),
        target_name=label.target_name,
        prediction_value=0.04,
        factor_score=0.04,
        feature_version="features-v0:split",
        label_version=label.label_version,
        training_window="2010-01-01..2018-12-31",
        validation_window="2019-01-01..2019-12-31",
        test_window="2020-01-01..2020-12-31",
    )


def primary_spec(label: LabelRecord, model_name: str) -> SpecificationRecord:
    return SpecificationRecord(
        run_id="coverage_test_run",
        spec_id=f"primary::{model_name}",
        family_id="primary_prediction",
        target_name=label.target_name,
        label_window="1_20",
        text_source="SEC_EDGAR",
        section="full",
        feature_method="dictionary_tone",
        model_name=model_name,
        model_id=f"{model_name}::{label.target_name}::split",
        hyperparameter_grid_id="default",
        split_id="split",
        split_method="rolling_year",
        portfolio_method="not_applicable",
        weighting="not_applicable",
        sector_neutral=False,
        transaction_cost_bps_one_way=None,
        metric_name="rank_ic",
        raw_metric=0.1,
        raw_p_value=0.5,
        specification_role="primary",
        preregistered=True,
        created_at_utc=utc(2020, 2, 1),
    )


def test_coverage_waterfall_excludes_train_labels_and_records_missing_feature() -> None:
    train_label = label_record("sec:aaa:2018:realized_volatility_1_20:labels-v0")
    test_label = label_record("sec:aaa:2020:realized_volatility_1_20:labels-v0")

    diagnostics = build_coverage_diagnostics(
        labels=[train_label, test_label],
        split_assignments=[
            assignment(train_label, "train"),
            assignment(test_label, "test"),
        ],
        features=[],
        model_manifest=[manifest("historical_mean"), manifest("ridge")],
        predictions=[prediction(test_label, "historical_mean")],
        tested_specifications=[primary_spec(test_label, "ridge")],
    )

    assert diagnostics.waterfall["counts"]["labels_total"] == 2
    assert diagnostics.waterfall["counts"]["eligible_oos_labels"] == 1
    assert diagnostics.waterfall["eligible_oos_coverage"] == 1.0
    assert diagnostics.waterfall["model_expected_prediction_coverage"] == 0.5
    assert diagnostics.waterfall["primary_spec_coverage"] == 1.0
    assert diagnostics.waterfall["counts"]["primary_covered_specifications"] == 1
    assert diagnostics.waterfall["counts"]["primary_expected_specifications"] == 1
    assert any(failure.failure_stage == "missing_feature" for failure in diagnostics.failures)
    historical_row = [
        row for row in diagnostics.by_model if row["model_name"] == "historical_mean"
    ][0]
    assert historical_row["model_expected_prediction_coverage"] == 1.0


def test_coverage_waterfall_reports_outside_configured_split_window() -> None:
    label = label_record("sec:aaa:2020:realized_volatility_1_20:labels-v0")

    diagnostics = build_coverage_diagnostics(
        labels=[label],
        split_assignments=[],
        features=[],
        model_manifest=[],
        predictions=[],
        tested_specifications=[],
    )

    assert diagnostics.waterfall["eligible_oos_coverage"] == 0.0
    assert diagnostics.failures[0].failure_stage == "outside_configured_split_window"
    assert (
        diagnostics.failures[0].failure_reason
        == "Label event date is outside the configured validation/test split window."
    )
