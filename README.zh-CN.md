# Financial 10-K Text Agent

[English](README.en.md) | 中文

## 项目定位

`Financial 10-K Text Agent` 是一个面向金融文本因子研究的 MVP 工程实现。
它不是通用 Financial RAG，而是围绕 SEC 10-K 文本构建可复现、可审计的
empirical finance pipeline：文本解析、事件标签、滚动切分、特征构建、模型
训练、样本外评估、事件型 long-short 回测、审计门槛和自动报告。

## 当前状态

当前代码已经完成 Step 1-14：

1. 项目脚手架
2. Config 与 Pydantic schema
3. Run manager 与状态机
4. 固定 universe manifest 校验
5. SEC EDGAR 10-K 元数据工具
6. SEC 10-K section parser
7. 价格数据与 label builder
8. rolling-year split 与 leakage checks
9. dictionary tone 与 train-window TF-IDF feature layer
10. 模型层：`historical_mean`、`industry_mean`、`ridge`、可选 `xgboost`
11. 样本外评估：RMSE、MAE、R2、directional accuracy、Pearson IC、rank IC
12. event-based long-short backtest 与 audit gate
13. Report Agent：生成 `report.md`、`report_summary.json` 与结论等级
14. 本地 MVP 部署：配置化输入路径、本地 raw 10-K 解析编排、复现文档、GitHub Actions CI

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
- `audit_report.json`
- `report.md`
- `report_summary.json`
- `orchestrator_report.json`
- `.github/workflows/tests.yml`
- `configs/text_factor_lab/e2e_smoke.yaml`
- `examples/e2e_smoke/*`
- `Dockerfile`
- `Makefile`

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
84 tests pass
ruff passes
```

## 当前边界

这仍然是 MVP，不是完整 production research system。后续还需要补 SEC 下载调度、
sector-neutral portfolio、完整组合时间序列、多重检验报告、云端 dashboard、
FinBERT / LLM embedding、earnings call transcript ingestion，以及 credit risk target。
