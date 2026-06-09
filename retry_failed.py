#!/usr/bin/env python3
"""
重试失败的抽取任务
"""
import os
import json
import time
import argparse
from typing import List, Dict, Set

def load_extract_prompt() -> str:
    optimized_path = "src/extract/extract_prompt_optimized.txt"
    prompt_path = "src/extract/extract_prompt.txt"
    
    if os.path.exists(optimized_path):
        with open(optimized_path, 'r', encoding='utf-8') as f:
            return f.read()
    elif os.path.exists(prompt_path):
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    return get_default_prompt()

def get_default_prompt() -> str:
    return """
你是一个可转债公告信息抽取专家。请仔细阅读以下公告文本，按照要求抽取相关字段。

## 抽取要求
1. 所有字段值必须来自公告文本，无法从文本中找到的字段请输出null
2. 每个关键字段必须提供evidence_text证据原文
3. 日期格式统一为YYYY-MM-DD
4. 金额单位统一为元（如遇到万元/亿元需转换）
5. 转股价格单位为元/股

## 字段定义

### 基础字段
- doc_id: 文档唯一标识（由系统生成）
- stock_code: 股票代码（6位数字）
- stock_name: 股票名称
- bond_code: 可转债代码（6位数字）
- bond_name: 可转债名称
- ann_type: 公告类型
- publish_date: 公告发布日期
- evidence_page: 证据所在页码
- evidence_text: 支持字段判断的公告原文片段

### 下修类公告
- trigger_rule: 转股价下修的市场价格触发条件
- original_conv_price: 修正前转股价格（元/股）
- new_conv_price: 修正后转股价格（元/股）
- pricing_base_date: 定价基准日
- avg_price_20d: 前20个交易日均价
- avg_price_1d: 前1个交易日均价
- effective_date: 调整生效日期
- adjustment_ratio: 下修幅度百分比

### 强赎类公告
- redemption_trigger: 提前强赎的价格天数触发规则
- redemption_price: 可转债赎回价格（元）
- record_date: 股权赎回登记截止日期
- last_convert_date: 投资者最后转股操作截止日
- delisting_date: 摘牌日期
- premium_rate: 赎回溢价率

## 输出格式
请以纯JSON格式输出：
{
    "doc_id": "",
    "stock_code": "",
    "stock_name": "",
    "bond_code": "",
    "bond_name": "",
    "ann_type": "",
    "publish_date": "",
    "trigger_rule": null,
    "original_conv_price": null,
    "new_conv_price": null,
    "pricing_base_date": null,
    "avg_price_20d": null,
    "avg_price_1d": null,
    "effective_date": null,
    "adjustment_ratio": null,
    "adjustment_type": null,
    "redemption_trigger": null,
    "redemption_price": null,
    "record_date": null,
    "last_convert_date": null,
    "delisting_date": null,
    "premium_rate": null,
    "evidence_page": null,
    "evidence_text": ""
}
"""

def get_failed_doc_ids(chunks: List[int] = None) -> Set[str]:
    """获取失败的文件doc_id"""
    all_doc_ids = set()
    
    parsed_dir = 'data/parsed'
    if os.path.exists(parsed_dir):
        md_files = [f for f in os.listdir(parsed_dir) if f.endswith('.md')]
        all_doc_ids = {os.path.splitext(f)[0] for f in md_files}
    
    # 获取所有已成功的doc_id
    success_ids = set()
    
    # 检查所有chunk
    for chunk_idx in range(5):
        chunk_file = f"outputs/extract_results/chunk_{chunk_idx}/structured_data_chunk_{chunk_idx}.json"
        if os.path.exists(chunk_file):
            try:
                with open(chunk_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    success_ids.update(item['doc_id'] for item in data)
            except:
                pass
    
    # 检查retry_chunk文件
    for chunk_idx in range(5):
        retry_file = f"outputs/extract_results/retry_chunk_{chunk_idx}/structured_data_retry_chunk_{chunk_idx}.json"
        if os.path.exists(retry_file):
            try:
                with open(retry_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    success_ids.update(item['doc_id'] for item in data)
            except:
                pass
    
    # 检查重试结果
    retry_file = "outputs/extract_results/retry/structured_data_retry.json"
    if os.path.exists(retry_file):
        try:
            with open(retry_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                success_ids.update(item['doc_id'] for item in data)
        except:
            pass
    
    return all_doc_ids - success_ids

def retry_extract(failed_ids: Set[str] = None, chunk_index: int = 0, total_chunks: int = 1, limit: int = None):
    """重试失败的抽取任务"""
    from dotenv import load_dotenv
    from openai import OpenAI
    
    load_dotenv()
    
    parsed_dir = 'data/parsed'
    
    if failed_ids:
        md_files = [f for f in os.listdir(parsed_dir) if f.endswith('.md') and os.path.splitext(f)[0] in failed_ids]
    else:
        md_files = [f for f in os.listdir(parsed_dir) if f.endswith('.md')]
    
    # 按块划分
    md_files = sorted(md_files)
    chunk_size = len(md_files) // total_chunks
    start_idx = chunk_index * chunk_size
    end_idx = start_idx + chunk_size if chunk_index < total_chunks - 1 else len(md_files)
    md_files = md_files[start_idx:end_idx]
    
    if limit:
        md_files = md_files[:limit]
    
    print(f"处理第 {chunk_index+1}/{total_chunks} 块: {len(md_files)} 个文件")
    
    client = OpenAI(
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
    )
    model = os.getenv("LLM_MODEL", "deepseek-ai/DeepSeek-V4-Pro")
    prompt_template = load_extract_prompt()
    
    results = []
    success_count = 0
    fail_count = 0
    
    for i, md_file in enumerate(md_files):
        md_path = os.path.join(parsed_dir, md_file)
        doc_id = os.path.splitext(md_file)[0]
        
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            content = content[:8000]
            prompt = f"{prompt_template}\n\n## 公告文本\n{content}\n\n## 请抽取以上公告的信息，输出JSON格式结果："
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "你是一个专业的金融文本信息抽取助手。请严格按照JSON格式输出结果，不要添加任何额外文本。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=2048,
                timeout=120
            )
            
            result = json.loads(response.choices[0].message.content)
            result['doc_id'] = doc_id
            results.append(result)
            success_count += 1
            print(f"[{chunk_index+1}] [{i+1}/{len(md_files)}] ✓ {doc_id}")
            
        except Exception as e:
            fail_count += 1
            print(f"[{chunk_index+1}] [{i+1}/{len(md_files)}] ✗ {doc_id}: {str(e)[:50]}")
        
        time.sleep(2)
    
    # 保存结果
    output_dir = f"outputs/extract_results/retry_chunk_{chunk_index}"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"structured_data_retry_chunk_{chunk_index}.json")
    
    # 先读取已存在的数据（避免覆盖）
    existing_data = []
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            print(f"发现已存在 {len(existing_data)} 条记录，将追加")
        except:
            pass
    
    # 合并新旧数据并去重
    combined = existing_data + results
    unique_results = []
    seen_ids = set()
    for item in combined:
        doc_id = item.get('doc_id')
        if doc_id and doc_id not in seen_ids:
            seen_ids.add(doc_id)
            unique_results.append(item)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(unique_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== 第 {chunk_index+1} 块完成 ===")
    print(f"  成功: {success_count}/{len(md_files)}")
    print(f"  失败: {fail_count}/{len(md_files)}")
    print(f"  结果保存到: {output_path}")
    
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='重试失败的抽取任务')
    parser.add_argument('--chunk', type=int, default=0, help='当前处理的块索引（从0开始）')
    parser.add_argument('--total-chunks', type=int, default=3, help='总块数')
    parser.add_argument('--limit', type=int, default=None, help='限制重试文件数')
    
    args = parser.parse_args()
    
    failed_ids = get_failed_doc_ids()
    print(f"发现 {len(failed_ids)} 个失败的文件需要重试")
    
    retry_extract(failed_ids, args.chunk, args.total_chunks, args.limit)
