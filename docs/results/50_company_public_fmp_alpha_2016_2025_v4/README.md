# 50-Company Applied-Grade Result Package V4

This compact package contains the public, license-safe outputs from
`50_company_public_fmp_alpha_2016_2025_v4`.

## Snapshot

| Field | Value |
| --- | ---: |
| Companies | 50 |
| SEC 10-K filings | 500 |
| Labels | 1,500 |
| OOS predictions | 8,133 |
| Feature records | 520,465 |
| Tested specifications | 594 |
| Multiple-testing families | 26 |
| Eligible OOS coverage | 100% |
| Audit failures | 0 |
| Audit warnings | 2 |

## Findings

- Preregistered Ridge volatility Rank IC: `0.2395`, raw p-value `0.00067`.
- Best exploratory result: TF-IDF/SVD-only Ridge Rank IC `0.3668`.
- TF-IDF/SVD-only industry-neutral Rank IC: `0.3416`.
- Primary industry-neutral Ridge point estimate: `0.2023`, but all three
  bootstrap confidence intervals include zero.
- Preregistered portfolio Sharpe: `-0.8539`, raw p-value `0.1147`.
- Portfolio evidence is diagnostic only and does not establish tradable alpha.

## Artifact Guide

| Artifact | Purpose |
| --- | --- |
| `empirical_report.md` | Paper-style interpretation and limitations |
| `factor_card.md` | Compact result and usage-boundary summary |
| `report.md` | Full automated pipeline report |
| `report_summary.json` | Machine-readable report summary |
| `evaluation_metrics.json` | OOS metrics including neutral Rank IC |
| `feature_ablation_summary.json` | Controlled feature-block comparison |
| `primary_rank_ic_bootstrap_report.json` | Three clustered bootstrap checks |
| `multiple_testing_report.json` | Bonferroni, Holm, and BH-FDR results |
| `specification_registry.json` | Primary, robustness, and exploratory registry |
| `audit_report.json` | Leakage, coverage, metadata, and boundary audit |
| `coverage_waterfall.json` | Raw, eligible-OOS, model, and primary coverage |
| `parser_manual_review_appendix.md` | Short-section manual-review inventory |
| `section_length_quality_report.json` | Section-level length and exclusion data |
| `prediction_distribution_report.json` | Prediction scale and outlier diagnostics |
| `feature_manifest.json` | Feature provenance and fit-scope metadata |
| `vocabulary_manifest.json` | Train-only vocabulary hashes and parameters |
| `model_manifest.json` | Model versions, windows, features, and parameters |
| `universe_quality_report.json` | Applied-grade universe quality disclosure |
| `delisting_application_report.json` | Delisting-return applicability check |
| `appendix_tables.md` | Supporting tables |

## Boundary

This is an applied-grade public-data pilot, not a CRSP/WRDS-equivalent
survivorship-free replication. Raw filings, market-data responses, price panels,
feature matrices, API keys, and private intermediate data are not included.
