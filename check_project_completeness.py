#!/usr/bin/env python3
# 项目完整性检查

import os
import sys
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

print('=' * 70)
print('项目完整性检查报告')
print('=' * 70)

# 1. 检查数据文件
print('\n1. 数据文件完整性检查')
print('-' * 50)

data_files = {
    'data/metadata/metadata.csv': '元数据',
    'data/bonds/bond_list.csv': '转债列表',
}

for path, desc in data_files.items():
    exists = os.path.exists(path)
    status = '[OK]' if exists else '[MISSING]'
    if exists:
        try:
            df = pd.read_csv(path, encoding='utf-8')
            print(f'{status} {desc} ({path}): {len(df)}条记录')
        except:
            print(f'{status} {desc} ({path}): 存在但无法读取')
    else:
        print(f'{status} {desc} ({path})')

# 2. 检查PDF和解析文件
print('\n2. PDF和解析文件检查')
print('-' * 50)

pdf_count = 0
if os.path.exists('data/pdf'):
    pdf_count = len([f for f in os.listdir('data/pdf') if f.endswith('.pdf')])
print(f'PDF文件数量: {pdf_count}')

md_count = 0
if os.path.exists('data/parsed'):
    md_count = len([f for f in os.listdir('data/parsed') if f.endswith('.md')])
print(f'Markdown解析文件: {md_count}')

if pdf_count > 0:
    print(f'[OK] PDF文件已下载')
else:
    print('[WARN] 没有PDF文件，需要运行下载步骤')

# 3. 检查输出文件
print('\n3. 输出文件检查')
print('-' * 50)

output_files = {
    'outputs/extract_results/records_validated.csv': '抽取结果',
    'outputs/extract_results/structured_data.json': '结构化数据',
    'outputs/event_chain/event_chains.csv': '事件链',
    'outputs/indicators/quantitative_indicators.csv': '量化指标',
    'outputs/eval/eval_manual_sample.csv': '评估样本',
    'outputs/eval/auto_eval_report.json': '自动评估报告',
}

for path, desc in output_files.items():
    exists = os.path.exists(path)
    status = '[OK]' if exists else '[MISSING]'
    if exists:
        try:
            if path.endswith('.csv'):
                df = pd.read_csv(path, encoding='utf-8')
                print(f'{status} {desc}: {len(df)}条记录')
            else:
                print(f'{status} {desc}: 存在')
        except:
            print(f'{status} {desc}: 存在但无法读取')
    else:
        print(f'{status} {desc}')

# 4. 检查代码模块
print('\n4. 代码模块完整性检查')
print('-' * 50)

modules = {
    'src/crawl/search_announcements.py': '爬虫模块',
    'src/crawl/download_pdfs.py': '下载模块',
    'src/parse/mineru_batch_parse.py': '解析模块',
    'src/extract/llm_extract.py': '抽取模块',
    'src/process/event_matching.py': '事件匹配模块',
    'src/indicator/calc_indicators.py': '指标计算模块',
    'pipeline_run.py': '主流程',
}

for path, desc in modules.items():
    exists = os.path.exists(path)
    status = '[OK]' if exists else '[MISSING]'
    print(f'{status} {desc} ({path})')

# 5. 检查配置文件
print('\n5. 配置文件检查')
print('-' * 50)

config_files = {
    'configs/crawl.yaml': '爬虫配置',
    'configs/model_config.yaml': '模型配置',
    'configs/section_rules.yaml': '章节规则',
}

for path, desc in config_files.items():
    exists = os.path.exists(path)
    status = '[OK]' if exists else '[MISSING]'
    print(f'{status} {desc} ({path})')

# 6. 检查数据统计
print('\n6. 数据统计')
print('-' * 50)

if os.path.exists('data/metadata/metadata.csv'):
    df = pd.read_csv('data/metadata/metadata.csv', encoding='utf-8')
    print(f'元数据总记录: {len(df)}')
    print(f'公告类型数量: {df["ann_type"].nunique()}')

    print('\n各公告类型数量:')
    for ann_type, count in df['ann_type'].value_counts().items():
        print(f'  - {ann_type}: {count}')

# 7. 检查事件链和指标
print('\n7. 事件链和指标统计')
print('-' * 50)

if os.path.exists('outputs/event_chain/event_chains.csv'):
    df_chain = pd.read_csv('outputs/event_chain/event_chains.csv', encoding='utf-8')
    print(f'事件链总记录: {len(df_chain)}')
    print(f'事件类型分布:')
    for event_type, count in df_chain['event_type'].value_counts().items():
        print(f'  - {event_type}: {count}')

if os.path.exists('outputs/indicators/quantitative_indicators.csv'):
    df_ind = pd.read_csv('outputs/indicators/quantitative_indicators.csv', encoding='utf-8')
    print(f'\n量化指标记录: {len(df_ind)}')

    # 下修幅度统计
    adj_records = df_ind[df_ind['adjustment_ratio_calc'].notna()]
    if len(adj_records) > 0:
        print(f'下修幅度计算记录: {len(adj_records)}')

    # 赎回溢价率统计
    red_records = df_ind[df_ind['premium_rate_calc'].notna()]
    if len(red_records) > 0:
        print(f'赎回溢价率计算记录: {len(red_records)}')

# 8. 缺失步骤分析
print('\n' + '=' * 70)
print('缺失步骤分析')
print('=' * 70)

issues = []

# 检查是否需要下载PDF
if pdf_count == 0 and len(df) > 0:
    issues.append('缺少PDF文件，需要运行: python pipeline_run.py --step download')

# 检查是否需要解析PDF
if md_count == 0 and pdf_count > 0:
    issues.append('PDF未解析，需要运行: python pipeline_run.py --step parse')

# 检查抽取结果
if os.path.exists('outputs/extract_results/records_validated.csv'):
    df_extract = pd.read_csv('outputs/extract_results/records_validated.csv', encoding='utf-8')
    if len(df_extract) < 10:
        issues.append(f'抽取结果不足({len(df_extract)}条)，需要运行更多抽取')

# 检查avg_price_1d
if os.path.exists('outputs/extract_results/records_validated.csv'):
    df_extract = pd.read_csv('outputs/extract_results/records_validated.csv', encoding='utf-8')
    avg_count = df_extract['avg_price_1d'].notna().sum()
    if avg_count == 0:
        issues.append('avg_price_1d未提取（当前使用简化公式计算赎回溢价率）')

# 检查评估报告
if not os.path.exists('outputs/eval/eval_report.md'):
    issues.append('缺少人工评估报告(eval_report.md)')

# 检查README和workflow
if not os.path.exists('README.md'):
    issues.append('缺少README.md')
if not os.path.exists('workflow_design.md'):
    issues.append('缺少workflow_design.md')

if issues:
    print('\n发现以下问题:')
    for i, issue in enumerate(issues, 1):
        print(f'{i}. {issue}')
else:
    print('\n[OK] 所有基本步骤都已完成')

# 9. 下一步建议
print('\n' + '=' * 70)
print('下一步建议')
print('=' * 70)

print('''
根据当前项目状态，建议按以下顺序执行:

1. 【可选】补充更多数据
   python pipeline_run.py --step crawl --limit 100

2. 【重要】下载PDF文件
   python pipeline_run.py --step download --limit 100

3. 【重要】解析PDF
   python pipeline_run.py --step parse --limit 100

4. 【重要】运行LLM抽取
   python pipeline_run.py --step extract --limit 100

5. 【重要】运行事件链匹配
   python pipeline_run.py --step process

6. 【重要】计算量化指标
   python pipeline_run.py --step indicator

7. 【重要】生成评估报告
   python pipeline_run.py --step eval

8. 【完成】一键运行
   python pipeline_run.py --step all --limit 50
''')