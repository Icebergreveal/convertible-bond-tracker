#!/usr/bin/env python3
import json
import os

def merge_all_results():
    extract_dir = 'outputs/extract_results'
    
    # 读取主文件
    all_data = []
    main_file = os.path.join(extract_dir, 'structured_data_merged_fixed.json')
    if os.path.exists(main_file):
        with open(main_file, 'r', encoding='utf-8') as f:
            all_data = json.load(f)
        print(f"读取主文件: {len(all_data)} 条")
    else:
        print(f"警告：主文件不存在")
        return
    
    # 读取reretry文件
    reretry_dirs = ['reretry_0', 'reretry_1', 'reretry_2']
    for dir_name in reretry_dirs:
        dir_path = os.path.join(extract_dir, dir_name)
        if os.path.exists(dir_path):
            files = os.listdir(dir_path)
            for filename in files:
                if filename.endswith('.json'):
                    file_path = os.path.join(dir_path, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        all_data.extend(data)
                    print(f"读取 {dir_name}/{filename}: {len(data)} 条")
    
    # 去重
    seen_ids = set()
    unique_data = []
    for item in all_data:
        doc_id = item.get('doc_id')
        if doc_id and doc_id not in seen_ids:
            seen_ids.add(doc_id)
            unique_data.append(item)
    
    print(f"\n合并前: {len(all_data)} 条")
    print(f"去重后: {len(unique_data)} 条")
    
    # 保存最终结果
    output_file = os.path.join(extract_dir, 'structured_data_merged_final.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(unique_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n最终结果已保存到: {output_file}")
    
    # 导出CSV
    try:
        import pandas as pd
        df = pd.DataFrame(unique_data)
        columns = ['doc_id', 'stock_code', 'stock_name', 'bond_code', 'bond_name',
                   'ann_type', 'publish_date', 'trigger_rule', 'original_conv_price',
                   'new_conv_price', 'effective_date', 'redemption_price', 'evidence_text']
        for col in columns:
            if col not in df.columns:
                df[col] = ''
        df = df[columns]
        df = df.sort_values(['bond_code', 'publish_date'])
        csv_path = os.path.join(extract_dir, '结构化数据最终结果.csv')
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"CSV已导出到: {csv_path}")
    except Exception as e:
        print(f"导出CSV失败: {e}")

if __name__ == "__main__":
    merge_all_results()