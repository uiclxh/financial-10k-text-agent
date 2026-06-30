from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from text_factor_lab.inference import build_primary_rank_ic_bootstrap_report
from text_factor_lab.schemas import LabelRecord, PredictionRecord


def _records() -> tuple[list[LabelRecord], list[PredictionRecord]]:
    labels: list[LabelRecord] = []
    predictions: list[PredictionRecord] = []
    for split_index, split_id in enumerate(["split_a", "split_b"]):
        for ticker_index, ticker in enumerate(["AAA", "BBB", "CCC", "DDD"]):
            event_date = date(2022 + split_index, 2, 1 + ticker_index)
            label = LabelRecord(
                label_id=f"{split_id}:{ticker}:realized_volatility_1_20:labels-v0",
                entity_id=ticker,
                ticker=ticker,
                event_time_utc=datetime.combine(
                    event_date,
                    datetime.min.time(),
                    tzinfo=UTC,
                ),
                prediction_time_utc=datetime.combine(
                    event_date,
                    datetime.min.time(),
                    tzinfo=UTC,
                ),
                label_start_date=event_date + timedelta(days=1),
                label_end_date=date(2022 + split_index, 3, 1),
                target_name="realized_volatility_1_20",
                target_value=float(ticker_index + split_index),
                benchmark_method="SPY",
                return_type="log",
                adjustment_method="adj_close",
                label_version="labels-v0",
            )
            labels.append(label)
            predictions.append(
                PredictionRecord(
                    run_id="bootstrap_run",
                    model_id=f"ridge::realized_volatility_1_20::{split_id}",
                    split_id=split_id,
                    label_id=label.label_id,
                    role="test",
                    ticker=ticker,
                    event_date=event_date,
                    target_name=label.target_name,
                    prediction_value=float(ticker_index),
                    factor_score=float(ticker_index),
                    sector="sector_a" if ticker_index < 2 else "sector_b",
                    industry="industry_a" if ticker_index < 2 else "industry_b",
                    feature_version="features-v0",
                    label_version="labels-v0",
                    training_window="2016..2020",
                    validation_window="2021",
                    test_window="2022",
                )
            )
    return labels, predictions


def test_primary_rank_ic_bootstrap_is_deterministic_and_clustered() -> None:
    labels, predictions = _records()

    first = build_primary_rank_ic_bootstrap_report(
        run_id="bootstrap_run",
        predictions=predictions,
        labels=labels,
        iterations=100,
        random_seed=7,
    )
    second = build_primary_rank_ic_bootstrap_report(
        run_id="bootstrap_run",
        predictions=predictions,
        labels=labels,
        iterations=100,
        random_seed=7,
    )

    assert first["status"] == "completed"
    assert first["rows"] == second["rows"]
    assert len(first["rows"]) == 6
    methods = {row["bootstrap_method"] for row in first["rows"]}
    assert methods == {
        "split_bootstrap",
        "event_date_bootstrap",
        "ticker_cluster_bootstrap",
    }
    assert all(
        row["ci_lower_95"] <= row["point_estimate"] <= row["ci_upper_95"]
        for row in first["rows"]
    )
