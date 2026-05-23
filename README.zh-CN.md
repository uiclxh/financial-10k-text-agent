# Financial 10-K Text Agent

[English](README.en.md) | 中文

## 项目定位

`Financial 10-K Text Agent` 是一个面向金融文本因子研究的 MVP 工程实现。
它不是通用 Financial RAG，而是围绕 SEC 10-K 文本构建可复现、可审计的
empirical finance pipeline：文本解析、事件标签、滚动切分、特征构建、
模型训练、样本外评估、组合回测、审计门槛和自动报告。

## 当前状态

当前代码已经完成以下研究级升级路径：

1. 项目脚手架
2. Config 与 Pydantic schema
3. Run manager 与状态机
4. 固定 universe manifest 校验
5. SEC EDGAR 10-K 元数据工具
6. SEC 10-K section parser
7. 价格数据与 label builder
8. Rolling-year split 与 leakage checks
9. Dictionary tone 与 train-window TF-IDF feature layer
10. 模型层：`historical_mean`、`industry_mean`、`ridge`、可选 `xgboost`
11. 样本外评估：RMSE、MAE、R2、directional accuracy、Pearson IC、rank IC
12. Event-based long-short backtest 与 audit gate
13. Report Agent：`report.md`、`report_summary.json` 与结论等级
14. 本地 MVP 部署：配置化输入路径、本地 raw 10-K 解析编排、复现文档、GitHub Actions CI
15. 研究级事件日对齐：NYSE 交易日历、节假日、提前收盘和 manifest 审计字段
16. 组合变体：equal-weight、value-weight、sector-neutral equal-weight、sector-neutral value-weight
17. 多重检验：tested-specification registry、Holm adjustment、Benjamini-Hochberg FDR
18. 实证报告：`empirical_report.md`、`factor_card.md`、`appendix_tables.md`
19. 研究级 universe schema：security master、dated membership intervals、entity link history
20. 当价格面板可用时，生成日频价格驱动的 portfolio return series
21. 日频持仓漂移会计：记录日初和日末 exposure，避免固定权重收益口径

## 关键命令

```bash
python -m text_factor_lab run --config configs/text_factor_lab/mvp_v0.yaml
python -m text_factor_lab run --config configs/text_factor_lab/mvp_v0.yaml --execute
python -m text_factor_lab run --config configs/text_factor_lab/e2e_smoke.yaml --execute
make smoke-run
python -m pytest
python -m ruff check .
python -m text_factor_lab build-features --help
python -m text_factor_lab build-models --help
python -m text_factor_lab evaluate-models --help
python -m text_factor_lab audit --help
python -m text_factor_lab report --help
```

## 主要产物

MVP pipeline 围绕以下 artifact 工作：

- `document_manifest.jsonl`
- `parsed_sections.jsonl`
- `labels.jsonl`
- `split_assignments.jsonl`
- `split_leakage.jsonl`
- `features.jsonl`
- `feature_manifest.json`
- `predictions.jsonl`
- `model_manifest.json`
- `tuning_log.json`
- `evaluation_metrics.json`
- `backtest_results.json`
- `portfolio_weights.jsonl`
- `portfolio_returns.jsonl`
- `portfolio_metrics.json`
- `tested_specifications.jsonl`
- `multiple_testing_report.json`
- `audit_report.json`
- `report.md`
- `report_summary.json`
- `empirical_report.md`
- `factor_card.md`
- `appendix_tables.md`
- `orchestrator_report.json`

## 部署与复现

部署说明见 [docs/deployment.md](docs/deployment.md)。该文档说明本地环境、
配置化输入路径、artifact 保留策略，以及 GitHub CI 的职责边界。

## 验证方式

```bash
python -m pytest
python -m ruff check .
```

当前本地验收结果：

```text
99 tests pass
ruff passes
```

## 当前边界

这仍然是 MVP / research framework，不是完整 production research system。
后续仍需补充 SEC 下载调度、真实 survivorship-free universe、CRSP/WRDS 或等价数据、
delisting returns、overlapping sub-portfolios、borrow costs、capacity / slippage diagnostics、
Deflated Sharpe、CPCV/PBO、云端 dashboard、FinBERT / LLM embedding、earnings-call
transcript ingestion，以及 credit-risk targets。
