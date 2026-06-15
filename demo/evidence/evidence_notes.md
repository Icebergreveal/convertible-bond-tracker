# Evidence Notes

## Demo 样本

- 事件：华海转债转股价格下修
- 转债代码：110076
- 股票代码：600521
- 股票简称：华海药业
- 样本公告：
  - `43bb52461db6a3dd`：预计触发提示
  - `6560c9ee54448a23`：董事会提议下修
  - `1f0b8841d52d4d13`：下修实施

## 关键字段证据

| 字段 | 结构化值 | 证据位置 | 证据说明 | 人工确认 |
|---|---:|---|---|---|
| `bond_code` | `110076` | `demo/parsed/1f0b8841d52d4d13.md` 第 2-3 行 | 公告抬头列出债券代码和债券简称。 | 通过 |
| `bond_name` | `华海转债` | `demo/parsed/1f0b8841d52d4d13.md` 第 3 行 | 公告抬头列出“债券简称：华海转债”。 | 通过 |
| `original_conv_price` | `33.06` | `demo/parsed/1f0b8841d52d4d13.md` 第 8-10 行 | 重要内容提示列出“修正前转股价格：33.06元/股”。 | 通过 |
| `new_conv_price` | `16.60` | `demo/parsed/1f0b8841d52d4d13.md` 第 8-10 行 | 重要内容提示列出“修正后转股价格：16.60元/股”。 | 通过 |
| `trigger` 节点 | 已触发/预计触发 | `demo/parsed/43bb52461db6a3dd.md` 第 53-54 行 | 文中说明已有 10 个交易日低于当期转股价格 80%，预计触发下修条件。 | 通过 |
| `proposal` 节点 | 董事会提议 | `demo/parsed/6560c9ee54448a23.md` 第 8-15 行 | 文中说明董事会审议通过并提议向下修正。 | 通过 |
| `implementation` 节点 | 实施下修 | `demo/parsed/1f0b8841d52d4d13.md` 第 141-152 行 | 文中说明董事会根据股东会授权，将转股价格由 33.06 元/股下修为 16.60 元/股。 | 通过 |

## 可展示的最终结果

- 抽取结果：`demo/extract/llm_extraction_demo.json`
- Pydantic 校验：`demo/extract/pydantic_validation_demo.json`
- 最终表格：`demo/final/final_result_demo.csv`
- 事件链：`demo/final/event_chain_demo.csv`

## 需要现场注意的质量问题

1. `demo/parsed/*.json` 记录的 parser 是 `PyPDF2`，不是 MinerU。若课程要求强制展示 MinerU，应替换真实 MinerU 解析文件；否则现场不要说“这是 MinerU 输出”。
2. `1f0b8841d52d4d13.md` 的生效日期文本存在解析噪声，现场不要把生效日期作为重点 evidence 字段。若老师问到，回到 PDF 原文做人工确认。
3. `final_result_demo.csv` 中部分 `evidence_page` 为空，这是正式输出仍需继续补强的点；demo 抽取 JSON 中加入了页面提示，但正式结果仍建议后续统一补齐 page_no。
4. `metadata_demo.csv` 中的 `publish_date` 是巨潮披露页日期；抽取结果中的日期可能来自公告正文或事件日期。答辩时不要混用二者，可以解释为“来源追踪日期”和“事件字段日期”口径不同。
