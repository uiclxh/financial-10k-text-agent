# Changelog

## [v0.13.0] - 2026-05-23

Daily price-driven portfolio return release.

- Added optional price-panel input to `build_evaluation_artifacts`.
- Added `--prices` to `evaluate-models`.
- Added `--portfolio-return-type` to `evaluate-models`.
- Added daily price-driven portfolio return simulation when a price panel is
  available.
- Added `return_source` to `PortfolioReturnRecord`.
- Marked label-window portfolio returns as `label_window`.
- Marked price-driven daily portfolio returns as `daily_price_panel`.
- Updated `run --execute` to use run-dir `prices.csv` for portfolio simulation
  when available.
- Added report summary tracking for portfolio return sources.
- Added tests for daily price-driven portfolio returns and e2e smoke return
  source validation.

Release notes: [docs/releases/v0.13.0.md](docs/releases/v0.13.0.md)

## [v0.12.0] - 2026-05-23

Research-grade universe schema release.

- Added `SecurityMasterRecord`.
- Added `UniverseMembershipRecord`.
- Added `EntityLinkHistoryRecord`.
- Added optional config paths for `security_master_file`, `membership_file`,
  and `entity_link_history_file`.
- Added `universe_data_level` with `exploratory`, `applied`, and
  `research_grade` levels.
- Added CSV loaders for security master, membership intervals, and entity link
  history.
- Extended `universe_quality_report.json` with research-grade table counts,
  linking diagnostics, low-confidence link counts, membership market-cap checks,
  and delisted membership counts.
- Added formal blockers for missing or inconsistent research-grade universe
  tables.
- Added research-grade universe example CSVs and template YAML.
- Added tests for table loading, passing research-grade quality reports, and
  missing-table blockers.

Release notes: [docs/releases/v0.12.0.md](docs/releases/v0.12.0.md)

## [v0.11.0] - 2026-05-23

Empirical report package release.

- Added `empirical_report.md` generation.
- Added `factor_card.md` generation.
- Added `appendix_tables.md` generation.
- Added structured interpretation policy to report summary.
- Added empirical report sections for research design, event-time alignment,
  text features, labels, models, OOS results, portfolio construction,
  multiple-testing adjustment, audit results, economic interpretation,
  limitations, and conclusion.
- Added factor card with audit status, evidence level, best prediction,
  best backtest, and usage boundary.
- Added appendix tables for sample coverage, feature summary, prediction
  metrics, portfolio results, portfolio variants, multiple-testing results,
  and audit checks.
- Integrated new report artifacts into CLI output and orchestrator stage
  outputs.
- Added report and e2e smoke tests for the new artifacts.

Release notes: [docs/releases/v0.11.0.md](docs/releases/v0.11.0.md)

## [v0.10.0] - 2026-05-23

Multiple-testing and specification-registry release.

- Added `TestedSpecificationRecord`, `MultipleTestingFamilyRecord`, and
  `MultipleTestingReportRecord` schemas.
- Added `text_factor_lab.inference` for tested-specification generation and
  multiple-testing adjustment.
- Added `tested_specifications.jsonl`.
- Added `multiple_testing_report.json`.
- Added Bonferroni, Holm, and Benjamini-Hochberg FDR adjusted p-values.
- Added specification families for Rank IC, Newey-West t-stat, and portfolio
  Sharpe diagnostics.
- Integrated inference artifacts into `evaluate-models`, `run --execute`,
  audit checks, and generated reports.
- Added tests for inference artifact generation, writer round trips, audit
  acceptance, and e2e smoke output.

Release notes: [docs/releases/v0.10.0.md](docs/releases/v0.10.0.md)

## [v0.9.0] - 2026-05-23

Portfolio variant release.

- Added optional `sector`, `industry`, and `market_cap` metadata to prediction
  records.
- Propagated metadata features through the model layer into predictions.
- Added portfolio variant fields to portfolio weight, return, and metric
  schemas.
- Added automatic portfolio construction variants:
  - `equal_weight`
  - `value_weight`
  - `sector_neutral_equal_weight`
  - `sector_neutral_value_weight`
- Added value-weight leg sizing from market cap when available.
- Added sector-neutral construction that ranks inside each sector and allocates
  balanced long and short exposure across eligible sectors.
- Added tests for value-weight and sector-neutral exposure behavior.

Release notes: [docs/releases/v0.9.0.md](docs/releases/v0.9.0.md)

## [v0.8.0] - 2026-05-22

Portfolio time-series backtest release.

- Added portfolio weight, return, and metric schemas.
- Added `portfolio_weights.jsonl`, `portfolio_returns.jsonl`, and
  `portfolio_metrics.json` artifacts.
- Added equal-weight dollar-neutral top/bottom portfolio construction from test
  factor scores.
- Added rebalance-level normalized weights, previous weights, trade weights, and
  realized turnover.
- Added portfolio return series with gross return, transaction cost, net return,
  exposure diagnostics, active position counts, and turnover.
- Added portfolio-level cumulative return, annualized return, annualized
  volatility, Sharpe ratio, max drawdown, hit rate, and average exposure metrics.
- Extended the local orchestrator and `evaluate-models` CLI to write the new
  portfolio artifacts.
- Added tests for portfolio time-series turnover and end-to-end artifact output.

Release notes: [docs/releases/v0.8.0.md](docs/releases/v0.8.0.md)

## [v0.7.0] - 2026-05-22

Research-grade event calendar release.

- Added `text_factor_lab.calendar` with NYSE market-session resolution powered
  by `pandas-market-calendars`.
- Replaced fixed 16:00 SEC event-date logic with market-calendar open/close
  schedule handling.
- Added event-date audit metadata to `DocumentManifestRecord`, including raw
  filing date, acceptance time, market open/close, early-close flag, event-date
  policy, resolved event date, and resolver version.
- Added tests for pre-open, intraday, after-close, weekend, holiday, and
  early-close filings.
- Added SEC manifest tests for event-date audit fields.

Release notes: [docs/releases/v0.7.0.md](docs/releases/v0.7.0.md)

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
scheduling, daily price-driven holdings, multiple-testing reports, cloud
dashboard packaging, FinBERT / LLM embedding modules, earnings-call ingestion,
and credit-risk targets.
