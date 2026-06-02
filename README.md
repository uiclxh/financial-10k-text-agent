# From SEC 10-K Filings to Volatility Signals

**An auditable, leakage-safe agentic pipeline for out-of-sample financial text
factor research.**

> Research question: **Can 10-K textual information forecast future realized
> volatility?**

This repository turns SEC 10-K filings into audited text factors and evaluates
them under rolling out-of-sample splits. Its strongest current result is
volatility forecasting evidence, not formal trading alpha. The framework is
designed for empirical finance experiments, not financial RAG.

## Headline Result

In the public 90-company experiment, `realized_volatility_1_20` is the clearest
out-of-sample target.

| Target | Best model | ALL_SPLITS Rank IC | Rank IC NW t-stat |
| --- | --- | ---: | ---: |
| `CAR_1_20` | industry mean | 0.1698 | 3.539 |
| `CAR_1_5` | industry mean | 0.1834 | 4.524 |
| `realized_volatility_1_20` | **XGBoost** | **0.3899** | **21.32** |

The preregistered primary prediction specification also passes:
`realized_volatility_1_20 / Ridge`, Rank IC `0.3335`, p about `6.85e-11`.

The preregistered primary portfolio specification does **not** pass after
transaction costs, sector neutrality, ALL_SPLITS aggregation, and
multiple-testing control: Sharpe `-0.3602`, p `0.4598`.

**Interpretation:** the current evidence supports leakage-controlled
out-of-sample volatility forecasting. It does not support a formal claim of
tradable alpha.

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

## Evidence Snapshot

Selected summaries are in [docs/results](docs/results/README.md).

- Sample: 90 companies, 883 10-K filings, 2,649 labels, 8,236 predictions.
- Feature ablation: TF-IDF/SVD is the strongest current text feature block for
  volatility prediction.
- Model comparison: XGBoost has the highest volatility Rank IC; Ridge provides
  the preregistered primary result.
- Return prediction remains weaker: CAR targets are often led by
  `industry_mean`, so they are not clean textual-alpha evidence.
- Portfolio evidence remains exploratory after costs and statistical controls.

## Why This Repository Is Different

- Leakage-safe event-time alignment with auditable `available_time_utc`.
- Train-window-only TF-IDF fitting and rolling-year out-of-sample splits.
- Dictionary tone, TF-IDF/SVD, Ridge, XGBoost, and baseline comparison.
- Cost-aware, sector-neutral, value-weighted portfolio diagnostics.
- Preregistered primary specifications and multiple-testing adjustment.
- Explicit public-data, licensed-data, and delisting-return boundaries.

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

## Formal CRSP/WRDS Replication Profile

The formal profile is scaffolded in
`configs/text_factor_lab/real_10k_large_universe_crsp_wrds.yaml`. It expects
private local CRSP/WRDS exports under `data_private/`, a licensed data manifest
at `data_manifests/crsp_wrds_data_manifest.template.json`, CRSP delisting
returns, survivorship-free membership intervals, and historical entity links.

```bash
python -m text_factor_lab run --config configs/text_factor_lab/real_10k_large_universe_crsp_wrds.yaml --execute
```

The command is designed to block with a clear missing-input report when private
licensed data is absent. Public GitHub outputs should use only compact templates
and summaries in `docs/results/`, never raw licensed data.

## Faster Licensed Alternative: Nasdaq Data Link / Sharadar

If WRDS approval is pending, use the Nasdaq Data Link / Sharadar profile:

```bash
$env:NASDAQ_DATA_LINK_API_KEY="your-api-key"
python scripts\extract_nasdaq_sharadar_company_panel.py --tickers MSFT NFLX NKE MCD META SBUX SONY V XOM LLY
python -m text_factor_lab run --config configs/text_factor_lab/real_10k_company_panel_nasdaq_sharadar.yaml --execute
```

This route is quicker to provision than WRDS and can include active and delisted
tickers, but it does not provide CRSP `DLRET`. Treat it as a licensed
applied-grade run unless a broader survivorship-free universe and delisting
return policy are documented.

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
