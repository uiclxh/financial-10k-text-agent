from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

from text_factor_lab.backtest import build_evaluation_artifacts
from text_factor_lab.inference import build_inference_artifacts
from text_factor_lab.models import build_model_artifacts
from text_factor_lab.models.training import (
    read_features_jsonl,
    read_labels_jsonl,
    read_split_assignments_jsonl,
)


@dataclass(frozen=True)
class FeatureSetSummary:
    feature_set: str
    feature_count: int
    prediction_count: int
    metric_count: int
    portfolio_metric_count: int
    multiple_testing_families: int


def main() -> int:
    run_dir = Path("runs/text_factor_lab/real_10k_2016_2025_public_v0")
    output_dir = run_dir / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)

    labels = read_labels_jsonl(run_dir / "labels.jsonl")
    features = read_features_jsonl(run_dir / "features.jsonl")
    assignments = read_split_assignments_jsonl(run_dir / "split_assignments.jsonl")

    feature_sets = {
        "dictionary_metadata": {
            "dictionary_tone",
            "metadata",
        },
        "tfidf_metadata": {
            "tfidf",
            "metadata",
        },
        "combined": {
            "dictionary_tone",
            "tfidf",
            "metadata",
        },
    }
    summaries: list[FeatureSetSummary] = []
    all_metric_rows = []
    all_portfolio_rows = []
    all_multiple_testing = {}

    for feature_set, families in feature_sets.items():
        selected_features = [feature for feature in features if feature.feature_family in families]
        model_result = build_model_artifacts(
            run_id=f"real_10k_2016_2025_public_v0::{feature_set}",
            labels=labels,
            features=selected_features,
            split_assignments=assignments,
            models=["historical_mean", "industry_mean", "ridge", "xgboost"],
            random_seed=42,
        )
        eval_result = build_evaluation_artifacts(
            run_id=f"real_10k_2016_2025_public_v0::{feature_set}",
            predictions=model_result.predictions,
            labels=labels,
            transaction_cost_bps_one_way=10.0,
            newey_west_lag=19,
        )
        inference_result = build_inference_artifacts(
            run_id=f"real_10k_2016_2025_public_v0::{feature_set}",
            metrics=eval_result.metrics,
            backtests=eval_result.backtests,
            portfolio_metrics=eval_result.portfolio_metrics,
        )
        summaries.append(
            FeatureSetSummary(
                feature_set=feature_set,
                feature_count=len(selected_features),
                prediction_count=len(model_result.predictions),
                metric_count=len(eval_result.metrics),
                portfolio_metric_count=len(eval_result.portfolio_metrics),
                multiple_testing_families=inference_result.multiple_testing_report.family_count,
            )
        )
        for metric in eval_result.metrics:
            if metric.role == "test" and metric.split_id == "ALL_SPLITS":
                all_metric_rows.append(
                    {"feature_set": feature_set, **metric.model_dump(mode="json")}
                )
        for metric in eval_result.portfolio_metrics:
            all_portfolio_rows.append(
                {"feature_set": feature_set, **metric.model_dump(mode="json")}
            )
        all_multiple_testing[feature_set] = inference_result.multiple_testing_report.model_dump(
            mode="json"
        )

    summary_payload = {
        "feature_set_summaries": [asdict(summary) for summary in summaries],
        "best_prediction_by_target": best_prediction_by_target(all_metric_rows),
        "best_portfolio_by_target": best_portfolio_by_target(all_portfolio_rows),
        "model_stability": model_stability(all_metric_rows, all_portfolio_rows),
        "multiple_testing": all_multiple_testing,
    }
    (output_dir / "real_10k_ablation_summary.json").write_text(
        json.dumps(summary_payload, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "real_10k_ablation_summary.md").write_text(
        render_markdown(summary_payload),
        encoding="utf-8",
    )
    print(json.dumps(summary_payload["feature_set_summaries"], indent=2))
    return 0


def best_prediction_by_target(rows: list[dict]) -> list[dict]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["target_name"]].append(row)
    output = []
    for _target, target_rows in sorted(grouped.items()):
        best = sorted(
            target_rows,
            key=lambda row: (-row["rank_ic"], row["rmse"], row["model_id"], row["feature_set"]),
        )[0]
        output.append(best)
    return output


def best_portfolio_by_target(rows: list[dict]) -> list[dict]:
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["target_name"]].append(row)
    output = []
    for _target, target_rows in sorted(grouped.items()):
        best = sorted(
            target_rows,
            key=lambda row: (
                -row["sharpe_ratio"],
                -row["annualized_return"],
                row["model_id"],
                row["feature_set"],
            ),
        )[0]
        output.append(best)
    return output


def model_stability(prediction_rows: list[dict], portfolio_rows: list[dict]) -> list[dict]:
    grouped = defaultdict(lambda: {"rank_ic": [], "sharpe": []})
    for row in prediction_rows:
        model = row["model_id"].split("::", 1)[0]
        grouped[(row["feature_set"], model)]["rank_ic"].append(row["rank_ic"])
    for row in portfolio_rows:
        model = row["model_id"].split("::", 1)[0]
        grouped[(row["feature_set"], model)]["sharpe"].append(row["sharpe_ratio"])
    output = []
    for (feature_set, model), values in sorted(grouped.items()):
        rank_values = values["rank_ic"]
        sharpe_values = values["sharpe"]
        output.append(
            {
                "feature_set": feature_set,
                "model": model,
                "mean_rank_ic": sum(rank_values) / len(rank_values) if rank_values else 0.0,
                "positive_rank_ic_count": sum(value > 0 for value in rank_values),
                "rank_ic_count": len(rank_values),
                "mean_sharpe": sum(sharpe_values) / len(sharpe_values) if sharpe_values else 0.0,
                "positive_sharpe_count": sum(value > 0 for value in sharpe_values),
                "sharpe_count": len(sharpe_values),
            }
        )
    return output


def render_markdown(payload: dict) -> str:
    lines = [
        "# Real 10-K Ablation Summary",
        "",
        "## Feature Sets",
        "",
        "| Feature set | Features | Predictions | Metrics | Portfolio metrics | MT families |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in payload["feature_set_summaries"]:
        lines.append(
            f"| {row['feature_set']} | {row['feature_count']} | "
            f"{row['prediction_count']} | {row['metric_count']} | "
            f"{row['portfolio_metric_count']} | {row['multiple_testing_families']} |"
        )
    lines.extend(["", "## Best Prediction By Target", ""])
    lines.extend(metric_table(payload["best_prediction_by_target"]))
    lines.extend(["", "## Best Portfolio By Target", ""])
    lines.extend(portfolio_table(payload["best_portfolio_by_target"]))
    lines.extend(["", "## Model Stability", ""])
    lines.extend(stability_table(payload["model_stability"]))
    lines.append("")
    return "\n".join(lines)


def metric_table(rows: list[dict]) -> list[str]:
    output = [
        "| Target | Feature set | Model | N | RMSE | Rank IC | Pearson IC | R2 |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        output.append(
            f"| {row['target_name']} | {row['feature_set']} | {row['model_id']} | "
            f"{row['observation_count']} | {row['rmse']:.4g} | {row['rank_ic']:.4g} | "
            f"{row['pearson_ic']:.4g} | {row['r_squared']:.4g} |"
        )
    return output


def portfolio_table(rows: list[dict]) -> list[str]:
    output = [
        "| Target | Feature set | Model | Variant | N | Ann Ret | Sharpe | Max DD | Turnover |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        output.append(
            f"| {row['target_name']} | {row['feature_set']} | {row['model_id']} | "
            f"{row['portfolio_variant']} | {row['observation_count']} | "
            f"{row['annualized_return']:.4g} | {row['sharpe_ratio']:.4g} | "
            f"{row['max_drawdown']:.4g} | {row['average_turnover']:.4g} |"
        )
    return output


def stability_table(rows: list[dict]) -> list[str]:
    output = [
        "| Feature set | Model | Mean Rank IC | Positive IC | Mean Sharpe | Positive Sharpe |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        output.append(
            f"| {row['feature_set']} | {row['model']} | {row['mean_rank_ic']:.4g} | "
            f"{row['positive_rank_ic_count']}/{row['rank_ic_count']} | "
            f"{row['mean_sharpe']:.4g} | {row['positive_sharpe_count']}/{row['sharpe_count']} |"
        )
    return output


if __name__ == "__main__":
    raise SystemExit(main())
