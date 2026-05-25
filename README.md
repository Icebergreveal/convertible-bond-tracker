# 可转债转股价下修与提前强赎双事件全生命周期跟踪及结构化分析

## 项目价值与目的

### 🎯 项目背景
可转债是上市公司重要的融资工具，转股价下修、提前强赎是其存续期内最核心的两大资本运作事件。目前巨潮资讯网相关公告分散、文本非结构化，人工整理耗时费力，难以快速梳理事件时间线、提取关键条款与价格数据。

### 💡 项目价值
1. **效率提升**：自动化处理替代人工整理，效率提升10倍以上
2. **数据标准化**：统一字段定义、日期格式、数值精度
3. **事件链构建**：自动匹配下修/强赎完整事件周期
4. **量化分析**：自动计算下修幅度、赎回溢价率等关键指标
5. **可追溯性**：每个字段都能回溯到公告原文证据

### 📊 应用场景
- 投资者：快速了解可转债重大事件，辅助投资决策
- 分析师：批量分析可转债条款，构建投资策略
- 监管者：监控可转债市场，发现异常行为
- 研究者：获取标准化数据，开展学术研究

---

## 技术路径

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  巨潮公告抓取   │ -> │   PDF文档解析   │ -> │   章节定位检查  │
│  (CNINFO API)  │    │   (MinerU API)  │    │  (Section Rules)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                     │                     │
         ▼                     ▼                     ▼
    metadata.csv          parsed_docs.jsonl      sections.jsonl
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               ▼
                    ┌─────────────────┐
                    │   LLM字段抽取   │
                    │  (Qwen/Qwen3)  │
                    └─────────────────┘
                               │
                               ▼
                    ┌─────────────────┐
                    │  Pydantic校验  │
                    └─────────────────┘
                               │
                               ▼
          ┌────────────────────┴────────────────────┐
          ▼                                         ▼
   ┌───────────────┐                        ┌───────────────┐
   │ 事件链匹配    │                        │ 量化指标计算  │
   │ (Event Chain)│                        │ (Indicators)  │
   └───────────────┘                        └───────────────┘
          │                                         │
          └────────────────────┬────────────────────┘
                               ▼
                    ┌─────────────────┐
                    │   人工评估报告  │
                    └─────────────────┘
```

### 技术栈

| 模块 | 技术 | 版本 | 说明 |
|---|---|---|---|
| 数据抓取 | requests | 2.31+ | 巨潮公告API调用 |
| PDF解析 | MinerU | latest | 专业PDF转Markdown |
| LLM调用 | OpenAI SDK | 1.0+ | 支持硅基流动等平台 |
| 数据校验 | Pydantic | 2.0+ | 结构化数据校验 |
| 配置管理 | PyYAML | 6.0+ | YAML配置文件解析 |
| 日志记录 | loguru | 0.7+ | 结构化日志 |
| 数据处理 | pandas | 2.0+ | 数据处理与分析 |

---

## 项目结构

```
项目2/
├── README.md                    # 项目说明文档
├── requirements.txt             # Python依赖清单
├── .env.example                # 环境变量模板
├── AGENTS.md                   # AI编码规则
├── topic_proposal.md           # 项目提案
├── crawl_spec.md               # 爬虫规范文档
├── difficulty_declaration.md   # 难度申请声明
├── workflow_design.md          # 工作流设计说明
├── eval_report_template.md     # 评估报告模板
├── ai_usage_statement.md       # AI使用声明
├── demo_script.md              # 演示脚本
├── ai_worklog_all.md           # AI工作日志

├── configs/                    # 配置文件目录
│   ├── crawl.yaml              # 爬虫配置
│   ├── model_config.yaml       # LLM模型配置
│   ├── section_rules.yaml      # 章节定位规则
│   └── workflow.yaml           # 工作流配置

├── data/                       # 数据目录
│   ├── metadata/               # 元数据目录
│   │   └── metadata.csv        # 公告元数据清单
│   ├── pdf/                    # PDF文件存储
│   └── parsed/                 # MinerU解析结果

├── prompts/                    # 提示词目录
│   └── extract_prompt.txt      # LLM抽取提示词

├── src/                        # 源代码目录
│   ├── __init__.py
│   ├── crawl/                  # 爬虫模块
│   │   ├── load_config.py      # 配置加载
│   │   ├── search_announcements.py # 公告搜索
│   │   ├── download_pdfs.py    # PDF下载
│   │   └── check_dataset.py    # 数据检查
│   ├── parse/                  # 解析模块
│   │   ├── mineru_batch_parse.py # MinerU批量解析
│   │   └── parse_check.py      # 解析质量检查
│   ├── section/                # 章节定位
│   │   └── route_sections.py   # Section路由
│   ├── schema/                 # Schema定义
│   │   └── schemas.py          # Pydantic模型
│   ├── extract/                # 字段抽取
│   │   ├── llm_extract.py      # LLM抽取
│   │   └── validate_results.py # 结果校验
│   ├── process/                # 数据处理
│   │   ├── standardize_data.py # 数据标准化
│   │   └── event_matching.py   # 事件链匹配
│   ├── indicator/              # 指标计算
│   │   └── calc_indicators.py  # 量化指标
│   └── eval/                   # 评估模块
│       └── gen_eval_template.py # 评估模板生成

├── pipeline_run.py             # 端到端工作流入口
└── outputs/                    # 输出目录
    ├── results/                # 抽取结果
    ├── event_chain/            # 事件链结果
    ├── indicators/             # 指标计算结果
    ├── eval/                   # 评估数据
    ├── reports/                # 报告文档
    └── logs/                   # 运行日志
```

---

## 核心功能

### 1. 公告抓取与元数据管理
- 自动搜索巨潮可转债公告
- 支持多关键词、多市场检索
- 生成标准化metadata.csv

### 2. PDF解析与章节定位
- MinerU专业PDF解析
- 智能识别目标章节（转股价格、赎回条款）
- 支持章节规则配置

### 3. 结构化字段抽取
- LLM驱动的智能抽取
- 17个核心字段定义
- 证据原文追溯

### 4. 事件链构建
- 下修四节点匹配：触发→提议→决议→实施
- 强赎四节点匹配：触发→决议→实施→摘牌
- 时间窗口约束匹配

### 5. 量化指标计算
- 下修幅度 = (原转股价 - 新转股价) / 原转股价 × 100%
- 赎回溢价率 = (赎回价格 - 100) / 100 × 100%
- 事件周期分析

---

## 快速开始

### 环境要求
- Python 3.10+
- 巨潮资讯网访问权限
- LLM API密钥（硅基流动/OpenAI等）
- MinerU API密钥

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，填入以下配置：
# - LLM_API_KEY
# - LLM_BASE_URL
# - LLM_MODEL
# - MINERU_API_KEY
```

### 运行项目

#### 单步运行
```bash
# 抓取公告（限制10条）
python pipeline_run.py --step crawl --limit 10

# PDF解析
python pipeline_run.py --step parse --limit 10

# 章节定位
python pipeline_run.py --step section

# LLM抽取
python pipeline_run.py --step extract --limit 10

# 事件链匹配
python pipeline_run.py --step process

# 指标计算
python pipeline_run.py --step indicator

# 生成评估模板
python pipeline_run.py --step eval
```

#### 完整运行
```bash
# 一键运行全部流程
python pipeline_run.py --step all --limit 10
```

---

## 输出文件说明

| 文件路径 | 说明 |
|---|---|
| `data/metadata/metadata.csv` | 公告元数据清单 |
| `data/pdf/*.pdf` | 下载的公告PDF |
| `data/parsed/*.md` | MinerU解析结果 |
| `outputs/extract_results/structured_data.json` | 结构化抽取结果 |
| `outputs/event_chain/event_chains.csv` | 事件链匹配结果 |
| `outputs/indicators/quantitative_indicators.csv` | 量化指标 |
| `outputs/eval/eval_manual_sample.csv` | 人工评估模板 |
| `outputs/logs/*.log` | 运行日志 |

---

## 字段定义

### 公共字段（10个）
| 字段 | 类型 | 说明 |
|---|---|---|
| doc_id | string | 公告唯一标识 |
| stock_code | string | 正股代码 |
| stock_name | string | 正股名称 |
| bond_code | string | 转债代码 |
| bond_name | string | 转债名称 |
| ann_type | string | 公告类型 |
| publish_date | date | 公告日期 |
| evidence_page | int | 证据页码 |
| evidence_text | string | 证据原文 |

### 下修专属字段（7个）
| 字段 | 类型 | 说明 |
|---|---|---|
| trigger_rule | string | 触发条件 |
| original_conv_price | float | 修正前转股价 |
| new_conv_price | float | 修正后转股价 |
| effective_date | date | 生效日期 |
| adjustment_ratio | float | 下修幅度(%) |

### 强赎专属字段（7个）
| 字段 | 类型 | 说明 |
|---|---|---|
| redemption_trigger | string | 强赎触发条件 |
| redemption_price | float | 赎回价格 |
| record_date | date | 登记日期 |
| last_convert_date | date | 最后转股日 |
| premium_rate | float | 赎回溢价率(%) |

---

## 项目进度与评估

### 难度档位
- **档位**：挑战档（1.1）
- **数据量**：150+ PDF公告，50+事件链
- **公告类型**：8种（下修4类+强赎4类）
- **字段数量**：17个结构化字段

### 评估指标
| 指标 | 目标值 |
|---|---|
| 数据质量 | ≥95% |
| 章节定位准确率 | ≥98% |
| 字段抽取准确率 | ≥90% |
| 证据完整性 | ≥95% |
| 事件链匹配准确率 | ≥95% |

---

## 合规说明

1. **数据来源**：仅使用巨潮资讯网公开可访问数据
2. **API Key安全**：存储在.env文件，不提交版本控制
3. **访问合规**：遵守robots.txt，设置合理请求间隔
4. **日志保留**：完整记录抓取和处理日志

---

## 许可证

MIT License

---

## 联系方式

如有问题或建议，请联系项目团队。