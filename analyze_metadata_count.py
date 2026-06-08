#!/usr/bin/env python3
# 元数据记录数统计分析

import pandas as pd
import sys

sys.stdout.reconfigure(encoding='utf-8')

print('=' * 70)
print('元数据记录数统计分析')
print('=' * 70)

# 读取主元数据文件
metadata_path = 'data/metadata/metadata.csv'
df = pd.read_csv(metadata_path, encoding='utf-8')

print(f'\n📊 主文件统计')
print(f'   总行数: {len(df)}')
print(f'   列数: {len(df.columns)}')

print(f'\n📋 公告类型分布')
print('-' * 50)
type_counts = df['ann_type'].value_counts()
for ann_type, count in type_counts.items():
    print(f'   {ann_type}: {count}条')

print(f'\n📋 数据来源分布 (notes字段)')
print('-' * 50)
notes_counts = df['notes'].value_counts().head(10)
for note, count in notes_counts.items():
    print(f'   {note}: {count}条')

print(f'\n📋 市场分布')
print('-' * 50)
# 从URL判断市场
df['market'] = df['announcement_url'].apply(lambda x: '深交所' if 'szse' in x else '上交所' if 'sse' in x else '未知')
market_counts = df['market'].value_counts()
for market, count in market_counts.items():
    print(f'   {market}: {count}条')

print(f'\n📋 下载状态分布')
print('-' * 50)
status_counts = df['download_status'].value_counts()
for status, count in status_counts.items():
    print(f'   {status}: {count}条')

# 计算总数验证
total_count = len(df)
print(f'\n' + '=' * 70)
print(f'总记录数验证: {total_count}条')
print('=' * 70)

# 检查是否有重复数据
duplicate_count = df.duplicated('doc_id').sum()
print(f'\n重复记录数: {duplicate_count}条')
print(f'唯一记录数: {len(df.drop_duplicates("doc_id"))}条')