# Financial 10-K Text Agent

An auditable financial NLP research pipeline for testing whether SEC 10-K text
features contain out-of-sample predictive information about future volatility
and abnormal-return targets.

This project is not a RAG demo, a generic FinBERT sentiment classifier, or an
AI trading bot. It is positioned at the intersection of financial NLP,
empirical asset pricing, rolling out-of-sample validation, and research audit.

## Current Release

Latest public result package:

[`docs/results/50_company_public_fmp_alpha_2016_2025_v1`](docs/results/50_company_public_fmp_alpha_2016_2025_v1/README.md)

| Field | Value |
| --- | --- |
| Run ID | `50_company_public_fmp_alpha_2016_2025_v1` |
| Universe | 50 U.S. large-cap firms |
| Sample | FY2016-FY2025 |
| SEC 10-K filings | 500 |
| Labels | 1,500 |
| OOS predictions | 4,716 |
| Feature records | 520k+ |
| Tested specifications | 568 |
| Eligible OOS coverage | 100% |
| Audit failures | 0 |
| Audit warnings | 2 |
| Result status | exploratory applied-grade run |

## Reproduce Locally

The repository includes a public smoke-test pipeline that can be run without
private API keys or licensed datasets.

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

To rerun the 50-company applied-data experiment, provide market-data API keys
and the required private data cache, then run:

```powershell
$env:FMP_API_KEY="..."
$env:ALPHAVANTAGE_API_KEY="..."
$env:SEC_USER_AGENT="financial-10k-text-agent contact:your_email@example.com"
python -m text_factor_lab run --config configs/text_factor_lab/50_company_public_fmp_alpha.yaml --execute
```

The committed 50-company public result package is a compact artifact summary;
raw SEC filings, API responses, full price panels, and private intermediate
datasets are intentionally not committed.

## Main Finding

The preregistered primary prediction specification uses Ridge on
`realized_volatility_1_20` and evaluates ALL_SPLITS Rank IC.

| Model | Target | Metric | Value | Raw p-value |
| --- | --- | ---: | ---: | ---: |
| Ridge | `realized_volatility_1_20` | Rank IC | 0.2606 | 0.00017 |

This provides exploratory out-of-sample evidence that 10-K text features contain
ranking information about future 20-day realized volatility. The claim is
deliberately framed as prediction evidence, not as a tradable-alpha claim.

## Best Observed Exploratory Prediction

The strongest observed model-comparison result is:

| Model | Target | Rank IC | Newey-West t-stat | RMSE |
| --- | --- | ---: | ---: | ---: |
| XGBoost | `realized_volatility_1_20` | 0.3133 | 6.8479 | 0.00834 |

This is reported as exploratory model-comparison evidence rather than the
preregistered primary claim.

## Pipeline

```text
SEC 10-K filings
-> section parsing
-> event-time label construction
-> rolling train / validation / test splits
-> dictionary tone + train-window-only TF-IDF/SVD features
-> historical mean / industry mean / Ridge / XGBoost
-> OOS Rank IC, Newey-West diagnostics, portfolio diagnostics
-> audit and multiple-testing reports
```

Core artifacts include document manifests, parsed section indexes, labels,
split assignments, feature manifests, model manifests, predictions, evaluation
metrics, portfolio diagnostics, multiple-testing reports, audit reports, and
empirical result summaries.

## Usage Boundary

This release is an applied-grade exploratory research run. It does not claim:

- Formal CRSP/WRDS-equivalent asset-pricing evidence
- A survivorship-free research-grade universe
- A production trading system
- Proven tradable alpha
- Investment advice

Portfolio outputs are diagnostic only. The preregistered primary portfolio
specification did not establish formal tradable alpha.

The main formal-result blockers are data-boundary issues, not pipeline failures:

- Market data uses a mixed FMP/Yahoo public-source stack
- Market-cap-at-selection values are applied-grade estimates
- The universe is a fixed active-company panel, not CRSP/WRDS survivorship-free
- Audit warnings are boundary disclosures, not failed pipeline checks

## License

Code is released under the [MIT License](LICENSE).

Public result summaries are provided for research demonstration only. Raw SEC
filings, licensed market data, API keys, and private intermediate datasets are
not committed.
