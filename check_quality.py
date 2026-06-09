#!/usr/bin/env python3
import json
import os

def check_extraction_quality():
    """检查抽取数据的质量，检测可能的幻觉"""
    merged_file = "outputs/extract_results/structured_data_merged.json"
    
    with open(merged_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"=== 抽取数据质量检查 ===")
    print(f"总记录数: {len(data)}")
    
    # 检查各种问题
    issues = {
        'no_evidence': 0,
        'short_evidence': 0,
        'missing_stock': 0,
        'missing_bond': 0,
        'suspicious_evidence': 0
    }
    
    suspicious_patterns = [
        '龙大美食', '龙大转债',  # 之前发现的幻觉示例
        '本公告', '根据公告',    # 通用模板词
        '董事会提议向下修正',    # 常见幻觉内容
    ]
    
    for item in data:
        # 检查evidence_text
        evidence = item.get('evidence_text', '')
        
        if not evidence or evidence.strip() == '':
            issues['no_evidence'] += 1
        elif len(evidence) < 20:
            issues['short_evidence'] += 1
        
        # 检查是否有可疑内容
        for pattern in suspicious_patterns:
            if pattern in evidence:
                issues['suspicious_evidence'] += 1
                break
        
        # 检查stock_name和bond_name
        if not item.get('stock_name') or item['stock_name'] == '':
            issues['missing_stock'] += 1
        if not item.get('bond_name') or item['bond_name'] == '':
            issues['missing_bond'] += 1
    
    print(f"\n问题统计:")
    print(f"  没有证据文本: {issues['no_evidence']}")
    print(f"  证据文本过短: {issues['short_evidence']}")
    print(f"  缺少股票名称: {issues['missing_stock']}")
    print(f"  缺少债券名称: {issues['missing_bond']}")
    print(f"  可疑内容: {issues['suspicious_evidence']}")
    
    # 显示一些样本
    print(f"\n=== 样本数据 ===")
    for i, item in enumerate(data[:5]):
        print(f"\n样本 {i+1}:")
        print(f"  doc_id: {item['doc_id']}")
        print(f"  stock_name: {item.get('stock_name', 'N/A')}")
        print(f"  bond_name: {item.get('bond_name', 'N/A')}")
        print(f"  ann_type: {item.get('ann_type', 'N/A')}")
        evidence = item.get('evidence_text', '')
        print(f"  evidence_text: {evidence[:100]}..." if len(evidence) > 100 else f"  evidence_text: {evidence}")
    
    # 检查与原始文档的匹配度
    print(f"\n=== 检查部分数据与原始文档的匹配 ===")
    parsed_dir = "data/parsed"
    
    for item in data[:3]:
        doc_id = item['doc_id']
        md_path = os.path.join(parsed_dir, f"{doc_id}.md")
        
        if os.path.exists(md_path):
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            stock_name = item.get('stock_name', '')
            bond_name = item.get('bond_name', '')
            
            stock_found = stock_name in content if stock_name else True
            bond_found = bond_name in content if bond_name else True
            
            print(f"\ndoc_id: {doc_id}")
            print(f"  stock_name '{stock_name}' 在原文中: {'✓ 存在' if stock_found else '✗ 不存在'}")
            print(f"  bond_name '{bond_name}' 在原文中: {'✓ 存在' if bond_found else '✗ 不存在'}")
            
            if not stock_found or not bond_found:
                print(f"  ⚠️ 可能存在幻觉！")

if __name__ == "__main__":
    check_extraction_quality()