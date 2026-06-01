#!/usr/bin/env python3
# avg_price_1d获取情况分析

import pandas as pd
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

print('=' * 70)
print('avg_price_1d 获取情况分析')
print('=' * 70)

# 1. 检查metadata中的公告类型分布
metadata_path = 'data/metadata/metadata.csv'
if os.path.exists(metadata_path):
    df = pd.read_csv(metadata_path, encoding='utf-8')
    print('\n1. 元数据公告类型分布')
    print('-' * 50)
    type_counts = df['ann_type'].value_counts()
    for ann_type, count in type_counts.items():
        print(f'{ann_type}: {count}条')

# 2. 检查records_validated中的avg_price提取情况
print('\n2. records_validated.csv 中 avg_price 提取情况')
print('-' * 50)
extract_path = 'outputs/extract_results/records_validated.csv'
if os.path.exists(extract_path):
    df_extract = pd.read_csv(extract_path, encoding='utf-8')
    print(f'总记录数: {len(df_extract)}')

    for ann_type in df_extract['ann_type'].unique():
        subset = df_extract[df_extract['ann_type'] == ann_type]
        avg_price_1d_count = subset['avg_price_1d'].notna().sum()
        avg_price_20d_count = subset['avg_price_20d'].notna().sum()
        new_conv_price_count = subset['new_conv_price'].notna().sum()

        print(f'\n{ann_type} ({len(subset)}条):')
        print(f'  avg_price_1d 非空: {avg_price_1d_count} ({(avg_price_1d_count/len(subset)*100):.0f}%)')
        print(f'  avg_price_20d 非空: {avg_price_20d_count} ({(avg_price_20d_count/len(subset)*100):.0f}%)')
        print(f'  new_conv_price 非空: {new_conv_price_count} ({(new_conv_price_count/len(subset)*100):.0f}%)')

# 3. 检查事件链数据中的avg_price
print('\n3. event_chains.csv 中 avg_price 情况')
print('-' * 50)
chain_path = 'outputs/event_chain/event_chains.csv'
if os.path.exists(chain_path):
    df_chain = pd.read_csv(chain_path, encoding='utf-8')
    print(f'总事件链数: {len(df_chain)}')

    avg_price_1d_count = df_chain['avg_price_1d'].notna().sum() if 'avg_price_1d' in df_chain.columns else 0
    avg_price_20d_count = df_chain['avg_price_20d'].notna().sum() if 'avg_price_20d' in df_chain.columns else 0

    print(f'avg_price_1d 非空: {avg_price_1d_count}')
    print(f'avg_price_20d 非空: {avg_price_20d_count}')

# 4. 检查强赎公告类型
print('\n4. 强赎类型公告分析（可能包含赎回价格和均价）')
print('-' * 50)
if os.path.exists(metadata_path):
    df = pd.read_csv(metadata_path, encoding='utf-8')
    redemption_types = ['强赎触发提示', '强赎决议', '强赎实施', '强赎结果']

    for ann_type in redemption_types:
        subset = df[df['ann_type'] == ann_type]
        if len(subset) > 0:
            print(f'\n{ann_type} ({len(subset)}条):')
            sample = subset.head(2)[['stock_name', 'bond_code', 'title', 'publish_date']]
            for idx, row in sample.iterrows():
                print(f'  - {row["stock_name"]} ({row["bond_code"]}) | {row["publish_date"]}')

# 5. 下修提议和实施公告
print('\n5. 下修提议和实施公告分析（可能包含均价和转股价）')
print('-' * 50)
if os.path.exists(metadata_path):
    df = pd.read_csv(metadata_path, encoding='utf-8')
    key_types = ['下修提议', '下修实施']

    for ann_type in key_types:
        subset = df[df['ann_type'] == ann_type]
        if len(subset) > 0:
            print(f'\n{ann_type} ({len(subset)}条):')
            sample = subset.head(3)[['stock_name', 'bond_code', 'title', 'publish_date']]
            for idx, row in sample.iterrows():
                print(f'  - {row["stock_name"]} ({row["bond_code"]}) | {row["publish_date"]}')

# 6. 总结
print('\n' + '=' * 70)
print('avg_price_1d 获取情况总结')
print('=' * 70)
print('''
当前状态: avg_price_1d 未被成功提取

原因分析:
1. records_validated.csv 中只有3条记录（都是下修触发提示类型）
2. 下修触发提示公告通常不包含均价信息
3. 均价信息更可能出现在【下修提议】和【下修实施】公告中

可获取avg_price_1d的公告类型:
  - 下修提议: 12条 (可能包含)
  - 下修实施: 246条 (可能包含)

可获取redemption_price的公告类型:
  - 强赎触发提示: 192条 (可能包含)
  - 强赎决议: 48条 (可能包含)
  - 强赎实施: 5条 (可能包含)
  - 强赎结果: 395条 (可能包含)

下一步:
1. 下载下修提议(12条)和下修实施(246条)的PDF
2. 使用MinerU解析PDF
3. 使用优化后的提示词进行LLM抽取
4. 验证avg_price_1d提取结果
''')