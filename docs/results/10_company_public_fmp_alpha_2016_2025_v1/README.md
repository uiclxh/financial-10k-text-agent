# 10-Company Public 10-K Pilot

Applied-grade result package for:

`10_company_public_fmp_alpha_2016_2025_v1`

## Scope

| Item | Value |
| --- | ---: |
| Companies | 10 |
| SEC annual filings | 100 |
| Sample years | FY2016-FY2025 |
| Labels | 300 |
| OOS predictions | 896 |
| Tested specifications | 472 |
| Audit failures | 0 |
| Audit warnings | 2 |

Data boundary:

- SEC EDGAR provides official 10-K filings and filing timestamps.
- FMP is the primary adjusted-price source.
- Yahoo is used only as fallback for selected price gaps.
- This is a mixed-source applied run, not a CRSP/WRDS formal replication.

## Main Findings

- Eligible OOS coverage is 100%; raw coverage is lower because train-window
  labels are not expected to receive OOS predictions.
- The best observed ALL_SPLITS prediction metric is
  `xgboost::CAR_1_5`, Rank IC `0.3212`, NW t-stat `4.1481`.
- The best realized-volatility ALL_SPLITS metric is
  `industry_mean::realized_volatility_1_20`, Rank IC `0.2545`,
  NW t-stat `4.1049`.
- The preregistered Ridge volatility prediction rule has negative Rank IC
  under the fixed score convention and must not be post-hoc sign-flipped.
- The preregistered portfolio rule does not pass; portfolio outputs are
  diagnostic only.

## Most Useful Files

| File | Purpose |
| --- | --- |
| `factor_card.md` | Fastest human-readable result card. |
| `empirical_report.md` | Paper-style empirical report. |
| `audit_report.json` | Audit status, warnings, and formal-result gate. |
| `coverage_waterfall.json` | Raw vs eligible OOS coverage explanation. |
| `evaluation_metrics.json` | OOS forecasting metrics. |
| `multiple_testing_report.json` | Bonferroni, Holm, and BH-FDR adjustment. |
| `specification_registry.json` | Preregistered primary rules and robustness setup. |
| `model_manifest.json` | Model versions, windows, features, and provenance. |
| `feature_manifest.json` | Dictionary and TF-IDF/SVD feature provenance. |
| `vocabulary_manifest.json` | Train-window-only vocabulary hashes and samples. |
| `section_length_quality_report.json` | Parser length checks and section exclusions. |
| `prediction_distribution_report.json` | Prediction scale and outlier diagnostics. |
| `universe_quality_report.json` | Applied-grade universe quality boundary. |
| `checksums.json` | SHA-256 hashes for committed public artifacts. |

## Included But Not Raw

The directory includes compact labels, predictions, model manifests, coverage
tables, audit files, and metrics. It intentionally excludes raw SEC filings,
full price panels, full feature matrices, and full daily portfolio return
series.

## Interpretation

Use this package to inspect an auditable financial NLP research workflow. Do not
use it as evidence of a production trading strategy or investment advice.
