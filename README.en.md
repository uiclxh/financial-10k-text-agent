# Financial 10-K Text Agent

English | [中文](README.zh-CN.md)

## Project Scope

`Financial 10-K Text Agent` is the MVP implementation of a financial text factor research agent. It is not a generic Financial RAG system. It is an empirical finance pipeline for reproducible and auditable text factor research:

```text
experiment config
  -> data acquisition
  -> document parsing
  -> label construction
  -> rolling split
  -> feature/model/backtest/audit/report extensions
```

The current version focuses on the first eight engineering steps: config, schemas, run management, SEC 10-K metadata, 10-K section parsing, price-based labels, rolling splits, and leakage checks.

## Current Version

- Current release: [v0.1.0 Foundation Release](docs/releases/v0.1.0.md)
- Python package version: `0.1.0`
- MVP config: [configs/text_factor_lab/mvp_v0.yaml](configs/text_factor_lab/mvp_v0.yaml)
- Global workflow spec: [FINANCIAL_TEXT_FACTOR_LAB_GLOBAL_WORKFLOW.md](FINANCIAL_TEXT_FACTOR_LAB_GLOBAL_WORKFLOW.md)

## Implemented Capabilities

### 1. Project Scaffold

- Python package: `text_factor_lab`
- CLI entry point: `python -m text_factor_lab`
- Test framework: `pytest`
- Linting: `ruff`
- Base folders: `configs/`, `src/`, `tests/`, `runs/`, `data/`

### 2. Config and Schemas

Implemented Pydantic schemas:

- experiment config
- document manifest
- features
- labels
- predictions
- model manifest
- run status
- universe manifest
- parsed sections
- rolling split assignments

Formal-run gates are encoded in schemas:

- SEC EDGAR formal runs require `sec_user_agent`
- formal runs require `available_time` and `license_note`
- labels must satisfy `prediction_time_utc < label_start_date`
- split windows must satisfy `train < validation < test`

### 3. Orchestrator / Run Manager

Run initialization now supports YAML config loading, run directory creation, `config_snapshot.yaml`, `run_status.json`, `failure_log.jsonl`, and universe quality report.

Command:

```bash
python -m text_factor_lab run --config configs/text_factor_lab/mvp_v0.yaml
```

### 4. Universe Manifest

The fixed universe manifest validator supports `entity_id`, `ticker`, `cik`, `company_name`, `selection_date`, `mapping_source`, `delisting_date`, `sector`, and `industry`.

The MVP sample universe is:

```text
configs/universe/us_large_cap_2010.csv
```

### 5. SEC EDGAR Filing Metadata

SEC EDGAR 10-K metadata utilities support CIK normalization, SEC submissions URL construction, SEC Archives document URL construction, annual filing filtering, acceptance time conversion to UTC, document manifest record creation, SEC license note, and SHA256 hash interface.

Core file:

```text
src/text_factor_lab/data/sec_edgar.py
```

### 6. SEC 10-K Section Parser

The 10-K parser supports HTML/text normalization, `script/style` removal, `Item 1`, `Item 1A`, `Item 3`, `Item 7` extraction, table-of-contents false-positive avoidance, section char spans, section text hashes, `missing` status for missing sections, `failed` status for empty sections, and default exclusion of `10-K/A` amendments.

Command:

```bash
python -m text_factor_lab parse-10k \
  --manifest-record path/to/manifest_record.json \
  --document path/to/10k.html \
  --output-dir runs/example/parsed
```

### 7. Price Data and Label Builder

The price and label layer supports CSV price panel loading, `simple_return`, `log_return`, forward trading windows, `CAR_1_n`, `realized_volatility_1_n`, `realized_volatility_annualized_1_n`, and label failure reports.

Explicit failure reasons include missing price, missing benchmark, insufficient forward window, and unsupported target.

Command:

```bash
python -m text_factor_lab build-labels \
  --document-manifest path/to/document_manifest.jsonl \
  --prices path/to/prices.csv \
  --labels-output runs/example/labels.jsonl \
  --failures-output runs/example/label_failures.jsonl \
  --target CAR_1_20 \
  --target realized_volatility_1_20
```

### 8. Rolling Year Split and Leakage Checks

The rolling split layer supports expanding train window, rolling validation window, rolling test window, embargo days, split assignment JSONL, and leakage report JSONL.

Implemented checks: train label window crossing validation embargo, validation label window crossing test embargo, test label start before/on event date, and unordered split windows.

Command:

```bash
python -m text_factor_lab build-splits \
  --labels runs/example/labels.jsonl \
  --assignments-output runs/example/split_assignments.jsonl \
  --leakage-output runs/example/split_leakage.jsonl \
  --sample-start 2010-01-01 \
  --sample-end 2024-12-31 \
  --train-years-min 5 \
  --validation-years 1 \
  --test-years 1 \
  --embargo-days 20
```

## Install and Validate

Recommended Python version: `Python >= 3.11`

Install development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run validation:

```bash
python -m pytest
python -m ruff check .
```

Current v0.1.0 acceptance result:

```text
54 passed
All checks passed
```

## Current Boundaries

v0.1.0 is a foundation release. It does not yet implement dictionary tone features, TF-IDF features, train-window-only vocabulary fitting, Ridge / XGBoost training, model comparison, factor backtest, econometric report, full audit/report agent, FinBERT / LLM embeddings / LSTM, earnings call transcript pipeline, or credit risk targets.

## Recommended Next Step

Next:

```text
Step 9: dictionary tone + TF-IDF feature layer
```

Then:

```text
Step 10: baseline / Ridge / XGBoost model layer
Step 11: out-of-sample evaluation
Step 12: factor backtest
Step 13: audit and report
Step 14: deployment and reproducibility packaging
```
