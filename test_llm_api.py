#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

print("="*60)
print("🔍 LLM API 诊断")
print("="*60)

# 1. 检查环境变量
print("\n1️⃣ 环境变量检查:")
print(f"  API_KEY: {'✅ 已设置' if os.getenv('LLM_API_KEY') else '❌ 未设置'}")
print(f"  BASE_URL: {os.getenv('LLM_BASE_URL', '❌ 未设置')}")
print(f"  MODEL: {os.getenv('LLM_MODEL', '❌ 未设置')}")

# 2. 测试API连接
print("\n2️⃣ API连接测试:")
try:
    client = OpenAI(
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
    )
    
    # 测试调用
    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "Qwen/Qwen2.5-4B-Instruct"),
        messages=[
            {"role": "user", "content": "你好，请回复'测试成功'"}
        ],
        max_tokens=100,
        timeout=30
    )
    
    print(f"  ✅ API连接成功！")
    print(f"  模型响应: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"  ❌ API调用失败:")
    print(f"  错误类型: {type(e).__name__}")
    print(f"  错误信息: {str(e)}")
    
    # 提供具体建议
    if "401" in str(e) or "403" in str(e):
        print("\n💡 建议: API Key无效或已过期，请检查.env文件中的LLM_API_KEY")
    elif "404" in str(e):
        print("\n💡 建议: 模型不存在，请确认SiliconFlow上该模型是否可用")
        print("  可用模型参考:")
        print("    - Qwen/Qwen2.5-7B-Instruct")
        print("    - Qwen/Qwen2.5-4B-Instruct")
        print("    - Qwen/Qwen2.5-3B-Instruct")
        print("    - Qwen/Qwen2.5-1.5B-Instruct")
    elif "timeout" in str(e).lower():
        print("\n💡 建议: 连接超时，请检查网络或减小并发数")
    else:
        print("\n💡 建议: 请检查API配置和网络连接")

# 3. 推荐模型列表
print("\n3️⃣ SiliconFlow 推荐模型:")
models = [
    ("Qwen/Qwen2.5-7B-Instruct", "7B参数，速度与质量平衡"),
    ("Qwen/Qwen2.5-4B-Instruct", "4B参数，速度快"),
    ("Qwen/Qwen2.5-3B-Instruct", "3B参数，极速"),
]
for model, desc in models:
    print(f"  - {model}: {desc}")

print("\n" + "="*60)
