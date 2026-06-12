# Empirical Report - 10_company_public_fmp_alpha_2016_2025_v1

## 1. Research Design

This experiment evaluates whether SEC 10-K text features contain out-of-sample information about configured return or volatility targets. The workflow uses rolling splits, validation-only model selection, artifact-level audit checks, and multiple-testing disclosure.

## 2. Data And Universe Construction

- Universe: `fixed_10_company_us_10k_fmp_alpha_pilot`.
- Selection date: `2016-01-01`.
- Sample window: `2016-01-01` to `2025-12-31`.
- Documents: 100.
- Labels: 300.

## 2.1 Licensed Data Stack

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

## 2.2 Coverage And Audit Diagnosis

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

## 3. Event-Time Alignment

The configured timezone is `America/New_York`. Document availability and prediction timestamps are audited before formal conclusions are allowed.

## 4. Text Feature Construction

- Methods: `dictionary_tone`, `tfidf`.
- Text scopes: `full`, `item_1`, `item_1a`, `item_3`, `item_7`.
- Feature records: 57850.

## 5. Label Construction

- Targets: `realized_volatility_1_20`, `CAR_1_5`, `CAR_1_20`.
- Return type: `log`.
- Benchmark: `SPY`.

## 6. Prediction Models

- Models: `historical_mean`, `industry_mean`, `ridge`, `xgboost`.
- Selection metric: `validation_rank_ic`.
- Tuning logs: 48.

## 7. Out-Of-Sample Forecasting Results

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

## 8. Portfolio Construction

The backtest uses `top_bottom_quintile` with `equal_weight` weighting in the configured summary backtest. Portfolio variant diagnostics are reported when available. These portfolio outputs are diagnostic only and should not be presented as formal trading-alpha evidence. Portfolio return sources: `daily_price_panel`, `monthly_common_rebalance_price_panel`. Position accounting: `drifted_daily_positions`, `monthly_rebalance_drifted_daily_positions`.

## 9. Factor Backtest Results

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

## 10. Sector-Neutral And Value-Weighted Robustness

| Model | Variant | Target | Direction | N | Ann Ret | Ann Vol | Sharpe | NW t | Max DD | Turnover |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| industry_mean::realized_volatility_1_20::train_2016_2021__val_2022_2022__test_2023_2023 | monthly_equal_weight | realized_volatility_1_20 | long_low_score | 204 | 1.1331 | 0.323713 | 2.50263 | 2.53529 | -0.129843 | 0.0147059 |
| industry_mean::realized_volatility_1_20::train_2016_2021__val_2022_2022__test_2023_2023 | monthly_value_weight | realized_volatility_1_20 | long_low_score | 204 | 1.05472 | 0.326151 | 2.37126 | 2.34684 | -0.129843 | 0.0138006 |
| ridge::realized_volatility_1_20::train_2016_2021__val_2022_2022__test_2023_2023 | monthly_value_weight | realized_volatility_1_20 | long_low_score | 204 | 0.902524 | 0.293979 | 2.3316 | 2.01316 | -0.19276 | 0.011927 |
| ridge::realized_volatility_1_20::train_2016_2021__val_2022_2022__test_2023_2023 | monthly_equal_weight | realized_volatility_1_20 | long_low_score | 204 | 0.896175 | 0.294403 | 2.31729 | 2.00153 | -0.192513 | 0.00980392 |
| industry_mean::CAR_1_5::train_2016_2021__val_2022_2022__test_2023_2023 | equal_weight | CAR_1_5 | long_high_score | 46 | 0.495709 | 0.20815 | 2.03685 | 2.03108 | -0.0502483 | 0.206522 |
| industry_mean::CAR_1_5::train_2016_2021__val_2022_2022__test_2023_2023 | value_weight | CAR_1_5 | long_high_score | 46 | 0.495709 | 0.20815 | 2.03685 | 2.03108 | -0.0502483 | 0.206522 |
| ridge::CAR_1_5::train_2016_2021__val_2022_2022__test_2023_2023 | equal_weight | CAR_1_5 | long_high_score | 46 | 0.495709 | 0.20815 | 2.03685 | 2.03108 | -0.0502483 | 0.206522 |
| ridge::CAR_1_5::train_2016_2021__val_2022_2022__test_2023_2023 | value_weight | CAR_1_5 | long_high_score | 46 | 0.495709 | 0.20815 | 2.03685 | 2.03108 | -0.0502483 | 0.206522 |
| xgboost::CAR_1_5::train_2016_2021__val_2022_2022__test_2023_2023 | equal_weight | CAR_1_5 | long_high_score | 46 | 0.495709 | 0.20815 | 2.03685 | 2.03108 | -0.0502483 | 0.206522 |
| xgboost::CAR_1_5::train_2016_2021__val_2022_2022__test_2023_2023 | value_weight | CAR_1_5 | long_high_score | 46 | 0.495709 | 0.20815 | 2.03685 | 2.03108 | -0.0502483 | 0.206522 |
| historical_mean::CAR_1_20::train_2016_2021__val_2022_2022__test_2023_2023 | equal_weight | CAR_1_20 | long_high_score | 181 | 0.568377 | 0.249646 | 1.92782 | 1.95282 | -0.110454 | 0.0524862 |
| historical_mean::CAR_1_20::train_2016_2021__val_2022_2022__test_2023_2023 | value_weight | CAR_1_20 | long_high_score | 181 | 0.568377 | 0.249646 | 1.92782 | 1.95282 | -0.110454 | 0.0524862 |

## 11. Delisting Return Handling

- Status: `not_applicable`.
- Labels with delisting return applied: `0`.
- Portfolio positions affected by delisting: `0`.
- Delisting returns applied in portfolio rows: `0`.
- Missing delisting returns: `0`.

## 12. Multiple Testing Adjustment

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

## 13. Specification Registry

- Role counts: primary=2, robustness=160, exploratory=310.
- Registry version: `specification-registry-v1`.
- Registry designation: `pre_registered_specification_registry`.
- Preregistration status: `pre_registered`.
- Preregistered primary rule count: `2`.

| Role | Status | Target | Model | Metric | Split | Portfolio | Raw metric | Raw p |
| --- | --- | --- | --- | --- | --- | --- | ---: | ---: |
| primary | pre_registered_primary | realized_volatility_1_20 | ridge | rank_ic | ALL_SPLITS | prediction_metric | -0.278788 | 0.0815252 |
| primary | pre_registered_primary | realized_volatility_1_20 | ridge | portfolio_sharpe | ALL_SPLITS | monthly_common_rebalance_top_bottom_quintile | -0.302787 | 0.62627 |

## 14. Failure Cases And Audit Results

| Status | Check | Stage | Message |
| --- | --- | --- | --- |
| warn | split_purge_and_leakage | split | 0 split records have severity=fail; 32 records were purged by embargo; 0 records have severity=warn |
| warn | mixed_market_data_source_boundary | data | Mixed market data source detected. Treat the run as an applied-grade pilot; do not present market-data-dependent portfolio evidence as a CRSP/WRDS-equivalent formal result. |

## 15. Economic Interpretation

The run shows positive out-of-sample prediction evidence, but audit or data-source boundaries prevent a formal trading-alpha conclusion.

## 16. Limitations

- Universe quality must be reviewed before formal empirical claims.
- Current portfolio diagnostics still rely on available event-window artifacts.
- Deflated Sharpe, CPCV/PBO, bootstrap intervals, and clustered errors are not included.
- Audit warnings should be resolved or disclosed.

## 17. Conclusion

Exploratory prediction evidence is present, but formal trading-alpha evidence is not established.
