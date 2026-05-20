# Financial 10-K Text Agent

Language / 语言:

- [中文](README.zh-CN.md)
- [English](README.en.md)

## Snapshot

Financial 10-K Text Agent is the MVP implementation of a financial text factor
research agent. It is designed to build reproducible, auditable text factors from
SEC filings, align them with event-time labels, and prepare leakage-safe rolling
splits for out-of-sample empirical finance experiments.

Current release:

- [v0.1.0: Foundation Release](docs/releases/v0.1.0.md)

Quick validation:

```bash
python -m pytest
python -m ruff check .
python -m text_factor_lab run --config configs/text_factor_lab/mvp_v0.yaml
```

The governing workflow specification is:

```text
FINANCIAL_TEXT_FACTOR_LAB_GLOBAL_WORKFLOW.md
```
