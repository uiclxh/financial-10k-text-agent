# Factor Card - 50_company_public_fmp_alpha_2016_2025_v4

| Field | Value |
| --- | --- |
| Conclusion | `exploratory_report` |
| Formal result allowed | `False` |
| Formal result blockers | `run_type is exploratory_run, so the run is intentionally not eligible for a formal empirical result.`, `market data uses a mixed FMP/Yahoo public-source stack, not a single CRSP/WRDS-equivalent research-grade source.`, `market_cap_at_selection is based on applied-grade estimates rather than licensed CRSP/Compustat/WRDS market-cap history.`, `the universe is an applied fixed-company panel, not a survivorship-free CRSP/WRDS research-grade universe.`, `audit_status is warn; warnings are boundary disclosures, not pipeline failures.` |
| Audit status | `warn` |
| Coverage | `0.496` |
| Eligible OOS coverage | `1` |
| Primary spec coverage | `1` |
| Primary prediction coverage | `1` |
| Primary portfolio coverage | `1` |
| Signal direction policy | `pre_registered_score_convention_no_post_hoc_sign_flip` |
| Primary prediction sign | `positive` |
| Universe | `fixed_50_company_sp500_sector_seed_fmp_alpha_pilot` |
| Sample | `2016-01-01..2025-12-31` |
| Targets | `realized_volatility_1_20`, `CAR_1_5`, `CAR_1_20` |
| Features | `dictionary_tone`, `tfidf` |
| Models | `historical_mean`, `industry_mean`, `ridge`, `xgboost` |
| Multiple-testing families | `26` |
| Git commit SHA | `b35d6dd806acfb592e4a0c8b72e9338d09120aab` |
| Package version | `0.16.0` |
| Dirty worktree flag | `False` |
| Portfolio return sources | `daily_price_panel`, `monthly_common_rebalance_price_panel` |
| Position accounting | `drifted_daily_positions`, `monthly_rebalance_drifted_daily_positions` |

## Best Observed Exploratory Ranking Result

- Model: `ridge_tfidf_svd_only::realized_volatility_1_20::ALL_SPLITS`.
- Target: `realized_volatility_1_20`.
- Split: `ALL_SPLITS`.
- Rank IC: `0.366849`.
- Rank IC Newey-West t-stat: `5.40552`.
- Aggregation: `split_mean_ic_weighted_error_metrics`.
- RMSE: `0.00992428`.
- Directional accuracy: `0.994924`.

The model is evaluated primarily as a cross-sectional ranking signal, not as a minimum-RMSE volatility point forecast.

The highest volatility Rank IC is `0.366849` from `ridge_tfidf_svd_only::realized_volatility_1_20::ALL_SPLITS`, while the lowest volatility RMSE is `0.0083638` from `xgboost::realized_volatility_1_20::ALL_SPLITS`.

The industry-mean baseline remains strong (Rank IC `0.292431`), so the current experiment does not fully isolate the incremental contribution of text from industry risk structure.

ALL_SPLITS Rank IC is an aggregation across rolling out-of-sample splits, not a complete monthly cross-sectional IC time series.

## Incremental Text Diagnostics

Industry-neutral Rank IC separately demeans realized targets and model predictions within each OOS split-industry group before applying tie-aware rank correlation. It is a descriptive incremental-signal diagnostic, not a causal decomposition.

| Model | Raw Rank IC | Industry-Neutral Rank IC | Neutral NW t | Groups | Singletons |
| --- | ---: | ---: | ---: | ---: | ---: |
| ridge_tfidf_svd_only::realized_volatility_1_20::ALL_SPLITS | 0.366849 | 0.341616 | 3.85574 | 116 | 76 |
| ridge_industry_plus_text::realized_volatility_1_20::ALL_SPLITS | 0.329571 | 0.325082 | 4.39941 | 116 | 76 |
| ridge_dictionary_only::realized_volatility_1_20::ALL_SPLITS | 0.224446 | 0.246534 | 5.26599 | 116 | 76 |
| ridge::realized_volatility_1_20::ALL_SPLITS | 0.239539 | 0.202274 | 1.37035 | 116 | 76 |
| xgboost::realized_volatility_1_20::ALL_SPLITS | 0.274064 | 0.199084 | 2.52555 | 116 | 76 |
| industry_mean::realized_volatility_1_20::ALL_SPLITS | 0.292431 | 0 | 0 | 116 | 72 |

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

## Primary Rank IC Confidence Intervals

Bootstrap uses `2000` deterministic resamples (seed `42`).

| Estimand | Method | Point | 95% CI | Bootstrap SE | Zero p | Clusters |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| all_splits_rank_ic | split_bootstrap | 0.239539 | [-0.005, 0.484079] | 0.106923 | 0.111 | 4 |
| all_splits_rank_ic | event_date_bootstrap | 0.239539 | [0.0718728, 0.37431] | 0.0759257 | 0.005 | 104 |
| all_splits_rank_ic | ticker_cluster_bootstrap | 0.239539 | [0.109139, 0.352151] | 0.0620213 | 0.001 | 49 |
| industry_neutral_all_splits_rank_ic | split_bootstrap | 0.202274 | [-0.115655, 0.520204] | 0.143984 | 0.117 | 4 |
| industry_neutral_all_splits_rank_ic | event_date_bootstrap | 0.202274 | [-0.154625, 0.427311] | 0.149263 | 0.366 | 104 |
| industry_neutral_all_splits_rank_ic | ticker_cluster_bootstrap | 0.202274 | [-0.178705, 0.418058] | 0.153562 | 0.357 | 49 |

## Preregistered Portfolio Result

- Model: `ridge::realized_volatility_1_20::ALL_SPLITS`.
- Target: `realized_volatility_1_20`.
- Portfolio: `monthly_common_rebalance_top_bottom_quintile`.
- Sharpe ratio: `-0.853889`.
- Raw p-value: `0.114733`.
- Interpretation: diagnostic only; the preregistered portfolio test does not establish formal tradable alpha.

Some split-level portfolio diagnostics may show high Sharpe ratios, but they are not the preregistered primary test and can remain statistically weak after Newey-West adjustment.

## Evidence Level

exploratory_prediction_evidence_not_formal_trading_alpha

## Primary Sign Convention

The preregistered prediction specification has a positive Rank IC under the current score convention.

## Diagnostics

- Vocabulary manifest rows: `20`.
- Section length flags: `{'manual_check_lt_100_words': 144, 'ok': 1840, 'warn_lt_500_words': 16}`.
- Section-level feature exclusions: `144`.
- Prediction ranking policy: Portfolio construction uses factor_score ordering to form ranks and quantiles; raw prediction magnitude is not used for equal-weight ranking except in explicitly risk-scaled variants.
- Portfolio interpretation: diagnostic only; current evidence does not establish formal trading alpha.

## Usage Boundary

Formal result is not allowed for data-boundary reasons, not because the pipeline failed:
- run_type is exploratory_run, so the run is intentionally not eligible for a formal empirical result.
- market data uses a mixed FMP/Yahoo public-source stack, not a single CRSP/WRDS-equivalent research-grade source.
- market_cap_at_selection is based on applied-grade estimates rather than licensed CRSP/Compustat/WRDS market-cap history.
- the universe is an applied fixed-company panel, not a survivorship-free CRSP/WRDS research-grade universe.
- audit_status is warn; warnings are boundary disclosures, not pipeline failures.

Report as exploratory prediction evidence and disclose tested specifications, data-source boundaries, and portfolio limitations.
