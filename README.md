# Financial 10-K Text Agent

An auditable financial NLP research pipeline for testing whether SEC 10-K text features contain out-of-sample predictive information about future realized volatility and abnormal-return targets.

This project is not a RAG demo, a generic FinBERT sentiment classifier, or an AI trading bot. It is positioned at the intersection of financial NLP, empirical asset-pricing workflow design, rolling out-of-sample validation, model-comparison diagnostics, and research audit.

The current empirical claim is deliberately narrow:

> SEC 10-K text features provide exploratory out-of-sample ranking evidence for future 20-day realized volatility. Return prediction is weaker, and the preregistered portfolio test does not establish tradable alpha.

---

## Current Release

Latest public result package:

[`docs/results/50_company_public_fmp_alpha_2016_2025_v4`](docs/results/50_company_public_fmp_alpha_2016_2025_v4/README.md)

| Field | Value |
| --- | --- |
| Run ID | `50_company_public_fmp_alpha_2016_2025_v4` |
| Universe | 50 U.S. large-cap firms |
| Sample | FY2016-FY2025 |
| SEC 10-K filings | 500 |
| Labels | 1,500 |
| OOS predictions | 8,133 |
| Feature records | 520k+ |
| Tested specifications | 594 |
| Multiple-testing families | 26 |
| Eligible OOS coverage | 100% |
| Model-expected prediction coverage | 98.546% |
| Primary prediction coverage | 100% |
| Primary portfolio coverage | 100% |
| Audit failures | 0 |
| Audit warnings | 2 |
| Result status | exploratory applied-grade run |

Model-expected prediction coverage is below 100% because expanded diagnostic specifications include a small number of missing model-label pairs caused by unavailable numeric feature vectors in malformed parsed sections. The preregistered primary prediction and primary portfolio specifications remain fully covered.

---

## Reproduce Locally

The repository includes a public smoke-test pipeline that can be run without private API keys or licensed datasets.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[dev,ml]"
python -m pytest -q
python -m ruff check .
python -m text_factor_lab run --config configs/text_factor_lab/e2e_smoke.yaml --execute
```

The smoke run writes artifacts to:

```text
runs/text_factor_lab/tflab_e2e_smoke_001/
```

To rerun the 50-company applied-data experiment, provide market-data API keys and the required private data cache, then run:

```powershell
$env:FMP_API_KEY="..."
$env:ALPHAVANTAGE_API_KEY="..."
$env:SEC_USER_AGENT="financial-10k-text-agent contact:your_email@example.com"
python -m text_factor_lab run --config configs/text_factor_lab/50_company_public_fmp_alpha_v4.yaml --execute
```

The committed public result package is a compact artifact summary. Raw SEC filings, API responses, full price panels, API keys, and private intermediate datasets are intentionally not committed.

---

## Main Finding

The preregistered primary prediction specification uses Ridge on `realized_volatility_1_20` and evaluates ALL_SPLITS Rank IC.

| Model | Target | Metric | Value | Raw p-value |
| --- | --- | ---: | ---: | ---: |
| Ridge | `realized_volatility_1_20` | Rank IC | 0.2395 | 0.00067 |

This provides exploratory out-of-sample evidence that 10-K text features contain ranking information about future 20-day realized volatility.

The claim is deliberately framed as prediction evidence, not as a tradable-alpha claim.

---

## Primary Portfolio Result

The preregistered primary portfolio specification uses monthly common rebalance, sector-neutral equal-weight long-short construction, and a Newey-West p-value from the ALL_SPLITS OOS return series.

| Model | Target | Portfolio | Sharpe | Raw p-value |
| --- | --- | --- | ---: | ---: |
| Ridge | `realized_volatility_1_20` | Monthly sector-neutral equal-weight | -0.8539 | 0.1147 |

The preregistered portfolio test does not establish formal tradable alpha. Portfolio outputs are reported as diagnostics only.

---

## Best Observed Exploratory Ranking Result

| Model | Feature set | Target | Rank IC | Newey-West t-stat | RMSE |
| --- | --- | --- | ---: | ---: | ---: |
| Ridge | TF-IDF/SVD only | `realized_volatility_1_20` | 0.3668 | 5.4055 | 0.00992 |

This is reported as exploratory model-comparison evidence rather than the preregistered primary claim.

The model is evaluated primarily as a cross-sectional ranking signal, not as a minimum-RMSE volatility point forecast.

---

## Incremental Text Diagnostics

Industry-neutral Rank IC separately demeans realized targets and model predictions within each OOS split-industry group before applying tie-aware rank correlation. It is a descriptive incremental-signal diagnostic, not a causal decomposition.

| Model | Raw Rank IC | Industry-neutral Rank IC | Neutral NW t-stat |
| --- | ---: | ---: | ---: |
| Ridge TF-IDF/SVD only | 0.3668 | 0.3416 | 3.8557 |
| Ridge industry + text | 0.3296 | 0.3251 | 4.3994 |
| Ridge dictionary only | 0.2244 | 0.2465 | 5.2660 |
| Ridge combined text | 0.2395 | 0.2023 | 1.3704 |
| XGBoost combined text | 0.2741 | 0.1991 | 2.5256 |
| Industry mean | 0.2924 | 0.0000 | 0.0000 |

The industry-mean baseline remains strong, but text-based models retain positive industry-neutral ranking diagnostics for future realized volatility. This supports an exploratory text-based volatility-ranking interpretation while avoiding a causal claim that text alone explains the signal.

---

## Feature Ablation Summary

Ridge variants use identical rolling splits, validation-only alpha selection, and tuning budgets. `industry_only` is the training-window industry-mean economic baseline rather than a Ridge fit.

For `realized_volatility_1_20`:

| Feature set | Estimator | Rank IC | Industry-neutral Rank IC | Rank IC NW t-stat | Neutral NW t-stat | RMSE |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| TF-IDF/SVD only | Ridge | 0.3668 | 0.3416 | 5.4055 | 3.8557 | 0.00992 |
| Industry + text | Ridge | 0.3296 | 0.3251 | 5.1073 | 4.3994 | 0.01076 |
| Industry only | Industry mean | 0.2924 | 0.0000 | 4.7084 | 0.0000 | 0.00913 |
| Dictionary only | Ridge | 0.2244 | 0.2465 | 2.9370 | 5.2660 | 0.00984 |
| Combined text | Ridge | 0.2395 | 0.2023 | 2.3457 | 1.3704 | 0.01932 |

The strongest observed volatility-ranking evidence comes from TF-IDF/SVD text representations rather than the pure industry baseline. Return-target evidence is materially weaker and should not be interpreted as robust stock-return alpha.

---

## Bootstrap Confidence Intervals

The primary Rank IC is evaluated with deterministic bootstrap resampling using 2,000 iterations and seed 42.

| Estimand | Bootstrap method | Point estimate | 95% CI | Two-sided zero p-value |
| --- | --- | ---: | --- | ---: |
| Raw Rank IC | Split bootstrap | 0.2395 | [-0.0050, 0.4841] | 0.111 |
| Raw Rank IC | Event-date bootstrap | 0.2395 | [0.0719, 0.3743] | 0.005 |
| Raw Rank IC | Ticker-cluster bootstrap | 0.2395 | [0.1091, 0.3522] | 0.001 |
| Industry-neutral Rank IC | Split bootstrap | 0.2023 | [-0.1157, 0.5202] | 0.117 |
| Industry-neutral Rank IC | Event-date bootstrap | 0.2023 | [-0.1546, 0.4273] | 0.366 |
| Industry-neutral Rank IC | Ticker-cluster bootstrap | 0.2023 | [-0.1787, 0.4181] | 0.357 |

The raw primary volatility Rank IC remains positive under event-date and ticker-cluster bootstrap checks. Split bootstrap is inconclusive because the run has only four OOS split clusters. The primary industry-neutral Rank IC is positive in point estimate but not bootstrap-robust.

---

## Data Quality And Parser Review

The parser quality review covers 2,000 parsed section records from 500 SEC 10-K filings.

| Item | Count |
| --- | ---: |
| Parsed section records | 2,000 |
| Manual-review records | 144 |
| Excluded section-level records | 144 |
| Short but included records | 494 |

Review policy:

- `item_1a` and `item_7` below 100 words require manual review and are excluded from their section-level feature scopes.
- Core sections from 100 to 499 words remain included but carry a warning.
- Short non-core sections remain included and are disclosed.
- Exclusion does not remove the filing from the experiment. Combined/full scope is reconstructed from the filing's remaining accepted sections.

This reduces malformed-section risk while preserving the document-level experiment. The dataset remains an applied-grade parser pipeline rather than a fully hand-verified research-grade text corpus.

---

## Pipeline

```text
SEC 10-K filings
-> section parsing and parser-quality review
-> event-time label construction
-> rolling train / validation / test splits
-> embargo-based leakage control
-> dictionary tone + train-window-only TF-IDF/SVD features
-> historical mean / industry mean / Ridge / XGBoost
-> feature ablation and industry-neutral diagnostics
-> OOS Rank IC, Newey-West diagnostics, bootstrap intervals
-> monthly and event-based portfolio diagnostics
-> multiple-testing report, specification registry, audit report
-> empirical report and factor card
```

Core artifacts include document manifests, parsed-section indexes, parser review, labels, split assignments, leakage logs, feature and vocabulary manifests, model and tuning manifests, predictions, evaluation metrics, portfolio diagnostics, multiple-testing reports, bootstrap reports, audit reports, empirical summaries, and factor cards.

---

## Research Design Controls

| Control | Implementation |
| --- | --- |
| Rolling validation/test workflow | Rolling train / validation / test splits |
| Leakage control | Embargo-based purge and split-leakage audit |
| Model selection | Validation-only Rank IC selection |
| TF-IDF leakage control | Train-window-only vocabulary fitting |
| Tie handling | Tie-aware average-rank Rank IC |
| Constant-prediction control | Constant predictions return zero Rank IC |
| Incremental-signal diagnostic | Industry-neutral Rank IC |
| Feature contribution check | Dictionary-only, TF-IDF/SVD-only, combined-text, industry-only, and industry-plus-text comparisons |
| Statistical uncertainty | Newey-West diagnostics and bootstrap confidence intervals |
| Data-snooping disclosure | Preregistered primary specifications and multiple-testing reports |
| Parser quality | Manual-review appendix for short or malformed sections |

---

## Usage Boundary

This release is an applied-grade exploratory research run. It does not claim:

- Formal CRSP/WRDS-equivalent asset-pricing evidence
- A survivorship-free research-grade universe
- A production trading system
- Proven tradable alpha
- Investment advice

Portfolio outputs are diagnostic only. The preregistered primary portfolio specification did not establish formal tradable alpha.

The main formal-result blockers are data-boundary issues, not pipeline failures:

- Market data uses a mixed FMP/Yahoo public-source stack
- Market-cap-at-selection values are applied-grade estimates
- The universe is a fixed active-company panel, not CRSP/WRDS survivorship-free
- Some expanded diagnostic specifications have partial missing model-label pairs due to parser/feature-vector limitations
- Audit warnings are boundary disclosures, not failed pipeline checks

---

## Recommended Interpretation

> In a fixed 50-company applied-grade panel, SEC 10-K text features provide exploratory out-of-sample evidence for ranking future 20-day realized volatility. TF-IDF/SVD text representations show the strongest observed volatility-ranking performance and retain positive industry-neutral diagnostics. Return prediction is weaker, and the preregistered portfolio test does not establish tradable alpha.

---

## License

Code is released under the [MIT License](LICENSE).

Public result summaries are provided for research demonstration only. Raw SEC filings, licensed market data, API keys, and private intermediate datasets are not committed.
