# Financial 10-K Text Agent

An auditable research pipeline that turns SEC 10-K filings into text factors,
out-of-sample forecasts, portfolio diagnostics, and empirical-finance reports.

The project is **not** a financial RAG demo and does **not** claim a proven
trading alpha. Its strongest contribution is a leakage-aware, reproducible
agentic workflow for testing whether financial text contains forecasting
information.

## Latest Public Result

Current release: **v0.16.0 - 10-Company FMP/Alpha Applied Pilot**.

The latest committed result package is:

[docs/results/10_company_public_fmp_alpha_2016_2025_v1](docs/results/10_company_public_fmp_alpha_2016_2025_v1/README.md)

It is a fixed 10-company U.S. 10-K pilot using:

- SEC EDGAR annual filings and filing timestamps.
- FMP adjusted prices, with Yahoo fallback only for selected gaps.
- Loughran-McDonald dictionary tone features.
- Train-window-only TF-IDF/SVD text representations.
- Rolling out-of-sample splits, audit gates, and multiple-testing disclosure.

Headline run status:

| Item | Value |
| --- | ---: |
| 10-K filings | 100 |
| Labels | 300 |
| OOS predictions | 896 |
| Eligible OOS coverage | 100% |
| Audit failures | 0 |
| Audit warnings | 2 |
| Tested specifications | 472 |
| Primary portfolio result | Diagnostic only |

Best observed prediction metric in the public artifact:

| Target | Best model | ALL_SPLITS Rank IC | NW t-stat |
| --- | --- | ---: | ---: |
| `CAR_1_5` | XGBoost | 0.3212 | 4.1481 |
| `realized_volatility_1_20` | industry mean | 0.2545 | 4.1049 |

Preregistered primary rules are deliberately stricter:

- Primary prediction: Ridge on `realized_volatility_1_20`, ALL_SPLITS Rank IC
  `-0.2788`, raw p-value `0.0815`.
- Primary portfolio: monthly sector-neutral equal-weight volatility portfolio,
  Sharpe `-0.3028`, raw p-value `0.6263`.

Interpretation: the public pilot validates the pipeline and shows exploratory
forecasting evidence, but it does **not** establish formal tradable alpha.

## Pipeline

```text
SEC 10-K filings
  -> document manifest and event-time alignment
  -> 10-K section parsing
  -> labels: realized volatility and CAR windows
  -> rolling train / validation / test splits
  -> dictionary tone, TF-IDF/SVD, metadata features
  -> historical mean, industry mean, Ridge, XGBoost
  -> OOS IC metrics and portfolio diagnostics
  -> audit report, multiple-testing report, empirical report
```

## What Is Included

- Config-driven local orchestrator.
- Pydantic-style artifact schemas and audit gates.
- SEC 10-K parser for Business, Risk Factors, Legal Proceedings, and MD&A.
- Event-date handling with trading-calendar aware metadata.
- Leakage controls for available time, label windows, splits, and TF-IDF fitting.
- Model comparison across baselines, Ridge, and optional XGBoost.
- Event-based and monthly portfolio diagnostics.
- Multiple-testing registry with primary, robustness, and exploratory specs.
- Compact public result artifacts under `docs/results/`.

## What Is Not Claimed

- No CRSP/WRDS survivorship-free universe in the public pilot.
- No formal delisting-return research claim.
- No production trading system.
- No investment advice.
- Portfolio outputs are diagnostics, not deployable strategy evidence.

## Quick Start

```bash
python -m pip install -e ".[dev]"
python -m text_factor_lab run --config configs/text_factor_lab/e2e_smoke.yaml --execute
python -m pytest -q
```

Useful entry points:

```bash
python -m text_factor_lab run --help
python -m text_factor_lab audit --help
python -m text_factor_lab report --help
```

## Documentation

- [Global workflow rules](FINANCIAL_TEXT_FACTOR_LAB_GLOBAL_WORKFLOW.md)
- [Architecture and roadmap](docs/system_architecture_and_roadmap.md)
- [10-company data stack](docs/data_sources_10_company_fmp_alpha.md)
- [Working paper positioning](docs/working_paper_positioning.md)
- [Public result artifacts](docs/results/README.md)

## License

Code is released under the [MIT License](LICENSE).

Public result summaries are provided for research demonstration only. Raw SEC
filings, licensed market data, API keys, and private intermediate datasets are
not committed.
