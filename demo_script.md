# Demo Script

## 演示目标

展示可转债转股价下修与提前强赎双事件全生命周期跟踪项目的端到端流程。

## 演示步骤

### 步骤1：环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 API Key
```

### 步骤2：数据抓取

```bash
# 抓取公告列表（限制10条演示）
python pipeline_run.py --step crawl --limit 10

# 查看metadata
cat data/metadata/metadata.csv | head -5
```

### 步骤3：PDF解析与章节定位

```bash
# 解析PDF
python pipeline_run.py --step parse --limit 10

# 章节定位
python pipeline_run.py --step section
```

### 步骤4：字段抽取与校验

```bash
# LLM字段抽取
python pipeline_run.py --step extract --limit 10

# 查看抽取结果
cat outputs/extract_results/structured_data.json | python -m json.tool | head -50
```

### 步骤5：事件链匹配与指标计算

```bash
# 数据标准化与事件匹配
python pipeline_run.py --step process

# 查看事件链
cat outputs/event_chain/event_chains.csv | head -5

# 计算指标
python pipeline_run.py --step indicator

# 查看指标计算结果
cat outputs/indicators/quantitative_indicators.csv | head -5
```

### 步骤6：生成评估模板

```bash
python pipeline_run.py --step eval
cat outputs/eval/eval_manual_sample.csv | head -3
```

## 证据链演示

```
1. 原始PDF: data/pdf/{doc_id}.pdf
   ↓
2. MinerU解析: data/parsed/{doc_id}.md
   ↓
3. Section定位: outputs/logs/section_analysis.log
   ↓
4. LLM抽取: outputs/extract_results/structured_data.json
   ↓
5. Pydantic校验: outputs/extract_results/records_validated.csv
   ↓
6. 事件链匹配: outputs/event_chain/event_chains.csv
   ↓
7. 指标计算: outputs/indicators/quantitative_indicators.csv
```

## 关键展示点

1. **数据来源**：巨潮资讯网官方公告
2. **字段完整性**：17个结构化字段，包含证据原文
3. **事件链完整**：下修/强赎四节点匹配
4. **指标量化**：下修幅度、赎回溢价率计算
5. **可追溯性**：每个字段都能回溯到公告原文

## 预期输出

```
# 事件链示例
bond_code,bond_name,event_type,complete,nodes,adjustment_ratio
128089,傲农转债,adjustment,True,trigger,proposal,resolution,implementation,15.32

# 指标示例
bond_code,adjustment_ratio,premium_rate,cycle_check
128089,15.32,,NORMAL
```