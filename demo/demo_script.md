# Demo Script: 华海转债证据链

## 现场开场

这一页我不现场重新跑全量数据，而是展示一条公告证据链：从巨潮公告 PDF、metadata、解析文本、section 定位、LLM 抽取、Pydantic 校验，到最终结构化结果和事件链。样本选择的是华海转债，债券代码 110076。

## 1. 原始 PDF 和 metadata

先看 `demo/PDF/1f0b8841d52d4d13.pdf`。这是华海药业关于向下修正“华海转债”转股价格暨转股停复牌的公告。

然后看 `demo/metadata/metadata_demo.csv`。这里可以看到同一个 `doc_id=1f0b8841d52d4d13`，对应股票代码 `600521`、转债代码 `110076`、转债简称 `华海转债`、公告标题、巨潮 PDF 链接，以及本地下载状态 `success`。这说明这个样本不是手工造的数据，而是从公告采集流程进入项目的真实公告。

## 2. 解析文本

接着打开 `demo/parsed/1f0b8841d52d4d13.md`。PDF 被解析成 Markdown 后，程序才能进行文本定位和字段抽取。这里有两个非常清楚的字段：

```text
债券代码：110076
修正前转股价格：33.06元/股
修正后转股价格：16.60元/股
```

现场不要重点讲生效日期那一行，因为当前解析文本里有 OCR 噪声；如果被问到，可以说明生效日期需要回到原始 PDF 做人工确认。

## 3. section 定位

然后打开 `demo/section/section_demo.json`。section 的作用是从整篇公告中定位真正和下修相关的段落，避免 LLM 读取大量历史调整、风险提示等无关内容。

这个 demo 里有四段定位结果：预触发、董事会提议、实施价格、审议与实施结果。比如 `6560c9ee54448a23` 的 section 匹配到“已有15个交易日”“审议通过”“提议向下修正”等关键词，因此可以判断它是 proposal 节点。

## 4. LLM 抽取和 Pydantic 校验

打开 `demo/extract/llm_extraction_demo.json`。这里展示的是已经通过校验的结构化字段，包括：

```text
bond_code = 110076
bond_name = 华海转债
original_conv_price = 33.06
new_conv_price = 16.6
trigger_rule = 连续交易日价格低于当期转股价格 80%
evidence_text = 对应公告原文片段
```

再打开 `demo/extract/pydantic_validation_demo.json`。LLM 的输出不是直接进最终表，而是先做 Pydantic 校验，检查必填字段、日期格式、数值字段和 evidence_text。这个 demo 的三条记录都能在 `records_validated.csv` 中找到，当前校验错误日志和警告日志都是 0 字节。

## 5. final result 和事件链

打开 `demo/final/final_result_demo.csv`。这里是最终结果表中的三条对应记录。实施公告这一行可以看到修正前转股价 `33.06`、修正后转股价 `16.6`、下修幅度 `49.77%`，并保留了 evidence_text。

最后打开 `demo/final/event_chain_demo.csv`。这里把多份公告合并成一条完整事件链：

```text
trigger -> proposal -> resolution -> implementation
```

也就是说，项目不只是抽取单份公告字段，还能把同一只转债在不同公告里的生命周期节点串起来。

## 6. 两个关键 evidence 解释

第一个字段是 `bond_code=110076`。证据来自解析文本中的“债券代码：110076”，这是公告正文里的明确字段，不是模型推断。

第二个字段是 `new_conv_price=16.60`。证据来自实施公告的重要内容提示“修正后转股价格：16.60元/股”。最终表里的 `new_conv_price=16.6` 与原文数值一致，只是在 CSV 中以数值形式展示。

如果老师继续追问，我会补充说明：当前 demo 解析文本里有少量 PDF 文本解析噪声，所以关键字段都保留 evidence_text，并且对日期类字段保留人工复核空间。
