# Financial 10-K Text Agent

一个面向 **SEC 10-K 文本因子研究** 的可审计 MVP pipeline。它不是普通
Financial RAG，而是把 10-K 文本转成可回测、可审计、可复现的金融文本因子，
用于比较 TF-IDF、dictionary tone、Ridge、XGBoost 等模型对未来收益、波动率
等标签的预测能力。

[English README](README.en.md) | [中文 README](README.zh-CN.md) |
[Global Workflow](FINANCIAL_TEXT_FACTOR_LAB_GLOBAL_WORKFLOW.md) |
[Deployment Guide](docs/deployment.md)

## 一眼看懂

```text
SEC 10-K / local filings
        |
        v
document manifest -> 10-K section parser -> parsed_sections.jsonl
        |                                      |
        v                                      v
price panel -> labels.jsonl             text features
        |                                      |
        v                                      v
rolling split -> models -> predictions -> evaluation/backtest
        |                                      |
        v                                      v
      audit -----------------------------> report.md
```

核心输出不是聊天答案，而是一组研究 artifact：

- `features.jsonl` / `feature_manifest.json`
- `labels.jsonl`
- `predictions.jsonl`
- `evaluation_metrics.json`
- `backtest_results.json`
- `audit_report.json`
- `report.md`

## 当前状态

当前版本：`v0.6.0`

已完成一个可复现的本地 MVP prototype：

- 配置驱动实验：`configs/text_factor_lab/*.yaml`
- SEC 10-K section parser：Item 1 / 1A / 3 / 7
- 标签构建：CAR、realized volatility
- 滚动年份切分与 leakage checks
- 文本特征：dictionary tone、train-window TF-IDF
- 模型：historical mean、industry mean、Ridge、optional XGBoost
- 样本外评估：RMSE、MAE、R2、directional accuracy、Pearson IC、rank IC
- event-based long-short backtest
- audit gate：防泄漏、coverage、schema、formal/exploratory gate
- report agent：自动生成 `report.md` 与 `report_summary.json`
- 一键本地 smoke run、GitHub Actions CI、Dockerfile、Makefile

本地验收：

```text
92 tests passed
ruff passed
```

## 最快运行

```bash
python -m pip install -e ".[dev]"
python -m text_factor_lab run --config configs/text_factor_lab/e2e_smoke.yaml --execute
```

也可以用 Make：

```bash
make install
make smoke-run
```

运行后查看：

```text
runs/text_factor_lab/tflab_e2e_smoke_001/report.md
runs/text_factor_lab/tflab_e2e_smoke_001/audit_report.json
runs/text_factor_lab/tflab_e2e_smoke_001/orchestrator_report.json
```

## 主要命令

```bash
python -m text_factor_lab run --config configs/text_factor_lab/mvp_v0.yaml
python -m text_factor_lab run --config configs/text_factor_lab/mvp_v0.yaml --execute
python -m text_factor_lab parse-10k --help
python -m text_factor_lab build-labels --help
python -m text_factor_lab build-splits --help
python -m text_factor_lab build-features --help
python -m text_factor_lab build-models --help
python -m text_factor_lab evaluate-models --help
python -m text_factor_lab audit --help
python -m text_factor_lab report --help
```

## 仓库地图

```text
src/text_factor_lab/
  calendar/        market-calendar event-date resolver
  data/            SEC metadata, prices, universe
  parsing/         SEC 10-K section parser
  labels/          event labels and target construction
  splits/          rolling split and leakage checks
  features/        dictionary tone and TF-IDF
  models/          baselines, Ridge, optional XGBoost
  backtest/        metrics and event-based factor backtest
  audit/           formal/exploratory audit gate
  reports/         report.md and report_summary.json
  orchestration/   run manager and one-command local pipeline

configs/text_factor_lab/
  mvp_v0.yaml      research MVP config template
  e2e_smoke.yaml   tiny end-to-end smoke run

examples/e2e_smoke/
  demo manifest and tiny price panel for CI/local validation

docs/releases/
  v0.1.0 ... v0.8.0 release notes
```

## Release 路线

| Release | 阶段 | 核心内容 |
|---|---|---|
| [v0.1.0](docs/releases/v0.1.0.md) | Foundation | package scaffold, config, schemas, run status |
| [v0.2.0](docs/releases/v0.2.0.md) | Data pipeline | universe, SEC metadata, parser, labels, splits, features |
| [v0.3.0](docs/releases/v0.3.0.md) | Research core | models, evaluation, backtest, audit |
| [v0.4.0](docs/releases/v0.4.0.md) | Report Agent | Markdown report, JSON summary, audit-gated conclusion |
| [v0.5.0](docs/releases/v0.5.0.md) | Orchestrator | artifact-aware `run --execute` controller |
| [v0.6.0](docs/releases/v0.6.0.md) | Deployment MVP | CI, Dockerfile, Makefile, e2e smoke run |
| [v0.8.0](docs/releases/v0.8.0.md) | Event Calendar | NYSE trading calendar, early close, event-date audit fields |

## 重要边界

这个仓库已经是 **可复现、可审计、可展示的 MVP research pipeline prototype**。
它还不是 production-grade 或 formal research-grade empirical result。

正式研究仍需补齐：

- research-grade dated universe
- historical ticker-CIK mapping
- delisted firms and sector source
- licensed/robust price and benchmark data
- portfolio time-series backtest
- sector-neutral / value-weight variants
- multiple-testing adjustment and robustness reports
- FinBERT / LLM embedding / earnings call / credit-risk extensions
