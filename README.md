# Financial 10-K Text Agent

Auditable research framework for turning SEC 10-K filings into financial text
factors. It is designed for empirical finance experiments, not financial RAG:
the pipeline builds text features, labels, models, portfolio tests, audit
reports, and preregistered multiple-testing artifacts.

## Current Release

`v0.15.0` adds target-aware portfolio construction, ALL_SPLITS monthly portfolio
aggregation, preregistered primary specification rules, and compact results from
a public 90-company SEC 10-K experiment.

## What It Does

```text
SEC 10-K filings
  -> manifest / parser
  -> labels and rolling splits
  -> dictionary tone, TF-IDF/SVD, metadata features
  -> historical_mean, industry_mean, Ridge, XGBoost
  -> OOS IC metrics and portfolio returns
  -> multiple-testing report, audit report, empirical report
```

## 90-Company Result Snapshot

Selected summaries are in [docs/results](docs/results/README.md).

- Sample: 90 companies, 883 10-K filings, 2,649 labels, 8,236 predictions.
- Best prediction target: `realized_volatility_1_20`.
- Best ALL_SPLITS volatility model: XGBoost, Rank IC `0.3899`.
- Preregistered primary prediction rule passes:
  `realized_volatility_1_20 / ridge`, Rank IC `0.3335`, p about `6.85e-11`.
- Preregistered primary portfolio rule does not pass:
  Sharpe `-0.3602`, p `0.4598`.
- Interpretation: 10-K text is useful for volatility forecasting; the tested
  portfolio evidence is not yet formal trading-alpha evidence after costs,
  sector neutrality, ALL_SPLITS aggregation, and multiple-testing control.

## Install And Smoke Run

```bash
python -m pip install -e ".[dev]"
python -m text_factor_lab run --config configs/text_factor_lab/e2e_smoke.yaml --execute
```

Optional Make targets:

```bash
make install
make test
make smoke-run
```

## Useful Commands

```bash
python -m text_factor_lab build-features --help
python -m text_factor_lab build-models --help
python -m text_factor_lab evaluate-models --help
python -m text_factor_lab audit --help
python -m text_factor_lab report --help
```

## Main Artifacts

- `evaluation_metrics.json`
- `portfolio_weights.jsonl`
- `portfolio_returns.jsonl`
- `portfolio_metrics.json`
- `monthly_portfolio_metrics.json`
- `tested_specifications.jsonl`
- `multiple_testing_report.json`
- `specification_registry.json`
- `audit_report.json`
- `empirical_report.md`
- `factor_card.md`

Large raw/generated artifacts are intentionally ignored by git. Compact result
summaries live in `docs/results/`.

## Release Notes

- [v0.15.0](docs/releases/v0.15.0.md): preregistered portfolio inference and
  90-company results
- [v0.14.0](docs/releases/v0.14.0.md): drifted daily portfolio accounting
- [Earlier releases](docs/releases): pipeline foundation through research
  universe, calendar, portfolio, inference, and reporting layers

## Boundaries

The public 90-company run is exploratory/applied-grade because it uses public
data and has incomplete formal coverage. Formal replication still requires a
survivorship-free licensed universe, delisting returns, and stricter market data
controls.

## License And Notices

MIT License. This repository is for research and education only. It is not
investment, trading, legal, accounting, or tax advice. Users are responsible for
all data licenses and redistribution limits.
