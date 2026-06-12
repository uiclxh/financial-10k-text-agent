# Working Paper Positioning

## Recommended Title

**A Leakage-Safe Financial 10-K Text Agent for Out-of-Sample Forecasting**

Alternative title:

**From SEC 10-K Filings to Auditable Text Factors: An Agentic Pipeline for
Financial NLP Research**

## Primary Research Question

**Can 10-K textual information produce leakage-controlled out-of-sample
forecasting signals?**

The paper should not be positioned as a stock-return prediction or trading-alpha
paper. The safer framing is an auditable empirical pipeline with applied-grade
evidence, explicit data boundaries, and diagnostic portfolio tests.

## Current Evidence Hierarchy

### Current Primary Public Package

The current primary public package is the **10-company FMP/Alpha/Yahoo fallback
pilot**:

[docs/results/10_company_public_fmp_alpha_2016_2025_v1](results/10_company_public_fmp_alpha_2016_2025_v1/README.md)

| Item | Value |
| --- | ---: |
| Companies | 10 |
| SEC 10-K filings | 100 |
| Labels | 300 |
| OOS predictions | 896 |
| Eligible OOS coverage | 100% |
| Audit failures | 0 |
| Audit warnings | 2 |
| Tested specifications | 472 |

Best observed ALL_SPLITS prediction metrics in this public package:

| Target | Best model | ALL_SPLITS Rank IC | Rank IC NW t-stat |
| --- | --- | ---: | ---: |
| `CAR_1_5` | XGBoost | 0.3212 | 4.1481 |
| `realized_volatility_1_20` | industry mean | 0.2545 | 4.1049 |

The preregistered primary prediction rule is intentionally stricter:
`ridge / realized_volatility_1_20 / ALL_SPLITS` has Rank IC `-0.2788` and raw
p-value `0.0815`. The negative sign must not be post-hoc inverted.

The preregistered primary portfolio rule does not pass:
monthly sector-neutral equal-weight volatility portfolio Sharpe `-0.3028`, raw
p-value `0.6263`.

### Historical Diagnostic Package

The earlier 90-company public run remains useful as a historical diagnostic
package. It suggested stronger realized-volatility evidence, but it should not
be described as the current primary public package because the repository now
centers the 10-company FMP/Alpha applied run.

### Future Replication Path

The next research-grade step is either:

- a larger non-WRDS public-data panel with the same audit gates, or
- a licensed CRSP/WRDS replication with survivorship-free universe construction,
  delisting returns, and formal security-master controls.

## Conclusion Policy

- Supported claim: the repository implements a leakage-aware, auditable
  financial text factor research pipeline.
- Supported claim: the current public package validates the end-to-end applied
  workflow with 100% eligible OOS coverage and no audit failures.
- Cautious claim: there is exploratory forecasting evidence in the public pilot.
- Unsupported claim: the current public package establishes formal tradable
  alpha.
- Required disclosure: portfolio results are diagnostic only.
- Required disclosure: the 10-company public run is applied-grade, mixed-source,
  and not a CRSP/WRDS survivorship-free replication.

## Contribution

The core contribution is an auditable financial-text research framework:

1. event-time alignment and leakage controls;
2. train-window-only feature fitting;
3. horizontal comparison of dictionary tone, TF-IDF/SVD, Ridge, XGBoost, and
   baselines;
4. out-of-sample volatility and CAR evaluation;
5. portfolio diagnostics with costs, drifted holdings, and exposure accounting;
6. preregistered primary specifications and multiple-testing adjustment;
7. transparent public-data, licensed-data, and delisting-return boundaries.
