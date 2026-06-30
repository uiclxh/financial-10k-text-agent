from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from text_factor_lab.backtest.evaluation import BACKTEST_VERSION
from text_factor_lab.inference import (
    build_inference_artifacts,
    write_multiple_testing_report_json,
    write_specification_registry_json,
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


def metric(
    model_id: str,
    rank_ic: float,
    *,
    split_id: str = "split",
    target_name: str = "CAR_1_20",
) -> EvaluationMetricRecord:
    return EvaluationMetricRecord(
        evaluation_version=BACKTEST_VERSION,
        run_id="inference_test_run",
        model_id=model_id,
        split_id=split_id,
        target_name=target_name,
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


def portfolio_metric(
    model_id: str,
    sharpe: float,
    *,
    split_id: str = "split",
    portfolio_method: str = "top_bottom_quintile_min_one_time_series",
    weighting: str = "value_weight",
    sector_neutral: bool = True,
    target_name: str = "CAR_1_20",
    newey_west_t_stat: float = 0.0,
) -> PortfolioMetricRecord:
    return PortfolioMetricRecord(
        run_id="inference_test_run",
        model_id=model_id,
        split_id=split_id,
        target_name=target_name,
        portfolio_variant="sector_neutral_value_weight",
        portfolio_method=portfolio_method,
        weighting=weighting,
        sector_neutral=sector_neutral,
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
        newey_west_t_stat=newey_west_t_stat,
        created_at_utc=utc(2020, 1, 1),
    )


def test_build_inference_artifacts_records_specs_and_adjustments() -> None:
    result = build_inference_artifacts(
        run_id="inference_test_run",
        metrics=[
            metric(
                "ridge::realized_volatility_1_20::ALL_SPLITS",
                0.4,
                split_id="ALL_SPLITS",
                target_name="realized_volatility_1_20",
            ),
            metric("ridge::CAR_1_20::split", 0.35),
            metric("xgboost::CAR_1_20::split", 0.25),
        ],
        backtests=[
            backtest("ridge::CAR_1_20::split", 2.5),
            backtest("xgboost::CAR_1_20::split", 1.0),
        ],
        portfolio_metrics=[
            portfolio_metric("ridge::CAR_1_20::split", 1.4),
            portfolio_metric(
                "ridge::realized_volatility_1_20::split",
                1.2,
                portfolio_method="monthly_common_rebalance_top_bottom_quintile",
                weighting="equal_weight",
                sector_neutral=True,
                target_name="realized_volatility_1_20",
                newey_west_t_stat=0.2,
            ),
            portfolio_metric(
                "ridge::realized_volatility_1_20::ALL_SPLITS",
                1.3,
                split_id="ALL_SPLITS",
                portfolio_method="monthly_common_rebalance_top_bottom_quintile",
                weighting="equal_weight",
                sector_neutral=True,
                target_name="realized_volatility_1_20",
                newey_west_t_stat=2.4,
            ),
        ],
    )

    assert len(result.tested_specifications) == 11
    assert result.multiple_testing_report.specification_count == 11
    assert result.multiple_testing_report.primary_specification_count == 2
    assert result.multiple_testing_report.robustness_specification_count > 0
    assert result.multiple_testing_report.family_count == 8
    assert result.multiple_testing_report.role_family_counts["primary"] == 2
    assert result.multiple_testing_report.role_family_counts["robustness"] >= 1
    assert any(
        spec.specification_role == "primary" and spec.preregistered
        for spec in result.tested_specifications
    )
    primary_portfolio = next(
        spec
        for spec in result.tested_specifications
        if spec.specification_role == "primary"
        and spec.metric_name == "portfolio_sharpe"
    )
    assert primary_portfolio.split_id == "ALL_SPLITS"
    assert primary_portfolio.raw_metric == 1.3
    assert primary_portfolio.p_value_method == (
        "all_splits_oos_return_series_newey_west_t_stat"
    )
    assert primary_portfolio.preregistered is True
    assert primary_portfolio.raw_p_value is not None
    assert 0.01 < primary_portfolio.raw_p_value < 0.02
    registry = result.specification_registry
    assert registry["registry_version"] == "specification-registry-v1"
    assert registry["registry_designation"] == "pre_registered_specification_registry"
    assert registry["preregistration"]["status"] == "pre_registered"
    assert registry["preregistration"]["primary_rules_are_preregistered"] is True
    assert len(registry["preregistered_primary_rules"]) == 2
    assert all(rule["preregistered"] for rule in registry["preregistered_primary_rules"])
    assert all(
        spec["rule_status"] == "pre_registered_primary"
        for spec in registry["primary_specifications"]
    )
    rank_family = next(
        family
        for family in result.multiple_testing_report.families
        if family.family_id == "exploratory::CAR_1_20::rank_ic"
    )
    assert rank_family.base_family_id == "CAR_1_20::rank_ic"
    assert rank_family.specification_role == "exploratory"
    assert rank_family.number_of_tests == 2
    assert len(rank_family.holm_adjusted_p_values) == 2
    assert len(rank_family.bh_fdr_adjusted_p_values) == 2
    assert all(0 <= value <= 1 for value in rank_family.bh_fdr_adjusted_p_values)
    assert any(
        spec.metric_name == "industry_neutral_rank_ic"
        and spec.specification_role == "robustness"
        for spec in result.tested_specifications
    )


def test_inference_writers_round_trip(tmp_path: Path) -> None:
    result = build_inference_artifacts(
        run_id="inference_test_run",
        metrics=[metric("ridge::CAR_1_20::split", 0.35)],
        backtests=[backtest("ridge::CAR_1_20::split", 2.5)],
        portfolio_metrics=[],
    )
    specs_path = tmp_path / "tested_specifications.jsonl"
    report_path = tmp_path / "multiple_testing_report.json"
    registry_path = tmp_path / "specification_registry.json"

    write_tested_specifications_jsonl(result.tested_specifications, specs_path)
    write_multiple_testing_report_json(result.multiple_testing_report, report_path)
    write_specification_registry_json(result.specification_registry, registry_path)

    specs = [
        SpecSchema.model_validate(json.loads(line))
        for line in specs_path.read_text(encoding="utf-8").splitlines()
    ]
    report = MultipleTestingReportRecord.model_validate(
        json.loads(report_path.read_text(encoding="utf-8"))
    )
    assert len(specs) == 3
    assert report.p_value_count == 3
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    assert registry["registry_version"] == "specification-registry-v1"
    assert registry["preregistration"]["status"] == "pre_registered"
    assert registry["specification_count"] == 3
