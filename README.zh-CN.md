# 从 SEC 10-K 年报到波动率信号

[主 README](README.md) | [English](README.en.md)

## 项目定位

本仓库是一个面向金融文本因子研究的可审计、泄漏安全 agent pipeline。当前最适合回答的研究问题是：

> **10-K 文本信息能否预测未来 realized volatility？**

现有证据支持样本外波动率预测，不支持将项目表述为已经发现正式可交易的股票收益 alpha。

## 最突出成果

| Target | 最优模型 | ALL_SPLITS Rank IC | Rank IC NW t-stat |
| --- | --- | ---: | ---: |
| `CAR_1_20` | industry mean | 0.1698 | 3.539 |
| `CAR_1_5` | industry mean | 0.1834 | 4.524 |
| `realized_volatility_1_20` | **XGBoost** | **0.3899** | **21.32** |

预注册的主要预测规则也通过检验：
`realized_volatility_1_20 / Ridge`，Rank IC `0.3335`，p 值约为 `6.85e-11`。

预注册的主要组合规则在交易成本、行业中性、ALL_SPLITS 聚合和多重检验控制后没有通过：
Sharpe `-0.3602`，p 值 `0.4598`。

## 研究链路

```text
SEC 10-K 年报
  -> 事件时间 manifest 与 parser
  -> 防泄漏 label 与 rolling split
  -> dictionary tone、TF-IDF/SVD、metadata features
  -> historical mean、industry mean、Ridge、XGBoost
  -> 样本外 IC 与 portfolio diagnostics
  -> 多重检验报告、审计报告、实证报告
```

## 核心特点

- 审计 `available_time_utc`，并使用市场交易日历对齐事件日。
- TF-IDF 词表只允许在训练窗口拟合。
- 支持交易成本、行业中性、等权和市值加权组合诊断。
- 使用预注册主要规则和多重检验校正，降低结果挑选风险。
- 明确披露 public、licensed 和退市收益数据边界。

## 验证

```bash
python -m pip install -e ".[dev]"
python -m text_factor_lab run --config configs/text_factor_lab/e2e_smoke.yaml --execute
python -m pytest -q
python -m ruff check src scripts tests
```

## 研究边界

公开的 90-company 实验属于 exploratory / applied-grade。要完成 formal replication，仍需要 licensed survivorship-free universe、历史 entity links、delisting returns 和更严格的市场数据控制。

更多信息见 [working paper 定位](docs/working_paper_positioning.md) 与
[精炼结果摘要](docs/results/README.md)。

## 许可

本项目使用 [MIT License](LICENSE)。仓库仅用于研究和教学，不构成投资、交易、法律、会计或税务建议。
