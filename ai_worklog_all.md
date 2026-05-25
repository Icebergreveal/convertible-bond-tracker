# AI Worklog - All Weeks

## Week 11 - Project Setup

### Task
创建项目骨架和基础文件

### Prompt
创建可转债转股价下修与提前强赎双事件分析项目的完整骨架

### AI Output
- README.md
- requirements.txt
- .env.example
- AGENTS.md
- configs/crawl.yaml
- configs/model_config.yaml
- configs/section_rules.yaml
- configs/workflow.yaml
- topic_proposal.md

### Verification
- 文件结构完整
- 配置文件格式正确
- 无硬编码API Key

## Week 12 - Crawl Module

### Task
开发巨潮公告爬虫与元数据管理系统

### Prompt
开发src/crawl/目录下的四个模块：load_config.py, search_announcements.py, download_pdfs.py, check_dataset.py

### AI Output
- src/crawl/load_config.py
- src/crawl/search_announcements.py
- src/crawl/download_pdfs.py
- src/crawl/check_dataset.py
- crawl_spec.md
- difficulty_declaration.md

### Verification
- python src/crawl/search_announcements.py --limit 10 运行成功
- python src/crawl/download_pdfs.py --limit 10 运行成功
- python src/crawl/check_dataset.py 运行成功

## Week 13 - Parse & Extract

### Task
开发MinerU解析、Section定位、LLM抽取与Pydantic校验

### Prompt
开发src/parse/, src/section/, src/schema/, src/extract/模块

### AI Output
- src/parse/mineru_batch_parse.py
- src/parse/parse_check.py
- src/section/route_sections.py
- src/schema/schemas.py
- src/extract/llm_extract.py
- src/extract/validate_results.py
- prompts/extract_prompt.txt

### Verification
- Schema定义完整
- 抽取流程可运行
- Pydantic校验生效

## Week 14-15 - Workflow & Evaluation

### Task
开发事件链匹配、指标计算、端到端工作流

### Prompt
开发src/process/, src/indicator/, src/eval/模块和pipeline_run.py

### AI Output
- src/process/standardize_data.py
- src/process/event_matching.py
- src/indicator/calc_indicators.py
- src/eval/gen_eval_template.py
- pipeline_run.py
- workflow_design.md
- eval_report_template.md
- ai_usage_statement.md
- demo_script.md

### Verification
- python pipeline_run.py --step all --limit 5 运行成功
- 事件链匹配正确
- 指标计算正确

## Issues Found & Fixed

1. **Issue**: 日期格式不统一
   - **Fix**: 添加parse_chinese_date函数统一日期格式

2. **Issue**: 数值精度不一致
   - **Fix**: 统一价格保留2位小数

3. **Issue**: 字段命名不统一
   - **Fix**: 制定字段命名规范

4. **Issue**: 缺少空值处理
   - **Fix**: 添加Optional类型和null处理逻辑

## Key Learning

1. AI生成代码需要严格审查
2. 金融文本需要精确的字段定义
3. 证据回溯是金融文本智能的核心
4. 工作流设计需要考虑可重跑性
5. 人工评估是验证结果的关键