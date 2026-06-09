#!/usr/bin/env python3
import os
import json
import time
import argparse
from multiprocessing import Pool, cpu_count
from typing import List, Dict
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class LLMClient:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
        )
        self.model = os.getenv("LLM_MODEL", "Qwen/Qwen3-8B-Instruct")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", 0))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", 2048))
        self.retry_count = 3
        self.retry_delay = 5

    def call_llm(self, prompt: str) -> str:
        for attempt in range(self.retry_count):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "你是一个专业的金融文本信息抽取助手。请根据用户提供的公告文本，抽取指定的字段信息，并以JSON格式输出结果。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    response_format={"type": "json_object"},
                    timeout=120
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"LLM调用失败 (尝试 {attempt + 1}/{self.retry_count}): {str(e)}")
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay)
        return None

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
- ann_type: 公告类型（见下方分类）
- publish_date: 公告发布日期
- evidence_page: 证据所在页码
- evidence_text: 支持字段判断的公告原文片段

### 转股价格调整相关字段（下修类公告）
- trigger_rule: 转股价下修的市场价格触发条件
- original_conv_price: 修正前转股价格（元/股）
- new_conv_price: 修正后转股价格（元/股）
- pricing_base_date: 定价基准日
- avg_price_20d: 前20个交易日均价
- avg_price_1d: 前1个交易日均价
- effective_date: 调整生效日期
- adjustment_ratio: 下修幅度百分比
- adjustment_type: 调整类型（主动下修/被动调整）

### 提前赎回相关字段（强赎类公告）
- redemption_trigger: 提前强赎的价格天数触发规则
- redemption_price: 可转债每张含利息赎回定价（元）
- record_date: 股权赎回登记截止日期
- last_convert_date: 投资者最后转股操作截止日
- delisting_date: 摘牌日期
- premium_rate: 赎回溢价率

## 公告类型分类
### 下修类公告
1. 触发转股价格向下修正条件的提示性公告
2. 董事会提议向下修正转股价格公告
3. 关于可转债转股价格调整的公告（股东大会决议）
4. 可转债转股价格向下修正实施公告

### 强赎类公告
1. 关于提前赎回可转债的提示性公告（触发提示）
2. 关于行使可转债提前赎回权的公告（董事会/股东大会决议）
3. 可转债提前赎回实施提示公告
4. 可转债赎回结果暨摘牌公告

## 输出格式
请以纯JSON格式输出，不要包含其他文本：
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

def process_file(args):
    md_file, parsed_dir, prompt_template = args
    llm_client = LLMClient()
    md_path = os.path.join(parsed_dir, md_file)
    doc_id = os.path.splitext(md_file)[0]
    
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = content[:8000]
        prompt = f"{prompt_template}\n\n## 公告文本\n{content}\n\n## 请抽取以上公告的信息，输出JSON格式结果："
        
        response = llm_client.call_llm(prompt)
        
        if response:
            try:
                result = json.loads(response)
                result['doc_id'] = doc_id
                time.sleep(0.5)
                return (doc_id, 'success', result)
            except json.JSONDecodeError:
                return (doc_id, 'json_error', response)
        else:
            return (doc_id, 'llm_failed', None)
    except Exception as e:
        return (doc_id, 'error', str(e))

def extract_parallel(chunk_index=0, total_chunks=1, limit=None, processes=None):
    parsed_dir = 'data/parsed'
    md_files = [f for f in os.listdir(parsed_dir) if f.endswith('.md')]
    
    if limit:
        md_files = md_files[:limit]
    
    chunk_size = len(md_files) // total_chunks
    start_idx = chunk_index * chunk_size
    end_idx = start_idx + chunk_size if chunk_index < total_chunks - 1 else len(md_files)
    
    chunk_files = md_files[start_idx:end_idx]
    print(f"处理第 {chunk_index+1}/{total_chunks} 块: {len(chunk_files)} 个文件 (索引: {start_idx}-{end_idx-1})")
    
    prompt_template = load_extract_prompt()
    
    if processes is None:
        processes = min(cpu_count(), 4)
    
    args_list = [(f, parsed_dir, prompt_template) for f in chunk_files]
    
    with Pool(processes=processes) as pool:
        results = []
        for i, (doc_id, status, data) in enumerate(pool.imap_unordered(process_file, args_list)):
            if status == 'success':
                results.append(data)
                print(f"[{chunk_index+1}] [{i+1}/{len(chunk_files)}] ✓ {doc_id}")
            elif status == 'json_error':
                print(f"[{chunk_index+1}] [{i+1}/{len(chunk_files)}] ✗ JSON解析失败: {doc_id}")
            elif status == 'llm_failed':
                print(f"[{chunk_index+1}] [{i+1}/{len(chunk_files)}] ✗ LLM调用失败: {doc_id}")
            else:
                print(f"[{chunk_index+1}] [{i+1}/{len(chunk_files)}] ✗ 处理错误 {doc_id}: {data}")
    
    output_dir = f"outputs/extract_results/chunk_{chunk_index}"
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, f"structured_data_chunk_{chunk_index}.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== 第 {chunk_index+1} 块完成 ===")
    print(f"  成功: {len(results)}/{len(chunk_files)}")
    print(f"  结果保存到: {output_path}")
    
    return results

def merge_results(total_chunks):
    all_results = []
    
    for i in range(total_chunks):
        chunk_path = f"outputs/extract_results/chunk_{i}/structured_data_chunk_{i}.json"
        if os.path.exists(chunk_path):
            with open(chunk_path, 'r', encoding='utf-8') as f:
                chunk_results = json.load(f)
                all_results.extend(chunk_results)
                print(f"已合并第 {i+1} 块: {len(chunk_results)} 条记录")
    
    output_path = "outputs/extract_results/structured_data_merged.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== 合并完成 ===")
    print(f"  总记录数: {len(all_results)}")
    print(f"  合并结果保存到: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='并行抽取公告数据')
    parser.add_argument('--chunk', type=int, default=0, help='当前处理的块索引（从0开始）')
    parser.add_argument('--total-chunks', type=int, default=1, help='总块数')
    parser.add_argument('--limit', type=int, default=None, help='限制处理文件数')
    parser.add_argument('--processes', type=int, default=None, help='并行进程数')
    parser.add_argument('--merge', action='store_true', help='合并所有块的结果')
    
    args = parser.parse_args()
    
    if args.merge:
        merge_results(args.total_chunks)
    else:
        extract_parallel(args.chunk, args.total_chunks, args.limit, args.processes)