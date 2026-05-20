# Financial 10-K Text Agent

English | [中文](README.zh-CN.md)

## Project Scope

`Financial 10-K Text Agent` is an MVP implementation of a financial text factor
research agent. It builds reproducible, auditable text factors from SEC 10-K
filings, aligns them with event-time labels, trains baseline models, evaluates
out-of-sample predictions, runs an event-based long-short backtest, and blocks
formal results that fail audit gates.

## Current Status

Implemented through Step 12:

1. Project scaffold
2. Config and Pydantic schemas
3. Run manager and status machine
4. Fixed universe manifest validation
5. SEC EDGAR 10-K metadata utilities
6. SEC 10-K section parser
7. Price data and label builder
8. Rolling-year splits and leakage checks
9. Dictionary tone and train-window TF-IDF features
10. Model layer: `historical_mean`, `industry_mean`, `ridge`, optional `xgboost`
11. Evaluation metrics: RMSE, MAE, R2, directional accuracy, Pearson IC, rank IC
12. Event-based long-short backtest and audit gate

## Key Commands

```bash
python -m text_factor_lab run --config configs/text_factor_lab/mvp_v0.yaml
python -m text_factor_lab build-features --help
python -m text_factor_lab build-models --help
python -m text_factor_lab evaluate-models --help
python -m text_factor_lab audit --help
```

## Artifacts

The MVP pipeline works with these research artifacts:

- `document_manifest.jsonl`
- `parsed_sections.jsonl`
- `labels.jsonl`
- `split_assignments.jsonl`
- `split_leakage.jsonl`
- `features.jsonl`
- `feature_manifest.json`
- `predictions.jsonl`
- `model_manifest.json`
- `tuning_log.json`
- `evaluation_metrics.json`
- `backtest_results.json`
- `audit_report.json`

## Validation

```bash
python -m pytest
python -m ruff check .
```

Current local acceptance result:

```text
74+ tests pass
ruff passes
```

## Boundaries

This is still an MVP, not a full research-grade production system. Remaining
work includes full sector-neutral portfolio construction, richer portfolio time
series, multiple-testing adjustment reports, final report generation, FinBERT /
LLM embedding modules, earnings-call transcript ingestion, and credit-risk
targets.
