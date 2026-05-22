# Step 14 Deployment And Reproducibility

This project is deployed local-first. The code, schemas, tests, and CI workflow
belong in GitHub; licensed filings, price panels, generated run artifacts, model
caches, and reports stay local unless they are small demo fixtures.

## Local Setup

Use Python 3.11 or newer. The GitHub CI workflow pins Python 3.11 as the
portable baseline.

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Optional XGBoost support:

```bash
python -m pip install -e ".[dev,ml]"
```

## Run Modes

Initialize a run workspace and write the run contract:

```bash
python -m text_factor_lab run --config configs/text_factor_lab/mvp_v0.yaml
```

Execute the local MVP pipeline against configured or existing artifacts:

```bash
python -m text_factor_lab run --config configs/text_factor_lab/mvp_v0.yaml --execute
```

The executable run command can copy configured inputs into the run directory:

```yaml
inputs:
  document_manifest_path: "local_inputs/document_manifest.jsonl"
  prices_path: "local_inputs/prices.csv"
  parsed_sections_path: null
  raw_filings_dir: "local_inputs/raw_filings"
  copy_inputs_to_run_dir: true
```

If `parsed_sections.jsonl` is absent and `raw_filings_dir` is provided, the
orchestrator parses local 10-K files listed by `document_manifest.jsonl`, writes
`parsed_sections.jsonl`, and then continues through features, models,
evaluation, audit, and report.

## Required Local Artifacts

For a full local execution from parsed text:

- `document_manifest.jsonl`
- `prices.csv`
- `parsed_sections.jsonl`

For a full local execution from raw local 10-K files:

- `document_manifest.jsonl`
- `prices.csv`
- `inputs.raw_filings_dir`

For a midstream execution:

- `labels.jsonl`
- `split_assignments.jsonl`
- `split_leakage.jsonl`
- `features.jsonl`
- `feature_manifest.json`
- `vocabulary.json`

The controller skips stages whose outputs already exist and records every
completed, skipped, blocked, or failed stage in `orchestrator_report.json`.

## End-To-End Smoke Run

The repository includes a tiny license-safe smoke run under `examples/e2e_smoke`.
It uses synthetic tickers, a small synthetic price panel, and the repository SEC
parser fixture. It is only for engineering validation.

```bash
python -m text_factor_lab run --config configs/text_factor_lab/e2e_smoke.yaml --execute
```

Equivalent Make target:

```bash
make smoke-run
```

Expected outputs are written to:

```text
runs/text_factor_lab/tflab_e2e_smoke_001/
```

Key artifacts:

- `orchestrator_report.json`
- `parsed_sections.jsonl`
- `labels.jsonl`
- `split_assignments.jsonl`
- `features.jsonl`
- `predictions.jsonl`
- `evaluation_metrics.json`
- `backtest_results.json`
- `audit_report.json`
- `report.md`

## Validation

Run these before creating a release or sharing artifacts:

```bash
make lint
make test
python -m ruff check .
python -m pytest
```

The GitHub Actions workflow at `.github/workflows/tests.yml` runs the same lint
and test checks on pull requests and pushes to `main`. The test suite includes
the `e2e_smoke` run, so CI verifies the local pipeline can execute end to end on
small fixtures.

## Docker

Build a local image:

```bash
make docker-build
```

Run the smoke pipeline inside the image:

```bash
make docker-smoke
```

The Docker image is intended for reproducible local validation. It does not
bundle licensed data and should not be treated as a production research service.

## Artifact Policy

Keep these local by default:

- `runs/`
- `data/raw/`
- `data/processed/`
- `/reports/`
- `model_cache/`
- `*.parquet`
- `*.pkl`
- `*.joblib`

Only commit small fixtures under `tests/fixtures/` when they are license-safe and
needed for CI.

## Deployment Boundary

Step 14 completes the local reproducible MVP deployment path and GitHub CI smoke
deployment. It does not claim production-grade cloud deployment. Research-grade
formal runs still require licensed or research-grade universe, prices, filing
coverage, and benchmark data.
