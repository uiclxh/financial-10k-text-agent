# Large Universe 10-K Experiment Analysis

## Data And Audit

- Documents: 883
- Labels: 2649
- Predictions: 8236
- Filing status counts: {'included': 90, 'missing_sec_cik': 1}
- Price status counts: {'ok': 91}
- Audit status: fail
- Audit coverage: 0.496
- Audit failures: 1
- Audit warnings: 1

## combined

### OOS Rank IC

| Family | Target | Rank IC | IC t | IC NW t | RMSE | N | Splits |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| historical_mean | CAR_1_20 | 0.0932 | 1.094 | 2.547 | 0.07344 | 357 | 4 |
| industry_mean | CAR_1_20 | 0.1698 | 1.373 | 3.539 | 0.07493 | 357 | 4 |
| ridge | CAR_1_20 | 0.0634 | 0.753 | 1.869 | 0.08441 | 357 | 4 |
| xgboost | CAR_1_20 | 0.0971 | 0.697 | 1.737 | 0.07363 | 357 | 4 |
| historical_mean | CAR_1_5 | 0.0549 | 2.186 | 4.228 | 0.03411 | 357 | 4 |
| industry_mean | CAR_1_5 | 0.1834 | 2.100 | 4.524 | 0.03373 | 357 | 4 |
| ridge | CAR_1_5 | 0.0160 | 0.201 | 0.446 | 0.04017 | 357 | 4 |
| xgboost | CAR_1_5 | 0.0216 | 0.138 | 0.322 | 0.03479 | 357 | 4 |
| historical_mean | realized_volatility_1_20 | -0.0213 | -0.372 | -0.475 | 0.00824 | 357 | 4 |
| industry_mean | realized_volatility_1_20 | 0.3144 | 3.420 | 10.170 | 0.00817 | 357 | 4 |
| ridge | realized_volatility_1_20 | 0.3335 | 6.671 | 14.737 | 0.01026 | 357 | 4 |
| xgboost | realized_volatility_1_20 | 0.3899 | 7.243 | 21.323 | 0.00786 | 357 | 4 |

### Top Monthly Net Portfolio Results

| Family | Target | Variant | Mean Sharpe | Mean NW t | NW>1.96 splits | Mean Ann Ret | Worst Max DD |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| xgboost | realized_volatility_1_20 | monthly_sector_neutral_value_weight | 1.383 | 1.732 | 2/4 | 0.199 | -0.153 |
| xgboost | realized_volatility_1_20 | monthly_sector_neutral_equal_weight | 1.345 | 1.717 | 2/4 | 0.192 | -0.151 |
| industry_mean | realized_volatility_1_20 | monthly_sector_neutral_value_weight | 0.978 | 1.177 | 1/4 | 0.138 | -0.150 |
| industry_mean | realized_volatility_1_20 | monthly_sector_neutral_equal_weight | 0.936 | 1.138 | 1/4 | 0.129 | -0.146 |
| xgboost | realized_volatility_1_20 | monthly_equal_weight | 0.702 | 0.680 | 0/4 | 0.158 | -0.341 |
| ridge | realized_volatility_1_20 | monthly_equal_weight | 0.689 | 0.879 | 2/4 | 0.172 | -0.394 |
| industry_mean | realized_volatility_1_20 | monthly_equal_weight | 0.624 | 0.722 | 0/4 | 0.130 | -0.409 |
| industry_mean | realized_volatility_1_20 | monthly_value_weight | 0.623 | 0.758 | 0/4 | 0.145 | -0.400 |
| xgboost | realized_volatility_1_20 | monthly_value_weight | 0.601 | 0.589 | 0/4 | 0.128 | -0.330 |
| ridge | realized_volatility_1_20 | monthly_value_weight | 0.594 | 0.773 | 1/4 | 0.162 | -0.407 |

### Multiple Testing

- Primary discoveries at 10% FDR: 1
- Robustness discoveries at 10% FDR: 10
- Exploratory discoveries at 10% FDR: 34

## dictionary_only

### OOS Rank IC

| Family | Target | Rank IC | IC t | IC NW t | RMSE | N | Splits |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ridge | CAR_1_20 | 0.1104 | 1.212 | 2.996 | 0.07403 | 357 | 4 |
| xgboost | CAR_1_20 | -0.0038 | -0.042 | -0.113 | 0.07525 | 357 | 4 |
| ridge | CAR_1_5 | 0.0362 | 0.384 | 0.742 | 0.03452 | 357 | 4 |
| xgboost | CAR_1_5 | 0.0728 | 0.594 | 1.334 | 0.03454 | 357 | 4 |
| ridge | realized_volatility_1_20 | 0.2765 | 6.188 | 14.176 | 0.00850 | 357 | 4 |
| xgboost | realized_volatility_1_20 | 0.3466 | 8.456 | 23.159 | 0.00853 | 357 | 4 |

### Top Monthly Net Portfolio Results

| Family | Target | Variant | Mean Sharpe | Mean NW t | NW>1.96 splits | Mean Ann Ret | Worst Max DD |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| ridge | realized_volatility_1_20 | monthly_equal_weight | 0.395 | 0.444 | 1/4 | 0.102 | -0.246 |
| xgboost | realized_volatility_1_20 | monthly_equal_weight | 0.380 | 0.468 | 0/4 | 0.071 | -0.398 |
| ridge | CAR_1_5 | monthly_equal_weight | -0.194 | -0.171 | 0/4 | 0.013 | -0.292 |
| xgboost | CAR_1_5 | monthly_equal_weight | -0.393 | -0.498 | 0/4 | -0.004 | -0.244 |
| ridge | CAR_1_20 | monthly_equal_weight | -0.992 | -0.973 | 0/4 | -0.197 | -0.309 |
| xgboost | CAR_1_20 | monthly_equal_weight | -1.174 | -1.163 | 0/4 | -0.204 | -0.309 |

### Multiple Testing

- Primary discoveries at 10% FDR: 1
- Robustness discoveries at 10% FDR: 7
- Exploratory discoveries at 10% FDR: 16

## tfidf_svd_only

### OOS Rank IC

| Family | Target | Rank IC | IC t | IC NW t | RMSE | N | Splits |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ridge | CAR_1_20 | 0.1474 | 0.959 | 2.341 | 0.08351 | 357 | 4 |
| xgboost | CAR_1_20 | 0.1087 | 0.710 | 1.722 | 0.07362 | 357 | 4 |
| ridge | CAR_1_5 | 0.0413 | 0.339 | 0.757 | 0.03631 | 357 | 4 |
| xgboost | CAR_1_5 | 0.0513 | 0.349 | 0.819 | 0.03459 | 357 | 4 |
| ridge | realized_volatility_1_20 | 0.3709 | 6.473 | 10.764 | 0.00848 | 357 | 4 |
| xgboost | realized_volatility_1_20 | 0.4067 | 5.990 | 13.856 | 0.00766 | 357 | 4 |

### Top Monthly Net Portfolio Results

| Family | Target | Variant | Mean Sharpe | Mean NW t | NW>1.96 splits | Mean Ann Ret | Worst Max DD |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| xgboost | realized_volatility_1_20 | monthly_equal_weight | 1.129 | 1.104 | 0/4 | 0.264 | -0.345 |
| ridge | realized_volatility_1_20 | monthly_equal_weight | 0.861 | 0.925 | 1/4 | 0.216 | -0.316 |
| xgboost | CAR_1_5 | monthly_equal_weight | -0.568 | -0.680 | 0/4 | -0.107 | -0.334 |
| ridge | CAR_1_20 | monthly_equal_weight | -0.662 | -0.827 | 0/4 | -0.104 | -0.277 |
| xgboost | CAR_1_20 | monthly_equal_weight | -1.086 | -1.047 | 0/4 | -0.215 | -0.380 |
| ridge | CAR_1_5 | monthly_equal_weight | -1.144 | -1.265 | 0/4 | -0.170 | -0.270 |

### Multiple Testing

- Primary discoveries at 10% FDR: 1
- Robustness discoveries at 10% FDR: 13
- Exploratory discoveries at 10% FDR: 21
