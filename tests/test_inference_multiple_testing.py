from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from text_factor_lab.inference import (
    build_inference_artifacts,
    write_multiple_testing_report_json,
    write_tested_specifications_jsonl,
)
from text_factor_lab.schemas import (
    EvaluationMetricRecord,
    MultipleTestingReportRecord,
    PortfolioBacktestRecord,
    PortfolioMetricRecord,
)
from text_factor_lab.schemas import (
    TestedSpecificationRecord as SpecSchema,
)


def utc(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=UTC)


def metric(model_id: str, rank_ic: float) -> EvaluationMetricRecord:
    return EvaluationMetricRecord(
        run_id="inference_test_run",
        model_id=model_id,
        split_id="split",
        target_name="CAR_1_20",
        role="test",
        observation_count=50,
        rmse=0.1,
        mae=0.08,
        r_squared=0.01,
        directional_accuracy=0.55,
        pearson_ic=rank_ic,
        rank_ic=rank_ic,
        created_at_utc=utc(2020, 1, 1),
    )


def backtest(model_id: str, t_stat: float) -> PortfolioBacktestRecord:
    return PortfolioBacktestRecord(
        run_id="inference_test_run",
        model_id=model_id,
        split_id="split",
        target_name="CAR_1_20",
        role="test",
        portfolio_method="top_bottom_quintile",
        weighting="equal_weight",
        rebalance_frequency="event_based",
        long_count=5,
        short_count=5,
        gross_long_short_return=0.02,
        turnover=2.0,
        transaction_cost_bps_one_way=10.0,
        net_long_short_return=0.018,
        sharpe_ratio=1.2,
        newey_west_lag=19,
        newey_west_t_stat=t_stat,
        created_at_utc=utc(2020, 1, 1),
    )


def portfolio_metric(model_id: str, sharpe: float) -> PortfolioMetricRecord:
    return PortfolioMetricRecord(
        run_id="inference_test_run",
        model_id=model_id,
        split_id="split",
        target_name="CAR_1_20",
        portfolio_variant="sector_neutral_value_weight",
        portfolio_method="top_bottom_quintile_min_one_time_series",
        weighting="value_weight",
        sector_neutral=True,
        observation_count=24,
        cumulative_return=0.1,
        annualized_return=0.2,
        annualized_volatility=0.1,
        sharpe_ratio=sharpe,
        max_drawdown=-0.05,
        hit_rate=0.6,
        average_turnover=0.8,
        average_gross_exposure=2.0,
        average_net_exposure=0.0,
        created_at_utc=utc(2020, 1, 1),
    )


def test_build_inference_artifacts_records_specs_and_adjustments() -> None:
    result = build_inference_artifacts(
        run_id="inference_test_run",
        metrics=[
            metric("ridge::CAR_1_20::split", 0.35),
            metric("xgboost::CAR_1_20::split", 0.25),
        ],
        backtests=[
            backtest("ridge::CAR_1_20::split", 2.5),
            backtest("xgboost::CAR_1_20::split", 1.0),
        ],
        portfolio_metrics=[portfolio_metric("ridge::CAR_1_20::split", 1.4)],
    )

    assert len(result.tested_specifications) == 5
    assert result.multiple_testing_report.specification_count == 5
    assert result.multiple_testing_report.family_count == 3
    rank_family = next(
        family
        for family in result.multiple_testing_report.families
        if family.family_id == "CAR_1_20::rank_ic"
    )
    assert rank_family.number_of_tests == 2
    assert len(rank_family.holm_adjusted_p_values) == 2
    assert len(rank_family.bh_fdr_adjusted_p_values) == 2
    assert all(0 <= value <= 1 for value in rank_family.bh_fdr_adjusted_p_values)


def test_inference_writers_round_trip(tmp_path: Path) -> None:
    result = build_inference_artifacts(
        run_id="inference_test_run",
        metrics=[metric("ridge::CAR_1_20::split", 0.35)],
        backtests=[backtest("ridge::CAR_1_20::split", 2.5)],
        portfolio_metrics=[],
    )
    specs_path = tmp_path / "tested_specifications.jsonl"
    report_path = tmp_path / "multiple_testing_report.json"

    write_tested_specifications_jsonl(result.tested_specifications, specs_path)
    write_multiple_testing_report_json(result.multiple_testing_report, report_path)

    specs = [
        SpecSchema.model_validate(json.loads(line))
        for line in specs_path.read_text(encoding="utf-8").splitlines()
    ]
    report = MultipleTestingReportRecord.model_validate(
        json.loads(report_path.read_text(encoding="utf-8"))
    )
    assert len(specs) == 2
    assert report.p_value_count == 2
