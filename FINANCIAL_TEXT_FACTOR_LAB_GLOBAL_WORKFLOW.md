# Financial Text Factor Lab Agent Global Workflow v1.3

This repository is governed by the local full workflow specification developed in `E:\financial_10K_text_agent\FINANCIAL_TEXT_FACTOR_LAB_GLOBAL_WORKFLOW.md`.

The MVP v0 implementation currently follows these active rules:

- 10-K only for the initial MVP.
- US large-cap fixed universe.
- Config-driven experiments via `configs/text_factor_lab/mvp_v0.yaml`.
- Pydantic schemas for config, manifests, features, labels, predictions, model manifest, and run status.
- Orchestrator-owned run initialization, config snapshot, `run_status.json`, and `failure_log.jsonl`.
- Formal run gates for `available_time`, `license_note`, no look-ahead leakage, and no train-test leakage.
- Rolling-year split design.
- Initial validation commands:

```bash
python -m pytest
python -m ruff check .
python -m text_factor_lab run --config configs/text_factor_lab/mvp_v0.yaml
```

The local full Chinese/English workflow remains the source-of-truth until direct `git push` connectivity to GitHub is restored. Once network access to `github.com:443` works, run:

```bash
git push -u origin main
```

to replace this abridged GitHub copy with the complete local specification and exact local commit history.
