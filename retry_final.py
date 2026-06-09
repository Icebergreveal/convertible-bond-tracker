#!/usr/bin/env python3
import json
import os
import time
import argparse
from openai import OpenAI
from dotenv import load_dotenv
from typing import Set, List

load_dotenv()

def get_unextracted_doc_ids() -> Set[str]:
    """获取未成功抽取的文件doc_id"""
    extract_dir = 'outputs/extract_results'
    
    # 获取已解析的markdown文件
    parsed_dir = 'data/parsed'
    if os.path.exists(parsed_dir):
        md_files = [f for f in os.listdir(parsed_dir) if f.endswith('.md')]
        all_doc_ids = {os.path.splitext(f)[0] for f in md_files}
    else:
        return set()
    
    # 获取所有已成功抽取的doc_id
    success_ids = set()
    
    # 检查所有chunk文件
    for chunk_idx in range(10):
        chunk_file = os.path.join(extract_dir, f'chunk_{chunk_idx}', f'structured_data_chunk_{chunk_idx}.json')
        if os.path.exists(chunk_file):
            try:
                with open(chunk_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        if item.get('stock_name') or item.get('bond_name'):
                            success_ids.add(item['doc_id'])
            except:
                pass
    
    # 检查所有retry_chunk文件
    for chunk_idx in range(10):
        retry_file = os.path.join(extract_dir, f'retry_chunk_{chunk_idx}', f'structured_data_retry_chunk_{chunk_idx}.json')
        if os.path.exists(retry_file):
            try:
                with open(retry_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        if item.get('stock_name') or item.get('bond_name'):
                            success_ids.add(item['doc_id'])
            except:
                pass
    
    # 检查retry文件
    retry_file = os.path.join(extract_dir, 'retry', 'structured_data_retry.json')
    if os.path.exists(retry_file):
        try:
            with open(retry_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    if item.get('stock_name') or item.get('bond_name'):
                        success_ids.add(item['doc_id'])
        except:
            pass
    
    return all_doc_ids - success_ids

def call_llm(client: OpenAI, model: str, prompt: str, retry_count: int = 3) -> dict:
    """调用LLM API"""
    for attempt in range(retry_count):
        try:
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
            
            content = response.choices[0].message.content
            
            # 清理可能的markdown代码块标记
            if content.startswith('```'):
                content = content.split('\n', 1)[1]
            if content.endswith('```'):
                content = content.rsplit('```', 1)[0]
            
            return json.loads(content.strip())
            
        except Exception as e:
            if attempt < retry_count - 1:
                print(f"LLM调用失败 (尝试 {attempt+1}/{retry_count}): {str(e)[:50]}")
                time.sleep(5)
            else:
                raise e

def process_chunk(chunk_index: int, total_chunks: int, limit: int = None):
    """处理指定块"""
    # 获取未抽取的文件
    failed_ids = get_unextracted_doc_ids()
    
    if not failed_ids:
        print("没有需要重试的文件")
        return []
    
    print(f"发现 {len(failed_ids)} 个失败的文件需要重试")
    
    # 分块处理
    failed_list = sorted(list(failed_ids))
    chunk_size = len(failed_list) // total_chunks
    start_idx = chunk_index * chunk_size
    end_idx = start_idx + chunk_size if chunk_index < total_chunks - 1 else len(failed_list)
    
    chunk_files = failed_list[start_idx:end_idx]
    
    if limit:
        chunk_files = chunk_files[:limit]
    
    print(f"处理第 {chunk_index+1}/{total_chunks} 块: {len(chunk_files)} 个文件 (索引: {start_idx}-{end_idx-1})")
    
    # 初始化LLM客户端
    client = OpenAI(
        api_key=os.getenv('LLM_API_KEY'),
        base_url=os.getenv('LLM_BASE_URL')
    )
    model = os.getenv('LLM_MODEL', 'deepseek-ai/DeepSeek-V4-Pro')
    
    results = []
    success_count = 0
    fail_count = 0
    
    for i, doc_id in enumerate(chunk_files, 1):
        md_path = f"data/parsed/{doc_id}.md"
        
        if not os.path.exists(md_path):
            print(f"[{chunk_index+1}] [{i}/{len(chunk_files)}] 文件不存在: {doc_id}")
            fail_count += 1
            continue
        
        # 读取markdown内容
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 构建prompt
        prompt = f"""
请从以下可转债公告中抽取关键信息，以JSON格式输出。

公告内容：
{content[:3000]}

请抽取以下字段（如果无法确定，输出null）：
- stock_code: 股票代码
- stock_name: 股票名称
- bond_code: 债券代码
- bond_name: 债券名称
- ann_type: 公告类型（如：下修类公告、强赎类公告等）
- publish_date: 发布日期（YYYY-MM-DD格式）
- trigger_rule: 触发条款
- original_conv_price: 修正前转股价格
- new_conv_price: 修正后转股价格
- effective_date: 生效日期
- redemption_price: 赎回价格
- evidence_text: 证据文本（公告中支持抽取结果的关键句子）

请只输出JSON，不要添加任何解释。
"""
        
        try:
            result = call_llm(client, model, prompt)
            result['doc_id'] = doc_id
            results.append(result)
            success_count += 1
            print(f"[{chunk_index+1}] [{i}/{len(chunk_files)}] OK {doc_id}")
            
        except Exception as e:
            fail_count += 1
            print(f"[{chunk_index+1}] [{i}/{len(chunk_files)}] FAIL {doc_id}: {str(e)[:50]}")
        
        time.sleep(2)
    
    # 保存结果到reretry文件夹
    output_dir = f"outputs/extract_results/reretry_{chunk_index}"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"structured_data_reretry_{chunk_index}.json")
    
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
    print(f"  成功: {success_count}/{len(chunk_files)}")
    print(f"  失败: {fail_count}/{len(chunk_files)}")
    print(f"  结果保存到: {output_path}")
    
    return unique_results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='重试失败的抽取任务（保存到reretry文件夹）')
    parser.add_argument('--chunk', type=int, default=0, help='当前处理的块索引（从0开始）')
    parser.add_argument('--total-chunks', type=int, default=3, help='总块数')
    parser.add_argument('--limit', type=int, help='限制处理的文件数量')
    
    args = parser.parse_args()
    
    process_chunk(args.chunk, args.total_chunks, args.limit)