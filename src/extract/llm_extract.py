import os
import json
import time
from typing import List, Dict, Optional
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
                    response_format={"type": "json_object"}
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"LLM调用失败 (尝试 {attempt + 1}/{self.retry_count}): {str(e)}")
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay)
        return None

def load_extract_prompt() -> str:
    prompt_path = "src/extract/extract_prompt.txt"
    if os.path.exists(prompt_path):
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
- trigger_rule: 转股价下修的市场价格触发条件（如连续30个交易日中有15个交易日收盘价低于转股价的85%）
- original_conv_price: 修正前转股价格（元/股）
- new_conv_price: 修正后转股价格（元/股）
- pricing_base_date: 定价基准日
- avg_price_20d: 前20个交易日均价
- avg_price_1d: 前1个交易日均价
- effective_date: 调整生效日期
- adjustment_ratio: 下修幅度百分比 = (修正前转股价 - 修正后转股价) / 修正前转股价 * 100%
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

def extract_fields(config: Dict, limit: int = None) -> List[Dict]:
    results = []
    md_files = []
    
    parsed_dir = config.get('output', {}).get('parsed_dir', 'data/parsed')
    
    if os.path.exists(parsed_dir):
        md_files = [f for f in os.listdir(parsed_dir) if f.endswith('.md')]
    
    if limit:
        md_files = md_files[:limit]
    
    llm_client = LLMClient()
    prompt_template = load_extract_prompt()
    
    success_count = 0
    fail_count = 0
    
    for md_file in md_files:
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
                    results.append(result)
                    success_count += 1
                    print(f"✅ 成功抽取: {doc_id}")
                except json.JSONDecodeError:
                    print(f"❌ JSON解析失败: {doc_id}")
                    fail_count += 1
            else:
                print(f"❌ LLM调用失败: {doc_id}")
                fail_count += 1
            
            time.sleep(1)
            
        except Exception as e:
            print(f"❌ 处理文件失败 {md_file}: {str(e)}")
            fail_count += 1
    
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
        f.write(f"Extract completed\n")
    
    print(f"\n=== 抽取完成 ===")
    print(f"  处理总数: {len(md_files)}")
    print(f"  成功: {success_count}")
    print(f"  失败: {fail_count}")
    print(f"  结果保存到: {output_path}")
    print(f"  日志保存到: {log_path}")
    
    return results

def batch_extract(limit=30):
    config = {
        'output': {
            'parsed_dir': 'data/parsed'
        }
    }
    return extract_fields(config, limit)

if __name__ == "__main__":
    print("🚀 开始LLM抽取...")
    batch_extract(3)
    print("✅ LLM抽取完成")
