# Text Factor Research Report - 50_company_public_fmp_alpha_2016_2025_v1

## Executive Summary

- Run type: `exploratory_run`.
- Conclusion level: `exploratory_report`.
- Formal result allowed: `False`.
Formal result is not allowed for data-boundary reasons, not because the pipeline failed:
- run_type is exploratory_run, so the run is intentionally not eligible for a formal empirical result.
- market data uses a mixed FMP/Yahoo public-source stack, not a single CRSP/WRDS-equivalent research-grade source.
- market_cap_at_selection is based on applied-grade estimates rather than licensed CRSP/Compustat/WRDS market-cap history.
- the universe is an applied fixed-company panel, not a survivorship-free CRSP/WRDS research-grade universe.
- audit_status is warn; warnings are boundary disclosures, not pipeline failures.
- Audit: `warn` with coverage 0.496, 0 failures, 2 warnings.

## Research Question

Estimate whether audited 10-K text features predict future volatility, abnormal return, or related factor targets under a leakage-controlled rolling-split workflow.

## Data And Sample

- Universe: `fixed_50_company_sp500_sector_seed_fmp_alpha_pilot`.
- Selection date: `2016-01-01`.
- Sample window: `2016-01-01` to `2025-12-31`.
- Timezone: `America/New_York`.
- Document type/source: `10-K` / `SEC_EDGAR`.
- Sections: `Business`, `Risk Factors`, `Legal Proceedings`, `MD&A`.
- Documents: 500.
- Labels: 1500.
- Predictions: 4716.

## Licensed Data Stack

- Market data provider: `fmp_alpha`.
- Filing provider: `sec_edgar`.
- Price source: `mixed_fmp_yahoo_adjusted_close`.
- Return source: `mixed_fmp_yahoo_closeadj_log_return`.
- Delisting return source: `fmp_alpha_listing_status_no_crsp_dlret`.
- Link source: `sec_cik_fmp_symbol_change_manual_fb_meta_dis_ge_review`.
- Public Yahoo fallback allowed: `True`.
- Licensed data manifest: `sec_fmp_yahoo_alpha_lm_fixed_applied_company_panel`.
- Raw licensed data committed: `False`.
- Data rights scope: `private local research artifacts only`.
- License note: Public SEC EDGAR filing; comply with SEC fair-access policy. Financial Modeling Prep API output stored under private local data paths; do not commit raw vendor data. Yahoo Finance chart endpoint is used only as a narrow price fallback for predeclared missing tickers in this applied-grade run; do not treat mixed vendor prices as CRSP/WRDS-equivalent market data. Alpha Vantage API output used as backup/cross-check data; do not commit raw output. Loughran-McDonald master dictionary is provided by Notre Dame SRAF for academic research use. Keep the downloaded CSV under data_private/ unless redistribution rights are separately confirmed.
- Permitted public outputs: `compact result summaries`, `audit summaries`, `schema and configuration files`.

## Coverage And Audit Diagnosis

- Raw label coverage: `0.496` (744 / 1500 labels).
- Raw label coverage includes train-window labels that are not expected to receive out-of-sample predictions; eligible OOS coverage is the prediction-completeness metric for validation/test labels.
- Eligible OOS coverage: `1` (744 / 744 validation/test labels).
- Model-expected prediction coverage: `1` (4716 / 4716 model-label pairs).
- Primary spec coverage: `1` (2 / 2 primary specifications).
- Primary prediction coverage: `1` (1 / 1).
- Primary portfolio coverage: `1` (1 / 1).
- Portfolio-eligible coverage: `1` (603 / 603 test labels).

### Coverage By Target

| target_name | labels_total | eligible_oos_labels | eligible_oos_coverage |
| --- | --- | --- | --- |
| CAR_1_20 | 500 | 247 | 1.0 |
| CAR_1_5 | 500 | 250 | 1.0 |
| realized_volatility_1_20 | 500 | 247 | 1.0 |

### Coverage By Split

| split_id | eligible_oos_labels | predicted_eligible_oos_labels | eligible_oos_coverage |
| --- | --- | --- | --- |
| train_2016_2020__val_2021_2021__test_2022_2022 | 294 | 294 | 1.0 |
| train_2016_2021__val_2022_2022__test_2023_2023 | 297 | 297 | 1.0 |
| train_2016_2022__val_2023_2023__test_2024_2024 | 294 | 294 | 1.0 |
| train_2016_2023__val_2024_2024__test_2025_2025 | 294 | 294 | 1.0 |

### Coverage By Model

| model_name | expected_label_pairs | predicted_label_pairs | model_expected_prediction_coverage |
| --- | --- | --- | --- |
| historical_mean | 97 | 97 | 1.0 |
| historical_mean | 98 | 98 | 1.0 |
| historical_mean | 97 | 97 | 1.0 |
| historical_mean | 97 | 97 | 1.0 |
| historical_mean | 100 | 100 | 1.0 |
| historical_mean | 101 | 101 | 1.0 |
| historical_mean | 100 | 100 | 1.0 |
| historical_mean | 100 | 100 | 1.0 |
| historical_mean | 97 | 97 | 1.0 |
| historical_mean | 98 | 98 | 1.0 |
| historical_mean | 97 | 97 | 1.0 |
| historical_mean | 97 | 97 | 1.0 |

### Top Failure Reasons

| Stage | Reason | Count |
| --- | --- | ---: |
| outside_configured_split_window | Label event date is outside the configured validation/test split window. | 120 |

## Label Construction

- Targets: `realized_volatility_1_20`, `CAR_1_5`, `CAR_1_20`.
- Return type: `log`.
- Portfolio return type: `simple`.
- Benchmark: `SPY`.
- Annualization days: 252.

## Feature Construction

- Methods: `dictionary_tone`, `tfidf`.
- Feature records: 520465.
- Feature manifests: 40.
- Feature versions: `dictionary-tone-v0`, `tfidf-svd-v0:train_2016_2020__val_2021_2021__test_2022_2022:full`, `tfidf-svd-v0:train_2016_2020__val_2021_2021__test_2022_2022:item_1`, `tfidf-svd-v0:train_2016_2020__val_2021_2021__test_2022_2022:item_1a`, `tfidf-svd-v0:train_2016_2020__val_2021_2021__test_2022_2022:item_3`, `tfidf-svd-v0:train_2016_2020__val_2021_2021__test_2022_2022:item_7`, `tfidf-svd-v0:train_2016_2021__val_2022_2022__test_2023_2023:full`, `tfidf-svd-v0:train_2016_2021__val_2022_2022__test_2023_2023:item_1`, `tfidf-svd-v0:train_2016_2021__val_2022_2022__test_2023_2023:item_1a`, `tfidf-svd-v0:train_2016_2021__val_2022_2022__test_2023_2023:item_3`, `tfidf-svd-v0:train_2016_2021__val_2022_2022__test_2023_2023:item_7`, `tfidf-svd-v0:train_2016_2022__val_2023_2023__test_2024_2024:full`, `tfidf-svd-v0:train_2016_2022__val_2023_2023__test_2024_2024:item_1`, `tfidf-svd-v0:train_2016_2022__val_2023_2023__test_2024_2024:item_1a`, `tfidf-svd-v0:train_2016_2022__val_2023_2023__test_2024_2024:item_3`, `tfidf-svd-v0:train_2016_2022__val_2023_2023__test_2024_2024:item_7`, `tfidf-svd-v0:train_2016_2023__val_2024_2024__test_2025_2025:full`, `tfidf-svd-v0:train_2016_2023__val_2024_2024__test_2025_2025:item_1`, `tfidf-svd-v0:train_2016_2023__val_2024_2024__test_2025_2025:item_1a`, `tfidf-svd-v0:train_2016_2023__val_2024_2024__test_2025_2025:item_3`, `tfidf-svd-v0:train_2016_2023__val_2024_2024__test_2025_2025:item_7`.
- Text scopes: `full`, `item_1`, `item_1a`, `item_3`, `item_7`.
- Vocabulary manifest rows: 20.

| Split | Scope | Fit Scope | Vocabulary Size | Hash | Sample Terms |
| --- | --- | --- | ---: | --- | --- |
| `train_2016_2020__val_2021_2021__test_2022_2022` | `full` | `train_window_only` | 10000 | `0392187c5df4` | `a-`, `aa`, `aa-`, `aa-rated`, `aaa`, `aar`, `ab`, `abandon` |
| `train_2016_2020__val_2021_2021__test_2022_2022` | `item_1` | `train_window_only` | 10000 | `43e80ea40ee0` | `a`, `a-`, `aar`, `ab`, `abandoned`, `abandonment`, `abasaglar`, `abate` |
| `train_2016_2020__val_2021_2021__test_2022_2022` | `item_1a` | `train_window_only` | 8174 | `314f1bd16e08` | `a-`, `ab`, `abandon`, `abandoned`, `abandoning`, `abandonment`, `abate`, `abatement` |
| `train_2016_2020__val_2021_2021__test_2022_2022` | `item_3` | `train_window_only` | 1542 | `831affde5744` | `a`, `abbott`, `ability`, `able`, `about`, `above`, `absence`, `accelerating` |
| `train_2016_2020__val_2021_2021__test_2022_2022` | `item_7` | `train_window_only` | 8944 | `c3e747875256` | `a`, `a-`, `aa`, `aa-`, `aa-rated`, `aaa`, `aapg`, `aar-stb` |
| `train_2016_2021__val_2022_2022__test_2023_2023` | `full` | `train_window_only` | 10000 | `11aaf201a127` | `a-`, `aa`, `aa-`, `aaa`, `aar`, `ab`, `abandon`, `abandoned` |

## Parser Section Length Quality

- Section rows checked: `2000`.
- Flag counts: `{'manual_check_lt_100_words': 144, 'ok': 1840, 'warn_lt_500_words': 16}`.
- Section-level feature exclusions: `144`.
- Core section rule: `item_1a` / `item_7` below 500 words is a warning; below 100 words requires manual review.
- Feature policy: `item_1a` / `item_7` sections below 100 words are excluded from section-level features until manually reviewed; other text scopes remain available.

## Model Setup

- Configured models: `historical_mean`, `industry_mean`, `ridge`, `xgboost`.
- Trained model manifests: 48.
- Model families: `baseline`, `linear_regularized`, `tree_boosting`.
- Tuning logs: 48.
- Selection metric: `validation_rank_ic`.

## Out-Of-Sample Prediction Results

- Signal direction policy: `pre_registered_score_convention_no_post_hoc_sign_flip`.
- Primary prediction sign: `positive`.
- Explanation: The preregistered prediction specification has a positive Rank IC under the current score convention.

| Model | Split | Target | N | Agg | IC Group | Rank IC | Rank IC t | Rank IC NW t | RMSE | Direction |
| --- | --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| xgboost::realized_volatility_1_20::ALL_SPLITS | ALL_SPLITS | realized_volatility_1_20 | 201 | split_mean_ic_weighted_error_metrics | split | 0.313338 | 2.72013 | 6.84785 | 0.00833559 | 1 |
| industry_mean::realized_volatility_1_20::ALL_SPLITS | ALL_SPLITS | realized_volatility_1_20 | 201 | split_mean_ic_weighted_error_metrics | split | 0.295218 | 1.98152 | 4.59628 | 0.00913094 | 1 |
| ridge::realized_volatility_1_20::ALL_SPLITS | ALL_SPLITS | realized_volatility_1_20 | 201 | split_mean_ic_weighted_error_metrics | split | 0.260604 | 1.85721 | 2.55689 | 0.0191692 | 0.925373 |
| historical_mean::CAR_1_20::ALL_SPLITS | ALL_SPLITS | CAR_1_20 | 201 | split_mean_ic_weighted_error_metrics | split | 0.253486 | 3.18728 | 7.24996 | 0.0760299 | 0.557214 |
| historical_mean::CAR_1_5::ALL_SPLITS | ALL_SPLITS | CAR_1_5 | 201 | split_mean_ic_weighted_error_metrics | split | 0.0944727 | 2.12264 | 3.52462 | 0.0437815 | 0.517413 |
| industry_mean::CAR_1_20::ALL_SPLITS | ALL_SPLITS | CAR_1_20 | 201 | split_mean_ic_weighted_error_metrics | split | 0.0917268 | 0.551344 | 1.54026 | 0.0839745 | 0.517413 |
| xgboost::CAR_1_20::ALL_SPLITS | ALL_SPLITS | CAR_1_20 | 201 | split_mean_ic_weighted_error_metrics | split | 0.0906335 | 0.530378 | 1.24713 | 0.0747513 | 0.542289 |
| industry_mean::CAR_1_5::ALL_SPLITS | ALL_SPLITS | CAR_1_5 | 201 | split_mean_ic_weighted_error_metrics | split | 0.0376383 | 0.290574 | 0.54708 | 0.0450735 | 0.492537 |
| xgboost::CAR_1_5::ALL_SPLITS | ALL_SPLITS | CAR_1_5 | 201 | split_mean_ic_weighted_error_metrics | split | 0.00704867 | 0.077804 | 0.112606 | 0.042157 | 0.517413 |
| ridge::CAR_1_5::ALL_SPLITS | ALL_SPLITS | CAR_1_5 | 201 | split_mean_ic_weighted_error_metrics | split | -0.0144141 | -0.354029 | -0.817104 | 0.104617 | 0.502488 |

## Prediction Distribution Diagnostics

- Ranking policy: Portfolio construction uses factor_score ordering to form ranks and quantiles; raw prediction magnitude is not used for equal-weight ranking except in explicitly risk-scaled variants.
- Outlier rule: outlier_count flags predictions outside the observed target range or with absolute value greater than five times the target absolute scale.
- Prediction scale guard: 0 model/target/role rows exceed warning thresholds.
- Scale guard policy: Scale guard warnings do not change rank-based portfolio sorting; they require reporting raw-magnitude instability and favor rank_score or winsorized diagnostics over raw prediction magnitudes.

| Model | Target | Role | N | Scale Ratio | Guard | Outliers | Prediction Range | Target Range |
| --- | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| `ridge` | `realized_volatility_1_20` | `validation` | 188 | 6.05677 | `pass` | 35 | [-0.082307, 0.346228] | [0.00604034, 0.0571639] |
| `ridge` | `realized_volatility_1_20` | `test` | 201 | 1.90018 | `pass` | 30 | [-0.0371031, 0.108622] | [0.00604034, 0.0571639] |
| `ridge` | `CAR_1_20` | `validation` | 188 | 3.62483 | `pass` | 21 | [-1.39397, 0.584125] | [-0.199324, 0.384561] |
| `ridge` | `CAR_1_5` | `validation` | 200 | 1.13843 | `pass` | 20 | [-0.340833, 0.437138] | [-0.113406, 0.383983] |
| `ridge` | `CAR_1_5` | `test` | 201 | 1.62055 | `pass` | 16 | [-0.622265, 0.276772] | [-0.113406, 0.383983] |
| `ridge` | `CAR_1_20` | `test` | 201 | 1.07245 | `pass` | 5 | [-0.248532, 0.412422] | [-0.199324, 0.384561] |
| `xgboost` | `realized_volatility_1_20` | `validation` | 188 | 0.883489 | `pass` | 0 | [0.0138361, 0.0505036] | [0.00604034, 0.0571639] |
| `industry_mean` | `realized_volatility_1_20` | `test` | 201 | 0.662197 | `pass` | 0 | [0.0101364, 0.0378537] | [0.00604034, 0.0571639] |
| `industry_mean` | `realized_volatility_1_20` | `validation` | 188 | 0.662197 | `pass` | 0 | [0.0101364, 0.0378537] | [0.00604034, 0.0571639] |
| `xgboost` | `realized_volatility_1_20` | `test` | 201 | 0.613035 | `pass` | 0 | [0.0124028, 0.0350435] | [0.00604034, 0.0571639] |

## Factor Backtest

Portfolio results are diagnostic only in the current applied-grade run; the evidence supports exploratory prediction signals, not formal trading alpha.

- Portfolio method: `top_bottom_quintile`.
- Weighting: `equal_weight`.
- One-way transaction cost: 10.0 bps.
- Newey-West lag: 19.
- Portfolio ranking uses `factor_score` ordering to form ranks and quantiles; raw prediction magnitude is diagnostic, not the equal-weight ranking weight.

| Model | Split | Target | Long | Short | Gross LS | Net LS | Sharpe | NW t-stat | Direction | Turnover |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| ridge::CAR_1_20::train_2016_2023__val_2024_2024__test_2025_2025 | train_2016_2023__val_2024_2024__test_2025_2025 | CAR_1_20 | 10 | 10 | 0.051517 | 0.049517 | 5.04654 | 1.00483 | long_high_score | 2 |
| historical_mean::CAR_1_20::train_2016_2023__val_2024_2024__test_2025_2025 | train_2016_2023__val_2024_2024__test_2025_2025 | CAR_1_20 | 10 | 10 | 0.0500627 | 0.0480627 | 5.9938 | 1.86662 | long_high_score | 2 |
| historical_mean::CAR_1_20::train_2016_2020__val_2021_2021__test_2022_2022 | train_2016_2020__val_2021_2021__test_2022_2022 | CAR_1_20 | 10 | 10 | 0.0412205 | 0.0392205 | 4.46359 | 2.11621 | long_high_score | 2 |
| historical_mean::CAR_1_5::train_2016_2020__val_2021_2021__test_2022_2022 | train_2016_2020__val_2021_2021__test_2022_2022 | CAR_1_5 | 10 | 10 | 0.0275464 | 0.0255464 | 5.72683 | 3.63922 | long_high_score | 2 |
| xgboost::CAR_1_20::train_2016_2020__val_2021_2021__test_2022_2022 | train_2016_2020__val_2021_2021__test_2022_2022 | CAR_1_20 | 10 | 10 | 0.0263319 | 0.0243319 | 1.96433 | 1.59417 | long_low_score | 2 |
| historical_mean::CAR_1_20::train_2016_2021__val_2022_2022__test_2023_2023 | train_2016_2021__val_2022_2022__test_2023_2023 | CAR_1_20 | 10 | 10 | 0.0195913 | 0.0175913 | 2.51084 | 1.18684 | long_high_score | 2 |
| ridge::CAR_1_5::train_2016_2022__val_2023_2023__test_2024_2024 | train_2016_2022__val_2023_2023__test_2024_2024 | CAR_1_5 | 10 | 10 | 0.0133025 | 0.0113025 | 3.91133 | 2.30787 | long_low_score | 2 |
| xgboost::CAR_1_5::train_2016_2022__val_2023_2023__test_2024_2024 | train_2016_2022__val_2023_2023__test_2024_2024 | CAR_1_5 | 10 | 10 | 0.0126636 | 0.0106636 | 4.01783 | 2.31105 | long_low_score | 2 |
| industry_mean::CAR_1_5::train_2016_2020__val_2021_2021__test_2022_2022 | train_2016_2020__val_2021_2021__test_2022_2022 | CAR_1_5 | 10 | 10 | 0.0122968 | 0.0102968 | 0.914811 | 0.451505 | long_low_score | 2 |
| ridge::CAR_1_20::train_2016_2020__val_2021_2021__test_2022_2022 | train_2016_2020__val_2021_2021__test_2022_2022 | CAR_1_20 | 10 | 10 | 0.00946623 | 0.00746623 | 0.685233 | 0.205436 | long_low_score | 2 |

## Delisting Return Handling

- Status: `not_applicable`.
- Labels with delisting return applied: `0`.
- Portfolio positions affected by delisting: `0`.
- Delisting returns applied in portfolio rows: `0`.
- Missing delisting returns: `0`.

## Multiple Testing Adjustment

- Specifications: 568; p-values: 568; families: 20.
- Registry roles: primary=2, robustness=164, exploratory=402.
- Role-split adjusted discoveries at 10% FDR: primary=1, robustness=9, exploratory=23.
- Methods: `bonferroni`, `holm`, `benjamini_hochberg_fdr`.

| Role | Family | Tests | Best raw p | Best BH-FDR p | Discoveries 5% | Discoveries 10% |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| exploratory | CAR_1_20::newey_west_t_stat | 8 | 0.000222286 | 0.00177828 | 2 | 3 |
| exploratory | CAR_1_20::portfolio_sharpe | 108 | 0.00342985 | 0.185212 | 0 | 0 |
| exploratory | CAR_1_20::rank_ic | 18 | 0.000265993 | 0.00316582 | 7 | 10 |
| exploratory | CAR_1_5::newey_west_t_stat | 8 | 0.000273465 | 0.00218772 | 1 | 1 |
| exploratory | CAR_1_5::portfolio_sharpe | 112 | 0.00559914 | 0.313552 | 0 | 0 |
| exploratory | CAR_1_5::rank_ic | 18 | 0.00739814 | 0.133167 | 0 | 0 |
| exploratory | realized_volatility_1_20::newey_west_t_stat | 8 | 0.496739 | 0.955925 | 0 | 0 |
| exploratory | realized_volatility_1_20::portfolio_sharpe | 104 | 0.013019 | 0.428519 | 0 | 0 |
| exploratory | realized_volatility_1_20::rank_ic | 18 | 1.37632e-05 | 0.000167075 | 9 | 9 |
| primary | realized_volatility_1_20::portfolio_sharpe | 1 | 0.108178 | 0.108178 | 0 | 0 |
| primary | realized_volatility_1_20::rank_ic | 1 | 0.000174313 | 0.000174313 | 1 | 1 |
| robustness | CAR_1_20::newey_west_t_stat | 8 | 5.11013e-06 | 3.39955e-05 | 4 | 4 |
| robustness | CAR_1_20::portfolio_sharpe | 48 | 0.0573377 | 0.966667 | 0 | 0 |
| robustness | CAR_1_20::rank_ic | 2 | 0.200955 | 0.40191 | 0 | 0 |
| robustness | CAR_1_5::newey_west_t_stat | 8 | 0.0208303 | 0.0713046 | 0 | 4 |
| robustness | CAR_1_5::portfolio_sharpe | 48 | 0.0793847 | 0.977999 | 0 | 0 |
| robustness | CAR_1_5::rank_ic | 2 | 0.839262 | 0.920991 | 0 | 0 |
| robustness | realized_volatility_1_20::newey_west_t_stat | 8 | 0.561523 | 0.995077 | 0 | 0 |
| robustness | realized_volatility_1_20::portfolio_sharpe | 39 | 0.0580997 | 0.8067 | 0 | 0 |
| robustness | realized_volatility_1_20::rank_ic | 1 | 5.05478e-06 | 5.05478e-06 | 1 | 1 |

## Specification Registry

- Role counts: primary=2, robustness=164, exploratory=402.
- Registry version: `specification-registry-v1`.
- Registry designation: `pre_registered_specification_registry`.
- Preregistration status: `pre_registered`.
- Preregistered primary rule count: `2`.

| Role | Status | Target | Model | Metric | Split | Portfolio | Raw metric | Raw p |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: |
| primary | pre_registered_primary | realized_volatility_1_20 | ridge | rank_ic | ALL_SPLITS | prediction_metric | 0.260604 | 0.000174313 |
| primary | pre_registered_primary | realized_volatility_1_20 | ridge | portfolio_sharpe | ALL_SPLITS | monthly_common_rebalance_top_bottom_quintile | -0.870379 | 0.108178 |

## Robustness Checks

- Current MVP report summarizes split-level and `ALL_SPLITS` metrics. Subperiod stability, Deflated Sharpe, CPCV/PBO, borrow costs, and capacity diagnostics should be added before making production research claims.

## Leakage Audit

| Status | Check | Stage | Message |
| --- | --- | --- | --- |
| warn | split_purge_and_leakage | split | 0 split records have severity=fail; 46 records were purged by embargo; 0 records have severity=warn |
| warn | mixed_market_data_source_boundary | data | Mixed market data source detected. Treat the run as an applied-grade pilot; do not present market-data-dependent portfolio evidence as a CRSP/WRDS-equivalent formal result. |

## Failure Cases

No blocking failures were recorded by the audit layer.

## Conclusion Level

The run is reportable as exploratory evidence only. Do not present it as a formal empirical-finance result.

## Reproducible Commands

- Git commit SHA: `753240be4524ea3eff153f60c22fd5338e8639eb`.
- Package version: `0.16.0`.
- Dirty worktree flag: `False`.

```bash
python -m text_factor_lab audit --run-id 50_company_public_fmp_alpha_2016_2025_v1 --run-dir runs\text_factor_lab\50_company_public_fmp_alpha_2016_2025_v1
python -m text_factor_lab report --run-id 50_company_public_fmp_alpha_2016_2025_v1 --run-dir runs\text_factor_lab\50_company_public_fmp_alpha_2016_2025_v1
```

Generated at `2026-06-16T03:51:55.554224+00:00` by `report-generator-v0`.
