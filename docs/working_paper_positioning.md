# Working Paper Positioning

## Recommended Title

**A Leakage-Safe Financial 10-K Text Agent for Out-of-Sample Volatility Forecasting**

Alternative title:

**From SEC 10-K Filings to Auditable Text Factors: An Agentic Pipeline for Financial NLP Research**

## Primary Research Question

**Can 10-K textual information produce leakage-controlled out-of-sample forecasting signals?**

The paper should not be positioned as a stock-return prediction or trading-alpha paper. The safer framing is an auditable empirical pipeline with applied-grade volatility evidence, explicit data boundaries, and diagnostic portfolio tests.

## Current Evidence Hierarchy

### Current Primary Public Package

The current primary public package is the **50-company FMP/Yahoo applied-grade pilot**:

[docs/results/50_company_public_fmp_alpha_2016_2025_v1](results/50_company_public_fmp_alpha_2016_2025_v1/README.md)

| Item | Value |
| --- | ---: |
| Companies | 50 |
| SEC 10-K filings | 500 |
| Labels | 1,500 |
| OOS predictions | 4,716 |
| Feature records | 520k+ |
| Eligible OOS coverage | 100% |
| Audit failures | 0 |
| Audit warnings | 2 |
| Tested specifications | 568 |

Preregistered primary prediction rule:

| Model | Target | Metric | Value | Raw p-value |
| --- | --- | ---: | ---: | ---: |
| Ridge | `realized_volatility_1_20` | Rank IC | 0.2606 | 0.00017 |

Best observed exploratory prediction:

| Model | Target | Rank IC | Newey-West t-stat | RMSE |
| --- | --- | ---: | ---: | ---: |
| XGBoost | `realized_volatility_1_20` | 0.3133 | 6.8479 | 0.00834 |

The preregistered primary portfolio rule does not establish formal tradable alpha. Portfolio outputs should remain diagnostic.

### Historical Diagnostic Packages

The earlier 10-company public pilot and 90-company summary remain useful as historical diagnostics. They should not be described as the current primary public package because the repository now centers the 50-company FMP/Yahoo applied run.

### Future Replication Path

The next research-grade step is either:

- a broader non-WRDS public-data panel with the same audit gates, or
- a licensed CRSP/WRDS replication with survivorship-free universe construction, delisting returns, and formal security-master controls.

## Conclusion Policy

- Supported claim: the repository implements a leakage-aware, auditable financial text factor research pipeline.
- Supported claim: the current public package validates the end-to-end applied workflow with 100% eligible OOS coverage and no audit failures.
- Supported claim: the preregistered primary volatility prediction is positive in the 50-company public package.
- Cautious claim: there is exploratory out-of-sample volatility forecasting evidence.
- Unsupported claim: the current public package establishes formal tradable alpha.
- Required disclosure: portfolio results are diagnostic only.
- Required disclosure: the 50-company public run is applied-grade, mixed-source, and not a CRSP/WRDS survivorship-free replication.

## Contribution

The core contribution is an auditable financial-text research framework:

1. event-time alignment and leakage controls;
2. train-window-only feature fitting;
3. horizontal comparison of dictionary tone, TF-IDF/SVD, Ridge, XGBoost, and baselines;
4. out-of-sample volatility and CAR evaluation;
5. portfolio diagnostics with costs, drifted holdings, and exposure accounting;
6. preregistered primary specifications and multiple-testing adjustment;
7. transparent public-data, licensed-data, and delisting-return boundaries.
