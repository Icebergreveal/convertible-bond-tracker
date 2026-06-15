# Evaluation Report - Final

## 评估样本

- 评估时间：2026-06-11
- 数据来源：巨潮资讯网公开公告，正式来源口径见 `DATA_PROVENANCE.md`
- 正式元数据：`data/metadata/metadata.csv`，1171 条
- 已校验抽取记录：`outputs/extract_results/records_validated.csv`，384 条
- 事件链结果：`outputs/event_chain/event_chains.csv`，169 条
- 量化指标结果：`outputs/indicators/quantitative_indicators.csv`，169 条

---

## 1. 数据质量概览

| 指标 | 当前值 | 依据文件 | 评估 |
|---|---:|---|---|
| 正式元数据记录 | 1171 条 | `data/metadata/metadata.csv` | 通过 |
| 已校验抽取记录 | 384 条 | `outputs/extract_results/records_validated.csv` | 通过 |
| 本地 PDF 文件 | 456 个 | `data/pdf/*.pdf` | 通过 |
| MinerU 解析 Markdown | 442 个 | `data/parsed/**/*.md` | 通过 |
| 事件链总数 | 169 条 | `outputs/event_chain/event_chains.csv` | 通过 |
| 量化指标记录 | 169 条 | `outputs/indicators/quantitative_indicators.csv` | 通过 |
| 四节点覆盖链 | 28 条 | `complete=true` | 待人工复核 |
| stage_unknown | 0 条 | `data/metadata/metadata.csv` | 已规则补全 |
| metadata 来源扫描违规 | 0 条 | CNINFO URL 与样例标记检查 | 通过 |

说明：384 条是“通过 Pydantic 校验的抽取记录”，不是 metadata 总量。

---

## 2. 抽取记录分布

| 公告大类 | 数量 | 占比 |
|---|---:|---:|
| 下修类公告 | 203 | 52.9% |
| 强赎类公告 | 181 | 47.1% |
| 合计 | 384 | 100.0% |

---

## 3. 字段完整率

### 3.1 公共字段完整率

| 字段名 | 填充数 | 总数 | 完整率 | 评估 |
|---|---:|---:|---:|---|
| doc_id | 384 | 384 | 100.0% | 通过 |
| stock_code | 352 | 384 | 91.7% | 待补充 |
| stock_name | 367 | 384 | 95.6% | 通过 |
| bond_code | 384 | 384 | 100.0% | 通过 |
| bond_name | 384 | 384 | 100.0% | 通过 |
| ann_type | 384 | 384 | 100.0% | 通过 |
| publish_date | 332 | 384 | 86.5% | 待补充 |
| evidence_text | 383 | 384 | 99.7% | 通过 |
| evidence_page | 243 | 384 | 63.3% | 待补充 |

### 3.2 下修类字段完整率

统计基数：203 条下修类公告。

| 字段名 | 填充数 | 总数 | 完整率 | 评估 |
|---|---:|---:|---:|---|
| original_conv_price | 174 | 203 | 85.7% | 待补充 |
| new_conv_price | 38 | 203 | 18.7% | 待补充 |
| trigger_rule | 200 | 203 | 98.5% | 通过 |
| adjustment_ratio | 25 | 203 | 12.3% | 待补充 |
| effective_date | 33 | 203 | 16.3% | 待补充 |
| pricing_base_date | 29 | 203 | 14.3% | 待补充 |

### 3.3 强赎类字段完整率

统计基数：181 条强赎类公告。

| 字段名 | 填充数 | 总数 | 完整率 | 评估 |
|---|---:|---:|---:|---|
| redemption_price | 146 | 181 | 80.7% | 待补充 |
| redemption_trigger | 116 | 181 | 64.1% | 待补充 |
| record_date | 122 | 181 | 67.4% | 待补充 |
| last_convert_date | 90 | 181 | 49.7% | 待补充 |
| delisting_date | 79 | 181 | 43.6% | 待补充 |
| premium_rate | 48 | 181 | 26.5% | 待补充 |

---

## 4. 事件链匹配结果

| 指标 | 数值 |
|---|---:|
| 事件链总数 | 169 |
| 下修事件链 | 121 |
| 强赎事件链 | 48 |
| 四节点覆盖链 | 28 |
| 四节点覆盖率 | 16.6% |
| 周期状态 NORMAL | 157 |
| 周期状态 LONG | 12 |

### 缺失节点分布

| missing_nodes | 数量 |
|---|---:|
| `<empty>` | 27 |
| resolution | 41 |
| proposal,resolution,implementation | 34 |
| proposal,resolution | 29 |
| resolution,implementation | 12 |
| resolution,implementation,result | 11 |
| resolution,result | 6 |
| implementation | 3 |
| trigger,implementation,result | 3 |
| trigger | 2 |
| implementation,result | 1 |

说明：当前事件链完整率低，主要原因是现有抽取记录多为单篇公告级信息，跨公告四节点闭环仍需要补充更多同一转债、同一事件周期内的公告。

---

## 5. 量化指标结果

| 指标 | 当前值 |
|---|---:|
| 下修幅度可计算记录 | 25 条 |
| 下修幅度均值 | 19.52% |
| 下修幅度范围 | -17.66% - 55.70% |
| 赎回溢价率可计算记录 | 48 条 |
| 赎回溢价率均值 | 2.82% |
| 赎回溢价率范围 | 0.33% - 15.00% |
| 周期检查 NORMAL | 61 条 |
| 周期检查 LONG | 12 条 |

说明：赎回溢价率中 48 条使用简化计算口径，即缺少转股价值时按转股价值 100 回退计算。下修幅度出现负值，说明仍有新旧转股价字段需要人工复核。

---

## 6. 人工评估状态

已补充 50 条公告级人工抽样复核，并完成 metadata 阶段分类规则扩展，结果文件如下：

| 文件 | 用途 |
|---|---|
| `outputs/eval/eval_manual_sample.csv` | 抽样样本与样本级人工结论 |
| `outputs/eval/manual_sample_review.csv` | 字段级复核记录，包含模型值、人工值、是否正确、错误类型 |
| `outputs/eval/manual_sample_review_summary.csv` | 维度级汇总统计 |
| `outputs/eval/manual_error_cases.md` | 典型错误公告、证据文本与修复建议 |
| `outputs/eval/stage_classification_summary.csv` | stage_unknown 规则补全与阶段分布 |
| `outputs/eval/stage_classification_review_queue.csv` | 阶段/范围/下载复核队列 |

### 阶段分类扩展

| 指标 | 数值 | 说明 |
|---|---:|---|
| 扩展前 stage_unknown | 700 | metadata 尚未细分阶段 |
| 本轮规则补充分阶段 | 700 | 依据 ann_type 与标题关键词 |
| 扩展后 stage_unknown | 0 | 已落入标准阶段 |
| 阶段复核队列 | 948 | 包含范围检查、重复 doc_id、本地 PDF 缺失等 |

### 人工抽样汇总

| 验证维度 | 完全正确 | 部分正确 | 错误/不匹配 | 严格准确率 | 结论 |
|---|---:|---:|---:|---:|---|
| 样本范围匹配 | 43 | 0 | 7 | 86.0% | 待过滤普通公司债 |
| 公告类型分类 | 38 | 12 | 0 | 76.0% | 大类可用，细分需复核 |
| 股票代码抽取 | 48 | 1 | 1 | 96.0% | 基本通过 |
| 转债/债券代码抽取 | 50 | 0 | 0 | 100.0% | 通过 |
| 日期字段内容准确性 | 44 | 5 | 1 | 88.0% | 待改进 |
| 价格数值严格准确性 | 33 | 16 | 1 | 66.0% | 待改进 |
| 证据文本相关性 | 47 | 2 | 1 | 94.0% | 基本通过 |

说明：人工样本扩大到 50 条后，代码和证据文本表现较稳定；价格数值、公告细分阶段和样本范围仍是主要优化点。严格准确率按 `TRUE` 单独计算，`PARTIAL` 不计入严格正确。

---

## 7. 错误与风险

| 问题 | 当前表现 | 优先级 |
|---|---|---|
| 事件链闭环需复核 | 四节点覆盖链 28/169，但尚未人工确认是否同一事件周期 | 高 |
| 证据页码不足 | evidence_page 填充率 63.3% | 高 |
| 下修实施字段不足 | new_conv_price、effective_date 填充率低 | 高 |
| 样本范围混入普通公司债 | 人工样本 7/50 需范围复核 | 高 |
| 阶段复核队列仍较大 | 948 条需做范围、重复或 PDF 缺失复核 | 高 |
| 价格精度压缩 | 多条赎回价被保留为 2 位小数 | 中 |
| 证据文本不完整 | 人工样本 3 条证据不足或阶段混用 | 中 |
| 强赎后续节点字段不足 | last_convert_date、delisting_date 填充率低 | 中 |
| 个别日期字段误抽 | 家联转债最后转股日被误填为赎回日 | 中 |

---

## 8. 结论

当前项目已经形成从 CNINFO metadata、PDF/Markdown、结构化抽取、Pydantic 校验、事件链匹配到指标计算的完整流程。真实数据口径下，正式 metadata 为 1171 条，已校验抽取记录为 384 条，事件链与指标记录均为 169 条。

本轮稳妥答辩版已完成两个关键补强：一是将 700 条 `stage_unknown` 规则补全为标准阶段，二是将人工抽样从 20 条扩展到 50 条。人工抽样显示，股票/债券代码和证据文本表现较好；主要问题集中在样本范围过滤、金额精度保留、公告细分阶段和事件链周期确认。后续优化重点不是扩大“看起来好看”的指标，而是继续复核阶段队列、提高 `evidence_page`、保留公告原始价格精度，并用人工复核结果回归测试抽取规则。
