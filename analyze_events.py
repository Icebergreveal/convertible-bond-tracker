#!/usr/bin/env python3
import json
import pandas as pd
from collections import defaultdict

def analyze_event_chains():
    """分析事件链并导出CSV"""
    # 读取合并数据
    with open('outputs/extract_results/structured_data_merged.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"总记录数: {len(data)}")
    
    # 按债券分组
    bond_groups = defaultdict(list)
    for item in data:
        bond_code = item.get('bond_code')
        if bond_code:
            bond_groups[bond_code].append(item)
    
    print(f"\n债券数量: {len(bond_groups)}")
    
    # 分析事件链
    event_chains = []
    for bond_code, items in bond_groups.items():
        if len(items) >= 2:
            # 按日期排序
            sorted_items = sorted(items, key=lambda x: x.get('publish_date') or '9999-99-99')
            
            chain_info = {
                'bond_code': bond_code,
                'bond_name': sorted_items[0].get('bond_name', ''),
                'stock_code': sorted_items[0].get('stock_code', ''),
                'stock_name': sorted_items[0].get('stock_name', ''),
                'event_count': len(items),
                'first_event_date': sorted_items[0].get('publish_date', ''),
                'last_event_date': sorted_items[-1].get('publish_date', ''),
                'event_types': '; '.join([item.get('ann_type', '') for item in sorted_items]),
                'events': sorted_items
            }
            event_chains.append(chain_info)
    
    # 按事件数量排序
    event_chains.sort(key=lambda x: x['event_count'], reverse=True)
    
    print(f"\n存在事件链的债券数量: {len(event_chains)}")
    print("\n事件链详情:")
    for i, chain in enumerate(event_chains[:5], 1):
        print(f"\n{i}. {chain['bond_name']} ({chain['bond_code']})")
        print(f"   事件数: {chain['event_count']}")
        print(f"   时间跨度: {chain['first_event_date']} ~ {chain['last_event_date']}")
        print(f"   事件类型: {chain['event_types']}")
    
    # 导出为CSV
    df = pd.DataFrame(data)
    
    # 选择关键字段
    columns = [
        'doc_id', 'stock_code', 'stock_name', 'bond_code', 'bond_name',
        'ann_type', 'publish_date', 'trigger_rule', 'original_conv_price',
        'new_conv_price', 'effective_date', 'redemption_price', 'evidence_text'
    ]
    
    # 确保所有列都存在
    for col in columns:
        if col not in df.columns:
            df[col] = ''
    
    df = df[columns]
    
    # 按债券和日期排序
    df = df.sort_values(['bond_code', 'publish_date'])
    
    # 保存CSV
    csv_path = 'outputs/extract_results/最终抽取结果.csv'
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    
    print(f"\n数据已导出到: {csv_path}")
    print(f"CSV记录数: {len(df)}")
    
    return event_chains, df

if __name__ == "__main__":
    analyze_event_chains()