#!/usr/bin/env python3
import json
import os

def fix_merge():
    extract_dir = "outputs/extract_results"
    all_results = []
    
    # 读取所有原始chunk文件
    for chunk_idx in range(5):
        chunk_file = os.path.join(extract_dir, f"chunk_{chunk_idx}", f"structured_data_chunk_{chunk_idx}.json")
        if os.path.exists(chunk_file):
            with open(chunk_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_results.extend(data)
                print(f"读取 chunk_{chunk_idx}: {len(data)} 条")
    
    # 读取所有retry_chunk文件
    for chunk_idx in range(5):
        retry_file = os.path.join(extract_dir, f"retry_chunk_{chunk_idx}", f"structured_data_retry_chunk_{chunk_idx}.json")
        if os.path.exists(retry_file):
            with open(retry_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_results.extend(data)
                print(f"读取 retry_chunk_{chunk_idx}: {len(data)} 条")
    
    # 读取单独的retry文件
    retry_file = os.path.join(extract_dir, "retry", "structured_data_retry.json")
    if os.path.exists(retry_file):
        with open(retry_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            all_results.extend(data)
            print(f"读取 retry: {len(data)} 条")
    
    # 去重
    unique_results = []
    seen_ids = set()
    for item in all_results:
        doc_id = item.get('doc_id')
        if doc_id and doc_id not in seen_ids:
            seen_ids.add(doc_id)
            unique_results.append(item)
    
    print(f"\n合并后总记录: {len(all_results)}")
    print(f"去重后记录: {len(unique_results)}")
    
    # 保存到临时文件
    temp_path = os.path.join(extract_dir, "structured_data_merged_fixed.json")
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(unique_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n修复结果保存到: {temp_path}")
    return unique_results

if __name__ == "__main__":
    fix_merge()