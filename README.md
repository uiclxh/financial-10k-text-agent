# Financial 10-K Text Agent

Language:

- [Chinese](README.zh-CN.md)
- [English](README.en.md)

## Snapshot

Financial 10-K Text Agent is an auditable empirical-finance pipeline for 10-K
text factor research. It is not a generic Financial RAG app. The current codebase
now covers Steps 1-14 of the MVP workflow:

```text
config -> universe -> SEC metadata -> parsing -> labels -> rolling splits
       -> text features -> model training -> evaluation -> backtest -> audit
       -> report -> local orchestrator -> CI/deployment packaging
```

Release notes:

- [v0.1.0 Phase 1 - Foundation / Project Initialization](docs/releases/v0.1.0.md)
- [v0.2.0 Phase 2 - Data, Parsing, Labels, Splits, Features](docs/releases/v0.2.0.md)
- [v0.3.0 Phase 3 - Models, Evaluation, Backtest, Audit](docs/releases/v0.3.0.md)
- [v0.4.0 Step 13 - Report Agent](docs/releases/v0.4.0.md)
- [v0.5.0 Step 14.1 - Artifact-Aware Orchestrator](docs/releases/v0.5.0.md)
- [v0.6.0 Step 14 - Complete Local MVP Deployment](docs/releases/v0.6.0.md)

Deployment guide:

- [Step 14 Deployment And Reproducibility](docs/deployment.md)

Quick validation:

```bash
python -m pytest
python -m ruff check .
python -m text_factor_lab run --config configs/text_factor_lab/mvp_v0.yaml
python -m text_factor_lab run --config configs/text_factor_lab/mvp_v0.yaml --execute
python -m text_factor_lab run --config configs/text_factor_lab/e2e_smoke.yaml --execute
python -m pytest
python -m ruff check .
```

Main implemented CLI commands:

```bash
python -m text_factor_lab parse-10k --help
python -m text_factor_lab build-labels --help
python -m text_factor_lab build-splits --help
python -m text_factor_lab build-features --help
python -m text_factor_lab build-models --help
python -m text_factor_lab evaluate-models --help
python -m text_factor_lab audit --help
python -m text_factor_lab report --help
```

The governing workflow specification is:

```text
FINANCIAL_TEXT_FACTOR_LAB_GLOBAL_WORKFLOW.md
```
