"""Factor portfolio construction and backtesting."""

from text_factor_lab.backtest.evaluation import (
    BACKTEST_VERSION,
    EvaluationBuildResult,
    ScoredPrediction,
    build_evaluation_artifacts,
    newey_west_t_stat,
    pearson_ic,
    read_labels_jsonl,
    read_predictions_jsonl,
    write_backtest_results_json,
    write_evaluation_metrics_json,
)

__all__ = [
    "BACKTEST_VERSION",
    "EvaluationBuildResult",
    "ScoredPrediction",
    "build_evaluation_artifacts",
    "newey_west_t_stat",
    "pearson_ic",
    "read_labels_jsonl",
    "read_predictions_jsonl",
    "write_backtest_results_json",
    "write_evaluation_metrics_json",
]
