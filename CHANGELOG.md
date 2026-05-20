# Changelog

## [v0.1.0] - 2026-05-20

MVP workflow release covering Steps 1-12.

Added:

- SEC 10-K metadata and section parsing foundations.
- Price-based label builder and rolling-year split layer.
- Dictionary tone and train-window TF-IDF feature layer.
- Model training layer with `historical_mean`, `industry_mean`, `ridge`, and optional `xgboost`.
- Evaluation metrics including RMSE, MAE, R2, directional accuracy, Pearson IC, and rank IC.
- Event-based long-short backtest with transaction cost, Newey-West t-stat, and Sharpe ratio.
- Audit gate with schema, coverage, prediction-label alignment, leakage, tuning, and tested-spec checks.

See full release notes:

- [docs/releases/v0.1.0.md](docs/releases/v0.1.0.md)
