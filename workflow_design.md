# Workflow Design

## 项目目标

可转债转股价下修与提前强赎双事件全生命周期跟踪及结构化分析

## 总流程图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           可转债事件分析完整流程                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  数据   │ -> │  公告   │ -> │  PDF    │ -> │  章节   │ -> │  LLM    │
│  抓取   │    │  下载   │    │  解析   │    │  定位   │    │  抽取   │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
     │              │              │              │              │
     ▼              ▼              ▼              ▼              ▼
metadata.csv    PDF文件      Markdown      sections.json   structured_data
     │              │              │              │              │
     └──────────────┴──────────────┴──────────────┴──────────────┘
                                │
                                ▼
                    ┌─────────────────────┐
                    │    Pydantic校验     │
                    └─────────────────────┘
                                │
              ┌─────────────────┴─────────────────┐
              ▼                                   ▼
      ┌───────────────┐                  ┌───────────────┐
      │   事件链匹配   │                  │  量化指标计算  │
      └───────────────┘                  └───────────────┘
              │                                   │
              └───────────────┬───────────────────┘
                              ▼
                    ┌─────────────────┐
                    │    评估报告     │
                    └─────────────────┘
```

## 详细工作流节点

### 节点1: 数据抓取 (crawl)

| 属性 | 说明 |
|---|---|
| **输入** | configs/crawl.yaml (关键词、市场、日期范围) |
| **输出** | data/metadata/metadata.csv |
| **处理逻辑** | 1. 构建巨潮API请求<br>2. 遍历8种公告类型<br>3. 合并去重<br>4. 保存元数据 |
| **成功标准** | 获取≥100条有效记录 |
| **失败处理** | 记录失败URL，保留样本数据 |
| **日志文件** | outputs/logs/crawl_download.log |

### 节点2: 公告下载 (download)

| 属性 | 说明 |
|---|---|
| **输入** | data/metadata/metadata.csv |
| **输出** | data/pdf/*.pdf |
| **处理逻辑** | 1. 读取待下载URL<br>2. 下载PDF文件<br>3. 更新download_status |
| **成功标准** | 下载成功率≥90% |
| **失败处理** | 标记pending状态，可重试 |
| **日志文件** | outputs/logs/crawl_download.log |

### 节点3: PDF解析 (parse)

| 属性 | 说明 |
|---|---|
| **输入** | data/pdf/*.pdf |
| **输出** | data/parsed/*.md |
| **处理逻辑** | 1. 调用MinerU API<br>2. PDF转Markdown<br>3. 存储解析结果 |
| **成功标准** | 解析成功率≥95% |
| **失败处理** | 使用备用解析器或标记失败 |
| **日志文件** | outputs/logs/parse_quality.log |

### 节点4: 章节定位 (route_sections)

| 属性 | 说明 |
|---|---|
| **输入** | data/parsed/*.md + configs/section_rules.yaml |
| **输出** | outputs/sections.jsonl |
| **处理逻辑** | 1. 识别下修/强赎相关章节<br>2. 提取关键段落<br>3. 标记章节类型 |
| **成功标准** | 章节识别准确率≥98% |
| **失败处理** | 标记未识别，依赖全文抽取 |
| **日志文件** | outputs/logs/section_analysis.log |

### 节点5: LLM字段抽取 (extract)

| 属性 | 说明 |
|---|---|
| **输入** | sections.jsonl + src/extract/extract_prompt_optimized.txt |
| **输出** | outputs/extract_results/structured_data.json |
| **处理逻辑** | 1. 构建抽取提示词<br>2. 调用LLM API<br>3. 解析JSON结果<br>4. 提取17个核心字段 |
| **成功标准** | 字段抽取完整率≥90% |
| **失败处理** | 重试3次，记录失败记录 |
| **日志文件** | outputs/logs/extract_quality.log |

### 节点6: Pydantic校验 (validate)

| 属性 | 说明 |
|---|---|
| **输入** | outputs/extract_results/structured_data.json |
| **输出** | outputs/extract_results/records_validated.csv |
| **处理逻辑** | 1. 加载Pydantic模型<br>2. 逐条校验字段<br>3. 输出校验报告 |
| **成功标准** | 校验通过率≥95% |
| **失败处理** | 详细记录错误类型 |
| **日志文件** | outputs/logs/validation_errors.jsonl |

### 节点7: 事件链匹配 (match_events)

| 属性 | 说明 |
|---|---|
| **输入** | outputs/extract_results/records_validated.csv |
| **输出** | outputs/event_chain/event_chains.csv |
| **处理逻辑** | 1. 按转债代码分组<br>2. 按时间排序公告<br>3. 匹配四阶段事件<br>4. 标记完整/不完整链 |
| **成功标准** | 事件链匹配准确率≥95% |
| **失败处理** | 标记不完整链，供人工复核 |
| **日志文件** | outputs/logs/event_matching.log |

### 节点8: 量化指标计算 (calculate_indicators)

| 属性 | 说明 |
|---|---|
| **输入** | outputs/event_chain/event_chains.csv |
| **输出** | outputs/indicators/quantitative_indicators.csv |
| **处理逻辑** | 1. 下修幅度计算<br>2. 赎回溢价率计算<br>3. 事件周期分析 |
| **成功标准** | 指标计算完成率100% |
| **失败处理** | 标记计算异常 |
| **日志文件** | outputs/logs/indicator_calc.log |

### 节点9: 评估报告 (eval_report)

| 属性 | 说明 |
|---|---|
| **输入** | outputs/indicators/quantitative_indicators.csv |
| **输出** | outputs/eval/eval_report.md |
| **处理逻辑** | 1. 统计各项指标<br>2. 生成评估报告<br>3. 人工复核 |
| **成功标准** | 报告生成完整 |
| **失败处理** | 记录错误 |
| **日志文件** | outputs/eval/auto_eval_report.json |

## 公告类型处理矩阵

| 公告类型 | 代码 | 下修字段 | 强赎字段 | 关键信息 |
|---|---|---|---|---|
| 下修触发提示 | 1001 | trigger_rule | - | 触发条件 |
| 下修提议 | 1002 | trigger_rule, original_conv_price | - | 提议下修 |
| 下修决议 | 1003 | trigger_rule, original_conv_price | - | 股东大会通过 |
| 下修实施 | 1004 | trigger_rule, original_conv_price, new_conv_price | - | 正式调整 |
| 强赎触发提示 | 2001 | - | redemption_trigger | 触发条件 |
| 强赎决议 | 2002 | - | redemption_trigger, redemption_price | 决定赎回 |
| 强赎实施 | 2003 | - | redemption_trigger, redemption_price, record_date | 开始执行 |
| 强赎结果 | 2004 | - | redemption_trigger, redemption_price, delisting_date | 完成赎回 |

## 运行命令详解

### 一键运行（推荐用于演示）

```bash
# 完整流程：抓取→下载→解析→抽取→校验→匹配→计算
python pipeline_run.py --step all --limit 50
```

### 分步运行（推荐用于调试）

```bash
# Step 1: 抓取公告元数据
python pipeline_run.py --step crawl --limit 50

# Step 2: 下载PDF文件
python pipeline_run.py --step download --limit 50

# Step 3: 解析PDF为Markdown
python pipeline_run.py --step parse --limit 50

# Step 4: 章节定位
python pipeline_run.py --step section

# Step 5: LLM字段抽取
python pipeline_run.py --step extract --limit 50

# Step 6: 数据校验
python pipeline_run.py --step validate

# Step 7: 事件链匹配
python pipeline_run.py --step process

# Step 8: 指标计算
python pipeline_run.py --step indicator

# Step 9: 生成评估报告
python pipeline_run.py --step eval
```

### 快速测试

```bash
# 测试3条记录
python pipeline_run.py --step all --limit 3

# 仅测试爬虫
python pipeline_run.py --step crawl --limit 10
```

### 查看结果

```bash
# 查看抽取结果
cat outputs/extract_results/records_validated.csv

# 查看事件链
cat outputs/event_chain/event_chains.csv

# 查看量化指标
cat outputs/indicators/quantitative_indicators.csv

# 查看评估报告
cat outputs/eval/eval_report.md
```

## 配置文件说明

### configs/crawl.yaml

```yaml
crawl:
  keywords:
    down: ["向下修正转债转股价格", "转股价格向下修正实施"]
    redemption: ["提前赎回", "强赎", "赎回安排"]
  markets:
    - szse
    - sse
  date_range:
    start: "2024-01-01"
    end: "2026-12-31"
  rate_limit: 1.0  # 请求间隔（秒）
```

### configs/model_config.yaml

```yaml
llm:
  provider: siliconflow
  base_url: https://api.siliconflow.cn/v1
  model: Qwen/Qwen3-8B
  temperature: 0
  max_tokens: 2048
```

### configs/section_rules.yaml

```yaml
rules:
  down_adjustment:
    keywords: ["转股价格", "向下修正", "下修"]
    required_sections: ["触发条件", "修正方案", "生效日期"]
  redemption:
    keywords: ["赎回", "强赎", "触发"]
    required_sections: ["赎回条件", "赎回价格", "登记日"]
```

## 人工检查点

| 检查点 | 检查内容 | 抽样比例 | 通过标准 |
|---|---|---|---|
| 1. 数据抓取 | 公告标题、日期、公司信息 | 5% | 无错误 |
| 2. PDF下载 | 文件完整性、可读性 | 10% | ≥95%可读 |
| 3. 章节定位 | 关键段落识别准确性 | 10% | ≥98%准确 |
| 4. 字段抽取 | 数值准确性、完整性 | 10% | ≥90%准确 |
| 5. 事件链匹配 | 节点完整性、时间顺序 | 20% | ≥95%准确 |

## 失败处理策略

| 节点 | 失败策略 | 重试次数 |
|---|---|---|
| crawl | 降级到样本数据 | 3 |
| download | 标记pending，后续重试 | 3 |
| parse | 使用备用解析器 | 2 |
| extract | 重试+记录 | 3 |
| validate | 详细错误记录 | 1 |
| process | 标记不完整链 | 1 |
| indicator | 标记异常 | 1 |

## 工作流监控

### 查看运行日志

```bash
# 实时查看爬虫日志
tail -f outputs/logs/crawl_download.log

# 查看错误日志
grep -i ERROR outputs/logs/*.log

# 查看今日日志
cat outputs/logs/$(date +%Y%m%d).log
```

### 查看处理进度

```bash
# 查看PDF下载进度
wc -l data/pdf/*.pdf 2>/dev/null | tail -1

# 查看解析进度
wc -l data/parsed/*.md 2>/dev/null | tail -1

# 查看抽取进度
wc -l outputs/extract_results/structured_data.json
```

## 快速开始

### 1. 克隆项目
```bash
git clone <repository_url>
cd 项目2
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置环境变量
```bash
cp .env.example .env
# 编辑.env填入API密钥
```

### 4. 一键运行
```bash
python pipeline_run.py --step all --limit 50
```

### 5. 查看结果
```bash
python -m src.eval.gen_eval_template
cat outputs/eval/eval_report.md
```
