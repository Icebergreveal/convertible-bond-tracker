#!/usr/bin/env python3
# 检查结构化抽取结果

import pandas as pd
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

print('=' * 70)
print('结构化抽取结果分析')
print('=' * 70)

# 检查文件是否存在
records_path = 'outputs/extract_results/records_validated.csv'
if not os.path.exists(records_path):
    print(f'\n❌ 文件不存在: {records_path}')
    print('   请先运行抽取: python pipeline_run.py --step extract --limit 50')
    sys.exit(1)

# 读取数据
df = pd.read_csv(records_path, encoding='utf-8')

print(f'\n📊 基本统计')
print(f'   总记录数: {len(df)}')
print(f'   字段数: {len(df.columns)}')

# 字段列表
all_fields = df.columns.tolist()
public_fields = ['doc_id', 'stock_code', 'stock_name', 'bond_code', 'bond_name', 'ann_type', 'publish_date']
down_fields = ['trigger_rule', 'original_conv_price', 'new_conv_price', 'pricing_base_date', 'avg_price_20d', 'avg_price_1d', 'effective_date', 'adjustment_ratio', 'adjustment_type']
redem_fields = ['redemption_trigger', 'redemption_price', 'record_date', 'last_convert_date', 'delisting_date', 'premium_rate']
evidence_fields = ['evidence_page', 'evidence_text', 'notes']

print(f'\n📋 字段统计 (公共字段: {len(public_fields)}个)')
print('-' * 50)

# 公共字段填充率
for field in public_fields:
    if field in df.columns:
        non_null = df[field].notna().sum()
        fill_rate = (non_null / len(df) * 100) if len(df) > 0 else 0
        status = '✅' if fill_rate > 50 else '⚠️' if fill_rate > 0 else '❌'
        print(f'   {status} {field}: {non_null}/{len(df)} ({fill_rate:.1f}%)')

print(f'\n📋 下修专属字段 ({len(down_fields)}个)')
print('-' * 50)
for field in down_fields:
    if field in df.columns:
        non_null = df[field].notna().sum()
        fill_rate = (non_null / len(df) * 100) if len(df) > 0 else 0
        status = '✅' if fill_rate > 50 else '⚠️' if fill_rate > 0 else '❌'
        print(f'   {status} {field}: {non_null}/{len(df)} ({fill_rate:.1f}%)')

print(f'\n📋 强赎专属字段 ({len(redem_fields)}个)')
print('-' * 50)
for field in redem_fields:
    if field in df.columns:
        non_null = df[field].notna().sum()
        fill_rate = (non_null / len(df) * 100) if len(df) > 0 else 0
        status = '✅' if fill_rate > 50 else '⚠️' if fill_rate > 0 else '❌'
        print(f'   {status} {field}: {non_null}/{len(df)} ({fill_rate:.1f}%)')

print(f'\n📋 证据字段 ({len(evidence_fields)}个)')
print('-' * 50)
for field in evidence_fields:
    if field in df.columns:
        non_null = df[field].notna().sum()
        fill_rate = (non_null / len(df) * 100) if len(df) > 0 else 0
        status = '✅' if fill_rate > 50 else '⚠️' if fill_rate > 0 else '❌'
        print(f'   {status} {field}: {non_null}/{len(df)} ({fill_rate:.1f}%)')

# 按公告类型统计
print(f'\n📊 公告类型分布')
print('-' * 50)
if 'ann_type' in df.columns:
    type_counts = df['ann_type'].value_counts()
    for ann_type, count in type_counts.items():
        print(f'   {ann_type}: {count}条')

# 总结
print(f'\n' + '=' * 70)
print('📈 总结')
print('=' * 70)

# 计算总体填充率
total_fields = len(public_fields) + len(down_fields) + len(redem_fields) + len(evidence_fields)
non_null_cells = 0
total_cells = len(df) * total_fields

for field in public_fields + down_fields + redem_fields + evidence_fields:
    if field in df.columns:
        non_null_cells += df[field].notna().sum()

overall_fill_rate = (non_null_cells / total_cells * 100) if total_cells > 0 else 0
print(f'\n   总体填充率: {non_null_cells}/{total_cells} ({overall_fill_rate:.1f}%)')
print(f'   记录数: {len(df)}条')
print(f'   字段数: {total_fields}个')

# 与metadata对比
metadata_path = 'data/metadata/metadata.csv'
if os.path.exists(metadata_path):
    metadata_df = pd.read_csv(metadata_path, encoding='utf-8')
    extract_rate = len(df) / len(metadata_df) * 100 if len(metadata_df) > 0 else 0
    print(f'   抽取覆盖率: {len(df)}/{len(metadata_df)} ({extract_rate:.1f}%)')