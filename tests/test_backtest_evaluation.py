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
    assert any(record.split_id == "ALL_SPLITS" for record in result.metrics)
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
    assert isclose(result.portfolio_returns[0].gross_long_short_return, 0.2)
    assert isclose(result.portfolio_returns[0].net_long_short_return, 0.199)
    assert result.portfolio_returns[1].turnover == 0.0
    assert result.portfolio_metrics[0].observation_count == 3


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
