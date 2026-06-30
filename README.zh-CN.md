# Financial 10-K Text Agent

一个可审计的金融 NLP 研究流水线，用于检验 SEC 10-K 文本特征是否包含对未来实现波动率和异常收益目标的样本外预测信息。

本项目不是 RAG 演示、通用 FinBERT 情绪分类器或 AI 交易机器人。它位于金融 NLP、实证资产定价工作流、滚动样本外验证、模型比较诊断和研究审计的交叉领域。

当前实证结论被刻意限定为：

> SEC 10-K 文本特征对未来 20 日实现波动率提供探索性的样本外排序证据。收益率预测更弱，预注册组合检验不能证明可交易 alpha。

---

## 当前版本

最新公开结果包：

[`docs/results/50_company_public_fmp_alpha_2016_2025_v4`](docs/results/50_company_public_fmp_alpha_2016_2025_v4/README.md)

| 字段 | 数值 |
| --- | --- |
| Run ID | `50_company_public_fmp_alpha_2016_2025_v4` |
| 股票池 | 50 家美国大盘公司 |
| 样本 | FY2016-FY2025 |
| SEC 10-K | 500 |
| Labels | 1,500 |
| OOS predictions | 8,133 |
| 特征记录 | 520k+ |
| Tested specifications | 594 |
| Multiple-testing families | 26 |
| Eligible OOS coverage | 100% |
| Model-expected prediction coverage | 98.546% |
| Primary prediction coverage | 100% |
| Primary portfolio coverage | 100% |
| Audit failures | 0 |
| Audit warnings | 2 |
| 结果状态 | exploratory applied-grade run |

模型预期覆盖率低于 100%，是因为扩展诊断规格中有少量 malformed section 无法生成数值特征向量。预注册主预测和主组合规格均保持 100% 覆盖。

---

## 本地复现

公开 smoke-test 不需要私有 API key 或授权数据：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[dev,ml]"
python -m pytest -q
python -m ruff check .
python -m text_factor_lab run --config configs/text_factor_lab/e2e_smoke.yaml --execute
```

输出目录：

```text
runs/text_factor_lab/tflab_e2e_smoke_001/
```

重跑 50-company applied-data 实验需要 API key 和私有数据缓存：

```powershell
$env:FMP_API_KEY="..."
$env:ALPHAVANTAGE_API_KEY="..."
$env:SEC_USER_AGENT="financial-10k-text-agent contact:your_email@example.com"
python -m text_factor_lab run --config configs/text_factor_lab/50_company_public_fmp_alpha_v4.yaml --execute
```

仓库只提交紧凑结果摘要。SEC 原始文件、API 响应、完整价格面板、API key 和私有中间数据不会提交。

---

## 主要结果

预注册主预测规格使用 Ridge 预测 `realized_volatility_1_20`，并评价 ALL_SPLITS Rank IC。

| 模型 | 目标 | 指标 | 数值 | Raw p-value |
| --- | --- | ---: | ---: | ---: |
| Ridge | `realized_volatility_1_20` | Rank IC | 0.2395 | 0.00067 |

该结果为 10-K 文本包含未来 20 日实现波动率排序信息提供了探索性样本外证据。它是预测证据，不是可交易 alpha 结论。

---

## 主组合结果

预注册主组合使用月度共同调仓、行业中性、等权多空构造，并基于 ALL_SPLITS OOS 收益序列计算 Newey-West p-value。

| 模型 | 目标 | 组合 | Sharpe | Raw p-value |
| --- | --- | --- | ---: | ---: |
| Ridge | `realized_volatility_1_20` | Monthly sector-neutral equal-weight | -0.8539 | 0.1147 |

主组合检验不能证明正式可交易 alpha。所有组合输出仅作为诊断。

---

## 最佳探索性排序结果

| 模型 | 特征集 | 目标 | Rank IC | Newey-West t-stat | RMSE |
| --- | --- | --- | ---: | ---: | ---: |
| Ridge | TF-IDF/SVD only | `realized_volatility_1_20` | 0.3668 | 5.4055 | 0.00992 |

该结果属于探索性模型比较，而不是预注册主结论。模型主要被评价为横截面排序信号，而不是最小 RMSE 的波动率点预测器。

---

## 文本增量诊断

Industry-neutral Rank IC 在每个 OOS split-industry 组内分别对真实目标和模型预测去均值，然后计算 tie-aware rank correlation。它是描述性增量诊断，不是因果分解。

| 模型 | Raw Rank IC | Industry-neutral Rank IC | Neutral NW t-stat |
| --- | ---: | ---: | ---: |
| Ridge TF-IDF/SVD only | 0.3668 | 0.3416 | 3.8557 |
| Ridge industry + text | 0.3296 | 0.3251 | 4.3994 |
| Ridge dictionary only | 0.2244 | 0.2465 | 5.2660 |
| Ridge combined text | 0.2395 | 0.2023 | 1.3704 |
| XGBoost combined text | 0.2741 | 0.1991 | 2.5256 |
| Industry mean | 0.2924 | 0.0000 | 0.0000 |

行业均值基准仍然很强，但文本模型在行业中性后保留了正向波动率排序点估计。这支持探索性的文本波动率排序解释，但不能声称文本独立导致了预测信号。

---

## 特征消融

所有 Ridge 变体使用相同 rolling splits、validation-only alpha 选择和调参预算。`industry_only` 是训练窗口行业均值基准，不是 Ridge 模型。

| 特征集 | Estimator | Rank IC | Neutral Rank IC | Rank IC NW t | Neutral NW t | RMSE |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| TF-IDF/SVD only | Ridge | 0.3668 | 0.3416 | 5.4055 | 3.8557 | 0.00992 |
| Industry + text | Ridge | 0.3296 | 0.3251 | 5.1073 | 4.3994 | 0.01076 |
| Industry only | Industry mean | 0.2924 | 0.0000 | 4.7084 | 0.0000 | 0.00913 |
| Dictionary only | Ridge | 0.2244 | 0.2465 | 2.9370 | 5.2660 | 0.00984 |
| Combined text | Ridge | 0.2395 | 0.2023 | 2.3457 | 1.3704 | 0.01932 |

最强的波动率排序证据来自 TF-IDF/SVD 文本表示，而不是纯行业基准。收益率目标证据明显更弱，不能解释为稳健股票收益 alpha。

---

## Bootstrap 置信区间

主 Rank IC 使用 seed 42 进行 2,000 次确定性 bootstrap：

| Estimand | Bootstrap method | Point | 95% CI | Zero p-value |
| --- | --- | ---: | --- | ---: |
| Raw Rank IC | Split bootstrap | 0.2395 | [-0.0050, 0.4841] | 0.111 |
| Raw Rank IC | Event-date bootstrap | 0.2395 | [0.0719, 0.3743] | 0.005 |
| Raw Rank IC | Ticker-cluster bootstrap | 0.2395 | [0.1091, 0.3522] | 0.001 |
| Industry-neutral Rank IC | Split bootstrap | 0.2023 | [-0.1157, 0.5202] | 0.117 |
| Industry-neutral Rank IC | Event-date bootstrap | 0.2023 | [-0.1546, 0.4273] | 0.366 |
| Industry-neutral Rank IC | Ticker-cluster bootstrap | 0.2023 | [-0.1787, 0.4181] | 0.357 |

原始主波动率 Rank IC 在 event-date 和 ticker-cluster bootstrap 下保持正向；split bootstrap 因只有 4 个 OOS split 而结论不明确。行业中性主 Rank IC 点估计为正，但 bootstrap 稳健性不足。

---

## 数据质量与 Parser Review

Parser quality review 覆盖 500 份 SEC 10-K 的 2,000 个 section：

| 项目 | 数量 |
| --- | ---: |
| Parsed section records | 2,000 |
| Manual-review records | 144 |
| Excluded section-level records | 144 |
| Short but included records | 494 |

- `item_1a` 和 `item_7` 低于 100 词时进入人工复核，并从对应 section-level 特征中排除。
- 核心 section 为 100 到 499 词时继续保留，但标记 warning。
- 较短的非核心 section 继续保留并披露。
- 排除异常 section 不会删除整份 filing；combined/full scope 由剩余合格 section 重建。

这降低了错误 section boundary 的风险，但数据仍属于 applied-grade parser pipeline，而不是逐份人工核验的 research-grade corpus。

---

## Pipeline

```text
SEC 10-K filings
-> section parsing and parser-quality review
-> event-time labels
-> rolling train / validation / test splits
-> embargo leakage control
-> dictionary tone + train-window-only TF-IDF/SVD
-> historical mean / industry mean / Ridge / XGBoost
-> feature ablation + industry-neutral diagnostics
-> OOS Rank IC + Newey-West + bootstrap
-> portfolio diagnostics
-> multiple testing + specification registry + audit
-> empirical report + factor card
```

---

## 研究设计控制

| 控制 | 实现 |
| --- | --- |
| Rolling validation/test | Rolling train / validation / test splits |
| Leakage control | Embargo purge 与 split leakage audit |
| Model selection | Validation-only Rank IC |
| TF-IDF leakage control | Train-window-only vocabulary |
| Tie handling | Tie-aware average-rank Rank IC |
| Constant prediction | 常数预测 Rank IC 强制为 0 |
| Incremental signal | Industry-neutral Rank IC |
| Feature contribution | Dictionary、TF-IDF/SVD、combined、industry、industry+text |
| Statistical uncertainty | Newey-West 与 bootstrap CI |
| Data snooping | 预注册主规格和多重检验 |
| Parser quality | 短 section 人工复核附录 |

---

## 使用边界

本版本是 applied-grade exploratory research run，不声称：

- 等同 CRSP/WRDS 的正式资产定价证据
- Survivorship-free research-grade universe
- 生产交易系统
- 已证明的可交易 alpha
- 投资建议

主要限制来自数据边界，而不是 pipeline failure：市场数据混用 FMP/Yahoo、selection-date market cap 属于 applied-grade estimates、股票池是固定 active-company panel、部分扩展诊断规格存在少量 parser/feature-vector 缺失。

---

## 推荐表述

> 在固定的 50-company applied-grade panel 中，SEC 10-K 文本特征对未来 20 日实现波动率提供探索性样本外排序证据。TF-IDF/SVD 表现最强，并保留正向行业中性诊断。收益率预测更弱，预注册组合检验不能证明可交易 alpha。

---

## License

代码使用 [MIT License](LICENSE)。公开结果仅用于研究展示；SEC 原始文件、授权市场数据、API key 和私有中间数据不提交。
