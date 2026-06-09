#!/usr/bin/env python3
import json
import os

def merge_all_results():
    """合并所有抽取结果，包括重试结果"""
    extract_dir = "outputs/extract_results"
    
    all_results = []
    
    # 读取主chunk文件
    for chunk_idx in range(5):
        chunk_file = os.path.join(extract_dir, f"chunk_{chunk_idx}", f"structured_data_chunk_{chunk_idx}.json")
        if os.path.exists(chunk_file):
            try:
                with open(chunk_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    all_results.extend(data)
                    print(f"读取 chunk_{chunk_idx}: {len(data)} 条记录")
            except Exception as e:
                print(f"读取 chunk_{chunk_idx} 失败: {e}")
    
    # 读取retry_chunk文件
    for chunk_idx in range(5):
        retry_file = os.path.join(extract_dir, f"retry_chunk_{chunk_idx}", f"structured_data_retry_chunk_{chunk_idx}.json")
        if os.path.exists(retry_file):
            try:
                with open(retry_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    all_results.extend(data)
                    print(f"读取 retry_chunk_{chunk_idx}: {len(data)} 条记录")
            except Exception as e:
                print(f"读取 retry_chunk_{chunk_idx} 失败: {e}")
    
    # 读取单独的重试文件
    retry_file = os.path.join(extract_dir, "retry", "structured_data_retry.json")
    if os.path.exists(retry_file):
        try:
            with open(retry_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_results.extend(data)
                print(f"读取 retry: {len(data)} 条记录")
        except Exception as e:
            print(f"读取 retry 失败: {e}")
    
    # 去重（基于doc_id）
    unique_results = []
    seen_ids = set()
    for item in all_results:
        doc_id = item.get('doc_id')
        if doc_id and doc_id not in seen_ids:
            seen_ids.add(doc_id)
            unique_results.append(item)
    
    print(f"\n合并后总记录数: {len(all_results)}")
    print(f"去重后记录数: {len(unique_results)}")
    print(f"去重数量: {len(all_results) - len(unique_results)}")
    
    # 保存合并结果
    output_path = os.path.join(extract_dir, "structured_data_merged.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(unique_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n合并结果已保存到: {output_path}")
    
    return unique_results

def check_unextracted_files():
    """检查还有哪些文件没有被抽取"""
    parsed_dir = "data/parsed"
    extract_dir = "outputs/extract_results"
    
    # 获取所有已解析的markdown文件
    if os.path.exists(parsed_dir):
        md_files = [f for f in os.listdir(parsed_dir) if f.endswith('.md')]
        all_doc_ids = {os.path.splitext(f)[0] for f in md_files}
    else:
        print("错误：data/parsed 目录不存在")
        return
    
    # 获取所有已成功抽取的doc_id
    success_ids = set()
    
    # 检查所有chunk文件
    for chunk_idx in range(5):
        chunk_file = os.path.join(extract_dir, f"chunk_{chunk_idx}", f"structured_data_chunk_{chunk_idx}.json")
        if os.path.exists(chunk_file):
            try:
                with open(chunk_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    success_ids.update(item['doc_id'] for item in data)
            except:
                pass
    
    # 检查retry_chunk文件
    for chunk_idx in range(5):
        retry_file = os.path.join(extract_dir, f"retry_chunk_{chunk_idx}", f"structured_data_retry_chunk_{chunk_idx}.json")
        if os.path.exists(retry_file):
            try:
                with open(retry_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    success_ids.update(item['doc_id'] for item in data)
            except:
                pass
    
    # 检查单独的重试文件
    retry_file = os.path.join(extract_dir, "retry", "structured_data_retry.json")
    if os.path.exists(retry_file):
        try:
            with open(retry_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                success_ids.update(item['doc_id'] for item in data)
        except:
            pass
    
    # 计算未抽取的文件
    unextracted_ids = all_doc_ids - success_ids
    
    print(f"\n=== 抽取状态统计 ===")
    print(f"已解析的markdown文件总数: {len(all_doc_ids)}")
    print(f"已成功抽取的文件数: {len(success_ids)}")
    print(f"未抽取的文件数: {len(unextracted_ids)}")
    
    if unextracted_ids:
        print(f"\n未抽取的文件列表:")
        for idx, doc_id in enumerate(sorted(unextracted_ids)[:20], 1):
            print(f"  {idx}. {doc_id}")
        if len(unextracted_ids) > 20:
            print(f"  ... 还有 {len(unextracted_ids) - 20} 个文件未列出")
    
    return unextracted_ids

if __name__ == "__main__":
    print("=== 开始合并所有结果 ===")
    merge_all_results()
    
    print("\n" + "="*50)
    print("=== 检查未抽取文件 ===")
    check_unextracted_files()