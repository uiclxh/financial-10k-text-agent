# 50-Company Public 10-K Pilot

Applied-grade result package for:

`50_company_public_fmp_alpha_2016_2025_v1`

## Scope

| Item | Value |
| --- | ---: |
| Companies | 50 |
| SEC 10-K filings | 500 |
| Sample years | FY2016-FY2025 |
| Labels | 1,500 |
| OOS predictions | 4,716 |
| Feature records | 520,465 |
| Tested specifications | 568 |
| Eligible OOS coverage | 100% |
| Audit failures | 0 |
| Audit warnings | 2 |

Data boundary:

- SEC EDGAR provides official 10-K filings and filing timestamps.
- Market data uses a mixed FMP/Yahoo public-source stack.
- Market-cap-at-selection values are applied-grade estimates.
- This is not a CRSP/WRDS-equivalent survivorship-free replication.

## Main Finding

The preregistered primary prediction specification is Ridge on
`realized_volatility_1_20`, evaluated by ALL_SPLITS Rank IC:

| Model | Target | Rank IC | Raw p-value |
| --- | --- | ---: | ---: |
| Ridge | `realized_volatility_1_20` | 0.2606 | 0.00017 |

This supports exploratory out-of-sample volatility prediction evidence.

## Best Observed Exploratory Prediction

| Model | Target | Rank IC | Newey-West t-stat | RMSE |
| --- | --- | ---: | ---: | ---: |
| XGBoost | `realized_volatility_1_20` | 0.3133 | 6.8479 | 0.00834 |

This is model-comparison evidence, not the preregistered primary claim.

## Most Useful Files

| File | Purpose |
| --- | --- |
| `factor_card.md` | Fastest human-readable result card. |
| `empirical_report.md` | Paper-style empirical result narrative. |
| `report.md` | Full automated run report. |
| `report_summary.json` | Machine-readable summary of the run. |
| `audit_report.json` | Audit status, warnings, and formal-result gate. |
| `coverage_waterfall.json` | Raw vs eligible OOS coverage explanation. |
| `evaluation_metrics.json` | OOS forecasting metrics. |
| `multiple_testing_report.json` | Bonferroni, Holm, and BH-FDR adjustment. |
| `specification_registry.json` | Preregistered primary and robustness setup. |
| `model_manifest.json` | Model windows, feature provenance, and reproducibility metadata. |
| `feature_manifest.json` | Dictionary and TF-IDF/SVD feature provenance. |
| `vocabulary_manifest.json` | Train-window-only vocabulary hashes and samples. |
| `section_length_quality_report.json` | Parser length checks and section exclusions. |
| `prediction_distribution_report.json` | Prediction scale and outlier diagnostics. |
| `universe_quality_report.json` | Applied-grade universe boundary. |
| `price_fallback_boundary_report.json` | Mixed-source market-data disclosure. |
| `checksums.json` | SHA-256 hashes for committed public artifacts. |

## Included But Not Raw

This directory intentionally excludes raw SEC filings, API responses, full price
panels, `features.jsonl`, full prediction rows, full daily portfolio returns,
portfolio weights, sparse feature matrices, and private/vendor intermediate data.

## Interpretation

Use this package as evidence of an auditable financial NLP research workflow.
Portfolio outputs are diagnostic only; this package does not establish a formal
tradable alpha or provide investment advice.
