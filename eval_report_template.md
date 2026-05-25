# Evaluation Report

## 评估样本

- 样本总数：根据数据规模抽样10%
- 抽样方式：随机抽样
- 评估时间：项目完成阶段

## Data Quality

| 指标 | 数值 | 评估 |
|---|---|---|
| 总记录数 | | |
| 成功下载数 | | |
| 下载成功率 | | ≥95%为合格 |
| 重复记录数 | | 0为合格 |
| 公告类型覆盖 | | 8种齐全为合格 |

## Section Quality

| 指标 | 数值 | 评估 |
|---|---|---|
| 目标章节命中数 | | |
| 章节定位准确率 | | ≥98%为合格 |
| 错误定位数 | | |

## Extraction Quality

| 字段 | 准确率 | 缺失率 | 备注 |
|---|---|---|---|
| trigger_rule | | | |
| original_conv_price | | | |
| new_conv_price | | | |
| redemption_price | | | |
| dates | | | |

## Evidence Quality

| 指标 | 数值 | 评估 |
|---|---|---|
| evidence_text存在率 | | ≥95%为合格 |
| 证据页码正确性 | | ≥90%为合格 |
| 幻觉检测 | | 0为合格 |

## Pipeline Stability

| 指标 | 数值 | 评估 |
|---|---|---|
| 批处理成功率 | | ≥95%为合格 |
| 失败重试率 | | <5%为合格 |
| 平均耗时 | | 记录 |

## 错误分类

| 错误类型 | 数量 | 示例 | 修复策略 |
|---|---|---|---|
| data_error | | | |
| parse_error | | | |
| section_error | | | |
| prompt_error | | | |
| schema_error | | | |
| hallucination | | | |
| normalization_error | | | |
| workflow_error | | | |

## 优化前后对比

| 指标 | 优化前 | 优化后 | 提升 |
|---|---|---|---|
| 抽取准确率 | | | |
| 证据完整性 | | | |
| 工作流稳定性 | | | |

## 局限性

1. 仅覆盖可转债下修和强赎两类事件
2. 依赖MinerU解析质量
3. LLM存在一定幻觉风险
4. 复杂表格可能解析不全