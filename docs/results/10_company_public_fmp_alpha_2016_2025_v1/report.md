# Text Factor Research Report - 10_company_public_fmp_alpha_2016_2025_v1

## Executive Summary

- Run type: `exploratory_run`.
- Conclusion level: `exploratory_report`.
- Formal result allowed: `False`.
- Audit: `warn` with coverage 0.487, 0 failures, 2 warnings.

## Research Question

Estimate whether audited 10-K text features predict future volatility, abnormal return, or related factor targets under a leakage-controlled rolling-split workflow.

## Data And Sample

- Universe: `fixed_10_company_us_10k_fmp_alpha_pilot`.
- Selection date: `2016-01-01`.
- Sample window: `2016-01-01` to `2025-12-31`.
- Timezone: `America/New_York`.
- Document type/source: `10-K` / `SEC_EDGAR`.
- Sections: `Business`, `Risk Factors`, `Legal Proceedings`, `MD&A`.
- Documents: 100.
- Labels: 300.
- Predictions: 896.

## Licensed Data Stack

- Market data provider: `fmp_alpha`.
- Filing provider: `sec_edgar`.
- Price source: `mixed_fmp_yahoo_adjusted_close`.
- Return source: `mixed_fmp_yahoo_closeadj_log_return`.
- Delisting return source: `fmp_alpha_listing_status_no_crsp_dlret`.
- Link source: `sec_cik_fmp_symbol_change_manual_fb_meta`.
- Public Yahoo fallback allowed: `True`.
- Licensed data manifest: `sec_fmp_yahoo_alpha_lm_fixed_10_company_pilot`.
- Raw licensed data committed: `False`.
- Data rights scope: `private local research artifacts only`.
- License note: Public SEC EDGAR filing; comply with SEC fair-access policy. Financial Modeling Prep API output stored under private local data paths; do not commit raw vendor data. Yahoo Finance chart endpoint is used only as a narrow price fallback for predeclared missing tickers in this applied-grade run; do not treat mixed vendor prices as CRSP/WRDS-equivalent market data. Alpha Vantage API output used as backup/cross-check data; do not commit raw output. Loughran-McDonald master dictionary is provided by Notre Dame SRAF for academic research use. Keep the downloaded CSV under data_private/ unless redistribution rights are separately confirmed.
- Permitted public outputs: `compact result summaries`, `audit summaries`, `schema and configuration files`.

## Coverage And Audit Diagnosis

- Raw label coverage: `0.486667` (146 / 300 labels).
- Raw label coverage includes train-window labels that are not expected to receive out-of-sample predictions; eligible OOS coverage is the prediction-completeness metric for validation/test labels.
- Eligible OOS coverage: `1` (146 / 146 validation/test labels).
- Model-expected prediction coverage: `1` (896 / 896 model-label pairs).
- Primary spec coverage: `1` (2 / 2 primary specifications).
- Primary prediction coverage: `1` (1 / 1).
- Primary portfolio coverage: `1` (1 / 1).
- Portfolio-eligible coverage: `1` (120 / 120 test labels).

### Coverage By Target

| target_name | labels_total | eligible_oos_labels | eligible_oos_coverage |
| --- | --- | --- | --- |
| CAR_1_20 | 100 | 48 | 1.0 |
| CAR_1_5 | 100 | 50 | 1.0 |
| realized_volatility_1_20 | 100 | 48 | 1.0 |

### Coverage By Split

| split_id | eligible_oos_labels | predicted_eligible_oos_labels | eligible_oos_coverage |
| --- | --- | --- | --- |
| train_2016_2020__val_2021_2021__test_2022_2022 | 56 | 56 | 1.0 |
| train_2016_2021__val_2022_2022__test_2023_2023 | 56 | 56 | 1.0 |
| train_2016_2022__val_2023_2023__test_2024_2024 | 56 | 56 | 1.0 |
| train_2016_2023__val_2024_2024__test_2025_2025 | 56 | 56 | 1.0 |

### Coverage By Model

| model_name | expected_label_pairs | predicted_label_pairs | model_expected_prediction_coverage |
| --- | --- | --- | --- |
| historical_mean | 18 | 18 | 1.0 |
| historical_mean | 18 | 18 | 1.0 |
| historical_mean | 18 | 18 | 1.0 |
| historical_mean | 18 | 18 | 1.0 |
| historical_mean | 20 | 20 | 1.0 |
| historical_mean | 20 | 20 | 1.0 |
| historical_mean | 20 | 20 | 1.0 |
| historical_mean | 20 | 20 | 1.0 |
| historical_mean | 18 | 18 | 1.0 |
| historical_mean | 18 | 18 | 1.0 |
| historical_mean | 18 | 18 | 1.0 |
| historical_mean | 18 | 18 | 1.0 |

### Top Failure Reasons

| Stage | Reason | Count |
| --- | --- | ---: |
| outside_configured_split_window | Label event date is outside the configured validation/test split window. | 18 |

## Label Construction

- Targets: `realized_volatility_1_20`, `CAR_1_5`, `CAR_1_20`.
- Return type: `log`.
- Portfolio return type: `simple`.
- Benchmark: `SPY`.
- Annualization days: 252.

## Feature Construction

- Methods: `dictionary_tone`, `tfidf`.
- Feature records: 57850.
- Feature manifests: 40.
- Feature versions: `dictionary-tone-v0`, `tfidf-svd-v0:train_2016_2020__val_2021_2021__test_2022_2022:full`, `tfidf-svd-v0:train_2016_2020__val_2021_2021__test_2022_2022:item_1`, `tfidf-svd-v0:train_2016_2020__val_2021_2021__test_2022_2022:item_1a`, `tfidf-svd-v0:train_2016_2020__val_2021_2021__test_2022_2022:item_3`, `tfidf-svd-v0:train_2016_2020__val_2021_2021__test_2022_2022:item_7`, `tfidf-svd-v0:train_2016_2021__val_2022_2022__test_2023_2023:full`, `tfidf-svd-v0:train_2016_2021__val_2022_2022__test_2023_2023:item_1`, `tfidf-svd-v0:train_2016_2021__val_2022_2022__test_2023_2023:item_1a`, `tfidf-svd-v0:train_2016_2021__val_2022_2022__test_2023_2023:item_3`, `tfidf-svd-v0:train_2016_2021__val_2022_2022__test_2023_2023:item_7`, `tfidf-svd-v0:train_2016_2022__val_2023_2023__test_2024_2024:full`, `tfidf-svd-v0:train_2016_2022__val_2023_2023__test_2024_2024:item_1`, `tfidf-svd-v0:train_2016_2022__val_2023_2023__test_2024_2024:item_1a`, `tfidf-svd-v0:train_2016_2022__val_2023_2023__test_2024_2024:item_3`, `tfidf-svd-v0:train_2016_2022__val_2023_2023__test_2024_2024:item_7`, `tfidf-svd-v0:train_2016_2023__val_2024_2024__test_2025_2025:full`, `tfidf-svd-v0:train_2016_2023__val_2024_2024__test_2025_2025:item_1`, `tfidf-svd-v0:train_2016_2023__val_2024_2024__test_2025_2025:item_1a`, `tfidf-svd-v0:train_2016_2023__val_2024_2024__test_2025_2025:item_3`, `tfidf-svd-v0:train_2016_2023__val_2024_2024__test_2025_2025:item_7`.
- Text scopes: `full`, `item_1`, `item_1a`, `item_3`, `item_7`.
- Vocabulary manifest rows: 20.

| Split | Scope | Fit Scope | Vocabulary Size | Hash | Sample Terms |
| --- | --- | --- | ---: | --- | --- |
| `train_2016_2020__val_2021_2021__test_2022_2022` | `full` | `train_window_only` | 5000 | `6f5ffe740982` | `ability of`, `about our`, `about the`, `abroad`, `absence`, `absence of`, `accelerate`, `accelerated` |
| `train_2016_2020__val_2021_2021__test_2022_2022` | `item_1` | `train_window_only` | 5000 | `6d266ccf4389` | `abbreviated`, `ability`, `ability to`, `able`, `able to`, `about`, `about our`, `about the` |
| `train_2016_2020__val_2021_2021__test_2022_2022` | `item_1a` | `train_window_only` | 5000 | `1a2d0c766544` | `ability of`, `about`, `about our`, `about the`, `above`, `abroad`, `accept`, `acceptable` |
| `train_2016_2020__val_2021_2021__test_2022_2022` | `item_3` | `train_window_only` | 3352 | `3071c968e91b` | `about`, `about one-third`, `about plaintiffs`, `above`, `above relating`, `access`, `access certain`, `access tokens` |
| `train_2016_2020__val_2021_2021__test_2022_2022` | `item_7` | `train_window_only` | 5000 | `223a34bce84d` | `ability`, `ability to`, `able`, `able to`, `about`, `about the`, `above`, `absence` |
| `train_2016_2021__val_2022_2022__test_2023_2023` | `full` | `train_window_only` | 5000 | `79712c25e522` | `ability of`, `about our`, `about the`, `abroad`, `absence`, `absence of`, `accelerate`, `accelerated` |

## Parser Section Length Quality

- Section rows checked: `400`.
- Flag counts: `{'manual_check_lt_100_words': 34, 'ok': 366}`.
- Section-level feature exclusions: `34`.
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
- Primary prediction sign: `negative`.
- Explanation: The preregistered volatility prediction specification contains ranking information, but the Rank IC sign is negative under the current score convention. This must not be post-hoc inverted or described as a positive volatility forecast.

| Model | Split | Target | N | Agg | IC Group | Rank IC | Rank IC t | Rank IC NW t | RMSE | Direction |
| --- | --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: |
| xgboost::CAR_1_5::ALL_SPLITS | ALL_SPLITS | CAR_1_5 | 40 | split_mean_ic_weighted_error_metrics | split | 0.321212 | 1.70466 | 4.1481 | 0.0347187 | 0.475 |
| industry_mean::CAR_1_5::ALL_SPLITS | ALL_SPLITS | CAR_1_5 | 40 | split_mean_ic_weighted_error_metrics | split | 0.284848 | 1.88151 | 4.34515 | 0.0317474 | 0.5 |
| industry_mean::realized_volatility_1_20::ALL_SPLITS | ALL_SPLITS | realized_volatility_1_20 | 40 | split_mean_ic_weighted_error_metrics | split | 0.254545 | 1.50868 | 4.10489 | 0.00753815 | 1 |
| historical_mean::CAR_1_20::ALL_SPLITS | ALL_SPLITS | CAR_1_20 | 40 | split_mean_ic_weighted_error_metrics | split | 0.221212 | 3.16594 | 5.9223 | 0.0661096 | 0.475 |
| industry_mean::CAR_1_20::ALL_SPLITS | ALL_SPLITS | CAR_1_20 | 40 | split_mean_ic_weighted_error_metrics | split | 0.19697 | 1.06864 | 2.4408 | 0.0648331 | 0.475 |
| ridge::CAR_1_5::ALL_SPLITS | ALL_SPLITS | CAR_1_5 | 40 | split_mean_ic_weighted_error_metrics | split | 0.0878788 | 0.95976 | 1.46531 | 0.0515 | 0.425 |
| historical_mean::CAR_1_5::ALL_SPLITS | ALL_SPLITS | CAR_1_5 | 40 | split_mean_ic_weighted_error_metrics | split | 0.0484848 | 1.37876 | 2.23498 | 0.0336345 | 0.4 |
| historical_mean::realized_volatility_1_20::ALL_SPLITS | ALL_SPLITS | realized_volatility_1_20 | 40 | split_mean_ic_weighted_error_metrics | split | -0.00909091 | -0.0548607 | -0.0986294 | 0.00709131 | 1 |
| xgboost::realized_volatility_1_20::ALL_SPLITS | ALL_SPLITS | realized_volatility_1_20 | 40 | split_mean_ic_weighted_error_metrics | split | -0.0212121 | -0.117304 | -0.237981 | 0.0111032 | 1 |
| ridge::CAR_1_20::ALL_SPLITS | ALL_SPLITS | CAR_1_20 | 40 | split_mean_ic_weighted_error_metrics | split | -0.0636364 | -0.469144 | -0.70296 | 0.108117 | 0.5 |

## Prediction Distribution Diagnostics

- Ranking policy: Portfolio construction uses factor_score ordering to form ranks and quantiles; raw prediction magnitude is not used for equal-weight ranking except in explicitly risk-scaled variants.
- Outlier rule: outlier_count flags predictions outside the observed target range or with absolute value greater than five times the target absolute scale.
- Prediction scale guard: 3 model/target/role rows exceed warning thresholds.
- Scale guard policy: Scale guard warnings do not change rank-based portfolio sorting; they require reporting raw-magnitude instability and favor rank_score or winsorized diagnostics over raw prediction magnitudes.

| Model | Target | Role | N | Scale Ratio | Guard | Outliers | Prediction Range | Target Range |
| --- | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| `ridge` | `realized_volatility_1_20` | `validation` | 32 | 1.35396e+12 | `fail` | 10 | [-3.35723e+10, 5.69821e+10] | [0.00767594, 0.0420855] |
| `ridge` | `realized_volatility_1_20` | `test` | 40 | 1.14652 | `pass` | 7 | [-0.0208455, 0.048252] | [0.00640545, 0.0420855] |
| `ridge` | `CAR_1_20` | `validation` | 32 | 7.01987e+12 | `fail` | 5 | [-5.78202e+11, 9.81379e+11] | [-0.1398, 0.125583] |
| `ridge` | `CAR_1_5` | `validation` | 40 | 3.79897e+12 | `fail` | 5 | [-2.29327e+11, 3.89235e+11] | [-0.102458, 0.0663883] |
| `ridge` | `CAR_1_20` | `test` | 40 | 1.96477 | `pass` | 4 | [-0.21669, 0.274676] | [-0.1398, 0.125583] |
| `ridge` | `CAR_1_5` | `test` | 40 | 1.50621 | `pass` | 2 | [-0.154324, 0.0519373] | [-0.102458, 0.0843011] |
| `xgboost` | `realized_volatility_1_20` | `validation` | 32 | 1.49069 | `pass` | 1 | [0.0129601, 0.0627364] | [0.00767594, 0.0420855] |
| `xgboost` | `realized_volatility_1_20` | `test` | 40 | 1.0075 | `pass` | 1 | [0.0128957, 0.042401] | [0.00640545, 0.0420855] |
| `industry_mean` | `CAR_1_20` | `test` | 40 | 0.785458 | `pass` | 0 | [-0.0567707, 0.109807] | [-0.1398, 0.125583] |
| `industry_mean` | `CAR_1_20` | `validation` | 32 | 0.785458 | `pass` | 0 | [-0.0567707, 0.109807] | [-0.1398, 0.125583] |

## Factor Backtest

Portfolio results are diagnostic only in the current applied-grade run; the evidence supports exploratory prediction signals, not formal trading alpha.

- Portfolio method: `top_bottom_quintile`.
- Weighting: `equal_weight`.
- One-way transaction cost: 10.0 bps.
- Newey-West lag: 19.
- Portfolio ranking uses `factor_score` ordering to form ranks and quantiles; raw prediction magnitude is diagnostic, not the equal-weight ranking weight.

| Model | Split | Target | Long | Short | Gross LS | Net LS | Sharpe | NW t-stat | Direction | Turnover |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| historical_mean::CAR_1_20::train_2016_2023__val_2024_2024__test_2025_2025 | train_2016_2023__val_2024_2024__test_2025_2025 | CAR_1_20 | 2 | 2 | 0.0948824 | 0.0928824 | 12.1803 | 2.25068 | long_high_score | 2 |
| historical_mean::CAR_1_5::train_2016_2023__val_2024_2024__test_2025_2025 | train_2016_2023__val_2024_2024__test_2025_2025 | CAR_1_5 | 2 | 2 | 0.0531399 | 0.0511399 | 9.18915 | 1.90594 | long_high_score | 2 |
| ridge::CAR_1_5::train_2016_2020__val_2021_2021__test_2022_2022 | train_2016_2020__val_2021_2021__test_2022_2022 | CAR_1_5 | 2 | 2 | 0.046668 | 0.044668 | 14.9593 | 5.58602 | long_high_score | 2 |
| xgboost::CAR_1_20::train_2016_2023__val_2024_2024__test_2025_2025 | train_2016_2023__val_2024_2024__test_2025_2025 | CAR_1_20 | 2 | 2 | 0.0440746 | 0.0420746 | 15.3531 | 3.36667 | long_high_score | 2 |
| ridge::CAR_1_20::train_2016_2020__val_2021_2021__test_2022_2022 | train_2016_2020__val_2021_2021__test_2022_2022 | CAR_1_20 | 2 | 2 | 0.0438234 | 0.0418234 | 4.61046 | 1.68097 | long_low_score | 2 |
| historical_mean::CAR_1_20::train_2016_2022__val_2023_2023__test_2024_2024 | train_2016_2022__val_2023_2023__test_2024_2024 | CAR_1_20 | 2 | 2 | 0.0432711 | 0.0412711 | 8.10337 | 1.76249 | long_high_score | 2 |
| xgboost::CAR_1_5::train_2016_2023__val_2024_2024__test_2025_2025 | train_2016_2023__val_2024_2024__test_2025_2025 | CAR_1_5 | 2 | 2 | 0.0417641 | 0.0397641 | 8.64335 | 2.02759 | long_high_score | 2 |
| industry_mean::CAR_1_5::train_2016_2023__val_2024_2024__test_2025_2025 | train_2016_2023__val_2024_2024__test_2025_2025 | CAR_1_5 | 2 | 2 | 0.0377559 | 0.0357559 | 7.99243 | 1.91932 | long_high_score | 2 |
| historical_mean::CAR_1_20::train_2016_2021__val_2022_2022__test_2023_2023 | train_2016_2021__val_2022_2022__test_2023_2023 | CAR_1_20 | 2 | 2 | 0.0360192 | 0.0340192 | 4.9556 | 0.863217 | long_high_score | 2 |
| industry_mean::CAR_1_20::train_2016_2021__val_2022_2022__test_2023_2023 | train_2016_2021__val_2022_2022__test_2023_2023 | CAR_1_20 | 2 | 2 | 0.0250948 | 0.0230948 | 2.78033 | 0.490992 | long_high_score | 2 |

## Delisting Return Handling

- Status: `not_applicable`.
- Labels with delisting return applied: `0`.
- Portfolio positions affected by delisting: `0`.
- Delisting returns applied in portfolio rows: `0`.
- Missing delisting returns: `0`.

## Multiple Testing Adjustment

- Specifications: 472; p-values: 472; families: 20.
- Registry roles: primary=2, robustness=160, exploratory=310.
- Role-split adjusted discoveries at 10% FDR: primary=1, robustness=5, exploratory=6.
- Methods: `bonferroni`, `holm`, `benjamini_hochberg_fdr`.

| Role | Family | Tests | Best raw p | Best BH-FDR p | Discoveries 5% | Discoveries 10% |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| exploratory | CAR_1_20::newey_west_t_stat | 8 | 6.55235e-08 | 5.24188e-07 | 2 | 3 |
| exploratory | CAR_1_20::portfolio_sharpe | 80 | 0.0907652 | 0.584544 | 0 | 0 |
| exploratory | CAR_1_20::rank_ic | 18 | 0.120815 | 0.720491 | 0 | 0 |
| exploratory | CAR_1_5::newey_west_t_stat | 8 | 4.62173e-05 | 0.000369738 | 2 | 2 |
| exploratory | CAR_1_5::portfolio_sharpe | 80 | 0.168749 | 0.95636 | 0 | 0 |
| exploratory | CAR_1_5::rank_ic | 18 | 0.00420046 | 0.0756083 | 0 | 1 |
| exploratory | realized_volatility_1_20::newey_west_t_stat | 8 | 0.424685 | 0.961147 | 0 | 0 |
| exploratory | realized_volatility_1_20::portfolio_sharpe | 72 | 0.0243409 | 0.460329 | 0 | 0 |
| exploratory | realized_volatility_1_20::rank_ic | 18 | 0.0825887 | 0.66995 | 0 | 0 |
| primary | realized_volatility_1_20::portfolio_sharpe | 1 | 0.62627 | 0.62627 | 0 | 0 |
| primary | realized_volatility_1_20::rank_ic | 1 | 0.0815252 | 0.0815252 | 0 | 1 |
| robustness | CAR_1_20::newey_west_t_stat | 8 | 0.000760807 | 0.00584576 | 2 | 2 |
| robustness | CAR_1_20::portfolio_sharpe | 48 | 0.133114 | 0.903607 | 0 | 0 |
| robustness | CAR_1_20::rank_ic | 2 | 0.425373 | 0.698306 | 0 | 0 |
| robustness | CAR_1_5::newey_west_t_stat | 8 | 2.32338e-08 | 1.8587e-07 | 2 | 2 |
| robustness | CAR_1_5::portfolio_sharpe | 44 | 0.173144 | 0.850147 | 0 | 0 |
| robustness | CAR_1_5::rank_ic | 2 | 0.0428111 | 0.0856222 | 0 | 1 |
| robustness | realized_volatility_1_20::newey_west_t_stat | 8 | 0.55401 | 0.903493 | 0 | 0 |
| robustness | realized_volatility_1_20::portfolio_sharpe | 39 | 0.035921 | 0.72294 | 0 | 0 |
| robustness | realized_volatility_1_20::rank_ic | 1 | 0.89732 | 0.89732 | 0 | 0 |

## Specification Registry

- Role counts: primary=2, robustness=160, exploratory=310.
- Registry version: `specification-registry-v1`.
- Registry designation: `pre_registered_specification_registry`.
- Preregistration status: `pre_registered`.
- Preregistered primary rule count: `2`.

| Role | Status | Target | Model | Metric | Split | Portfolio | Raw metric | Raw p |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: |
| primary | pre_registered_primary | realized_volatility_1_20 | ridge | rank_ic | ALL_SPLITS | prediction_metric | -0.278788 | 0.0815252 |
| primary | pre_registered_primary | realized_volatility_1_20 | ridge | portfolio_sharpe | ALL_SPLITS | monthly_common_rebalance_top_bottom_quintile | -0.302787 | 0.62627 |

## Robustness Checks

- Current MVP report summarizes split-level and `ALL_SPLITS` metrics. Subperiod stability, Deflated Sharpe, CPCV/PBO, borrow costs, and capacity diagnostics should be added before making production research claims.

## Leakage Audit

| Status | Check | Stage | Message |
| --- | --- | --- | --- |
| warn | split_purge_and_leakage | split | 0 split records have severity=fail; 32 records were purged by embargo; 0 records have severity=warn |
| warn | mixed_market_data_source_boundary | data | Mixed market data source detected. Treat the run as an applied-grade pilot; do not present market-data-dependent portfolio evidence as a CRSP/WRDS-equivalent formal result. |

## Failure Cases

No blocking failures were recorded by the audit layer.

## Conclusion Level

The run is reportable as exploratory evidence only. Do not present it as a formal empirical-finance result.

## Reproducible Commands

- Git commit SHA: `48e48ef6a2c1f18cc8c3aab3678491eb97c9d9f2`.
- Package version: `0.15.0`.
- Dirty worktree flag: `True`.

```bash
python -m text_factor_lab audit --run-id 10_company_public_fmp_alpha_2016_2025_v1 --run-dir runs\text_factor_lab\10_company_public_fmp_alpha_2016_2025_v1
python -m text_factor_lab report --run-id 10_company_public_fmp_alpha_2016_2025_v1 --run-dir runs\text_factor_lab\10_company_public_fmp_alpha_2016_2025_v1
```

Generated at `2026-06-12T13:03:10.184223+00:00` by `report-generator-v0`.
