# Workflow Design

## 项目目标

可转债转股价下修与提前强赎双事件全生命周期跟踪及结构化分析

## 总流程图

```
Collect → Audit → Parse → Inspect/Route → Extract → Validate → Match Events → Calculate Metrics → Report
```

## 节点表

| 节点 | 输入 | 输出 | 成功标准 | 失败处理 | 日志 |
|---|---|---|---|---|---|
| crawl | 配置文件 | metadata.csv | 成功获取公告列表 | 记录失败URL | crawl.log |
| download | metadata.csv | PDF文件 | 下载成功 | 记录失败原因 | download.log |
| audit | metadata + PDF | 质量报告 | 通过检查 | 标记问题记录 | dataset_check.log |
| parse | PDF文件 | Markdown文件 | 解析成功 | 记录解析失败 | parse.log |
| route_sections | Markdown + 规则 | 章节定位 | 找到目标章节 | 标记未找到 | section_analysis.log |
| extract | 章节内容 | 抽取结果 | 生成JSON | 记录LLM错误 | extract.log |
| validate | 抽取结果 | 校验结果 | Pydantic通过 | 记录校验错误 | validation_errors.jsonl |
| match_events | 标准化数据 | 事件链 | 匹配成功 | 标记不完整链 | event_chains.csv |
| calculate_indicators | 事件链 | 指标计算 | 计算完成 | 记录计算错误 | indicators.csv |
| report | 所有数据 | 评估报告 | 报告生成 | 记录报告错误 | eval_report.md |

## 人工检查点

1. 数据质量检查后抽样复核
2. Section定位结果抽查（≥10%）
3. 抽取结果人工评估（≥10%）
4. 事件链匹配结果检查

## 配置文件

- configs/workflow.yaml - 工作流参数配置
- configs/crawl.yaml - 抓取配置
- configs/model_config.yaml - LLM配置
- configs/section_rules.yaml - 章节规则

## 最小运行命令

```bash
python pipeline_run.py --config configs/crawl.yaml --step crawl --limit 10
python pipeline_run.py --config configs/crawl.yaml --step parse --limit 10
python pipeline_run.py --config configs/crawl.yaml --step all --limit 10
```

## 工作流模式说明

### 顺序流水线
基础模式，按顺序执行各节点

### 条件分支
根据公告类型（下修/强赎）选择不同抽取字段

### 失败重试
对不稳定节点（如PDF下载、LLM调用）进行有限重试

### Human-in-the-loop
Section定位和抽取结果需要人工抽样确认