#!/usr/bin/env python3
# 检查赎回溢价率计算的可行性

import pandas as pd
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

print('=' * 70)
print('赎回溢价率计算可行性分析')
print('=' * 70)

# 检查metadata.csv中的强赎类型公告
metadata_path = 'data/metadata/metadata.csv'
if os.path.exists(metadata_path):
    df = pd.read_csv(metadata_path, encoding='utf-8')

    print('\n1. 元数据中的强赎类型公告')
    print('-' * 50)

    redemption_types = ['强赎触发提示', '强赎决议', '强赎实施', '强赎结果']
    for ann_type in redemption_types:
        subset = df[df['ann_type'] == ann_type]
        print(f'{ann_type}: {len(subset)}条')

    # 检查records_validated.csv中的数据
    print('\n2. 抽取结果中的公告类型')
    print('-' * 50)
    extract_path = 'outputs/extract_results/records_validated.csv'
    if os.path.exists(extract_path):
        df_extract = pd.read_csv(extract_path, encoding='utf-8')
        print(f'总记录数: {len(df_extract)}')

        for ann_type in df_extract['ann_type'].unique():
            subset = df_extract[df_extract['ann_type'] == ann_type]
            redemption_price_count = subset['redemption_price'].notna().sum()
            print(f'{ann_type}: {len(subset)}条 (有redemption_price: {redemption_price_count})')

    # 检查事件链数据
    print('\n3. 事件链数据')
    print('-' * 50)
    event_chain_path = 'outputs/event_chain/event_chains.csv'
    if os.path.exists(event_chain_path):
        df_chain = pd.read_csv(event_chain_path, encoding='utf-8')
        print(f'总事件链数: {len(df_chain)}')
        print(f'\n事件类型分布:')
        print(df_chain['event_type'].value_counts())

        # 检查有redemption_price的事件
        redemption_records = df_chain[df_chain['redemption_price'].notna()]
        print(f'\n有redemption_price的事件: {len(redemption_records)}')

        if len(redemption_records) > 0:
            print('\n样本数据:')
            for idx, row in redemption_records.head(5).iterrows():
                print(f"  - {row['bond_name']} ({row['bond_code']}) | redemption_price: {row['redemption_price']}")

    # 检查量化指标数据
    print('\n4. 量化指标计算结果')
    print('-' * 50)
    indicators_path = 'outputs/indicators/quantitative_indicators.csv'
    if os.path.exists(indicators_path):
        df_ind = pd.read_csv(indicators_path, encoding='utf-8')
        print(f'总记录数: {len(df_ind)}')

        # 检查赎回溢价率计算
        redemption_records = df_ind[df_ind['redemption_price'].notna()]
        print(f'有redemption_price的记录: {len(redemption_records)}')

        if len(redemption_records) > 0:
            print('\n样本数据:')
            for idx, row in redemption_records.head(5).iterrows():
                print(f"  - {row['bond_name']} ({row['bond_code']})")
                print(f"    redemption_price: {row['redemption_price']}")
                print(f"    premium_rate_calc: {row['premium_rate_calc']}")
                print(f"    calc_method: {row.get('calc_method', 'N/A')}")
        else:
            print('\n没有有redemption_price的记录，无法计算赎回溢价率')

            # 检查calc_indicators.py中的计算逻辑
            print('\n检查计算代码...')
            calc_path = 'src/indicator/calc_indicators.py'
            if os.path.exists(calc_path):
                with open(calc_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    has_avg_price_1d = 'avg_price_1d' in content
                    has_conversion_value = 'conversion_value' in content
                    has_calc_method = 'calc_method' in content
                    print(f'包含avg_price_1d: {has_avg_price_1d}')
                    print(f'包含conversion_value: {has_conversion_value}')
                    print(f'包含calc_method: {has_calc_method}')
    else:
        print('quantitative_indicators.csv不存在')

# 总结
print('\n' + '=' * 70)
print('赎回溢价率计算状态')
print('=' * 70)

print('''
当前状态: ⚠️ 无法正常计算赎回溢价率

原因:
1. records_validated.csv中只有3条记录，全部是下修类型
2. 这3条记录都没有redemption_price字段
3. 没有强赎类型的公告被抽取

解决方案:
1. 需要抽取更多强赎类型的公告（强赎触发提示/决议/实施/结果）
2. 从这些公告中提取redemption_price
3. 如果公告中有avg_price_1d，则使用精确计算
4. 否则使用简化计算（假设转股价值=100）

下一步:
- 从metadata.csv中筛选强赎类型公告
- 下载PDF并解析
- 运行LLM抽取提取redemption_price
- 重新计算赎回溢价率
''')