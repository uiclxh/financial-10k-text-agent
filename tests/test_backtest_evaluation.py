from __future__ import annotations

import json
from datetime import UTC, date, datetime
from math import isclose
from pathlib import Path

import pandas as pd

from text_factor_lab.backtest import (
    build_evaluation_artifacts,
    newey_west_t_stat,
    read_labels_jsonl,
    read_predictions_jsonl,
)
from text_factor_lab.data import build_price_panel
from text_factor_lab.schemas import LabelRecord, PredictionRecord

SPLIT_ID = "train_2010_2014__val_2015_2015__test_2016_2016"


def utc(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=UTC)


def label(document_id: str, ticker: str, year: int, value: float) -> LabelRecord:
    return LabelRecord(
        label_id=f"{document_id}:CAR_1_20:labels-v0",
        entity_id=f"CIK{ticker}",
        ticker=ticker,
        event_time_utc=utc(year, 3, 1),
        prediction_time_utc=utc(year, 3, 1),
        label_start_date=date(year, 3, 2),
        label_end_date=date(year, 3, 31),
        target_name="CAR_1_20",
        target_value=value,
        benchmark_method="SPY",
        return_type="log",
        adjustment_method="adj_close",
        label_version="labels-v0",
    )


def volatility_label(document_id: str, ticker: str, year: int, value: float) -> LabelRecord:
    return label(document_id, ticker, year, value).model_copy(
        update={
            "label_id": f"{document_id}:realized_volatility_1_20:labels-v0",
            "target_name": "realized_volatility_1_20",
        }
    )


def prediction(
    label_record: LabelRecord,
    *,
    model_id: str,
    role: str,
    value: float,
    sector: str | None = None,
    market_cap: float | None = None,
) -> PredictionRecord:
    return PredictionRecord(
        run_id="eval_test_run",
        model_id=model_id,
        split_id=SPLIT_ID,
        label_id=label_record.label_id,
        role=role,
        ticker=label_record.ticker,
        event_date=label_record.event_time_utc.date(),
        target_name=label_record.target_name,
        prediction_value=value,
        factor_score=value,
        sector=sector,
        industry=sector,
        market_cap=market_cap,
        feature_version=f"features-v0:{SPLIT_ID}",
        label_version=label_record.label_version,
        training_window="2010-01-01..2014-12-31",
        validation_window="2015-01-01..2015-12-31",
        test_window="2016-01-01..2016-12-31",
    )


def fixture_records() -> tuple[list[LabelRecord], list[PredictionRecord]]:
    rows = [
        ("sec:val:a", "AAA", 2015, "validation", 0.1, 0.2),
        ("sec:val:b", "BBB", 2015, "validation", 0.4, 0.3),
        ("sec:test:a", "CCC", 2016, "test", -0.2, 0.1),
        ("sec:test:b", "DDD", 2016, "test", 0.0, 0.2),
        ("sec:test:c", "EEE", 2016, "test", 0.1, 0.8),
        ("sec:test:d", "FFF", 2016, "test", 0.3, 0.9),
        ("sec:test:e", "GGG", 2016, "test", 0.5, 0.7),
    ]
    labels = [
        label(document_id, ticker, year, target)
        for document_id, ticker, year, _, target, _ in rows
    ]
    labels_by_document = {record.label_id.rsplit(":", 2)[0]: record for record in labels}
    predictions = [
        prediction(
            labels_by_document[document_id],
            model_id="ridge::CAR_1_20::split",
            role=role,
            value=score,
        )
        for document_id, _, _, role, _, score in rows
    ]
    return labels, predictions


def write_jsonl(records: list, path: Path) -> None:
    path.write_text(
        "".join(record.model_dump_json() + "\n" for record in records),
        encoding="utf-8",
    )


def test_build_evaluation_artifacts_computes_metrics_and_backtests() -> None:
    labels, predictions = fixture_records()

    result = build_evaluation_artifacts(
        run_id="eval_test_run",
        predictions=predictions,
        labels=labels,
        transaction_cost_bps_one_way=10.0,
        newey_west_lag=2,
    )

    assert len(result.metrics) == 4
    assert len(result.backtests) == 1
    assert len(result.portfolio_weights) == 2
    assert len(result.portfolio_returns) == 1
    assert len(result.portfolio_metrics) == 1
    test_metric = next(
        record
        for record in result.metrics
        if record.role == "test" and record.split_id != "ALL_SPLITS"
    )
    assert test_metric.observation_count == 5
    assert test_metric.rank_ic > 0
    assert test_metric.directional_accuracy >= 0
    assert test_metric.rank_method == "average"
    assert test_metric.constant_prediction_policy == "return_zero"
    assert test_metric.aggregation_method == "pooled_window_metrics_with_date_ic_diagnostics"
    assert test_metric.ic_observation_count >= 1
    assert any(record.split_id == "ALL_SPLITS" for record in result.metrics)
    aggregate_metric = next(
        record
        for record in result.metrics
        if record.role == "test" and record.split_id == "ALL_SPLITS"
    )
    assert aggregate_metric.aggregation_method == "split_mean_ic_weighted_error_metrics"
    assert aggregate_metric.split_count == 1
    assert aggregate_metric.model_id == "ridge::CAR_1_20::ALL_SPLITS"
    backtest = result.backtests[0]
    assert backtest.long_count == 1
    assert backtest.short_count == 1
    assert backtest.gross_long_short_return == 0.5
    assert backtest.net_long_short_return == 0.498
    assert backtest.turnover == 2.0
    assert backtest.sharpe_ratio != 0.0
    portfolio_return = result.portfolio_returns[0]
    assert portfolio_return.gross_exposure == 2.0
    assert portfolio_return.net_exposure == 0.0
    assert portfolio_return.turnover == 1.0
    assert portfolio_return.active_position_count == 2
    assert result.portfolio_metrics[0].observation_count == 1
    assert result.portfolio_metrics[0].newey_west_lag == 0


def test_constant_baseline_has_zero_ic_diagnostics_and_all_splits_metric() -> None:
    labels: list[LabelRecord] = []
    predictions: list[PredictionRecord] = []
    split_specs = [
        ("train_2010_2014__val_2015_2015__test_2016_2016", 2016),
        ("train_2010_2015__val_2016_2016__test_2017_2017", 2017),
    ]
    for split_id, year in split_specs:
        split_labels = [
            label(f"sec:{year}:a", f"A{year}", year, 0.1),
            label(f"sec:{year}:b", f"B{year}", year, 0.4),
        ]
        labels.extend(split_labels)
        for label_record in split_labels:
            predictions.append(
                prediction(
                    label_record,
                    model_id=f"historical_mean::CAR_1_20::{split_id}",
                    role="test",
                    value=0.25,
                ).model_copy(
                    update={
                        "split_id": split_id,
                        "feature_version": f"features-v0:{split_id}",
                    }
                )
            )

    result = build_evaluation_artifacts(
        run_id="constant_baseline_test",
        predictions=predictions,
        labels=labels,
        newey_west_lag=1,
    )

    split_metrics = [
        record
        for record in result.metrics
        if record.role == "test" and record.split_id != "ALL_SPLITS"
    ]
    assert len(split_metrics) == 2
    for metric in split_metrics:
        assert metric.rank_ic == 0.0
        assert metric.rank_ic_t_stat == 0.0
        assert metric.rank_ic_newey_west_t_stat == 0.0
        assert metric.industry_neutral_rank_ic == 0.0
        assert metric.industry_neutral_rank_ic_t_stat == 0.0
        assert metric.industry_neutral_rank_ic_newey_west_t_stat == 0.0
        assert metric.ic_grouping == "event_date_cross_section"

    aggregate = next(
        record
        for record in result.metrics
        if record.role == "test" and record.split_id == "ALL_SPLITS"
    )
    assert aggregate.rank_ic == 0.0
    assert aggregate.rank_ic_t_stat == 0.0
    assert aggregate.rank_ic_newey_west_t_stat == 0.0
    assert aggregate.industry_neutral_rank_ic == 0.0
    assert aggregate.industry_neutral_rank_ic_t_stat == 0.0
    assert aggregate.industry_neutral_rank_ic_newey_west_t_stat == 0.0
    assert aggregate.rank_method == "average"
    assert aggregate.constant_prediction_policy == "return_zero"
    assert aggregate.aggregation_method == "split_mean_ic_weighted_error_metrics"
    assert aggregate.ic_grouping == "split"
    assert aggregate.split_count == 2


def test_industry_neutral_rank_ic_removes_pure_industry_level_signal() -> None:
    labels = [
        label(f"sec:test:{ticker}", ticker, 2016, target)
        for ticker, target in [
            ("A1", 1.0),
            ("A2", 2.0),
            ("B1", 10.0),
            ("B2", 11.0),
        ]
    ]
    predictions = [
        prediction(
            label_record,
            model_id="ridge::CAR_1_20::split",
            role="test",
            value=1.0 if label_record.ticker.startswith("A") else 10.0,
            sector="industry_a" if label_record.ticker.startswith("A") else "industry_b",
        )
        for label_record in labels
    ]

    result = build_evaluation_artifacts(
        run_id="industry_neutral_test",
        predictions=predictions,
        labels=labels,
        newey_west_lag=1,
    )

    metric = next(
        row
        for row in result.metrics
        if row.role == "test" and row.split_id != "ALL_SPLITS"
    )
    assert metric.rank_ic > 0.8
    assert metric.industry_neutral_rank_ic == 0.0
    assert metric.industry_neutral_group_count == 2
    assert metric.industry_neutral_singleton_group_count == 0


def test_industry_neutral_rank_ic_retains_within_industry_signal() -> None:
    labels = [
        label(f"sec:test:{ticker}", ticker, 2016, target)
        for ticker, target in [
            ("A1", 1.0),
            ("A2", 2.0),
            ("B1", 10.0),
            ("B2", 11.0),
        ]
    ]
    predictions = [
        prediction(
            label_record,
            model_id="ridge::CAR_1_20::split",
            role="test",
            value=label_record.target_value,
            sector="industry_a" if label_record.ticker.startswith("A") else "industry_b",
        )
        for label_record in labels
    ]

    result = build_evaluation_artifacts(
        run_id="industry_neutral_test",
        predictions=predictions,
        labels=labels,
        newey_west_lag=1,
    )

    metric = next(
        row
        for row in result.metrics
        if row.role == "test" and row.split_id != "ALL_SPLITS"
    )
    assert metric.industry_neutral_rank_ic == 1.0


def test_constant_baseline_does_not_create_portfolio_or_extreme_quantiles() -> None:
    labels = [
        label(f"sec:test:{ticker}", ticker, 2016, target).model_copy(
            update={
                "label_start_date": date(2016, 3, 2),
                "label_end_date": date(2016, 5, 31),
            }
        )
        for ticker, target in zip(
            ["AAA", "BBB", "CCC", "DDD"],
            [-0.2, 0.0, 0.2, 0.4],
            strict=True,
        )
    ]
    predictions = [
        prediction(
            label_record,
            model_id="historical_mean::CAR_1_20::split",
            role="test",
            value=0.25,
        )
        for label_record in labels
    ]
    price_rows = [
        (day.date().isoformat(), ticker, 100.0)
        for ticker in ["AAA", "BBB", "CCC", "DDD"]
        for day in pd.bdate_range("2016-03-01", "2016-05-31")
    ]
    price_panel = build_price_panel(
        pd.DataFrame(price_rows, columns=["date", "ticker", "adj_close"])
    )

    result = build_evaluation_artifacts(
        run_id="constant_portfolio_test",
        predictions=predictions,
        labels=labels,
        price_panel=price_panel,
        newey_west_lag=1,
    )

    assert result.backtests == []
    assert result.portfolio_weights == []
    assert result.portfolio_returns == []
    assert result.portfolio_metrics == []
    assert result.factor_panel
    assert result.monthly_portfolio_weights == []
    assert result.monthly_portfolio_returns == []
    assert result.monthly_portfolio_metrics == []
    for rebalance_date in {record.rebalance_date for record in result.factor_panel}:
        date_rows = [
            record for record in result.factor_panel if record.rebalance_date == rebalance_date
        ]
        assert len({record.factor_score for record in date_rows}) == 1
        assert len({record.rank for record in date_rows}) == 1
        assert {record.quantile for record in date_rows} == {3}


def test_portfolio_time_series_tracks_rebalance_turnover() -> None:
    labels = [
        label("sec:test:a", "AAA", 2016, -0.2),
        label("sec:test:b", "BBB", 2016, 0.4),
        label("sec:test:c", "AAA", 2016, 0.1).model_copy(
            update={
                "label_id": "sec:test:c:CAR_1_20:labels-v0",
                "event_time_utc": utc(2016, 4, 1),
                "prediction_time_utc": utc(2016, 4, 1),
                "label_start_date": date(2016, 4, 2),
                "label_end_date": date(2016, 4, 30),
            }
        ),
        label("sec:test:d", "CCC", 2016, 0.3).model_copy(
            update={
                "label_id": "sec:test:d:CAR_1_20:labels-v0",
                "event_time_utc": utc(2016, 4, 1),
                "prediction_time_utc": utc(2016, 4, 1),
                "label_start_date": date(2016, 4, 2),
                "label_end_date": date(2016, 4, 30),
            }
        ),
    ]
    predictions = [
        prediction(labels[0], model_id="ridge::CAR_1_20::split", role="test", value=0.1),
        prediction(labels[1], model_id="ridge::CAR_1_20::split", role="test", value=0.9),
        prediction(labels[2], model_id="ridge::CAR_1_20::split", role="test", value=0.8),
        prediction(labels[3], model_id="ridge::CAR_1_20::split", role="test", value=0.2),
    ]
    predictions[2] = predictions[2].model_copy(update={"event_date": date(2016, 4, 1)})
    predictions[3] = predictions[3].model_copy(update={"event_date": date(2016, 4, 1)})

    result = build_evaluation_artifacts(
        run_id="eval_test_run",
        predictions=predictions,
        labels=labels,
        transaction_cost_bps_one_way=10.0,
        newey_west_lag=1,
    )

    assert len(result.portfolio_returns) == 2
    assert [record.turnover for record in result.portfolio_returns] == [1.0, 2.0]
    assert result.portfolio_metrics[0].observation_count == 2
    assert result.portfolio_metrics[0].average_gross_exposure == 2.0


def test_validation_selected_signal_direction_freezes_validation_choice() -> None:
    labels = [
        label("sec:val:a", "AAA", 2015, 0.5),
        label("sec:val:b", "BBB", 2015, -0.5),
        label("sec:test:a", "CCC", 2016, 0.3),
        label("sec:test:b", "DDD", 2016, -0.2),
    ]
    predictions = [
        prediction(labels[0], model_id="ridge::CAR_1_20::split", role="validation", value=0.1),
        prediction(labels[1], model_id="ridge::CAR_1_20::split", role="validation", value=0.9),
        prediction(labels[2], model_id="ridge::CAR_1_20::split", role="test", value=0.1),
        prediction(labels[3], model_id="ridge::CAR_1_20::split", role="test", value=0.9),
    ]

    result = build_evaluation_artifacts(
        run_id="eval_test_run",
        predictions=predictions,
        labels=labels,
        transaction_cost_bps_one_way=10.0,
        newey_west_lag=1,
        portfolio_signal_direction="validation_selected",
    )

    assert result.backtests[0].signal_direction == "long_low_score"
    assert result.backtests[0].gross_long_short_return == 0.5
    assert result.portfolio_weights[0].signal_direction == "long_low_score"
    assert result.portfolio_returns[0].signal_direction == "long_low_score"
    assert result.portfolio_metrics[0].signal_direction == "long_low_score"


def test_target_aware_long_low_vol_forces_volatility_direction() -> None:
    labels = [
        volatility_label("sec:test:a", "AAA", 2016, 0.1),
        volatility_label("sec:test:b", "BBB", 2016, 0.5),
    ]
    predictions = [
        prediction(
            labels[0],
            model_id="ridge::realized_volatility_1_20::split",
            role="test",
            value=0.1,
        ),
        prediction(
            labels[1],
            model_id="ridge::realized_volatility_1_20::split",
            role="test",
            value=0.9,
        ),
    ]

    result = build_evaluation_artifacts(
        run_id="eval_test_run",
        predictions=predictions,
        labels=labels,
        transaction_cost_bps_one_way=10.0,
        newey_west_lag=1,
        portfolio_signal_direction="long_high_score",
        target_aware_portfolio_policy="long_low_vol",
    )

    assert result.backtests[0].signal_direction == "long_low_score"
    assert result.backtests[0].target_aware_policy == "long_low_vol"
    assert result.portfolio_weights[0].target_aware_policy == "long_low_vol"
    assert result.portfolio_returns[0].signal_direction == "long_low_score"


def test_target_aware_risk_scaled_uses_inverse_predicted_vol_weights() -> None:
    labels = [
        volatility_label(f"sec:test:{index}", f"T{index:02d}", 2016, 0.0)
        for index in range(10)
    ]
    scores = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    predictions = [
        prediction(
            label_record,
            model_id="ridge::realized_volatility_1_20::split",
            role="test",
            value=score,
        )
        for label_record, score in zip(labels, scores, strict=True)
    ]

    result = build_evaluation_artifacts(
        run_id="eval_test_run",
        predictions=predictions,
        labels=labels,
        transaction_cost_bps_one_way=10.0,
        newey_west_lag=1,
        portfolio_signal_direction="long_high_score",
        target_aware_portfolio_policy="risk_scaled",
    )

    long_weights = {
        record.ticker: record.normalized_weight
        for record in result.portfolio_weights
        if record.side == "long" and record.portfolio_variant == "equal_weight"
    }
    assert result.backtests[0].signal_direction == "long_low_score"
    assert result.backtests[0].target_aware_policy == "risk_scaled"
    assert isclose(long_weights["T00"], 2.0 / 3.0)
    assert isclose(long_weights["T01"], 1.0 / 3.0)


def test_portfolio_variants_include_value_and_sector_neutral() -> None:
    rows = [
        ("sec:test:a", "AAA", -0.4, 0.1, "Tech", 100.0),
        ("sec:test:b", "BBB", 0.2, 0.9, "Tech", 300.0),
        ("sec:test:c", "CCC", -0.1, 0.2, "Finance", 200.0),
        ("sec:test:d", "DDD", 0.5, 0.8, "Finance", 600.0),
    ]
    labels = [
        label(document_id, ticker, 2016, target)
        for document_id, ticker, target, _, _, _ in rows
    ]
    predictions = [
        prediction(
            label_record,
            model_id="ridge::CAR_1_20::split",
            role="test",
            value=score,
            sector=sector,
            market_cap=market_cap,
        )
        for label_record, (_, _, _, score, sector, market_cap) in zip(labels, rows, strict=True)
    ]

    result = build_evaluation_artifacts(
        run_id="eval_test_run",
        predictions=predictions,
        labels=labels,
        transaction_cost_bps_one_way=10.0,
        newey_west_lag=1,
    )

    variants = {record.portfolio_variant for record in result.portfolio_metrics}
    assert variants == {
        "equal_weight",
        "value_weight",
        "sector_neutral_equal_weight",
        "sector_neutral_value_weight",
    }
    sector_neutral_returns = [
        record for record in result.portfolio_returns if record.sector_neutral
    ]
    assert sector_neutral_returns
    assert all(abs(record.net_exposure) < 1e-12 for record in sector_neutral_returns)
    value_weights = [
        record for record in result.portfolio_weights if record.portfolio_variant == "value_weight"
    ]
    assert any(abs(record.normalized_weight) != 0.5 for record in value_weights)


def test_daily_price_panel_drives_portfolio_returns() -> None:
    labels = [
        label("sec:test:a", "AAA", 2016, 0.0).model_copy(
            update={"label_start_date": date(2016, 3, 2), "label_end_date": date(2016, 3, 4)}
        ),
        label("sec:test:b", "BBB", 2016, 0.0).model_copy(
            update={"label_start_date": date(2016, 3, 2), "label_end_date": date(2016, 3, 4)}
        ),
    ]
    predictions = [
        prediction(labels[0], model_id="ridge::CAR_1_20::split", role="test", value=0.1),
        prediction(labels[1], model_id="ridge::CAR_1_20::split", role="test", value=0.9),
    ]
    price_panel = build_price_panel(
        pd.DataFrame(
            [
                ("2016-03-01", "AAA", 100.0),
                ("2016-03-02", "AAA", 90.0),
                ("2016-03-03", "AAA", 81.0),
                ("2016-03-04", "AAA", 72.9),
                ("2016-03-01", "BBB", 100.0),
                ("2016-03-02", "BBB", 110.0),
                ("2016-03-03", "BBB", 121.0),
                ("2016-03-04", "BBB", 133.1),
            ],
            columns=["date", "ticker", "adj_close"],
        )
    )

    result = build_evaluation_artifacts(
        run_id="eval_test_run",
        predictions=predictions,
        labels=labels,
        price_panel=price_panel,
        portfolio_return_type="simple",
        transaction_cost_bps_one_way=10.0,
        newey_west_lag=1,
    )

    assert len(result.portfolio_returns) == 3
    assert {record.return_source for record in result.portfolio_returns} == {
        "daily_price_panel"
    }
    assert [record.date for record in result.portfolio_returns] == [
        date(2016, 3, 2),
        date(2016, 3, 3),
        date(2016, 3, 4),
    ]
    assert {record.position_accounting for record in result.portfolio_returns} == {
        "drifted_daily_positions"
    }
    assert isclose(result.portfolio_returns[0].gross_long_short_return, 0.2)
    assert isclose(result.portfolio_returns[0].net_long_short_return, 0.199)
    assert isclose(result.portfolio_returns[0].ending_gross_exposure or 0.0, 1.6666666667)
    assert isclose(result.portfolio_returns[1].gross_long_short_return, 1.0 / 6.0)
    assert isclose(result.portfolio_returns[2].gross_long_short_return, 0.1442857143)
    assert result.portfolio_returns[1].turnover == 0.0
    assert result.portfolio_metrics[0].observation_count == 3
    assert result.portfolio_metrics[0].mean_period_return != 0.0
    assert result.portfolio_metrics[0].newey_west_lag == 2


def test_daily_portfolio_exits_position_after_delisting_return() -> None:
    labels = [
        label("sec:test:a", "AAA", 2016, 0.0).model_copy(
            update={"label_start_date": date(2016, 3, 2), "label_end_date": date(2016, 3, 4)}
        ),
        label("sec:test:b", "BBB", 2016, 0.0).model_copy(
            update={"label_start_date": date(2016, 3, 2), "label_end_date": date(2016, 3, 4)}
        ),
    ]
    predictions = [
        prediction(labels[0], model_id="ridge::CAR_1_20::split", role="test", value=0.1),
        prediction(labels[1], model_id="ridge::CAR_1_20::split", role="test", value=0.9),
    ]
    price_panel = build_price_panel(
        pd.DataFrame(
            [
                ("2016-03-01", "AAA", "", "", ""),
                ("2016-03-02", "AAA", "-0.2", "-0.5", "500"),
                ("2016-03-03", "AAA", "0.5", "", ""),
                ("2016-03-01", "BBB", "", "", ""),
                ("2016-03-02", "BBB", "0.1", "", ""),
                ("2016-03-03", "BBB", "0.1", "", ""),
            ],
            columns=["date", "ticker", "ret", "dlret", "dlstcd"],
        )
    )

    result = build_evaluation_artifacts(
        run_id="eval_test_run",
        predictions=predictions,
        labels=labels,
        price_panel=price_panel,
        portfolio_return_type="simple",
        transaction_cost_bps_one_way=0.0,
        newey_west_lag=1,
    )

    assert result.portfolio_returns[0].delisting_returns_applied == 1
    assert result.portfolio_returns[0].positions_affected_by_delisting == 1
    assert result.portfolio_returns[1].active_position_count == 1
    assert result.delisting_application_report["delisting_returns_applied"] >= 1


def test_monthly_common_rebalance_uses_active_signals_and_sector_neutral() -> None:
    rows = [
        ("sec:test:a", "AAA", -0.4, 0.1, "Tech", 100.0),
        ("sec:test:b", "BBB", 0.2, 0.9, "Tech", 300.0),
        ("sec:test:c", "CCC", -0.1, 0.2, "Finance", 200.0),
        ("sec:test:d", "DDD", 0.5, 0.8, "Finance", 600.0),
    ]
    labels = [
        label(document_id, ticker, 2016, target).model_copy(
            update={"label_start_date": date(2016, 3, 2), "label_end_date": date(2016, 5, 31)}
        )
        for document_id, ticker, target, _, _, _ in rows
    ]
    predictions = [
        prediction(
            label_record,
            model_id="ridge::CAR_1_20::split",
            role="test",
            value=score,
            sector=sector,
            market_cap=market_cap,
        )
        for label_record, (_, _, _, score, sector, market_cap) in zip(labels, rows, strict=True)
    ]
    price_rows = []
    for ticker in ["AAA", "BBB", "CCC", "DDD"]:
        price = 100.0
        for day in pd.bdate_range("2016-03-01", "2016-05-31"):
            if ticker in {"BBB", "DDD"} and day > pd.Timestamp("2016-03-31"):
                price *= 1.002
            elif ticker in {"AAA", "CCC"} and day > pd.Timestamp("2016-03-31"):
                price *= 0.999
            price_rows.append((day.date().isoformat(), ticker, price))
    price_panel = build_price_panel(
        pd.DataFrame(price_rows, columns=["date", "ticker", "adj_close"])
    )

    result = build_evaluation_artifacts(
        run_id="eval_test_run",
        predictions=predictions,
        labels=labels,
        price_panel=price_panel,
        portfolio_return_type="simple",
        transaction_cost_bps_one_way=10.0,
        newey_west_lag=1,
    )

    assert result.factor_panel
    assert all(
        record.signal_event_date <= record.rebalance_date for record in result.factor_panel
    )
    monthly_variants = {
        record.portfolio_variant for record in result.monthly_portfolio_metrics
    }
    assert "monthly_equal_weight" in monthly_variants
    assert "monthly_sector_neutral_equal_weight" in monthly_variants
    aggregate_monthly = [
        record
        for record in result.monthly_portfolio_metrics
        if record.split_id == "ALL_SPLITS"
    ]
    assert aggregate_monthly
    assert {
        record.model_id for record in aggregate_monthly
    } == {"ridge::CAR_1_20::ALL_SPLITS"}
    assert all(
        record.portfolio_method == "monthly_common_rebalance_top_bottom_quintile"
        for record in aggregate_monthly
    )
    assert {
        record.return_source for record in result.monthly_portfolio_returns
    } == {"monthly_common_rebalance_price_panel"}
    sector_neutral_returns = [
        record for record in result.monthly_portfolio_returns if record.sector_neutral
    ]
    assert sector_neutral_returns
    sector_neutral_weights = [
        record for record in result.monthly_portfolio_weights if record.sector_neutral
    ]
    weights_by_rebalance: dict[date, float] = {}
    for record in sector_neutral_weights:
        weights_by_rebalance[record.rebalance_date] = (
            weights_by_rebalance.get(record.rebalance_date, 0.0)
            + record.normalized_weight
        )
    assert all(abs(net_weight) < 1e-12 for net_weight in weights_by_rebalance.values())
    assert all(record.newey_west_lag >= 0 for record in result.monthly_portfolio_metrics)


def test_newey_west_t_stat_handles_small_samples() -> None:
    assert newey_west_t_stat([], lag=2) == 0.0
    assert newey_west_t_stat([0.1], lag=2) == 0.0


def test_evaluate_models_cli_writes_artifacts(tmp_path: Path, capsys) -> None:
    from text_factor_lab.cli import main

    labels, predictions = fixture_records()
    labels_path = tmp_path / "labels.jsonl"
    predictions_path = tmp_path / "predictions.jsonl"
    metrics_path = tmp_path / "evaluation_metrics.json"
    backtest_path = tmp_path / "backtest_results.json"
    weights_path = tmp_path / "portfolio_weights.jsonl"
    returns_path = tmp_path / "portfolio_returns.jsonl"
    portfolio_metrics_path = tmp_path / "portfolio_metrics.json"
    write_jsonl(labels, labels_path)
    write_jsonl(predictions, predictions_path)

    exit_code = main(
        [
            "evaluate-models",
            "--run-id",
            "eval_test_run",
            "--predictions",
            str(predictions_path),
            "--labels",
            str(labels_path),
            "--metrics-output",
            str(metrics_path),
            "--backtest-output",
            str(backtest_path),
            "--portfolio-weights-output",
            str(weights_path),
            "--portfolio-returns-output",
            str(returns_path),
            "--portfolio-metrics-output",
            str(portfolio_metrics_path),
            "--transaction-cost-bps-one-way",
            "10",
            "--newey-west-lag",
            "2",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "metrics=4" in captured.out
    assert "portfolio_returns=1" in captured.out
    assert len(json.loads(metrics_path.read_text(encoding="utf-8"))) == 4
    assert len(json.loads(backtest_path.read_text(encoding="utf-8"))) == 1
    assert len(returns_path.read_text(encoding="utf-8").splitlines()) == 1
    assert len(json.loads(portfolio_metrics_path.read_text(encoding="utf-8"))) == 1


def test_backtest_readers_round_trip_jsonl(tmp_path: Path) -> None:
    labels, predictions = fixture_records()
    labels_path = tmp_path / "labels.jsonl"
    predictions_path = tmp_path / "predictions.jsonl"
    write_jsonl(labels, labels_path)
    write_jsonl(predictions, predictions_path)

    assert len(read_labels_jsonl(labels_path)) == 7
    assert len(read_predictions_jsonl(predictions_path)) == 7
