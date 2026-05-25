import os
import json
import csv
from datetime import datetime
from typing import List, Dict, Callable

def batch_process(items: List, batch_size: int, process_func: Callable, **kwargs) -> List[Dict]:
    """
    分批处理数据
    
    Args:
        items: 待处理的项目列表
        batch_size: 每批处理的数量
        process_func: 处理函数
        kwargs: 传递给处理函数的额外参数
    
    Returns:
        处理结果列表
    """
    results = []
    total_items = len(items)
    num_batches = (total_items + batch_size - 1) // batch_size
    
    print(f"开始分批处理: 共 {total_items} 条数据, 分成 {num_batches} 批, 每批 {batch_size} 条")
    
    for batch_idx in range(num_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, total_items)
        batch_items = items[start_idx:end_idx]
        
        print(f"\n处理批次 [{batch_idx + 1}/{num_batches}]: {start_idx + 1}-{end_idx}")
        
        try:
            batch_results = process_func(batch_items, **kwargs)
            results.extend(batch_results)
            print(f"批次 [{batch_idx + 1}] 完成: {len(batch_results)} 条成功")
        except Exception as e:
            print(f"批次 [{batch_idx + 1}] 失败: {str(e)}")
            # 记录失败的批次
            for item in batch_items:
                results.append({
                    'status': 'failed',
                    'error': str(e),
                    'item': item
                })
    
    print(f"\n分批处理完成: 共处理 {len(results)} 条")
    return results

def create_versioned_output(base_dir: str, data_type: str, data: List[Dict]) -> str:
    """
    创建带版本号的输出文件（按日期分区存储）
    
    Args:
        base_dir: 基础目录
        data_type: 数据类型（如extract_results, event_chain, indicators）
        data: 要保存的数据
    
    Returns:
        保存的文件路径
    """
    current_date = datetime.now().strftime("%Y%m%d")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    version_dir = os.path.join(base_dir, data_type, current_date)
    os.makedirs(version_dir, exist_ok=True)
    
    file_path = os.path.join(version_dir, f"{data_type}_{timestamp}.json")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    latest_symlink = os.path.join(base_dir, data_type, "latest.json")
    if os.path.exists(latest_symlink):
        os.remove(latest_symlink)
    try:
        os.symlink(file_path, latest_symlink)
    except:
        pass
    
    return file_path

def save_metadata_version(metadata_path: str) -> str:
    """
    保存metadata版本
    
    Args:
        metadata_path: 当前metadata文件路径
    
    Returns:
        版本文件路径
    """
    current_date = datetime.now().strftime("%Y%m%d")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    version_dir = os.path.join("data", "metadata", "versions")
    os.makedirs(version_dir, exist_ok=True)
    
    version_path = os.path.join(version_dir, f"metadata_{timestamp}.csv")
    
    with open(metadata_path, 'r', encoding='utf-8') as src:
        with open(version_path, 'w', encoding='utf-8') as dst:
            dst.write(src.read())
    
    return version_path

def load_versioned_data(base_dir: str, data_type: str, date_str: str = None) -> List[Dict]:
    """
    加载指定日期版本的数据
    
    Args:
        base_dir: 基础目录
        data_type: 数据类型
        date_str: 日期字符串（格式：YYYYMMDD），默认为最新版本
    
    Returns:
        加载的数据
    """
    if date_str:
        version_dir = os.path.join(base_dir, data_type, date_str)
        if not os.path.exists(version_dir):
            raise ValueError(f"版本目录不存在: {version_dir}")
        
        files = sorted([f for f in os.listdir(version_dir) if f.endswith('.json')], reverse=True)
        if not files:
            raise ValueError(f"版本目录中无数据文件: {version_dir}")
        
        file_path = os.path.join(version_dir, files[0])
    else:
        file_path = os.path.join(base_dir, data_type, "latest.json")
        if not os.path.exists(file_path):
            raise ValueError("未找到最新版本文件")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_version_history(base_dir: str, data_type: str) -> List[str]:
    """
    获取数据版本历史
    
    Args:
        base_dir: 基础目录
        data_type: 数据类型
    
    Returns:
        版本日期列表
    """
    data_dir = os.path.join(base_dir, data_type)
    if not os.path.exists(data_dir):
        return []
    
    version_dirs = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
    return sorted(version_dirs, reverse=True)

def batch_extract_with_versioning(extract_func: Callable, items: List, batch_size: int = 50) -> str:
    """
    分批抽取并保存版本
    
    Args:
        extract_func: 抽取函数
        items: 待抽取的项目列表
        batch_size: 每批处理数量
    
    Returns:
        保存的文件路径
    """
    results = batch_process(items, batch_size, extract_func)
    
    success_count = sum(1 for r in results if r.get('status') != 'failed')
    fail_count = len(results) - success_count
    
    print(f"\n抽取完成: 成功 {success_count}, 失败 {fail_count}")
    
    file_path = create_versioned_output("outputs", "extract_results", results)
    print(f"结果已保存到: {file_path}")
    
    return file_path

if __name__ == "__main__":
    print("=== 分批处理测试 ===")
    
    test_items = list(range(100))
    
    def test_process(batch):
        results = []
        for item in batch:
            results.append({
                'id': item,
                'status': 'success',
                'processed_at': datetime.now().isoformat()
            })
        return results
    
    results = batch_process(test_items, batch_size=30, process_func=test_process)
    print(f"处理结果: {len(results)} 条")
    
    print("\n=== 版本管理测试 ===")
    test_data = [{'id': 1, 'value': 'test'}]
    file_path = create_versioned_output("outputs", "test_data", test_data)
    print(f"版本文件保存到: {file_path}")
    
    history = get_version_history("outputs", "test_data")
    print(f"版本历史: {history}")