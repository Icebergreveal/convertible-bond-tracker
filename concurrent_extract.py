#!/usr/bin/env python3
import os
import json
import time
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple
from dotenv import load_dotenv
from openai import OpenAI
import threading

load_dotenv()

class LLMClient:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("LLM_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
        )
        self.model = os.getenv("LLM_MODEL", "Qwen/Qwen3-32B-Instruct")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", 0))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", 2048))
        self.retry_count = 3
        self.retry_delay = 2
        self._lock = threading.Lock()

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
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay)
                else:
                    return None
        return None

def load_extract_prompt() -> str:
    return """
你是一个可转债公告信息抽取专家。请仔细阅读以下公告文本，按照要求抽取相关字段。

## 抽取要求
1. 所有字段值必须来自公告文本，无法从文本中找到的字段请输出null
2. 每个关键字段必须提供evidence_text证据原文
3. 日期格式统一为YYYY-MM-DD
4. 金额单位统一为元（如遇到万元/亿元需转换）
5. 转股价格单位为元/股

## 字段定义
- doc_id: 文档唯一标识
- stock_code: 股票代码（6位数字）
- stock_name: 股票名称
- bond_code: 可转债代码（6位数字）
- bond_name: 可转债名称
- ann_type: 公告类型
- publish_date: 公告发布日期
- trigger_rule: 转股价下修的市场价格触发条件
- original_conv_price: 修正前转股价格（元/股）
- new_conv_price: 修正后转股价格（元/股）
- pricing_base_date: 定价基准日
- avg_price_20d: 前20个交易日均价
- avg_price_1d: 前1个交易日均价
- effective_date: 调整生效日期
- adjustment_ratio: 下修幅度百分比
- adjustment_type: 调整类型
- redemption_trigger: 提前强赎的价格天数触发规则
- redemption_price: 可转债每张赎回定价（元）
- record_date: 股权赎回登记截止日期
- last_convert_date: 投资者最后转股操作截止日
- delisting_date: 摘牌日期
- premium_rate: 赎回溢价率
- evidence_page: 证据所在页码
- evidence_text: 支持字段判断的公告原文片段

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

def process_single_file(md_file: str, parsed_dir: str, prompt_template: str, client: LLMClient, thread_id: int) -> Tuple[str, str, Dict]:
    md_path = os.path.join(parsed_dir, md_file)
    doc_id = os.path.splitext(md_file)[0]
    
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = content[:8000]
        prompt = f"{prompt_template}\n\n## 公告文本\n{content}\n\n## 请抽取以上公告的信息，输出JSON格式结果："
        
        response = client.call_llm(prompt)
        
        if response:
            try:
                result = json.loads(response)
                result['doc_id'] = doc_id
                return (doc_id, 'success', result)
            except json.JSONDecodeError:
                return (doc_id, 'json_error', None)
        else:
            return (doc_id, 'llm_failed', None)
    except Exception as e:
        return (doc_id, 'error', str(e))

def concurrent_extract(limit: int = None, workers: int = 5) -> List[Dict]:
    parsed_dir = 'data/parsed'
    md_files = [f for f in os.listdir(parsed_dir) if f.endswith('.md')]
    
    if limit:
        md_files = md_files[:limit]
    
    print(f"开始并发抽取，共 {len(md_files)} 个文件，使用 {workers} 个线程")
    
    prompt_template = load_extract_prompt()
    llm_client = LLMClient()
    
    results = []
    success_count = 0
    fail_count = 0
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(process_single_file, f, parsed_dir, prompt_template, llm_client, i % workers): f 
            for i, f in enumerate(md_files)
        }
        
        for future in as_completed(futures):
            md_file = futures[future]
            try:
                doc_id, status, data = future.result()
                
                if status == 'success':
                    results.append(data)
                    success_count += 1
                    print(f"[✓] 成功抽取: {doc_id}")
                elif status == 'json_error':
                    fail_count += 1
                    print(f"[✗] JSON解析失败: {doc_id}")
                elif status == 'llm_failed':
                    fail_count += 1
                    print(f"[✗] LLM调用失败: {doc_id}")
                else:
                    fail_count += 1
                    print(f"[✗] 处理错误 {doc_id}: {data}")
                    
            except Exception as e:
                fail_count += 1
                print(f"[✗] 线程执行错误: {str(e)}")
    
    output_dir = "outputs/extract_results"
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, "structured_data.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    log_path = "outputs/logs/extract_quality.log"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(f"Extract started at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total processed: {len(md_files)}\n")
        f.write(f"Success: {success_count}\n")
        f.write(f"Failed: {fail_count}\n")
    
    print(f"\n{'='*60}")
    print(f"✅ 抽取完成！")
    print(f"  处理总数: {len(md_files)}")
    print(f"  成功: {success_count}")
    print(f"  失败: {fail_count}")
    print(f"  结果保存到: {output_path}")
    print(f"{'='*60}")
    
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='并发抽取公告数据')
    parser.add_argument('--limit', type=int, default=None, help='限制处理文件数')
    parser.add_argument('--workers', type=int, default=5, help='并发线程数（默认5）')
    
    args = parser.parse_args()
    
    print("🚀 开始并发LLM抽取...")
    concurrent_extract(args.limit, args.workers)
    print("✅ LLM抽取完成")
