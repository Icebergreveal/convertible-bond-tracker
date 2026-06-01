#!/usr/bin/env python3
# 检查LLM抽取状态并准备抽取更多数据

import os
import sys
import pandas as pd
import json

sys.stdout.reconfigure(encoding='utf-8')

print('=' * 70)
print('LLM抽取状态检查')
print('=' * 70)

# 1. 检查当前抽取结果
print('\n1. 当前抽取结果')
print('-' * 50)

extract_path = 'outputs/extract_results/records_validated.csv'
if os.path.exists(extract_path):
    df_extract = pd.read_csv(extract_path, encoding='utf-8')
    print(f'records_validated.csv 当前记录数: {len(df_extract)}')

    if len(df_extract) > 0:
        print('\n公告类型分布:')
        for ann_type, count in df_extract['ann_type'].value_counts().items():
            print(f'  - {ann_type}: {count}')

        print('\n各字段非空统计:')
        key_fields = ['stock_code', 'bond_code', 'new_conv_price', 'avg_price_1d', 'redemption_price']
        for field in key_fields:
            if field in df_extract.columns:
                non_null = df_extract[field].notna().sum()
                print(f'  - {field}: {non_null}/{len(df_extract)} ({(non_null/len(df_extract)*100):.0f}%)')
else:
    print('records_validated.csv 不存在')

# 2. 检查可用的Markdown文件
print('\n2. 可用的Markdown解析文件')
print('-' * 50)

parsed_dir = 'data/parsed'
if os.path.exists(parsed_dir):
    md_files = [f for f in os.listdir(parsed_dir) if f.endswith('.md')]
    print(f'Markdown文件总数: {len(md_files)}')

    # 检查哪些文件已经被抽取
    extracted_doc_ids = set()
    if os.path.exists(extract_path):
        df_extract = pd.read_csv(extract_path, encoding='utf-8')
        extracted_doc_ids = set(df_extract['doc_id'].tolist())

    print(f'已抽取的doc_id数: {len(extracted_doc_ids)}')

    # 统计各类型
    un抽取_files = []
    for md_file in md_files:
        doc_id = md_file.replace('.md', '')
        if doc_id not in extracted_doc_ids:
            un抽取_files.append(md_file)

    print(f'未抽取的Markdown文件: {len(un抽取_files)}')

    # 显示前10个未抽取文件
    if un抽取_files:
        print('\n前10个未抽取文件:')
        for f in un抽取_files[:10]:
            print(f'  - {f}')
else:
    print('data/parsed/ 目录不存在')

# 3. 检查structured_data.json
print('\n3. 检查structured_data.json')
print('-' * 50)

structured_path = 'outputs/extract_results/structured_data.json'
if os.path.exists(structured_path):
    with open(structured_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, list):
        print(f'structured_data.json 记录数: {len(data)}')
    else:
        print(f'structured_data.json 是字典，包含 {len(data)} 个键')
else:
    print('structured_data.json 不存在')

# 4. 总结
print('\n' + '=' * 70)
print('抽取准备总结')
print('=' * 70)

if os.path.exists(parsed_dir) and os.path.exists(extract_path):
    print(f'''
当前状态:
- records_validated.csv: {len(df_extract)} 条记录
- Markdown文件总数: {len(md_files)}
- 未抽取文件数: {len(un抽取_files)}

下一步:
如果要补充LLM抽取，可以运行:
  python pipeline_run.py --step extract --limit {min(50, len(un抽取_files))}

这将抽取最多 {min(50, len(un抽取_files))} 条新记录
''')