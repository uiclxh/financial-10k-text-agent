# Financial Text Factor Lab Agent Global Workflow v1.3

本文档定义 `Financial Text Factor Lab Agent` 的全局 workflow、工程执行细则、数据口径、验收测试和失败处理机制。系统目标不是做泛化金融聊天机器人，而是构建一个可复现、可审计、可横向比较的金融文本因子研究 agent。

核心研究任务：

- 基于 `10-K / 10-Q / earnings call transcripts` 构造金融文本特征。
- 横向比较 `dictionary tone`、`TF-IDF`、`FinBERT`、`LLM embeddings`、`XGBoost`、`LSTM / Transformer sequence model` 等方法。
- 预测 `realized volatility`、`abnormal return / post-event drift`、`sentiment / attention factor`，后期再扩展到 `credit risk`。
- 用固定 schema、固定时间口径、固定样本切分、固定审计规则，保证每次实验能复现和解释。

---

## 1. 总体定位

### 1.1 Agent 的边界

本项目 agent 定位为：

```text
Financial Text Factor Lab Agent
```

它应当完成完整研究闭环：

```text
research question
  -> experiment config
  -> data acquisition
  -> data permission check
  -> document parsing
  -> timestamp alignment
  -> feature extraction
  -> label construction
  -> model training
  -> out-of-sample evaluation
  -> factor backtest
  -> econometric tests
  -> leakage audit
  -> factor card / research report
```

任何不能复现、不能审计、不能解释数据来源和时间戳的结果，都不得作为正式研究结论输出。

### 1.2 与普通 Financial RAG 的区别

Financial RAG 关注：

- 是否找到正确证据。
- 回答是否有 citation。
- 是否减少 hallucination。

Text Factor Lab 进一步关注：

- 文本信号是否有预测力。
- 预测力是否样本外成立。
- 结果是否存在 look-ahead bias。
- 因子是否有经济意义。
- 多模型、多窗口、多 section 比较是否经过统计检验和多重测试披露。

### 1.3 Run 类型

所有实验必须标记为以下之一：

```text
exploratory_run
formal_run
```

`exploratory_run` 可用于数据探索、模型试验和 debug。  
`formal_run` 才能进入正式模型比较、factor card 和 research report。

进入 `formal_run` 的硬条件：

- 所有输入数据有 `source_id`、`license_note`、`retrieval_time_utc`、`available_time_utc`。
- 所有文本和标签通过 schema 校验。
- 所有特征满足 `feature_time <= prediction_time`。
- 所有标签满足 `prediction_time < label_start_time`。
- 无 train-test leakage。
- coverage 达到 experiment config 中设定阈值。

---

## 2. 六阶段开发路线

### 2.1 Phase 1: 扩展现有 RAG 底座为文本因子实验模块

目标：

- 建立面向文本因子研究的实验目录、配置、schema、状态机和 run snapshot。
- 保留文档 ingestion、BM25 检索、证据引用、评估报告能力，但不把 RAG 摘要默认当作因子。

必须实现：

- `experiment config`：记录数据窗口、ticker universe、文本来源、标签定义、模型参数、随机种子、coverage threshold。
- `document manifest`：记录公司、ticker、CIK、文档类型、财政期、发布日期、可用时间、license。
- `run snapshot`：保存配置、代码版本、输入数据 hash、输出路径、状态机日志。
- `schema validator`：校验 manifest、features、labels、predictions、metrics。
- `orchestrator`：统一调度 Data -> Parsing -> Feature -> Label -> Model -> Backtest -> Audit -> Report。

禁止：

- 在没有 timestamp 的文本上构造正式预测标签。
- 在没有 fixed random seed 和时间切分规则时报告模型优劣。
- 将 RAG 生成摘要直接作为因子，除非摘要生成过程被固定、缓存、版本化和审计。

建议目录：

```text
src/text_factor_lab/
  orchestration/
  schemas/
  data/
  parsing/
  features/
  labels/
  models/
  evaluation/
  backtest/
  audit/
  reports/
configs/text_factor_lab/
data/text_factor_lab/
runs/text_factor_lab/
reports/text_factor_lab/
```

### 2.2 Phase 2: 先实现 10-K + realized volatility / abnormal return

目标：

- 先用 SEC 10-K 建立最小可复现实验闭环。
- 第一优先级 target 是 `realized volatility`。
- 第二优先级 target 是 `abnormal return / post-event drift`。

必须实现：

- SEC filing metadata 对齐。
- EDGAR acceptance datetime 解析。
- US equity trading calendar。
- event day 规则。
- adj close 价格对齐。
- `realized_volatility[1,20]`。
- `CAR[1,20]` 或 `CAR[0,5]`。
- market benchmark abnormal return。

MVP 阶段 benchmark：

```text
AR_market = stock_return - market_return
market_return = SPY return or CRSP value-weighted market return
```

后续可扩展：

```text
AR_industry = stock_return - industry_return
AR_factor = stock_return - predicted_return_from_factor_model
```

最小验收标准：

- 能对固定 US large-cap universe 跑通 `10-K -> text features -> labels -> model -> audit -> report`。
- 至少包含 historical mean、industry mean、dictionary tone、TF-IDF + Ridge、XGBoost。
- 输出 model comparison table 和 factor card。

### 2.3 Phase 3: 加入 FinBERT / embeddings，再加入 earnings call

目标：

- 在 10-K pipeline 稳定后加入 FinBERT 和 LLM embeddings。
- earnings call transcripts 只能在权限、时间戳和解析质量达标后进入 formal run。

必须实现：

- FinBERT sentiment aggregate。
- LLM embedding vector。
- section-level aggregation。
- embedding model version 记录。
- transcript metadata 校验。

Earnings call 必须字段：

```text
company
ticker
call_date
call_time
quarter
speaker
speaker_role
section
source_id
license_note
available_time_utc
```

硬规则：

- 如果 transcript 没有明确 `call_time` 和 `license_note`，只能进入 `exploratory_run`，不能进入 `formal_run`。
- 如果 speaker role 不标准，必须经过 role normalization，并保留 raw speaker role。
- 如果 analyst question 和 management answer 无法稳定分割，不能报告 Q&A section-level 因子。
- 如果 transcript 来源不允许缓存或发布，系统只能保存 source reference 和 derived features，不能保存原文。

### 2.4 Phase 4: 加入 rolling out-of-sample backtest 和更高阶模型

目标：

- 从静态横截面预测扩展到时间滚动样本外预测。
- 按模型复杂度逐级加入，不把 LSTM 作为早期主线。

模型层级：

```text
Level 0: historical mean / industry mean
Level 1: dictionary tone
Level 2: TF-IDF + Ridge / ElasticNet
Level 3: FinBERT sentiment aggregate
Level 4: LLM embedding + Ridge / LightGBM / XGBoost
Level 5: LSTM / Transformer sequence model
```

Phase 4 主线模型：

- Ridge / ElasticNet。
- XGBoost or LightGBM。
- Embedding + linear / tree model。
- rolling year split。

LSTM / Transformer sequence model 规则：

- 仅作为 research extension。
- 必须先证明 Level 0-4 baseline 已稳定。
- 必须记录 truncation、padding、tokenization、sequence length、sample coverage。
- 如果结果不超过 TF-IDF + Ridge 或 embedding + Ridge，不得包装为改进。

推荐切分：

```text
train:      years <= T
validation: year  = T + 1
test:       year  = T + 2
roll forward and repeat
```

禁止：

- 随机打乱跨时间样本后报告最终性能。
- 使用未来年份文本训练过去年份预测。
- 在 test set 上调参。

### 2.5 Phase 5: 自动生成 research report 与 factor cards

目标：

- 每个 formal run 自动生成可审计报告。
- 每个候选文本因子自动生成 factor card。

research report 必须包含：

- research question。
- run type。
- 数据来源和 license summary。
- 样本窗口。
- ticker universe。
- coverage report。
- 文本类型。
- 标签定义。
- 特征方法。
- 模型列表。
- tested specifications。
- 样本外指标。
- 经济回测结果。
- 统计显著性检验。
- multiple testing disclosure。
- 失败案例。
- leakage audit。
- reproducible commands。

factor card 必须包含：

```text
factor_name
factor_family
text_source
text_section
feature_method
prediction_target
sample_period
coverage
IC / rank IC
IC_t_stat
Newey_West_t_stat
long_short_return
Sharpe
t_stat
turnover
sector_neutrality_status
tested_specifications_count
multiple_testing_adjustment
top_positive_examples
top_negative_examples
known_failure_modes
leakage_audit_status
production_readiness
```

结论规则：

- 如果统计显著但经济收益不显著，必须明确说明。
- 如果经济收益显著但交易成本后失效，必须明确说明。
- 如果因子只在某个行业、某个时间段或某类公司有效，必须标注为 conditional factor。
- 不允许把单次 backtest 结果描述为 stable alpha。

### 2.6 Phase 6: 扩展到 crypto market sentiment / volatility

目标：

- 复用文本因子框架到 crypto 市场。
- 接入 Binance 等 public market data，构造 funding rate、open interest、mark price、realized volatility 等标签。

适用文本来源：

- crypto news。
- project announcements。
- exchange notices。
- macro / regulatory events。
- research reports。

可用市场标签：

- forward return。
- realized volatility。
- funding rate change。
- open interest change。
- basis / premium change。

Binance 数据规则：

- Binance 插件仅作为 public market data source。
- 不得执行交易。
- 所有 crypto 标签必须记录 symbol、market type、bar interval、timezone、data retrieval time。
- crypto 默认 timezone 使用 UTC。

---

## 3. 数据源、权限与覆盖率规则

### 3.1 数据源优先级

正式研究优先使用可复现、可重新下载、可审计的数据源：

1. SEC EDGAR filings。
2. 官方 investor relations transcript 或可授权 transcript source。
3. CRSP / Compustat / WRDS 等结构化研究数据。
4. FRED / Treasury / rating agency 数据。
5. Binance public market data for crypto extension。

### 3.2 Transcript 权限硬规则

Earnings call transcript 是高风险数据源，必须单独管控：

- 来源必须统一记录 `source_id` 和 `license_note`。
- 缺少 `call_time` 的 transcript 不得进入 formal run。
- 缺少 `license_note` 的 transcript 不得进入 formal run。
- 覆盖率低于 config threshold 时不得与 10-K 模型做正式公平比较。
- speaker role 标准化失败时，不得输出 role-level 因子。
- Q&A 分割失败时，不得输出 Q&A 因子。

### 3.3 Credit Risk 数据规则

Credit risk 不进入前两个 milestone。

原因：

- rating downgrade 频率低，样本不平衡。
- CDS spread 数据不一定稳定获得。
- default proxy 容易变成会计变量预测，而不是文本预测。
- 信用风险通常是低频事件，不适合和 earnings call 短窗口 return 混在同一早期框架。

目标顺序：

```text
Stage 1: realized volatility
Stage 2: abnormal return / post-event drift
Stage 3: sentiment factor / attention factor
Stage 4: credit risk
```

进入 credit risk 阶段前必须具备：

- rating / CDS / default proxy 的可复现数据源。
- leverage、profitability、size、industry、past return、volatility 等结构性控制变量。
- class imbalance 处理方案。
- low-frequency event evaluation protocol。

### 3.4 Manifest 强制规则

任何进入实验的数据都必须写入 manifest：

```text
source_id
source_type
source_url_or_path
retrieval_time_utc
available_time_utc
company_id
ticker
CIK
document_type
fiscal_period
event_time_utc
timezone
hash_sha256
license_note
```

如果缺少 `available_time_utc`，该数据只能用于 exploratory run。

---

## 4. 时间、Return 与 Label 口径

### 4.1 Timezone 规则

US equities 默认：

```text
timezone = America/New_York
```

系统内部保存：

```text
*_time_utc
timezone
local_time
```

Crypto 默认：

```text
timezone = UTC
```

### 4.2 Event Date 规则

US equities 的 SEC filing / earnings call event date：

- 如果事件在开盘前发布：`event_date = 当日交易日`。
- 如果事件在交易时段发布：`event_date = 当日交易日`。
- 如果事件在收盘后发布：`event_date = 下一交易日`。
- 如果事件在非交易日发布：`event_date = 下一交易日`。

默认 US regular trading hours：

```text
market_open  = 09:30 America/New_York
market_close = 16:00 America/New_York
```

### 4.3 Return 规则

正式 label 默认使用 log return：

```text
daily_log_return_t = log(adj_close_t / adj_close_{t-1})
```

用于投资组合回测时，同时保存 simple return：

```text
daily_simple_return_t = adj_close_t / adj_close_{t-1} - 1
```

所有 return 必须记录：

```text
return_type = log | simple
price_field = adj_close
adjustment_method
```

### 4.4 Abnormal Return 规则

MVP 默认：

```text
AR_market = stock_log_return - market_log_return
market_return = SPY log return or CRSP value-weighted market log return
```

扩展版本：

```text
AR_industry = stock_log_return - industry_log_return
AR_factor = stock_log_return - predicted_return_from_factor_model
```

CAR 定义：

```text
CAR[a,b] = sum(AR_t for t in event_date + a through event_date + b)
```

推荐标签：

```text
CAR[1,20]
CAR[0,5]
post_event_drift[1,60]
```

### 4.5 Realized Volatility 规则

默认：

```text
realized_vol_raw = std(daily_log_return over forward window)
realized_vol_annualized = realized_vol_raw * sqrt(252)
```

两个字段都必须保存，禁止只保存一个未说明口径的 `volatility`。

推荐标签：

```text
realized_volatility[1,20]
realized_volatility[1,60]
```

---

## 5. Agent 分工与执行协议

### 5.1 Orchestrator / Controller Agent

职责：

- 读取 experiment config。
- 初始化 run directory。
- 检查前置 artifact 是否存在。
- 按顺序调用各 agent。
- 校验每一步 schema。
- 更新 run status。
- 在失败时生成 failure log。
- 决定 run 是否可以进入 formal report。

执行顺序：

```text
Data
  -> Parsing
  -> Feature
  -> Label
  -> Model
  -> Backtest & Econometrics
  -> Audit
  -> Report
```

### 5.2 Run 状态机

合法状态：

```text
created
data_ready
parsed
features_ready
labels_ready
trained
evaluated
audited
reported
failed
rejected
```

状态门槛：

- `audit_status != pass` -> cannot report as formal result。
- `coverage < threshold` -> cannot compare models formally。
- `missing available_time_utc > 0` -> formal run fails。
- `missing license_note > 0` -> formal run fails。
- `test leakage detected` -> run rejected。
- `schema validation failed` -> run failed。

### 5.3 Data Agent

职责：

- 下载 SEC filings、transcripts、价格、行业、市值、信用风险数据。
- 维护数据 manifest。
- 检查 ticker、CIK、company name 映射。
- 检查 data availability time 和 license。

输出：

```text
document_manifest.parquet
market_data_manifest.parquet
data_quality_report.json
```

### 5.4 Parsing Agent

职责：

- 解析 10-K section。
- 解析 earnings call speaker 和 section。
- 清洗 boilerplate。
- 保留 paragraph / sentence / speaker-level trace。

输出：

```text
parsed_documents.jsonl
section_chunks.jsonl
speaker_turns.jsonl
parsing_quality_report.json
```

### 5.5 Feature Agent

职责：

- 生成 dictionary tone。
- 生成 TF-IDF。
- 生成 FinBERT sentiment。
- 生成 LLM embeddings。
- 生成 section-aware features。

输出：

```text
features.parquet
feature_manifest.json
feature_quality_report.json
```

### 5.6 Label Agent

职责：

- 构造 realized volatility。
- 构造 abnormal return。
- 构造 post-event drift。
- 后期构造 credit risk 标签。
- 检查 label availability 和 forward window。

输出：

```text
labels.parquet
label_manifest.json
label_quality_report.json
```

### 5.7 Model Agent

职责：

- 训练 Level 0-5 模型。
- 统一输出 prediction 和 factor score。
- 记录 model manifest。

输出：

```text
predictions.parquet
model_manifest.json
model_metrics.json
```

### 5.8 Backtest & Econometrics Agent

职责：

- 计算 IC / rank IC。
- 构造 long-short portfolio。
- 做 event study。
- 做行业中性、市值中性、风格因子控制。
- 做 Newey-West、clustered standard errors、bootstrap CI、多重测试披露。

输出：

```text
backtest_results.json
portfolio_returns.parquet
econometric_tests.json
```

### 5.9 Audit Agent

职责：

- 检查 look-ahead bias。
- 检查 train-test leakage。
- 检查 timestamp alignment。
- 检查重复样本。
- 检查 survivorship bias。
- 检查 schema。
- 检查 coverage。
- 检查 license。

输出：

```text
leakage_audit.json
reproducibility_audit.json
failure_cases.jsonl
audit_summary.json
```

### 5.10 Report Agent

职责：

- 生成 research report。
- 生成 factor card。
- 生成模型对比表。
- 生成失败案例分析。

输出：

```text
research_report.md
factor_cards.md
comparison_tables.csv
```

---

## 6. 最小 Schema

### 6.1 document_manifest

```text
document_id: str
entity_id: str
ticker: str
cik: str
company_name: str
document_type: enum[10-K, 10-Q, earnings_call]
fiscal_year: int
fiscal_period: str
source_id: str
source_url_or_path: str
retrieval_time_utc: datetime
available_time_utc: datetime
event_time_utc: datetime
event_date: date
timezone: str
hash_sha256: str
license_note: str
parser_version: str
```

### 6.2 parsed_documents / section_chunks

```text
chunk_id: str
document_id: str
entity_id: str
ticker: str
document_type: str
section: str
subsection: str
speaker: str | null
speaker_role_raw: str | null
speaker_role_normalized: str | null
text: str
text_hash_sha256: str
start_char: int | null
end_char: int | null
parser_version: str
```

### 6.3 features.parquet

```text
feature_id: str
entity_id: str
ticker: str
event_time_utc: datetime
prediction_time_utc: datetime
feature_time_utc: datetime
feature_family: str
feature_name: str
feature_value: float | vector_ref
feature_version: str
source_document_id: str
source_chunk_id: str | null
```

### 6.4 labels.parquet

```text
label_id: str
entity_id: str
ticker: str
event_time_utc: datetime
prediction_time_utc: datetime
label_start_date: date
label_end_date: date
target_name: str
target_value: float
benchmark_method: str
return_type: enum[log, simple]
adjustment_method: str
label_version: str
```

### 6.5 predictions.parquet

```text
run_id: str
model_id: str
split_id: str
ticker: str
event_date: date
target_name: str
prediction_value: float
factor_score: float
feature_version: str
label_version: str
training_window: str
validation_window: str
test_window: str
```

### 6.6 model_manifest.json

```text
model_id: str
model_name: str
model_family: str
model_level: int
model_version: str
hyperparameters: object
random_seed: int
training_window: str
validation_window: str
test_window: str
feature_version: str
label_version: str
code_commit: str | null
```

### 6.7 run_status.json

```text
run_id: str
run_type: enum[exploratory_run, formal_run]
status: enum[created, data_ready, parsed, features_ready, labels_ready, trained, evaluated, audited, reported, failed, rejected]
created_at_utc: datetime
updated_at_utc: datetime
config_path: str
failure_reason: str | null
audit_status: enum[pass, warn, fail, not_run]
coverage: float
```

---

## 7. 特征全局规则

### 7.1 文本表征方法

至少支持：

- Dictionary: tone、uncertainty、litigation、liquidity、risk terms。
- Lexical: TF-IDF、n-gram。
- Domain LM: FinBERT sentiment。
- General LLM: embeddings、section embeddings。
- Sequential: LSTM / Transformer sequence input。

### 7.2 Section-Aware 规则

10-K 至少区分：

- Risk Factors。
- MD&A。
- Business。
- Legal Proceedings。
- Management discussion of liquidity。

Earnings call 至少区分：

- Prepared remarks。
- Q&A。
- Management answer。
- Analyst question。
- CEO speech。
- CFO speech。

不得只报告全文级别结果，而忽略 section-level 对照。

---

## 8. 模型比较规则

### 8.1 公平比较

所有模型比较必须满足：

- 相同样本。
- 相同标签。
- 相同时间切分。
- 相同缺失值处理规则。
- 相同评价指标。
- 相同交易成本假设。

### 8.2 Baseline 强制规则

任何复杂模型必须至少与以下 baseline 比较：

- historical mean。
- industry mean。
- dictionary tone。
- TF-IDF + Ridge / ElasticNet。

如果复杂模型无法超过 baseline，报告中必须明确写出。

---

## 9. 统计显著性与多重测试规则

### 9.1 必须报告的检验

正式报告至少包含：

- IC time-series mean。
- IC time-series t-stat。
- rank IC。
- Newey-West adjusted t-stat。
- long-short return t-stat。
- subperiod stability test。

视样本结构加入：

- clustered standard errors by firm。
- clustered standard errors by date。
- two-way clustered standard errors by firm and date。
- bootstrap confidence interval。

### 9.2 Multiple Testing

如果同一项目测试多个模型、多个窗口、多个文本 section，则报告必须披露：

```text
tested_models
tested_targets
tested_windows
tested_sections
tested_specifications_count
selected_specification_rule
multiple_testing_adjustment
```

可用调整：

- Bonferroni。
- Holm。
- Benjamini-Hochberg FDR。
- White's Reality Check。
- Deflated Sharpe Ratio。

未做 multiple-testing adjustment 时，必须在报告中标注：

```text
multiple_testing_adjustment = not_applied
```

并将结论等级最高限制为 `exploratory` 或 `statistically_significant_pre_adjustment`。

---

## 10. 防泄漏与审计规则

### 10.1 Look-Ahead Bias

所有 formal run 必须通过：

```text
feature_time_utc <= prediction_time_utc
prediction_time_utc < label_start_time
label_end_time <= evaluation_time
```

任何违反时间顺序的样本必须剔除；如果剔除后 coverage 不足，则 formal run 失败。

### 10.2 Train-Test Leakage

禁止：

- 对全样本 fit scaler、PCA、TF-IDF vocabulary。
- 对全样本选择特征。
- 用 test set 调参。
- 对同一事件生成多个高度重复样本后跨 split 分散。

### 10.3 Reproducibility

每次 formal run 必须保存：

```text
config
input manifests
feature manifest
label manifest
model manifest
metrics
audit report
failure log
reproducible commands
```

---

## 11. 失败处理机制

### 11.1 Failure Log

任何失败必须记录：

```text
run_id
stage
status_before_failure
failure_type
failure_message
affected_artifacts
recoverable: true | false
recommended_action
created_at_utc
```

### 11.2 失败类型

```text
data_missing
license_missing
timestamp_missing
schema_validation_failed
coverage_below_threshold
parser_failed
label_window_unavailable
train_test_leakage
lookahead_bias_detected
model_training_failed
metric_computation_failed
audit_failed
```

### 11.3 失败后处理

- `license_missing`：降级为 exploratory run 或移除数据源。
- `timestamp_missing`：降级为 exploratory run。
- `coverage_below_threshold`：不得做 formal model comparison。
- `schema_validation_failed`：停止后续 pipeline。
- `train_test_leakage`：run rejected。
- `lookahead_bias_detected`：run rejected。
- `audit_failed`：不得生成 formal report。

---

## 12. 报告结论规则

### 12.1 结论等级

研究结论必须标注等级：

```text
exploratory
statistically_significant_pre_adjustment
statistically_significant_after_adjustment
economically_significant
robust
production_candidate
rejected
```

### 12.2 禁止性表述

禁止在没有充分证据时使用：

- stable alpha。
- reliable predictor。
- production-ready。
- causal effect。
- guaranteed improvement。

应使用：

- in this sample。
- under this specification。
- out-of-sample over this period。
- after these controls。
- before transaction costs。
- after transaction costs。

---

## 13. MVP v0 范围

MVP v0 只做最稳闭环：

```text
text_source: 10-K only
universe: US large-cap fixed universe
sample_period: 2010-2024
features: TF-IDF + dictionary tone
targets: realized_volatility[1,20], CAR[1,20]
models: historical mean, industry mean, Ridge, XGBoost
split: rolling year split
outputs: audit report + model comparison table + factor card
```

MVP v0 暂不做：

- FinBERT。
- LLM embedding。
- LSTM。
- earnings call。
- credit risk。
- crypto。
- production UI。

MVP v0 验收测试：

- `document_manifest` schema pass。
- `labels` schema pass。
- event date rule unit tests pass。
- log return calculation unit tests pass。
- realized volatility raw / annualized unit tests pass。
- rolling split 无未来数据。
- TF-IDF vocabulary 只在 train window fit。
- formal run audit pass。
- 生成 `research_report.md`、`factor_cards.md`、`comparison_tables.csv`。

---

## 14. 后续里程碑

### Milestone 1

建立 `text_factor_lab` 目录、schema、orchestrator、run status、failure log。

### Milestone 2

完成 10-K 到 realized volatility / CAR 标签的 MVP v0。

### Milestone 3

加入 FinBERT、LLM embedding 和 section-level comparison。

### Milestone 4

加入 earnings call，但只允许合规 transcript 进入 formal run。

### Milestone 5

加入 advanced econometrics、multiple testing adjustment、factor stability analysis。

### Milestone 6

在数据条件充分时扩展 credit risk。

### Milestone 7

接入 crypto market data，扩展到 funding rate、open interest、volatility sentiment factor。

---

## 15. Experiment Config 模板

MVP v0 必须提供一个可直接运行的 `experiment_config.yaml`。任何 pipeline 不得依赖代码中的隐式默认值完成 formal run。

推荐文件路径：

```text
configs/text_factor_lab/mvp_v0.yaml
```

最小模板：

```yaml
run:
  run_id: "tflab_10k_mvp_v0_001"
  run_type: "formal_run"
  random_seed: 42
  output_dir: "runs/text_factor_lab/tflab_10k_mvp_v0_001"

universe:
  name: "us_large_cap_fixed"
  selection_date: "2010-01-01"
  tickers_file: "configs/universe/us_large_cap_2010.csv"
  survivorship_bias_control: true
  allow_delisted_firms: true
  historical_ticker_mapping: true

sample:
  start_date: "2010-01-01"
  end_date: "2024-12-31"
  timezone: "America/New_York"

text_source:
  document_type: "10-K"
  source: "SEC_EDGAR"
  sections:
    - "Risk Factors"
    - "MD&A"
    - "Business"
    - "Legal Proceedings"
  require_available_time: true
  require_license_note: true

labels:
  targets:
    - "realized_volatility_1_20"
    - "CAR_1_20"
  return_type: "log"
  portfolio_return_type: "simple"
  price_field: "adj_close"
  market_benchmark: "SPY"
  annualization_days: 252

split:
  method: "rolling_year"
  train_years_min: 5
  validation_years: 1
  test_years: 1
  embargo_days: 20

features:
  methods:
    - "dictionary_tone"
    - "tfidf"
  dictionary_tone:
    dictionaries:
      - "loughran_mcdonald"
      - "risk_uncertainty"
  tfidf:
    max_features: 50000
    ngram_range: [1, 2]
    min_df: 5
    fit_scope: "train_window_only"

models:
  enabled:
    - "historical_mean"
    - "industry_mean"
    - "ridge"
    - "xgboost"
  tuning:
    selection_metric: "validation_rank_ic"
    save_tuning_log: true

backtest:
  rebalance_frequency: "event_based"
  portfolio_method: "top_bottom_quintile"
  weighting: "equal_weight"
  holding_window_days: 20
  transaction_cost_bps_one_way: 10
  sector_neutral: true
  newey_west_lag: 19

audit:
  coverage_threshold: 0.8
  require_license_note: true
  require_available_time: true
  reject_on_lookahead: true
  reject_on_train_test_leakage: true
```

Config 校验规则：

- `run_type=formal_run` 时，`require_available_time` 和 `require_license_note` 必须为 true。
- `tfidf.fit_scope` 必须为 `train_window_only`。
- `split.method` 的第一版只允许 `rolling_year`。
- `backtest.newey_west_lag` 不得小于 `holding_window_days - 1`，除非报告明确说明不使用重叠窗口。
- 所有 config 必须被复制到 run directory，作为 run snapshot 的一部分。

---

## 16. Universe 构造规则

MVP v0 的 universe 必须在 sample start 前固定，避免 survivorship bias。

硬规则：

- 不得使用 2024 年仍然存在的公司倒推 2010 年 universe。
- universe selection date 必须早于或等于 sample start date。
- large-cap 判定必须基于 selection date 当时可获得的市值或指数成分。
- 如果样本期内公司退市，应保留到其退市前的所有可用样本。
- ticker 变更、并购、退市、CIK 映射必须按历史时间版本保存。
- 同一公司不同 ticker 历史必须映射到稳定的 `entity_id`。

MVP v0 推荐 universe：

```text
固定 2010-01-01 前可确定的 US large-cap universe
优先使用当时的 S&P 500 / Russell 1000 成分或市值排名
保留 delisted firms until delisting date
```

Universe manifest 最小字段：

```text
entity_id
ticker
historical_ticker
cik
company_name
sector
industry
selection_date
market_cap_at_selection
entry_date
exit_date
delisting_date
mapping_source
mapping_available_time_utc
```

禁止：

- 用当前 ticker list 作为历史 universe。
- 删除样本期中退市或被并购的公司后再回测。
- 在没有 historical ticker-CIK mapping 的情况下合并跨年份 filing。

---

## 17. Backtest 组合构造规则

所有 formal run 的组合回测必须明确记录组合形成方式。

默认组合规则：

```text
At each rebalance date:
1. 使用 test period 内当时可得的 factor_score 排序。
2. long top quintile。
3. short bottom quintile。
4. 默认 equal-weight。
5. 可选 value-weight，但必须单独报告。
6. 持有期与 label window 保持一致。
7. 使用 simple return 计算组合收益。
8. 默认交易成本为单边 10 bps。
9. turnover = sum(abs(w_t - w_{t-1})).
10. sector-neutral portfolio 在每个 sector 内分别排序和分组。
```

Event-based portfolio：

- 每个事件只在其 `prediction_time` 后进入组合。
- 如果同一 ticker 多个事件窗口重叠，必须定义聚合规则。
- 默认聚合规则为保留最新事件信号，旧信号在同一 ticker 上被替换。

Calendar portfolio：

- 每月或每周 rebalance 时，只使用 rebalance date 前已发布且未过期的最新 factor score。
- signal expiry 默认等于 holding window。

Overlapping window 规则：

- 如果 holding windows overlap，必须报告 Newey-West adjusted t-stat。
- Newey-West lag 至少等于 `holding_window_days - 1`。
- 如果使用非重叠窗口，必须在报告中写明 sampling rule。

交易成本规则：

- 默认单边交易成本：`10 bps`。
- turnover 必须在交易成本前和交易成本后都报告。
- long-short return 必须同时报告 gross 和 net。

---

## 18. Hyperparameter Tuning 规则

调参必须只使用 validation window。

硬规则：

- Hyperparameters must be selected using validation window only。
- Selected hyperparameters are then applied once to the test window。
- No test-period metric can be used for model selection。
- 每个 rolling split 可以单独调参，但必须保存该 split 的调参记录。
- 如果使用历史 validation performance 选择固定参数，必须在 config 中声明。
- 所有搜索过的参数组合必须保存到 `tuning_log.json`。

调参指标规则：

- 对纯数值预测任务，例如 realized volatility，默认可使用 `validation_rmse` 或 `validation_mae`。
- 对因子排序任务，例如 long-short portfolio 或 rank prediction，默认使用 `validation_rank_ic`。
- 如果同一模型同时服务 prediction 和 ranking，必须在 config 中指定 primary selection metric。

MVP v0 推荐参数网格：

```yaml
ridge:
  alpha: [0.01, 0.1, 1.0, 10.0, 100.0]

elasticnet:
  alpha: [0.001, 0.01, 0.1, 1.0]
  l1_ratio: [0.1, 0.5, 0.9]

xgboost:
  max_depth: [2, 3, 4]
  learning_rate: [0.03, 0.1]
  n_estimators: [100, 300]
  subsample: [0.8, 1.0]
  colsample_bytree: [0.8, 1.0]
```

`tuning_log.json` 最小字段：

```text
run_id
split_id
model_id
parameter_grid
searched_parameters
validation_metric
selected_parameters
selection_reason
created_at_utc
```

公平比较规则：

- 复杂模型的调参预算必须披露。
- 如果 XGBoost 搜索空间远大于 Ridge，报告必须标注 tuning budget difference。
- 不允许只报告最佳复杂模型而隐藏失败参数组合。

---

## 19. 工程测试与命令级验收

MVP v0 必须有可执行测试，而不是只在文档中声明规则。

推荐测试文件：

```text
tests/test_event_date.py
tests/test_label_calculation.py
tests/test_rolling_split.py
tests/test_tfidf_no_leakage.py
tests/test_schema_validation.py
tests/test_formal_run_gate.py
tests/test_backtest_construction.py
tests/test_failure_handling.py
```

最低测试覆盖：

- 开盘前、交易时段、收盘后、非交易日 event date。
- log return 和 simple return 计算。
- CAR[a,b] 窗口。
- realized volatility raw / annualized。
- rolling split 不包含未来年份。
- TF-IDF vocabulary 只在 train window fit。
- schema 缺少 required field 时失败。
- formal run 缺少 `available_time_utc` 时失败。
- formal run 缺少 `license_note` 时失败。
- look-ahead bias detected 时 run rejected。
- coverage 低于 threshold 时不能 formal compare。
- backtest top/bottom quintile 权重和 turnover 计算。

命令级验收：

```bash
python -m text_factor_lab.run --config configs/text_factor_lab/mvp_v0.yaml
python -m text_factor_lab.audit --run-id tflab_10k_mvp_v0_001
python -m text_factor_lab.report --run-id tflab_10k_mvp_v0_001
pytest tests/test_event_date.py
pytest tests/test_label_calculation.py
pytest tests/test_rolling_split.py
pytest tests/test_tfidf_no_leakage.py
pytest tests/test_schema_validation.py
pytest tests/test_formal_run_gate.py
```

MVP v0 通过标准：

- 全部 unit tests pass。
- `run_status.json.status = reported`。
- `run_status.json.audit_status = pass`。
- 生成 `research_report.md`。
- 生成 `factor_cards.md`。
- 生成 `comparison_tables.csv`。
- formal report 中包含 tested specifications 和 multiple-testing disclosure。

---

## 20. Sentiment / Attention Target Definition

Sentiment / attention 不得作为模糊概念进入 formal run，必须明确 target definition。

### 20.1 Sentiment target

可选定义：

```text
analyst_sentiment_change
news_sentiment_change
market_reaction_direction
earnings_call_tone_surprise
management_tone_change
```

推荐 MVP 后扩展：

- `management_tone_change = current management tone - trailing 4-quarter management tone average`。
- `earnings_call_tone_surprise = current call tone - expected tone from firm historical tone`。
- `market_reaction_direction = sign(CAR[0,1])`，只能作为 market-implied sentiment proxy。

禁止：

- 把模型自己生成的情绪解释当作 ground truth sentiment。
- 在没有外部标签或明确定义 proxy 的情况下训练 sentiment target。

### 20.2 Attention target

可选定义：

```text
post_filing_abnormal_volume
EDGAR_download_attention
news_coverage_count_change
Google_Trends_change
analyst_question_intensity
```

推荐定义：

```text
post_filing_abnormal_volume[1,5]
  = log(volume over days 1-5) - log(expected volume from trailing window)

analyst_question_intensity
  = number of analyst questions / total call length
```

注意：

- Attention target 必须记录数据源和 availability。
- 如果使用 Google Trends、news count 或 EDGAR download，必须记录查询时间和 revision policy。
- Attention target 不能与 text feature 来自同一未分离的衍生变量，否则可能构成 mechanical correlation。

---

## 21. Machine-Executable Schema 规则

文本 schema 必须落地为可执行校验代码。MVP v0 至少实现 Pydantic 或 Pandera schema。

推荐路径：

```text
src/text_factor_lab/schemas/config.py
src/text_factor_lab/schemas/document_manifest.py
src/text_factor_lab/schemas/features.py
src/text_factor_lab/schemas/labels.py
src/text_factor_lab/schemas/predictions.py
src/text_factor_lab/schemas/model_manifest.py
src/text_factor_lab/schemas/run_status.py
```

最低字段约束：

```text
ticker: non-empty string
entity_id: non-empty string
event_time_utc: timezone-aware datetime
available_time_utc: timezone-aware datetime
prediction_time_utc: timezone-aware datetime
target_value: finite float
factor_score: finite float
coverage: 0 <= coverage <= 1
run_type: enum[exploratory_run, formal_run]
status: known run state enum
```

跨字段约束：

```text
available_time_utc <= prediction_time_utc
feature_time_utc <= prediction_time_utc
prediction_time_utc < label_start_time
label_start_date <= label_end_date
event_date is a valid trading date after event-time adjustment
```

`experiment_config.yaml` 必须由 `src/text_factor_lab/schemas/config.py` 校验。Config schema 失败时，run status 直接进入 `failed`，不得启动 data pipeline。

---

## 22. SEC 10-K Parsing Protocol

MVP v0 只解析 SEC 10-K。解析器必须优先保证稳定性和可审计性，而不是追求所有格式完美覆盖。

目标 section：

```text
Item 1. Business
Item 1A. Risk Factors
Item 3. Legal Proceedings
Item 7. Management's Discussion and Analysis
```

解析规则：

- 优先使用 SEC EDGAR company submissions 和 filing document。
- HTML 必须先清理 script、style、inline XBRL tag 和隐藏文本。
- 目录中的 item heading 不得误判为正文 section。
- section extraction 必须保存 `start_char`、`end_char`、`text_hash_sha256`。
- 如果某个 section extraction 失败，记录 `parser_failed_section`，但不一定导致整个 document 失败。
- 如果核心 section `Item 1A` 和 `Item 7` 同时失败，该 document 不得进入 formal feature set。
- 所有 parser version 必须写入 manifest。

Heading 变体必须支持：

```text
Item 1A. Risk Factors
ITEM 1A - RISK FACTORS
Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations
Management Discussion and Analysis
```

Amendment policy：

- `10-K/A` 默认不覆盖原始 `10-K`。
- 如果 config 指定 `amendment_policy: use_latest_amendment`，必须保存原始 filing 和 amended filing 的 mapping。
- amendment 的 available time 必须使用 amendment filing 的 acceptance time。

质量报告必须包含：

```text
documents_total
documents_parsed
section_parse_rate_by_item
failed_sections
html_cleaning_warnings
amendment_count
parser_version
```

---

## 23. MVP 数据接口选择

MVP v0 必须固定数据接口，不允许在同一个 formal run 中混用多个未对齐来源。

推荐优先级：

```text
SEC filings: SEC EDGAR company submissions + filing documents
price data: CRSP if available
price fallback: Stooq / Polygon / Yahoo Finance only for exploratory or clearly caveated run
market benchmark: SPY for MVP, CRSP value-weighted for research-grade run
sector: GICS if available, SIC/NAICS as fallback
universe: historical S&P 500 constituents as preferred MVP universe
```

Large-cap universe 默认方案：

```text
preferred: historical S&P 500 constituents known as of 2010-01-01
fallback: 2009-12-31 market cap top N with delisted firms retained
```

如果没有 WRDS / CRSP 权限，可以使用公开数据完成 MVP exploratory run，但 report 必须披露：

```text
price data source limits
benchmark limitations
survivorship bias residual risk
delisting return availability
historical constituent availability
```

Formal research-grade run 优先使用 CRSP/Compustat/WRDS 或其他可审计机构数据。

---

## 24. Label 边界情况处理

Label builder 必须对边界情况做确定性处理。

规则：

- 如果 forward window 内有效交易日不足，标记 `label_window_unavailable`，样本剔除。
- 如果 event_date 后不足目标窗口长度，例如 20 个交易日，标签无效。
- 如果 adj close 缺失，标签无效，除非 data source 提供可审计修复值。
- 如果 benchmark return 缺失，abnormal return 标签无效。
- 如果公司退市，delisting return 必须在可获得时纳入 forward return。
- 如果 delisting return 不可获得，必须在 label quality report 中披露。
- 如果股票停牌导致 forward window return 不可计算，标签无效。
- 如果公司在 holding window 内 merger / acquisition，必须记录 corporate action flag。

Label quality report 必须包含：

```text
labels_requested
labels_created
labels_invalid
invalid_reason_counts
missing_price_count
missing_benchmark_count
insufficient_forward_window_count
delisting_events_count
corporate_action_count
```

---

## 25. Feature Preprocessing 规则

MVP v0 的 feature preprocessing 必须固定并记录版本。

默认 TF-IDF preprocessing：

```text
remove_html: true
lowercase: true
remove_numbers: configurable
remove_punctuation: true
stopwords: sklearn_english + financial_stopwords
ngram_range: [1, 2]
min_df: 5
max_df: 0.95
sublinear_tf: true
fit_scope: train_window_only
```

TF-IDF 规则：

- vocabulary 只能在 train window fit。
- validation 和 test 只能 transform。
- full-text features 和 section-level features 必须分开保存。
- 每个 split 的 vocabulary hash 必须保存。

Dictionary tone 规则：

```text
dictionary_source: Loughran-McDonald or project-local dictionary
dictionary_version: required
normalization_denominator: total_words or total_non_stopwords
negation_handling: enabled | disabled
section_level: true
```

Dictionary feature 必须保存：

```text
positive_count
negative_count
uncertainty_count
litigious_count
risk_count
total_words
normalized_score
dictionary_version
```

禁止：

- 在 test window 上重新 fit TF-IDF vocabulary。
- 把 section-level 和 full-document feature 混成同名字段。
- 不记录 preprocessing version 就比较模型。

---

## 26. Report 模板

Report Agent 必须按固定结构生成 `research_report.md`，避免每次报告口径漂移。

固定结构：

```text
1. Executive Summary
2. Research Question
3. Run Metadata
4. Data and Sample
5. Universe Construction
6. Label Construction
7. Feature Construction
8. Model Setup
9. Hyperparameter Tuning
10. Out-of-Sample Prediction Results
11. Factor Backtest
12. Statistical Tests
13. Robustness Checks
14. Multiple Testing Disclosure
15. Leakage Audit
16. Failure Cases and Exclusions
17. Conclusion Level
18. Reproducible Commands
19. Appendix: Schema and Config Snapshot
```

Report 必须包含：

- run_id。
- run_type。
- audit_status。
- config snapshot path。
- data source summary。
- coverage summary。
- tested specifications count。
- gross and net backtest results。
- conclusion level。

如果 `audit_status != pass`，Report Agent 只能生成 exploratory failure report，不得生成 formal research report。

---

## 27. 环境复现规则

MVP v0 必须记录运行环境，避免结果只能在单台机器上复现。

最低要求：

```text
python_version: 3.11 recommended
package_versions_locked: true
random_seed_fixed: true
timezone_database_version_recorded: true
```

推荐文件：

```text
pyproject.toml
requirements.lock
environment.yml
Dockerfile
```

Run snapshot 必须保存：

```text
python_version
platform
package_lock_hash
config_hash
code_commit_or_source_hash
random_seed
```

如果使用 deep learning：

- 记录 CUDA version。
- 记录 torch / tensorflow deterministic setting。
- 记录 model cache path 和 model version。
- 记录 tokenizer version。

---

## 28. GitHub / CI 工程规则

如果项目进入 GitHub 展示或协作开发，必须加入基础 CI。

推荐文件：

```text
.github/workflows/tests.yml
pyproject.toml
.pre-commit-config.yaml
tests/fixtures/
tests/sample_data/
tests/expected_outputs/
```

CI 至少运行：

```text
ruff or equivalent lint
black or equivalent formatting check
pytest
schema validation tests
MVP smoke test on tiny fixture dataset
```

Fixture 规则：

- `tests/fixtures/` 保存最小 10-K-like 文本样本。
- `tests/sample_data/` 保存最小价格和 benchmark 样本。
- `tests/expected_outputs/` 保存 event date、label、split、schema validation 的预期结果。
- fixture 不得包含受限版权 transcript 原文。

Pull request gate：

- schema test fail -> cannot merge。
- formal run gate test fail -> cannot merge。
- look-ahead leakage test fail -> cannot merge。
- MVP smoke test fail -> cannot merge。

---

## 29. 项目最高规则

1. 先复现，再复杂。
2. 先时间正确，再追求精度。
3. 先 baseline，再深度模型。
4. 先 volatility，再 return，再 sentiment，再 credit risk。
5. 先 10-K，再 earnings call。
6. 先 schema，再 pipeline。
7. 先 audit，再 report。
8. 先 disclose tested specifications，再挑选最佳模型。
9. 先因子证据，再 agent 叙事。

如果一个功能会提升展示效果但降低可复现性，应延后。

如果一个模型更复杂但无法超过简单 baseline，应保留结果但不得包装为改进。

如果一个结果无法解释数据来源、权限、时间顺序、样本覆盖和评估口径，则不得进入正式报告。
