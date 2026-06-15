# Demo Evidence Pack

本目录用于答辩 Demo，不用于现场重新跑全量流程。建议展示案例为 **华海转债（110076）转股价格下修完整链**。

## 文件清单

| 展示环节 | 文件 |
|---|---|
| 原始公告 PDF | `demo/PDF/43bb52461db6a3dd.pdf`、`demo/PDF/6560c9ee54448a23.pdf`、`demo/PDF/1f0b8841d52d4d13.pdf` |
| metadata 记录 | `demo/metadata/metadata_demo.csv` |
| PDF 解析文本 | `demo/parsed/*.md`、`demo/parsed/*.json` |
| section 定位 | `demo/section/section_demo.json` |
| LLM 抽取结果展示 | `demo/extract/llm_extraction_demo.json` |
| Pydantic 校验展示 | `demo/extract/pydantic_validation_demo.json` |
| 最终表格对应行 | `demo/final/final_result_demo.csv` |
| 完整事件链 | `demo/final/event_chain_demo.csv` |
| 字段证据说明 | `demo/evidence/evidence_notes.md` |
| 现场讲稿 | `demo/demo_script.md` |

## 推荐展示顺序

1. 打开 `demo/PDF/1f0b8841d52d4d13.pdf`，说明这是巨潮公告原始 PDF。
2. 打开 `demo/metadata/metadata_demo.csv`，指出 `doc_id`、`bond_code`、`bond_name`、`title`、`pdf_url` 和 `download_status=success`。
3. 打开 `demo/parsed/1f0b8841d52d4d13.md`，展示转债代码、修正前转股价格、修正后转股价格的解析文本。
4. 打开 `demo/section/section_demo.json`，说明 section 模块如何从全文中定位触发、提议、实施相关段落。
5. 打开 `demo/extract/llm_extraction_demo.json`，展示结构化字段和 evidence_text。
6. 打开 `demo/extract/pydantic_validation_demo.json`，说明 LLM 输出经过字段类型、日期格式、数值字段和 evidence 字段校验。
7. 打开 `demo/final/final_result_demo.csv`，展示最终表中的对应行。
8. 打开 `demo/final/event_chain_demo.csv`，展示 `trigger,proposal,resolution,implementation` 完整事件链。
9. 用 `demo/evidence/evidence_notes.md` 解释至少两个关键字段的 evidence。

## 口径提醒

- 当前 `demo/parsed/*.json` 中记录的 parser 是 `PyPDF2`，不是 MinerU。如果答辩要求必须展示 MinerU，请替换为真实 MinerU 解析产物；如果不替换，现场应表述为“PDF 解析后的 Markdown 文本”。
- `1f0b8841d52d4d13.md` 中生效日期行存在解析噪声，所以现场主讲 evidence 建议聚焦在 `bond_code`、`original_conv_price`、`new_conv_price` 和事件节点。
- `metadata_demo.csv` 是 demo 副本，已按本地 PDF 存在状态修正 `bond_code`、`event_stage` 和 `download_status`，便于现场展示。
