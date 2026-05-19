# Remote Upload Check

Date: 2026-05-19

This repository was populated through the GitHub plugin/API because local `git push` connectivity to `github.com:443` was unavailable.

## Local validation before upload

```text
python -m pytest       -> 18 passed
python -m ruff check . -> All checks passed
python -m text_factor_lab run --config configs/text_factor_lab/mvp_v0.yaml -> Run initialized
```

## API-uploaded MVP step 1-3 files

Core scaffold, config, schema, orchestrator, and tests have been uploaded through GitHub plugin/API:

```text
.gitignore
README.md
pyproject.toml
requirements.lock
configs/text_factor_lab/mvp_v0.yaml
configs/universe/us_large_cap_2010.csv
configs/text_factor_lab/.gitkeep
configs/universe/.gitkeep
data/.gitkeep
src/text_factor_lab/__init__.py
src/text_factor_lab/__main__.py
src/text_factor_lab/cli.py
src/text_factor_lab/audit/__init__.py
src/text_factor_lab/backtest/__init__.py
src/text_factor_lab/data/__init__.py
src/text_factor_lab/features/__init__.py
src/text_factor_lab/labels/__init__.py
src/text_factor_lab/models/__init__.py
src/text_factor_lab/orchestration/__init__.py
src/text_factor_lab/orchestration/run_manager.py
src/text_factor_lab/parsing/__init__.py
src/text_factor_lab/reports/__init__.py
src/text_factor_lab/schemas/__init__.py
src/text_factor_lab/schemas/base.py
src/text_factor_lab/schemas/config.py
src/text_factor_lab/schemas/document_manifest.py
src/text_factor_lab/schemas/features.py
src/text_factor_lab/schemas/labels.py
src/text_factor_lab/schemas/model_manifest.py
src/text_factor_lab/schemas/predictions.py
src/text_factor_lab/schemas/run_status.py
tests/test_config_schema.py
tests/test_project_smoke.py
tests/test_run_manager.py
tests/test_schema_validation.py
tests/expected_outputs/.gitkeep
tests/fixtures/.gitkeep
tests/sample_data/.gitkeep
```

## Plugin/API spot checks

The following remote files were fetched back through the GitHub plugin/API and confirmed readable:

```text
.gitignore
README.md
FINANCIAL_TEXT_FACTOR_LAB_GLOBAL_WORKFLOW.md
src/text_factor_lab/orchestration/run_manager.py
src/text_factor_lab/schemas/config.py
tests/test_run_manager.py
tests/test_schema_validation.py
```

## Known difference

`FINANCIAL_TEXT_FACTOR_LAB_GLOBAL_WORKFLOW.md` on GitHub is currently an abridged placeholder. The complete source-of-truth file remains local at:

```text
E:\financial_10K_text_agent\FINANCIAL_TEXT_FACTOR_LAB_GLOBAL_WORKFLOW.md
```

Reason: the full workflow file is large and contains Chinese text; local direct GitHub network access is currently blocked, and uploading it through the plugin without direct file streaming risks corrupting or truncating the document.

When local access to `github.com:443` works, run:

```bash
git push -u origin main
```

to synchronize the complete local file and exact commit history.
