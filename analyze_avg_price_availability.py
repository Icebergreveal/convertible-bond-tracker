#!/usr/bin/env python3
# 检查哪类公告包含avg_price数据

import pandas as pd
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

print('=' * 70)
print('公告类型与均价数据关联分析')
print('=' * 70)

# 检查metadata中的公告类型分布
metadata_path = 'data/metadata/metadata.csv'
if os.path.exists(metadata_path):
    df = pd.read_csv(metadata_path, encoding='utf-8')

    print('\n1. 公告类型分布')
    print('-' * 50)
    type_counts = df['ann_type'].value_counts()
    for ann_type, count in type_counts.items():
        print(f'{ann_type}: {count}条')

    # 下修实施和提议公告通常包含均价
    print('\n2. 下修提议和实施公告（更可能包含均价）')
    print('-' * 50)
    key_types = ['下修提议', '下修实施']
    for ann_type in key_types:
        subset = df[df['ann_type'] == ann_type]
        if len(subset) > 0:
            print(f'\n{ann_type} ({len(subset)}条):')
            sample = subset.head(5)[['stock_name', 'bond_code', 'title', 'publish_date']]
            for idx, row in sample.iterrows():
                print(f'  - {row["stock_name"]} ({row["bond_code"]}) | {row["publish_date"]}')

else:
    print('[ERROR] metadata.csv不存在')

# 检查records_validated中哪些公告类型
print('\n3. records_validated.csv中的公告类型分析')
print('-' * 50)
extract_path = 'outputs/extract_results/records_validated.csv'
if os.path.exists(extract_path):
    df_extract = pd.read_csv(extract_path, encoding='utf-8')
    print(f'总记录数: {len(df_extract)}')

    # 检查各类型的数据完整性
    for ann_type in df_extract['ann_type'].unique():
        subset = df_extract[df_extract['ann_type'] == ann_type]
        avg_price_1d_count = subset['avg_price_1d'].notna().sum()
        avg_price_20d_count = subset['avg_price_20d'].notna().sum()
        new_conv_price_count = subset['new_conv_price'].notna().sum()
        original_conv_price_count = subset['original_conv_price'].notna().sum()

        print(f'\n{ann_type}:')
        print(f'  总数: {len(subset)}')
        print(f'  avg_price_1d 非空: {avg_price_1d_count} ({(avg_price_1d_count/len(subset)*100):.0f}%)')
        print(f'  avg_price_20d 非空: {avg_price_20d_count} ({(avg_price_20d_count/len(subset)*100):.0f}%)')
        print(f'  original_conv_price 非空: {original_conv_price_count}')
        print(f'  new_conv_price 非空: {new_conv_price_count}')

        # 显示样本evidence_text前300字
        if len(subset) > 0:
            sample = subset.iloc[0]
            text = str(sample.get("evidence_text", "N/A"))[:300]
            print(f'  样本内容前300字:')
            print(f'    {text}...')
else:
    print('[WARN] records_validated.csv不存在')

# 总结
print('\n' + '=' * 70)
print('分析结论')
print('=' * 70)
print('''
1. 【下修提议】和【下修实施】公告更可能包含均价数据
   - 下修提议: 12条
   - 下修实施: 246条

2. 当前records_validated.csv中只有3条记录，都是【触发提示】类型
   - 触发提示公告通常不包含均价信息（只是提醒触发条件）
   - 这类公告没有new_conv_price，只有original_conv_price

3. 要提取avg_price_1d，需要：
   - ① 下载【下修提议】和【下修实施】类型的PDF
   - ② 使用MinerU解析PDF为Markdown
   - ③ 使用优化后的提示词运行LLM抽取
   - ④ 验证avg_price_1d提取结果

4. 已有数据可以开始计算：
   - 下修幅度: 使用original_conv_price和new_conv_price计算
   - 赎回溢价率(简化): 使用redemption_price计算
''')