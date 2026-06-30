# Text Factor Research Report - 50_company_public_fmp_alpha_2016_2025_v4

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
- Predictions: 8133.

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
- Model-expected prediction coverage: `0.98546` (8133 / 8253 model-label pairs).
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
| missing_model_prediction | The model was expected to score this eligible OOS label. | 120 |

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
- Manual-review appendix: `runs\text_factor_lab\50_company_public_fmp_alpha_2016_2025_v4\parser_manual_review_appendix.md`.

## Model Setup

- Configured models: `historical_mean`, `industry_mean`, `ridge`, `xgboost`.
- Trained model manifests: 84.
- Model families: `baseline`, `linear_regularized`, `tree_boosting`.
- Tuning logs: 84.
- Selection metric: `validation_rank_ic`.

## Out-Of-Sample Prediction Results

- Signal direction policy: `pre_registered_score_convention_no_post_hoc_sign_flip`.
- Primary prediction sign: `positive`.
- Explanation: The preregistered prediction specification has a positive Rank IC under the current score convention.

| Model | Split | Target | N | Agg | IC Group | Rank IC | Neutral Rank IC | Rank IC NW t | Neutral NW t | RMSE | Direction |
| --- | --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ridge_tfidf_svd_only::realized_volatility_1_20::ALL_SPLITS | ALL_SPLITS | realized_volatility_1_20 | 197 | split_mean_ic_weighted_error_metrics | split | 0.366849 | 0.341616 | 5.40552 | 3.85574 | 0.00992428 | 0.994924 |
| ridge_industry_plus_text::realized_volatility_1_20::ALL_SPLITS | ALL_SPLITS | realized_volatility_1_20 | 197 | split_mean_ic_weighted_error_metrics | split | 0.329571 | 0.325082 | 5.10729 | 4.39941 | 0.0107598 | 0.984772 |
| industry_mean::realized_volatility_1_20::ALL_SPLITS | ALL_SPLITS | realized_volatility_1_20 | 201 | split_mean_ic_weighted_error_metrics | split | 0.292431 | 0 | 4.70844 | 0 | 0.00913094 | 1 |
| xgboost::realized_volatility_1_20::ALL_SPLITS | ALL_SPLITS | realized_volatility_1_20 | 197 | split_mean_ic_weighted_error_metrics | split | 0.274064 | 0.199084 | 5.68383 | 2.52555 | 0.0083638 | 1 |
| ridge::realized_volatility_1_20::ALL_SPLITS | ALL_SPLITS | realized_volatility_1_20 | 197 | split_mean_ic_weighted_error_metrics | split | 0.239539 | 0.202274 | 2.34566 | 1.37035 | 0.0193159 | 0.923858 |
| ridge_dictionary_only::realized_volatility_1_20::ALL_SPLITS | ALL_SPLITS | realized_volatility_1_20 | 197 | split_mean_ic_weighted_error_metrics | split | 0.224446 | 0.246534 | 2.93698 | 5.26599 | 0.00984473 | 1 |
| ridge_dictionary_only::CAR_1_5::ALL_SPLITS | ALL_SPLITS | CAR_1_5 | 197 | split_mean_ic_weighted_error_metrics | split | 0.0938971 | -0.0916314 | 2.46264 | -1.35811 | 0.0466023 | 0.51269 |
| industry_mean::CAR_1_20::ALL_SPLITS | ALL_SPLITS | CAR_1_20 | 201 | split_mean_ic_weighted_error_metrics | split | 0.0917249 | 0 | 1.54287 | 0 | 0.0839745 | 0.517413 |
| ridge_dictionary_only::CAR_1_20::ALL_SPLITS | ALL_SPLITS | CAR_1_20 | 197 | split_mean_ic_weighted_error_metrics | split | 0.0757218 | -0.0250873 | 1.00708 | -0.349271 | 0.0893545 | 0.492386 |
| ridge_tfidf_svd_only::CAR_1_5::ALL_SPLITS | ALL_SPLITS | CAR_1_5 | 197 | split_mean_ic_weighted_error_metrics | split | 0.0624085 | -0.0312071 | 1.34007 | -0.402003 | 0.136282 | 0.51269 |

The model is evaluated primarily as a cross-sectional ranking signal, not as a minimum-RMSE volatility point forecast.

The highest volatility Rank IC is `0.366849` from `ridge_tfidf_svd_only::realized_volatility_1_20::ALL_SPLITS`, while the lowest volatility RMSE is `0.0083638` from `xgboost::realized_volatility_1_20::ALL_SPLITS`.

The industry-mean baseline remains strong (Rank IC `0.292431`), so the current experiment does not fully isolate the incremental contribution of text from industry risk structure.

ALL_SPLITS Rank IC is an aggregation across rolling out-of-sample splits, not a complete monthly cross-sectional IC time series.

## Industry-Neutral Incremental Signal

Industry-neutral Rank IC separately demeans realized targets and model predictions within each OOS split-industry group before applying tie-aware rank correlation. It is a descriptive incremental-signal diagnostic, not a causal decomposition.

| Model | Raw Rank IC | Industry-Neutral Rank IC | Neutral NW t | Groups | Singletons |
| --- | ---: | ---: | ---: | ---: | ---: |
| ridge_tfidf_svd_only::realized_volatility_1_20::ALL_SPLITS | 0.366849 | 0.341616 | 3.85574 | 116 | 76 |
| ridge_industry_plus_text::realized_volatility_1_20::ALL_SPLITS | 0.329571 | 0.325082 | 4.39941 | 116 | 76 |
| ridge_dictionary_only::realized_volatility_1_20::ALL_SPLITS | 0.224446 | 0.246534 | 5.26599 | 116 | 76 |
| ridge::realized_volatility_1_20::ALL_SPLITS | 0.239539 | 0.202274 | 1.37035 | 116 | 76 |
| xgboost::realized_volatility_1_20::ALL_SPLITS | 0.274064 | 0.199084 | 2.52555 | 116 | 76 |
| industry_mean::realized_volatility_1_20::ALL_SPLITS | 0.292431 | 0 | 0 | 116 | 72 |

## Feature Ablation

Ridge variants use identical rolling splits, validation-only alpha selection, and tuning budgets. industry_only is the training-window industry-mean economic baseline rather than a Ridge fit.

| Feature Set | Estimator | Target | Rank IC | Neutral Rank IC | Rank IC NW t | Neutral NW t | RMSE |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| combined_text | ridge | CAR_1_20 | -0.0458733 | 0.240533 | -0.708303 | 2.72793 | 0.125395 |
| dictionary_only | ridge | CAR_1_20 | 0.0757218 | -0.0250873 | 1.00708 | -0.349271 | 0.0893545 |
| industry_only | industry_mean | CAR_1_20 | 0.0917249 | 0 | 1.54287 | 0 | 0.0839745 |
| industry_plus_text | ridge | CAR_1_20 | -0.0577176 | 0.209681 | -1.31049 | 3.15496 | 0.128214 |
| tfidf_svd_only | ridge | CAR_1_20 | -0.0369358 | 0.0736017 | -0.79872 | 1.05663 | 0.130323 |
| combined_text | ridge | CAR_1_5 | -0.011184 | -0.104078 | -0.558567 | -2.10952 | 0.0955484 |
| dictionary_only | ridge | CAR_1_5 | 0.0938971 | -0.0916314 | 2.46264 | -1.35811 | 0.0466023 |
| industry_only | industry_mean | CAR_1_5 | 0.0308508 | 0 | 0.444417 | 0 | 0.0450735 |
| industry_plus_text | ridge | CAR_1_5 | 0.0183328 | -0.113224 | 0.922493 | -2.79707 | 0.0956145 |
| tfidf_svd_only | ridge | CAR_1_5 | 0.0624085 | -0.0312071 | 1.34007 | -0.402003 | 0.136282 |
| combined_text | ridge | realized_volatility_1_20 | 0.239539 | 0.202274 | 2.34566 | 1.37035 | 0.0193159 |
| dictionary_only | ridge | realized_volatility_1_20 | 0.224446 | 0.246534 | 2.93698 | 5.26599 | 0.00984473 |
| industry_only | industry_mean | realized_volatility_1_20 | 0.292431 | 0 | 4.70844 | 0 | 0.00913094 |
| industry_plus_text | ridge | realized_volatility_1_20 | 0.329571 | 0.325082 | 5.10729 | 4.39941 | 0.0107598 |
| tfidf_svd_only | ridge | realized_volatility_1_20 | 0.366849 | 0.341616 | 5.40552 | 3.85574 | 0.00992428 |

## Primary Rank IC Bootstrap

Bootstrap uses `2000` deterministic resamples (seed `42`).

| Estimand | Method | Point | 95% CI | Bootstrap SE | Zero p | Clusters |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| all_splits_rank_ic | split_bootstrap | 0.239539 | [-0.005, 0.484079] | 0.106923 | 0.111 | 4 |
| all_splits_rank_ic | event_date_bootstrap | 0.239539 | [0.0718728, 0.37431] | 0.0759257 | 0.005 | 104 |
| all_splits_rank_ic | ticker_cluster_bootstrap | 0.239539 | [0.109139, 0.352151] | 0.0620213 | 0.001 | 49 |
| industry_neutral_all_splits_rank_ic | split_bootstrap | 0.202274 | [-0.115655, 0.520204] | 0.143984 | 0.117 | 4 |
| industry_neutral_all_splits_rank_ic | event_date_bootstrap | 0.202274 | [-0.154625, 0.427311] | 0.149263 | 0.366 | 104 |
| industry_neutral_all_splits_rank_ic | ticker_cluster_bootstrap | 0.202274 | [-0.178705, 0.418058] | 0.153562 | 0.357 | 49 |

## Prediction Distribution Diagnostics

- Ranking policy: Portfolio construction uses factor_score ordering to form ranks and quantiles; raw prediction magnitude is not used for equal-weight ranking except in explicitly risk-scaled variants.
- Outlier rule: outlier_count flags predictions outside the observed target range or with absolute value greater than five times the target absolute scale.
- Prediction scale guard: 0 model/target/role rows exceed warning thresholds.
- Scale guard policy: Scale guard warnings do not change rank-based portfolio sorting; they require reporting raw-magnitude instability and favor rank_score or winsorized diagnostics over raw prediction magnitudes.

| Model | Target | Role | N | Scale Ratio | Guard | Outliers | Prediction Range | Target Range |
| --- | --- | --- | ---: | ---: | --- | ---: | --- | --- |
| `ridge` | `realized_volatility_1_20` | `validation` | 184 | 4.5125 | `pass` | 35 | [-0.0724944, 0.257952] | [0.00604034, 0.0571639] |
| `ridge` | `realized_volatility_1_20` | `test` | 197 | 1.91644 | `pass` | 30 | [-0.0371235, 0.109551] | [0.00604034, 0.0571639] |
| `ridge_industry_plus_text` | `realized_volatility_1_20` | `validation` | 184 | 1.58193 | `pass` | 23 | [-0.0112339, 0.0904292] | [0.00604034, 0.0571639] |
| `ridge` | `CAR_1_20` | `validation` | 184 | 3.61142 | `pass` | 21 | [-1.38881, 0.570836] | [-0.199324, 0.384561] |
| `ridge_industry_plus_text` | `CAR_1_20` | `validation` | 184 | 2.86739 | `pass` | 20 | [-1.10269, 0.653834] | [-0.199324, 0.384561] |
| `ridge_tfidf_svd_only` | `CAR_1_20` | `validation` | 184 | 3.33258 | `pass` | 17 | [-0.710785, 1.28158] | [-0.199324, 0.384561] |
| `ridge_industry_plus_text` | `CAR_1_5` | `test` | 197 | 1.58133 | `pass` | 17 | [-0.607204, 0.271407] | [-0.113406, 0.383983] |
| `ridge_tfidf_svd_only` | `CAR_1_5` | `validation` | 196 | 2.02858 | `pass` | 16 | [-0.434362, 0.778941] | [-0.113406, 0.383983] |
| `ridge` | `CAR_1_5` | `test` | 197 | 1.62025 | `pass` | 14 | [-0.622146, 0.283831] | [-0.113406, 0.383983] |
| `ridge_industry_plus_text` | `CAR_1_5` | `validation` | 196 | 1.54973 | `pass` | 13 | [-0.278064, 0.595071] | [-0.113406, 0.383983] |

## Factor Backtest

Portfolio results are diagnostic only in the current applied-grade run; the evidence supports exploratory prediction signals, not formal trading alpha.

- Portfolio method: `top_bottom_quintile`.
- Weighting: `equal_weight`.
- One-way transaction cost: 10.0 bps.
- Newey-West lag: 19.
- Portfolio ranking uses `factor_score` ordering to form ranks and tie-aware quantiles. Tied boundary groups are never split, and a constant-score cross-section does not form a long-short portfolio.

| Model | Split | Target | Long | Short | Gross LS | Net LS | Sharpe | NW t-stat | Direction | Turnover |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| xgboost::CAR_1_20::train_2016_2020__val_2021_2021__test_2022_2022 | train_2016_2020__val_2021_2021__test_2022_2022 | CAR_1_20 | 10 | 10 | 0.0493392 | 0.0473392 | 3.54014 | 1.7705 | long_low_score | 2 |
| ridge::CAR_1_20::train_2016_2023__val_2024_2024__test_2025_2025 | train_2016_2023__val_2024_2024__test_2025_2025 | CAR_1_20 | 9 | 9 | 0.0438471 | 0.0418471 | 4.21056 | 0.804857 | long_high_score | 2 |
| ridge::CAR_1_20::train_2016_2020__val_2021_2021__test_2022_2022 | train_2016_2020__val_2021_2021__test_2022_2022 | CAR_1_20 | 10 | 10 | 0.0300813 | 0.0280813 | 2.0921 | 0.881389 | long_low_score | 2 |
| industry_mean::CAR_1_5::train_2016_2020__val_2021_2021__test_2022_2022 | train_2016_2020__val_2021_2021__test_2022_2022 | CAR_1_5 | 11 | 12 | 0.00669874 | 0.00469874 | 0.388443 | 0.203576 | long_low_score | 2 |
| ridge::CAR_1_5::train_2016_2021__val_2022_2022__test_2023_2023 | train_2016_2021__val_2022_2022__test_2023_2023 | CAR_1_5 | 9 | 9 | 0.00335533 | 0.00135533 | 1.04062 | 0.415438 | long_high_score | 2 |
| industry_mean::realized_volatility_1_20::train_2016_2022__val_2023_2023__test_2024_2024 | train_2016_2022__val_2023_2023__test_2024_2024 | realized_volatility_1_20 | 11 | 11 | 0.00137463 | -0.000625368 | 0.806586 | 0.122749 | long_low_score | 2 |
| ridge::realized_volatility_1_20::train_2016_2022__val_2023_2023__test_2024_2024 | train_2016_2022__val_2023_2023__test_2024_2024 | realized_volatility_1_20 | 9 | 9 | 0.0010603 | -0.000939696 | 0.652373 | 0.106756 | long_low_score | 2 |
| xgboost::realized_volatility_1_20::train_2016_2022__val_2023_2023__test_2024_2024 | train_2016_2022__val_2023_2023__test_2024_2024 | realized_volatility_1_20 | 9 | 9 | 0.000769527 | -0.00123047 | 0.476114 | 0.0790228 | long_low_score | 2 |
| ridge::realized_volatility_1_20::train_2016_2023__val_2024_2024__test_2025_2025 | train_2016_2023__val_2024_2024__test_2025_2025 | realized_volatility_1_20 | 9 | 9 | -0.000193753 | -0.00219375 | -0.0862476 | -0.0147581 | long_low_score | 2 |
| xgboost::realized_volatility_1_20::train_2016_2020__val_2021_2021__test_2022_2022 | train_2016_2020__val_2021_2021__test_2022_2022 | realized_volatility_1_20 | 10 | 10 | -0.0010676 | -0.0030676 | -0.352872 | -0.0558039 | long_low_score | 2 |

## Delisting Return Handling

- Status: `not_applicable`.
- Labels with delisting return applied: `0`.
- Portfolio positions affected by delisting: `0`.
- Delisting returns applied in portfolio rows: `0`.
- Missing delisting returns: `0`.

## Multiple Testing Adjustment

- Specifications: 594; p-values: 594; families: 26.
- Registry roles: primary=2, robustness=188, exploratory=404.
- Role-split adjusted discoveries at 10% FDR: primary=1, robustness=16, exploratory=41.
- Methods: `bonferroni`, `holm`, `benjamini_hochberg_fdr`.

| Role | Family | Tests | Best raw p | Best BH-FDR p | Discoveries 5% | Discoveries 10% |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| exploratory | CAR_1_20::industry_neutral_rank_ic | 30 | 5.28093e-08 | 1.58428e-06 | 2 | 2 |
| exploratory | CAR_1_20::newey_west_t_stat | 4 | 0.00732389 | 0.0292956 | 1 | 1 |
| exploratory | CAR_1_20::portfolio_sharpe | 72 | 0.0155864 | 0.429351 | 0 | 0 |
| exploratory | CAR_1_20::rank_ic | 30 | 0.000823076 | 0.0246923 | 2 | 10 |
| exploratory | CAR_1_5::industry_neutral_rank_ic | 30 | 0.0153563 | 0.227541 | 0 | 0 |
| exploratory | CAR_1_5::newey_west_t_stat | 4 | 0.12624 | 0.504959 | 0 | 0 |
| exploratory | CAR_1_5::portfolio_sharpe | 72 | 0.0117287 | 0.422233 | 0 | 0 |
| exploratory | CAR_1_5::rank_ic | 30 | 0.00783496 | 0.235049 | 0 | 0 |
| exploratory | realized_volatility_1_20::industry_neutral_rank_ic | 30 | 5.4678e-06 | 0.000124936 | 10 | 10 |
| exploratory | realized_volatility_1_20::newey_west_t_stat | 4 | 0.575098 | 0.902306 | 0 | 0 |
| exploratory | realized_volatility_1_20::portfolio_sharpe | 68 | 0.0113305 | 0.247642 | 0 | 0 |
| exploratory | realized_volatility_1_20::rank_ic | 30 | 1.82092e-05 | 0.00033741 | 18 | 18 |
| primary | realized_volatility_1_20::portfolio_sharpe | 1 | 0.114733 | 0.114733 | 0 | 0 |
| primary | realized_volatility_1_20::rank_ic | 1 | 0.000667721 | 0.000667721 | 1 | 1 |
| robustness | CAR_1_20::industry_neutral_rank_ic | 5 | 0.000632706 | 0.00316353 | 2 | 2 |
| robustness | CAR_1_20::newey_west_t_stat | 8 | 3.84613e-14 | 3.0769e-13 | 4 | 4 |
| robustness | CAR_1_20::portfolio_sharpe | 48 | 0.0223164 | 0.535593 | 0 | 0 |
| robustness | CAR_1_20::rank_ic | 5 | 0.290646 | 0.60677 | 0 | 0 |
| robustness | CAR_1_5::industry_neutral_rank_ic | 5 | 0.0982828 | 0.242826 | 0 | 0 |
| robustness | CAR_1_5::newey_west_t_stat | 8 | 0.0022125 | 0.0177 | 1 | 1 |
| robustness | CAR_1_5::portfolio_sharpe | 48 | 0.0415628 | 0.975302 | 0 | 0 |
| robustness | CAR_1_5::rank_ic | 5 | 0.189622 | 0.948109 | 0 | 0 |
| robustness | realized_volatility_1_20::industry_neutral_rank_ic | 5 | 7.14439e-07 | 3.5722e-06 | 5 | 5 |
| robustness | realized_volatility_1_20::newey_west_t_stat | 8 | 0.595602 | 0.988225 | 0 | 0 |
| robustness | realized_volatility_1_20::portfolio_sharpe | 39 | 0.0471502 | 0.619766 | 0 | 0 |
| robustness | realized_volatility_1_20::rank_ic | 4 | 8.35347e-08 | 3.34139e-07 | 4 | 4 |

## Specification Registry

- Role counts: primary=2, robustness=188, exploratory=404.
- Registry version: `specification-registry-v1`.
- Registry designation: `pre_registered_specification_registry`.
- Preregistration status: `pre_registered`.
- Preregistered primary rule count: `2`.

| Role | Status | Target | Model | Metric | Split | Portfolio | Raw metric | Raw p |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: |
| primary | pre_registered_primary | realized_volatility_1_20 | ridge | rank_ic | ALL_SPLITS | prediction_metric | 0.239539 | 0.000667721 |
| primary | pre_registered_primary | realized_volatility_1_20 | ridge | portfolio_sharpe | ALL_SPLITS | monthly_common_rebalance_top_bottom_quintile | -0.853889 | 0.114733 |

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

- Git commit SHA: `b35d6dd806acfb592e4a0c8b72e9338d09120aab`.
- Package version: `0.16.0`.
- Dirty worktree flag: `False`.

```bash
python -m text_factor_lab audit --run-id 50_company_public_fmp_alpha_2016_2025_v4 --run-dir runs\text_factor_lab\50_company_public_fmp_alpha_2016_2025_v4
python -m text_factor_lab report --run-id 50_company_public_fmp_alpha_2016_2025_v4 --run-dir runs\text_factor_lab\50_company_public_fmp_alpha_2016_2025_v4
```

Generated at `2026-06-30T02:59:50.428696+00:00` by `report-generator-v0`.
