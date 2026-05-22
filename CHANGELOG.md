# Changelog

## [v0.6.0] - 2026-05-21

Step 14 release for complete local MVP deployment packaging.

- Added config-level input paths for `document_manifest.jsonl`, `prices.csv`,
  `parsed_sections.jsonl`, and local `raw_filings_dir`.
- Extended `run --execute` so it can copy configured inputs into the run
  directory, parse local raw 10-K filings when parsed sections are absent, and
  continue through features, models, evaluation, audit, and report.
- Upgraded `pipeline_contract.json` and `orchestrator_report.json` to describe
  the complete local MVP controller.
- Added GitHub Actions CI for lint and test on pushes and pull requests.
- Added `Dockerfile`, `Makefile`, and a committed `e2e_smoke` fixture run
  config for one-command local validation.
- Added Step 14 deployment and reproducibility documentation.
- Added tests for configured input paths, raw filing parsing orchestration, and
  the full `e2e_smoke` CLI pipeline.

Release notes: [docs/releases/v0.6.0.md](docs/releases/v0.6.0.md)

## [v0.5.0] - 2026-05-21

Step 14.1 release for the artifact-aware orchestrator.

- Added `python -m text_factor_lab run --config <path> --execute`.
- Added resumable run-dir orchestration for labels, splits, features, models,
  evaluation, audit, and report.
- Added `orchestrator_report.json` with completed, skipped, blocked, and failed
  stage records.
- Added standard run-dir artifact conventions to `pipeline_contract.json`.
- Preserved initialization-only behavior when `--execute` is not provided.
- Added tests for successful midstream orchestration and missing-input blocking.

Release notes: [docs/releases/v0.5.0.md](docs/releases/v0.5.0.md)

## [v0.4.0] - 2026-05-20

Step 13 release for the Report Agent.

- Added `text_factor_lab.reports` with Markdown and JSON report generation.
- Added `python -m text_factor_lab report` CLI support.
- Added formal/exploratory/diagnostic conclusion levels.
- Added report gating so failed audits do not produce formal reports by default.
- Added run status update from `audited` to `reported`.
- Added report generator tests and CLI coverage.

Release notes: [docs/releases/v0.4.0.md](docs/releases/v0.4.0.md)

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

Future research-grade work includes formal universe construction, SEC download
scheduling, richer portfolio time-series backtests, cloud dashboard packaging,
FinBERT / LLM embedding modules, earnings-call ingestion, and credit-risk
targets.
