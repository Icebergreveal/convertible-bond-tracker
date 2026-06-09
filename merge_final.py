#!/usr/bin/env python3
import json
import os

def merge_all_results():
    """合并所有结果到最终文件"""
    extract_dir = 'outputs/extract_results'
    
    # 主文件路径
    main_file = os.path.join(extract_dir, 'structured_data_merged_fixed.json')
    
    # 所有reretry文件
    reretry_files = [
        os.path.join(extract_dir, f'rereretry_{i}', f'structured_data_reretry_{i}.json')
        for i in range(3)
    ]
    
    # 读取主文件
    all_data = []
    if os.path.exists(main_file):
        with open(main_file, 'r', encoding='utf-8') as f:
            all_data = json.load(f)
        print(f"读取主文件: {len(all_data)} 条")
    else:
        print(f"警告：主文件 {main_file} 不存在")
        return
    
    # 读取reretry文件
    for i, reretry_file in enumerate(reretry_files):
        if os.path.exists(reretry_file):
            with open(reretry_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_data.extend(data)
            print(f"读取 reretry_{i}: {len(data)} 条")
        else:
            print(f"警告：reretry_{i} 文件不存在")
    
    # 去重（基于doc_id）
    seen_ids = set()
    unique_data = []
    for item in all_data:
        doc_id = item.get('doc_id')
        if doc_id and doc_id not in seen_ids:
            seen_ids.add(doc_id)
            unique_data.append(item)
    
    # 统计信息
    print(f"\n合并前记录数: {len(all_data)}")
    print(f"去重后记录数: {len(unique_data)}")
    print(f"重复记录数: {len(all_data) - len(unique_data)}")
    
    # 保存最终结果
    output_file = os.path.join(extract_dir, 'structured_data_merged_final.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(unique_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n最终结果已保存到: {output_file}")
    
    # 导出为CSV
    try:
        import pandas as pd
        df = pd.DataFrame(unique_data)
        
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
        
        csv_path = os.path.join(extract_dir, '结构化数据最终结果.csv')
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"CSV已导出到: {csv_path}")
        
    except Exception as e:
        print(f"导出CSV失败: {e}")

if __name__ == "__main__":
    merge_all_results()