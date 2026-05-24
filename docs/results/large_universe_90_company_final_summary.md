# Final Algorithm Rerun Analysis - 90 Company Large Universe

## Run Setup

- Output: `runs\text_factor_lab\real_10k_large_universe_2016_2025_public_v0\analysis\final_algo_rerun_validation_risk_scaled`
- Upstream artifacts reused: fixed 10-K documents, labels, features, predictions, and prices from `public_v0`.
- Rerun scope: evaluation, portfolio construction, multiple testing, and specification registry.
- Portfolio policy: `validation_selected` signal direction + `risk_scaled` target-aware policy.
- Transaction cost: 10 bps one-way.
- Primary portfolio p-value: ALL_SPLITS monthly OOS return-series Newey-West t-stat.

## Data And Audit

- Documents: 883
- Tickers with 10-K documents: 90
- Labels: 2649
- Predictions: 8236
- Targets: {'CAR_1_5': 883, 'CAR_1_20': 883, 'realized_volatility_1_20': 883}
- Models: historical_mean, industry_mean, ridge, xgboost
- Rolling test splits: 4
- Audit status inherited from upstream run: fail (coverage=0.496, failures=1, warnings=1)

## ALL_SPLITS Prediction Results

| Target | Best model | Rank IC | Rank IC NW t | RMSE | N |
| --- | --- | ---: | ---: | ---: | ---: |
| CAR_1_20 | industry_mean | 0.1698 | 3.539 | 0.07493 | 357 |
| CAR_1_5 | industry_mean | 0.1834 | 4.524 | 0.03373 | 357 |
| realized_volatility_1_20 | xgboost | 0.3899 | 21.32 | 0.007863 | 357 |

Full model table:

| Target | Model | Rank IC | Rank IC NW t | RMSE | Directional Acc |
| --- | --- | ---: | ---: | ---: | ---: |
| CAR_1_20 | industry_mean | 0.1698 | 3.539 | 0.07493 | 0.5462 |
| CAR_1_20 | xgboost | 0.09706 | 1.737 | 0.07363 | 0.5546 |
| CAR_1_20 | historical_mean | 0.09321 | 2.547 | 0.07344 | 0.5238 |
| CAR_1_20 | ridge | 0.06341 | 1.869 | 0.08441 | 0.5014 |
| CAR_1_5 | industry_mean | 0.1834 | 4.524 | 0.03373 | 0.5406 |
| CAR_1_5 | historical_mean | 0.05491 | 4.228 | 0.03411 | 0.5098 |
| CAR_1_5 | xgboost | 0.02162 | 0.3217 | 0.03479 | 0.479 |
| CAR_1_5 | ridge | 0.01601 | 0.4458 | 0.04017 | 0.507 |
| realized_volatility_1_20 | xgboost | 0.3899 | 21.32 | 0.007863 | 1 |
| realized_volatility_1_20 | ridge | 0.3335 | 14.74 | 0.01026 | 1 |
| realized_volatility_1_20 | industry_mean | 0.3144 | 10.17 | 0.008174 | 1 |
| realized_volatility_1_20 | historical_mean | -0.02134 | -0.4745 | 0.008236 | 1 |

## ALL_SPLITS Monthly Portfolio Results

Top positive net monthly portfolios after cost:

| Target | Model | Variant | Direction | Policy | Sharpe | NW t | Raw p | Ann Ret | Max DD | Role |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| CAR_1_5 | industry_mean | monthly_equal_weight | long_low_score | risk_scaled | 1.658 | 2.249 | 0.0245 | 0.3762 | -0.1636 | exploratory |
| CAR_1_5 | industry_mean | monthly_value_weight | long_low_score | risk_scaled | 1.617 | 2.195 | 0.02813 | 0.3956 | -0.1515 | exploratory |
| CAR_1_20 | historical_mean | monthly_equal_weight | long_low_score | risk_scaled | 1.408 | 1.859 | 0.06304 | 0.2816 | -0.1235 | exploratory |
| CAR_1_5 | xgboost | monthly_sector_neutral_equal_weight | long_low_score | risk_scaled | 1.04 | 1.933 | 0.05327 | 0.1532 | -0.1334 | robustness |
| CAR_1_5 | xgboost | monthly_sector_neutral_value_weight | long_low_score | risk_scaled | 0.9839 | 1.864 | 0.06235 | 0.1452 | -0.1241 | robustness |
| CAR_1_20 | historical_mean | monthly_value_weight | long_low_score | risk_scaled | 0.9111 | 1.18 | 0.2379 | 0.1752 | -0.1696 | exploratory |
| CAR_1_20 | ridge | monthly_sector_neutral_equal_weight | long_low_score | risk_scaled | 0.728 | 1.074 | 0.2828 | 0.1105 | -0.1276 | robustness |
| CAR_1_20 | ridge | monthly_sector_neutral_value_weight | long_low_score | risk_scaled | 0.6171 | 0.9031 | 0.3665 | 0.09106 | -0.1197 | robustness |
| CAR_1_5 | industry_mean | monthly_sector_neutral_value_weight | long_high_score | risk_scaled | 0.6086 | 0.7208 | 0.4711 | 0.06445 | -0.157 | exploratory |
| CAR_1_5 | industry_mean | monthly_sector_neutral_equal_weight | long_high_score | risk_scaled | 0.605 | 0.7285 | 0.4663 | 0.06359 | -0.1593 | exploratory |
| realized_volatility_1_20 | historical_mean | monthly_equal_weight | long_low_score | risk_scaled | 0.5731 | 1.072 | 0.2837 | 0.09615 | -0.3344 | exploratory |
| realized_volatility_1_20 | historical_mean | monthly_value_weight | long_low_score | risk_scaled | 0.5731 | 1.072 | 0.2837 | 0.09615 | -0.3344 | exploratory |

Top positive sector-neutral portfolios:

| Target | Model | Variant | Sharpe | NW t | Ann Ret | Max DD |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| CAR_1_5 | xgboost | monthly_sector_neutral_equal_weight | 1.04 | 1.933 | 0.1532 | -0.1334 |
| CAR_1_5 | xgboost | monthly_sector_neutral_value_weight | 0.9839 | 1.864 | 0.1452 | -0.1241 |
| CAR_1_20 | ridge | monthly_sector_neutral_equal_weight | 0.728 | 1.074 | 0.1105 | -0.1276 |
| CAR_1_20 | ridge | monthly_sector_neutral_value_weight | 0.6171 | 0.9031 | 0.09106 | -0.1197 |
| CAR_1_5 | industry_mean | monthly_sector_neutral_value_weight | 0.6086 | 0.7208 | 0.06445 | -0.157 |
| CAR_1_5 | industry_mean | monthly_sector_neutral_equal_weight | 0.605 | 0.7285 | 0.06359 | -0.1593 |
| CAR_1_20 | historical_mean | monthly_sector_neutral_equal_weight | 0.2988 | 0.3964 | 0.0349 | -0.1419 |
| CAR_1_20 | historical_mean | monthly_sector_neutral_value_weight | 0.2882 | 0.3758 | 0.03332 | -0.1572 |
| CAR_1_5 | ridge | monthly_sector_neutral_equal_weight | 0.2773 | 0.406 | 0.03375 | -0.2583 |
| CAR_1_20 | industry_mean | monthly_sector_neutral_value_weight | 0.1837 | 0.2162 | 0.01531 | -0.1894 |

## Multiple Testing And Preregistered Rules

- Specification registry: specification-registry-v1 / pre_registered
- Tested specifications: 572; families: 20
- Role counts: {'exploratory': 406, 'primary': 2, 'robustness': 164}
- Primary discoveries after adjustment: 5%=1, 10%=1
- Robustness discoveries at 10% FDR: 11
- Primary prediction spec: realized_volatility_1_20 / ridge / Rank IC=0.3335, p=6.849e-11, method=fisher_z_rank_ic.
- Primary portfolio spec: realized_volatility_1_20 / ridge / Sharpe=-0.3602, p=0.4598, method=all_splits_oos_return_series_newey_west_t_stat.

## Feature And Model Interpretation

- The clearest sample-out prediction signal is future realized volatility, not CAR. XGBoost and Ridge rank volatility well, and industry_mean is a strong baseline.
- Return targets show weaker text-model evidence: CAR_1_5 and CAR_1_20 are often led by industry_mean rather than Ridge/XGBoost, so this is not clean textual alpha evidence.
- Feature-ablation reference from the same large-universe run shows TF-IDF/SVD is stronger than dictionary-only for volatility prediction, while dictionary-only remains directionally useful but weaker.
- The positive portfolio results after the new rules mostly appear in CAR_1_5 industry_mean or non-primary robustness/exploratory variants. They are useful diagnostics, but not formal primary evidence.
- Sector-neutral positive results exist, especially XGBoost CAR_1_5, but their raw p-values are near threshold and do not constitute primary multiple-testing-adjusted evidence.
- The preregistered primary portfolio rule does not pass: realized_volatility_1_20 / Ridge / monthly sector-neutral equal-weight has negative Sharpe and p=0.4598.

## Feature Ablation Reference

| Feature source | Best volatility model | Vol Rank IC | Vol NW t | Note |
| --- | --- | ---: | ---: | --- |
| combined | xgboost | 0.3899 | 21.32 |  |
| dictionary_only | xgboost | 0.3466 | 23.16 |  |
| tfidf_svd_only | xgboost | 0.4067 | 13.86 | strongest text feature block |

## Bottom Line

- Formal prediction evidence: yes, for realized volatility.
- Formal portfolio evidence: no, because the preregistered primary portfolio fails under ALL_SPLITS return-series p-value.
- Best research direction: keep volatility as the primary target, use TF-IDF/SVD or richer text embeddings, and treat CAR portfolios as exploratory until they pass sector-neutral, cost-adjusted, multiple-testing-adjusted ALL_SPLITS tests.
