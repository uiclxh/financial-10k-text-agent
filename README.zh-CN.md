# Financial 10-K Text Agent

[English](README.en.md) | 中文

## 项目定位

`Financial 10-K Text Agent` 是一个金融文本因子研究 agent 的 MVP 工程实现。它不是普通的 Financial RAG，而是面向 empirical finance 的可复现研究流水线：

```text
experiment config
  -> data acquisition
  -> document parsing
  -> label construction
  -> rolling split
  -> feature/model/backtest/audit/report 后续扩展
```

当前版本专注于把前八步基础工程打稳：配置、schema、运行状态、SEC 10-K 元数据、10-K section 解析、价格标签、rolling split 与防泄漏检查。

## 当前版本

- 当前 release: [v0.1.0 Foundation Release](docs/releases/v0.1.0.md)
- Python package version: `0.1.0`
- MVP config: [configs/text_factor_lab/mvp_v0.yaml](configs/text_factor_lab/mvp_v0.yaml)
- 全局规范: [FINANCIAL_TEXT_FACTOR_LAB_GLOBAL_WORKFLOW.md](FINANCIAL_TEXT_FACTOR_LAB_GLOBAL_WORKFLOW.md)

## 已完成能力

### 1. 项目脚手架

- Python package: `text_factor_lab`
- CLI 入口: `python -m text_factor_lab`
- 测试框架: `pytest`
- 代码规范: `ruff`
- 基础目录: `configs/`, `src/`, `tests/`, `runs/`, `data/`

### 2. Config 与 Schema

已实现 Pydantic schema：

- experiment config
- document manifest
- features
- labels
- predictions
- model manifest
- run status
- universe manifest
- parsed sections
- rolling split assignments

Formal run 的关键 gate 已经写入 schema：

- SEC EDGAR formal run 必须有 `sec_user_agent`
- formal run 必须要求 `available_time` 与 `license_note`
- label 必须满足 `prediction_time_utc < label_start_date`
- split window 必须满足 `train < validation < test`

### 3. Orchestrator / Run Manager

已实现 run 初始化：

- 读取 YAML config
- 创建 run directory
- 写入 `config_snapshot.yaml`
- 写入 `run_status.json`
- 写入 `failure_log.jsonl`
- 输出 universe quality report

命令：

```bash
python -m text_factor_lab run --config configs/text_factor_lab/mvp_v0.yaml
```

### 4. Universe Manifest

已实现固定 universe manifest 校验：`entity_id`、`ticker`、`cik`、`company_name`、`selection_date`、`mapping_source`、`delisting_date`、`sector`、`industry`。

MVP 示例 universe 位于：

```text
configs/universe/us_large_cap_2010.csv
```

### 5. SEC EDGAR Filing Metadata

已实现 SEC EDGAR 10-K 元数据构建工具：CIK 标准化、SEC submissions URL、SEC Archives document URL、annual filing 过滤、acceptance time 转 UTC、document manifest record 构建、SEC license note、SHA256 hash 接口。

核心文件：

```text
src/text_factor_lab/data/sec_edgar.py
```

### 6. SEC 10-K Section Parser

已实现 10-K section 解析：HTML/text normalization、跳过 `script/style`、识别 `Item 1`, `Item 1A`, `Item 3`, `Item 7`、避免把 table of contents 当正文、输出 section char span 与 text hash、缺失 section 写入 `missing`、空 section 写入 `failed`、`10-K/A` 默认不覆盖原始 `10-K`。

命令：

```bash
python -m text_factor_lab parse-10k \
  --manifest-record path/to/manifest_record.json \
  --document path/to/10k.html \
  --output-dir runs/example/parsed
```

### 7. Price Data 与 Label Builder

已实现价格数据和标签构建：CSV price panel loader、`simple_return`、`log_return`、forward trading window、`CAR_1_n`、`realized_volatility_1_n`、`realized_volatility_annualized_1_n`、label failure report。

失败会显式记录：missing price、missing benchmark、insufficient forward window、unsupported target。

命令：

```bash
python -m text_factor_lab build-labels \
  --document-manifest path/to/document_manifest.jsonl \
  --prices path/to/prices.csv \
  --labels-output runs/example/labels.jsonl \
  --failures-output runs/example/label_failures.jsonl \
  --target CAR_1_20 \
  --target realized_volatility_1_20
```

### 8. Rolling Year Split 与防泄漏检查

已实现 rolling split：expanding train window、rolling validation window、rolling test window、embargo days、split assignment JSONL、leakage report JSONL。

已检测：train label window crossing validation embargo、validation label window crossing test embargo、test label start before/on event date、unordered split windows。

命令：

```bash
python -m text_factor_lab build-splits \
  --labels runs/example/labels.jsonl \
  --assignments-output runs/example/split_assignments.jsonl \
  --leakage-output runs/example/split_leakage.jsonl \
  --sample-start 2010-01-01 \
  --sample-end 2024-12-31 \
  --train-years-min 5 \
  --validation-years 1 \
  --test-years 1 \
  --embargo-days 20
```

## 安装与验证

建议 Python 版本：`Python >= 3.11`

安装开发依赖：

```bash
python -m pip install -e ".[dev]"
```

运行测试：

```bash
python -m pytest
python -m ruff check .
```

当前 v0.1.0 验收结果：

```text
54 passed
All checks passed
```

## 当前边界

v0.1.0 是 foundation release，还没有实现 dictionary tone feature、TF-IDF feature、train-window-only vocabulary fitting、Ridge / XGBoost training、model comparison、factor backtest、econometric report、full audit/report agent、FinBERT / LLM embedding / LSTM、earnings call transcript pipeline、credit risk target。

## 推荐开发顺序

下一步：

```text
Step 9: dictionary tone + TF-IDF feature layer
```

之后：

```text
Step 10: baseline / Ridge / XGBoost model layer
Step 11: out-of-sample evaluation
Step 12: factor backtest
Step 13: audit and report
Step 14: deployment and reproducibility packaging
```
