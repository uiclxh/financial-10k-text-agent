# Financial 10-K Text Agent

An auditable research pipeline for turning SEC 10-K filings into financial text
factors. The project is not a chatbot or financial RAG demo: it is a
configuration-driven empirical finance workflow for text features, event-time
labels, model comparison, portfolio backtests, audit gates, and reproducible
reports.

[English README](README.en.md) | [Chinese README](README.zh-CN.md) |
[Global Workflow](FINANCIAL_TEXT_FACTOR_LAB_GLOBAL_WORKFLOW.md) |
[Deployment Guide](docs/deployment.md)

## Fast Mental Model

```text
SEC 10-K / local filings
        |
        v
document manifest -> 10-K parser -> parsed sections
        |                              |
        v                              v
price panel -> labels -> splits -> text features
                                      |
                                      v
                         models -> predictions
                                      |
                                      v
                    evaluation -> portfolio backtest
                                      |
                                      v
                              audit -> report
```

## What It Produces

The core outputs are research artifacts, not conversational answers:

- `document_manifest.jsonl`
- `parsed_sections.jsonl`
- `labels.jsonl`
- `split_assignments.jsonl`
- `features.jsonl` and `feature_manifest.json`
- `predictions.jsonl`
- `evaluation_metrics.json`
- `backtest_results.json`
- `portfolio_weights.jsonl`
- `portfolio_returns.jsonl`
- `portfolio_metrics.json`
- `tested_specifications.jsonl`
- `multiple_testing_report.json`
- `audit_report.json`
- `report.md` and `report_summary.json`
- `empirical_report.md`
- `factor_card.md`
- `appendix_tables.md`

## Current Status

Current package version: `v0.12.0`

The repository now contains a runnable MVP research framework:

- one-command local orchestration with `run --execute`
- SEC 10-K section parsing
- CAR and realized-volatility label construction
- rolling-year splits and leakage checks
- dictionary tone and train-window TF-IDF features
- `historical_mean`, `industry_mean`, `ridge`, and optional `xgboost`
- RMSE, MAE, R2, directional accuracy, Pearson IC, and rank IC
- event-level long-short backtest
- portfolio time-series artifacts
- equal-weight, value-weight, sector-neutral equal-weight, and sector-neutral
  value-weight portfolio variants when metadata is available
- tested-specification registry and Holm / Benjamini-Hochberg FDR
  multiple-testing adjustment report
- empirical report, factor card, and appendix table report artifacts
- research-grade universe schemas for security master, membership intervals,
  and entity link history
- NYSE calendar event-date alignment with holiday and early-close handling
- audit-gated Markdown/JSON reports
- GitHub Actions CI, Dockerfile, Makefile, and e2e smoke fixture

## Quick Start

```bash
python -m pip install -e ".[dev]"
python -m text_factor_lab run --config configs/text_factor_lab/e2e_smoke.yaml --execute
```

Or with Make:

```bash
make install
make smoke-run
```

Key run outputs:

```text
runs/text_factor_lab/tflab_e2e_smoke_001/report.md
runs/text_factor_lab/tflab_e2e_smoke_001/audit_report.json
runs/text_factor_lab/tflab_e2e_smoke_001/orchestrator_report.json
```

## Main Commands

```bash
python -m text_factor_lab run --config configs/text_factor_lab/mvp_v0.yaml
python -m text_factor_lab run --config configs/text_factor_lab/mvp_v0.yaml --execute
python -m text_factor_lab build-features --help
python -m text_factor_lab build-models --help
python -m text_factor_lab evaluate-models --help
python -m text_factor_lab audit --help
python -m text_factor_lab report --help
```

## Release Map

| Release | Focus | Summary |
|---|---|---|
| [v0.1.0](docs/releases/v0.1.0.md) | Foundation | package scaffold, config, schemas, run status |
| [v0.2.0](docs/releases/v0.2.0.md) | Data pipeline | universe, SEC metadata, parser, labels, splits, features |
| [v0.3.0](docs/releases/v0.3.0.md) | Research core | models, evaluation, event backtest, audit |
| [v0.4.0](docs/releases/v0.4.0.md) | Report Agent | Markdown report, JSON summary, audit-gated conclusion |
| [v0.5.0](docs/releases/v0.5.0.md) | Orchestrator | artifact-aware `run --execute` controller |
| [v0.6.0](docs/releases/v0.6.0.md) | Deployment MVP | CI, Dockerfile, Makefile, e2e smoke run |
| [v0.7.0](docs/releases/v0.7.0.md) | Event Calendar | NYSE trading calendar and event-date audit fields |
| [v0.8.0](docs/releases/v0.8.0.md) | Portfolio Series | portfolio weights, returns, turnover, metrics |
| [v0.9.0](docs/releases/v0.9.0.md) | Portfolio Variants | value-weight and sector-neutral portfolio construction |
| [v0.10.0](docs/releases/v0.10.0.md) | Multiple Testing | tested specs, Holm, BH-FDR adjustment report |
| [v0.11.0](docs/releases/v0.11.0.md) | Empirical Reports | empirical report, factor card, appendix tables |
| [v0.12.0](docs/releases/v0.12.0.md) | Research Universe | security master, membership intervals, entity links |

## Boundaries

This is a strong MVP research framework, not yet a full empirical finance
replication package. Remaining research-grade work includes licensed CRSP/WRDS
or equivalent universe population, delisting returns, daily price-driven
holdings, Deflated Sharpe, CPCV/PBO, FinBERT / LLM embedding modules,
earnings-call ingestion, and credit-risk targets.
