#!/usr/bin/env python3
import json
import os

# 读取合并数据
with open('outputs/extract_results/structured_data_merged.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=== 抽取数据质量检查 ===")
print(f"总记录数: {len(data)}")

# 统计问题
no_evidence = 0
missing_stock = 0
missing_bond = 0
suspicious = 0

suspicious_words = ['龙大美食', '龙大转债']

for item in data:
    ev = item.get('evidence_text')
    if ev is None or ev == '':
        no_evidence += 1
    
    if not item.get('stock_name') or item['stock_name'] == '':
        missing_stock += 1
    
    if not item.get('bond_name') or item['bond_name'] == '':
        missing_bond += 1
    
    if ev:
        for word in suspicious_words:
            if word in ev:
                suspicious += 1
                break

print("\n问题统计:")
print(f"  没有证据文本: {no_evidence}")
print(f"  缺少股票名称: {missing_stock}")
print(f"  缺少债券名称: {missing_bond}")
print(f"  包含可疑内容: {suspicious}")

# 显示前5条数据
print("\n=== 样本数据 ===")
for i, item in enumerate(data[:5]):
    print(f"\n样本 {i+1}:")
    print(f"  doc_id: {item['doc_id']}")
    print(f"  stock_name: {item.get('stock_name', 'N/A')}")
    print(f"  bond_name: {item.get('bond_name', 'N/A')}")
    print(f"  ann_type: {item.get('ann_type', 'N/A')}")

# 检查一条数据是否与原文匹配
print("\n=== 检查数据与原文匹配 ===")
for item in data[:2]:
    doc_id = item['doc_id']
    md_path = f"data/parsed/{doc_id}.md"
    
    if os.path.exists(md_path):
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        stock = item.get('stock_name', '')
        bond = item.get('bond_name', '')
        
        stock_ok = stock in content if stock else True
        bond_ok = bond in content if bond else True
        
        print(f"\ndoc_id: {doc_id}")
        print(f"  stock_name '{stock}' 在原文中: {'✓' if stock_ok else '✗'}")
        print(f"  bond_name '{bond}' 在原文中: {'✓' if bond_ok else '✗'}")
        
        if not stock_ok or not bond_ok:
            print(f"  ⚠️ 可能存在幻觉！")