# Working Paper Positioning

## Recommended Title

**A Leakage-Safe Financial 10-K Text Agent for Out-of-Sample Volatility
Forecasting**

Alternative title:

**From SEC 10-K Filings to Volatility Signals: An Auditable Agentic Pipeline for
Financial Text Factor Research**

## Primary Research Question

**Can 10-K textual information forecast future realized volatility?**

The working paper should not be positioned as a stock-return prediction paper.
The strongest current evidence is for `realized_volatility_1_20`, while return
targets are weaker and are often led by the `industry_mean` baseline.

## Current Evidence

| Target | Best model | ALL_SPLITS Rank IC | Rank IC NW t-stat |
| --- | --- | ---: | ---: |
| `CAR_1_20` | industry mean | 0.1698 | 3.539 |
| `CAR_1_5` | industry mean | 0.1834 | 4.524 |
| `realized_volatility_1_20` | XGBoost | 0.3899 | 21.32 |

The preregistered primary prediction specification is
`realized_volatility_1_20 / Ridge`, with Rank IC `0.3335` and p about
`6.85e-11`.

## Conclusion Policy

- Supported claim: 10-K text contains out-of-sample information about future
  realized volatility.
- Unsupported claim: the current pipeline has established formal tradable
  alpha.
- Required disclosure: the preregistered primary portfolio rule does not pass
  after transaction costs, sector neutrality, ALL_SPLITS aggregation, and
  multiple-testing control.
- Required disclosure: the public 90-company run is exploratory/applied-grade.
  Formal replication still requires licensed survivorship-free data and
  delisting-return controls.

## Contribution

The core contribution is an auditable financial-text research pipeline:

1. event-time alignment and leakage controls;
2. train-window-only feature fitting;
3. horizontal comparison of dictionary tone, TF-IDF/SVD, Ridge, XGBoost, and
   baselines;
4. out-of-sample volatility and CAR evaluation;
5. portfolio robustness tests with costs and sector neutrality;
6. preregistered specifications and multiple-testing adjustment;
7. transparent data-license and delisting-return boundaries.
