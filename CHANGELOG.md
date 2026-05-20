# Changelog

## [v0.3.0] - 2026-05-20

Phase 3 release for Steps 9-12: models, evaluation, event-based backtest, and
audit gate.

- Added `historical_mean`, `industry_mean`, `ridge`, and optional `xgboost`.
- Added validation-safe prediction flow for Ridge and XGBoost.
- Added RMSE, MAE, R2, directional accuracy, Pearson IC, and rank IC.
- Added event-based long-short backtest with transaction cost, Newey-West t-stat,
  and Sharpe ratio.
- Added audit checks for schema validity, coverage, prediction-label alignment,
  feature lookahead, TF-IDF fit scope, vocabulary alignment, tuning leakage, and
  tested-specification disclosure.

Release notes: [docs/releases/v0.3.0.md](docs/releases/v0.3.0.md)

## [v0.2.0] - 2026-05-20

Phase 2 release for Steps 4-8 plus features: universe, SEC metadata, parsing,
price labels, rolling splits, leakage checks, and text features.

- Added fixed universe validation.
- Added SEC EDGAR 10-K metadata helpers.
- Added 10-K section parser for Item 1, Item 1A, Item 3, and Item 7.
- Added price loader, CAR labels, realized volatility labels, and label failures.
- Added rolling-year split assignments and leakage reports.
- Added dictionary tone and train-window TF-IDF features.
- Added `feature_manifest.json` and `vocabulary.json`.

Release notes: [docs/releases/v0.2.0.md](docs/releases/v0.2.0.md)

## [v0.1.0] - 2026-05-20

Phase 1 release for Steps 1-3: project initialization, schema layer, and
orchestrator scaffold.

- Added Python package scaffold.
- Added MVP config.
- Added Pydantic schema foundations.
- Added run manager initialization.
- Added run status, config snapshot, and failure log foundations.

Release notes: [docs/releases/v0.1.0.md](docs/releases/v0.1.0.md)

## Planned

Step 13-14 will be released later after report generation, CLI polish,
dashboard/deployment packaging, and reproducibility hardening are implemented.
