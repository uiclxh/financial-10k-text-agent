# Appendix Tables - 50_company_public_fmp_alpha_2016_2025_v1

## Table 1 Sample Coverage

| Item | Count |
| --- | ---: |
| Documents | 500 |
| Labels | 1500 |
| Predictions | 4716 |
| Features | 520465 |

## Table 1B Coverage Waterfall

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

## Table 2 Feature Summary

| Item | Value |
| --- | --- |
| Methods | `dictionary_tone`, `tfidf` |
| Versions | `dictionary-tone-v0`, `tfidf-svd-v0:train_2016_2020__val_2021_2021__test_2022_2022:full`, `tfidf-svd-v0:train_2016_2020__val_2021_2021__test_2022_2022:item_1`, `tfidf-svd-v0:train_2016_2020__val_2021_2021__test_2022_2022:item_1a`, `tfidf-svd-v0:train_2016_2020__val_2021_2021__test_2022_2022:item_3`, `tfidf-svd-v0:train_2016_2020__val_2021_2021__test_2022_2022:item_7`, `tfidf-svd-v0:train_2016_2021__val_2022_2022__test_2023_2023:full`, `tfidf-svd-v0:train_2016_2021__val_2022_2022__test_2023_2023:item_1`, `tfidf-svd-v0:train_2016_2021__val_2022_2022__test_2023_2023:item_1a`, `tfidf-svd-v0:train_2016_2021__val_2022_2022__test_2023_2023:item_3`, `tfidf-svd-v0:train_2016_2021__val_2022_2022__test_2023_2023:item_7`, `tfidf-svd-v0:train_2016_2022__val_2023_2023__test_2024_2024:full`, `tfidf-svd-v0:train_2016_2022__val_2023_2023__test_2024_2024:item_1`, `tfidf-svd-v0:train_2016_2022__val_2023_2023__test_2024_2024:item_1a`, `tfidf-svd-v0:train_2016_2022__val_2023_2023__test_2024_2024:item_3`, `tfidf-svd-v0:train_2016_2022__val_2023_2023__test_2024_2024:item_7`, `tfidf-svd-v0:train_2016_2023__val_2024_2024__test_2025_2025:full`, `tfidf-svd-v0:train_2016_2023__val_2024_2024__test_2025_2025:item_1`, `tfidf-svd-v0:train_2016_2023__val_2024_2024__test_2025_2025:item_1a`, `tfidf-svd-v0:train_2016_2023__val_2024_2024__test_2025_2025:item_3`, `tfidf-svd-v0:train_2016_2023__val_2024_2024__test_2025_2025:item_7` |
| Text scopes | `full`, `item_1`, `item_1a`, `item_3`, `item_7` |

## Table 3 OOS Prediction Metrics

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

## Table 4 Portfolio Return Summary

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

## Table 5 Portfolio Variant Metrics

| Model | Variant | Target | Direction | N | Ann Ret | Ann Vol | Sharpe | NW t | Max DD | Turnover |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ridge::CAR_1_5::train_2016_2023__val_2024_2024__test_2025_2025 | sector_neutral_equal_weight | CAR_1_5 | long_low_score | 16 | 2.66975 | 0.226544 | 5.85952 | 1.64257 | -0.0269592 | 0.3125 |
| ridge::CAR_1_5::train_2016_2023__val_2024_2024__test_2025_2025 | sector_neutral_value_weight | CAR_1_5 | long_low_score | 16 | 2.66975 | 0.226544 | 5.85952 | 1.64257 | -0.0269592 | 0.3125 |
| industry_mean::CAR_1_20::train_2016_2021__val_2022_2022__test_2023_2023 | sector_neutral_equal_weight | CAR_1_20 | long_low_score | 82 | 2.3146 | 0.239614 | 5.13 | 5.86559 | -0.0515937 | 0.0853659 |
| industry_mean::CAR_1_20::train_2016_2021__val_2022_2022__test_2023_2023 | sector_neutral_value_weight | CAR_1_20 | long_low_score | 82 | 2.3146 | 0.239614 | 5.13 | 5.86559 | -0.0515937 | 0.0853659 |
| historical_mean::CAR_1_5::train_2016_2023__val_2024_2024__test_2025_2025 | sector_neutral_equal_weight | CAR_1_5 | long_high_score | 16 | 1.97981 | 0.230233 | 4.86041 | 1.23932 | -0.0439631 | 0.3125 |
| historical_mean::CAR_1_5::train_2016_2023__val_2024_2024__test_2025_2025 | sector_neutral_value_weight | CAR_1_5 | long_high_score | 16 | 1.97981 | 0.230233 | 4.86041 | 1.23932 | -0.0439631 | 0.3125 |
| industry_mean::CAR_1_5::train_2016_2023__val_2024_2024__test_2025_2025 | sector_neutral_equal_weight | CAR_1_5 | long_low_score | 16 | 1.88368 | 0.240043 | 4.53344 | 1.72623 | -0.035445 | 0.3125 |
| industry_mean::CAR_1_5::train_2016_2023__val_2024_2024__test_2025_2025 | sector_neutral_value_weight | CAR_1_5 | long_low_score | 16 | 1.88368 | 0.240043 | 4.53344 | 1.72623 | -0.035445 | 0.3125 |
| industry_mean::CAR_1_5::train_2016_2022__val_2023_2023__test_2024_2024 | sector_neutral_equal_weight | CAR_1_5 | long_high_score | 16 | 1.05772 | 0.175963 | 4.18938 | 1.86117 | -0.0132418 | 0.3125 |
| industry_mean::CAR_1_5::train_2016_2022__val_2023_2023__test_2024_2024 | sector_neutral_value_weight | CAR_1_5 | long_high_score | 16 | 1.05772 | 0.175963 | 4.18938 | 1.86117 | -0.0132418 | 0.3125 |
| xgboost::CAR_1_20::train_2016_2022__val_2023_2023__test_2024_2024 | sector_neutral_equal_weight | CAR_1_20 | long_high_score | 61 | 0.519775 | 0.167491 | 2.5836 | 2.38882 | -0.0422846 | 0.0819672 |
| xgboost::CAR_1_20::train_2016_2022__val_2023_2023__test_2024_2024 | sector_neutral_value_weight | CAR_1_20 | long_high_score | 61 | 0.519775 | 0.167491 | 2.5836 | 2.38882 | -0.0422846 | 0.0819672 |

## Table 6 Multiple-Testing-Adjusted Results

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

## Table 7 Primary Specification Registry

- Role counts: primary=2, robustness=164, exploratory=402.
- Registry version: `specification-registry-v1`.
- Registry designation: `pre_registered_specification_registry`.
- Preregistration status: `pre_registered`.
- Preregistered primary rule count: `2`.

| Role | Status | Target | Model | Metric | Split | Portfolio | Raw metric | Raw p |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: |
| primary | pre_registered_primary | realized_volatility_1_20 | ridge | rank_ic | ALL_SPLITS | prediction_metric | 0.260604 | 0.000174313 |
| primary | pre_registered_primary | realized_volatility_1_20 | ridge | portfolio_sharpe | ALL_SPLITS | monthly_common_rebalance_top_bottom_quintile | -0.870379 | 0.108178 |

## Table 8 Audit Checks

| Status | Check | Stage | Message |
| --- | --- | --- | --- |
| warn | split_purge_and_leakage | split | 0 split records have severity=fail; 46 records were purged by embargo; 0 records have severity=warn |
| warn | mixed_market_data_source_boundary | data | Mixed market data source detected. Treat the run as an applied-grade pilot; do not present market-data-dependent portfolio evidence as a CRSP/WRDS-equivalent formal result. |
