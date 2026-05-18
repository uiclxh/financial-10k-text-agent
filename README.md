# Financial 10-K Text Agent

This project implements the MVP v0 of the Financial Text Factor Lab Agent:

- 10-K only
- US large-cap fixed universe
- dictionary tone and TF-IDF features
- realized volatility and CAR labels
- rolling year split
- baseline, Ridge, and XGBoost model comparison
- audit report, factor cards, and reproducible run outputs

The governing specification is:

```text
FINANCIAL_TEXT_FACTOR_LAB_GLOBAL_WORKFLOW.md
```

Initial local commands:

```bash
python -m pytest
python -m text_factor_lab --help
```
