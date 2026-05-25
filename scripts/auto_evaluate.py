#!/usr/bin/env python3
import os
import json
import csv
import argparse
from datetime import datetime
from typing import List, Dict

def load_extract_results(input_path: str) -> List[Dict]:
    """加载抽取结果"""
    if not os.path.exists(input_path):
        print(f"错误: 输入文件不存在 {input_path}")
        return []
    
    with open(input_path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print(f"错误: JSON解析失败 {input_path}")
            return []

def load_validation_errors(error_path: str) -> List[Dict]:
    """加载校验错误"""
    errors = []
    if os.path.exists(error_path):
        with open(error_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        errors.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return errors

def evaluate_field_completeness(records: List[Dict]) -> Dict:
    """评估字段完整性"""
    if not records:
        return {}
    
    total_records = len(records)
    field_stats = {}
    
    key_fields = [
        'doc_id', 'stock_code', 'stock_name', 'bond_code', 'bond_name',
        'ann_type', 'publish_date', 'original_conv_price', 'new_conv_price',
        'redemption_price', 'effective_date', 'evidence_page', 'evidence_text'
    ]
    
    for field in key_fields:
        filled_count = 0
        for record in records:
            value = record.get(field)
            if value is not None and value != '' and str(value).lower() != 'nan':
                filled_count += 1
        
        field_stats[field] = {
            'filled': filled_count,
            'total': total_records,
            'rate': (filled_count / total_records) * 100
        }
    
    return field_stats

def evaluate_data_quality(records: List[Dict]) -> Dict:
    """评估数据质量"""
    quality = {
        'valid_date_format': 0,
        'invalid_date_format': 0,
        'valid_numeric': 0,
        'invalid_numeric': 0,
        'abnormal_prices': 0
    }
    
    import re
    date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    
    for record in records:
        publish_date = record.get('publish_date', '')
        if date_pattern.match(str(publish_date)):
            quality['valid_date_format'] += 1
        elif publish_date and str(publish_date).lower() != 'nan':
            quality['invalid_date_format'] += 1
        
        conv_price = record.get('original_conv_price')
        try:
            if conv_price and str(conv_price).lower() != 'nan':
                price = float(conv_price)
                if price > 0:
                    quality['valid_numeric'] += 1
                else:
                    quality['abnormal_prices'] += 1
        except:
            if conv_price:
                quality['invalid_numeric'] += 1
    
    return quality

def evaluate_event_coverage(records: List[Dict]) -> Dict:
    """评估事件类型覆盖"""
    event_types = {}
    for record in records:
        ann_type = record.get('ann_type', '未知')
        if ann_type not in event_types:
            event_types[ann_type] = 0
        event_types[ann_type] += 1
    
    return event_types

def generate_evaluation_report(
    records: List[Dict],
    errors: List[Dict],
    output_path: str
) -> Dict:
    """生成评估报告"""
    report = {
        'report_time': datetime.now().isoformat(),
        'summary': {},
        'field_completeness': {},
        'data_quality': {},
        'event_coverage': {},
        'validation_errors': [],
        'recommendations': []
    }
    
    total_records = len(records)
    total_errors = len(errors)
    
    report['summary'] = {
        'total_records': total_records,
        'total_errors': total_errors,
        'error_rate': (total_errors / (total_records + total_errors)) * 100 if (total_records + total_errors) > 0 else 0,
        'data_source': 'outputs/extract_results/structured_data.json'
    }
    
    report['field_completeness'] = evaluate_field_completeness(records)
    report['data_quality'] = evaluate_data_quality(records)
    report['event_coverage'] = evaluate_event_coverage(records)
    report['validation_errors'] = errors[:10]
    
    report['recommendations'] = generate_recommendations(report)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    return report

def generate_recommendations(report: Dict) -> List[str]:
    """生成优化建议"""
    recommendations = []
    
    completeness = report['field_completeness']
    for field, stats in completeness.items():
        if stats['rate'] < 80:
            recommendations.append(f"字段 {field} 填充率仅 {stats['rate']:.1f}%，建议优化抽取prompt或增加样本")
    
    quality = report['data_quality']
    if quality['invalid_date_format'] > 0:
        recommendations.append(f"发现 {quality['invalid_date_format']} 条日期格式错误记录，建议检查日期解析逻辑")
    
    if quality['invalid_numeric'] > 0:
        recommendations.append(f"发现 {quality['invalid_numeric']} 条数值格式错误记录，建议增强数值校验")
    
    if quality['abnormal_prices'] > 0:
        recommendations.append(f"发现 {quality['abnormal_prices']} 条异常价格记录，建议检查价格单位处理")
    
    if report['summary']['error_rate'] > 10:
        recommendations.append(f"错误率 {report['summary']['error_rate']:.1f}% 较高，建议检查LLM抽取逻辑和校验规则")
    
    if not recommendations:
        recommendations.append("数据质量良好，继续保持")
    
    return recommendations

def print_report_summary(report: Dict, output_path: str):
    """打印报告摘要"""
    print("=" * 60)
    print("自动化评估报告")
    print("=" * 60)
    
    summary = report['summary']
    print("\n【总体摘要】")
    print("  总记录数: %d" % summary['total_records'])
    print("  校验错误: %d" % summary['total_errors'])
    print("  错误率: %.2f%%" % summary['error_rate'])
    
    print("\n【字段完整性】")
    for field, stats in report['field_completeness'].items():
        if stats['rate'] >= 80:
            status = "[OK]"
        elif stats['rate'] >= 50:
            status = "[WARN]"
        else:
            status = "[FAIL]"
        print("  %s %s: %d/%d (%.1f%%)" % (status, field, stats['filled'], stats['total'], stats['rate']))
    
    print("\n【数据质量】")
    quality = report['data_quality']
    print("  日期格式正确: %d" % quality['valid_date_format'])
    print("  日期格式错误: %d" % quality['invalid_date_format'])
    print("  数值格式正确: %d" % quality['valid_numeric'])
    print("  数值格式错误: %d" % quality['invalid_numeric'])
    print("  异常价格: %d" % quality['abnormal_prices'])
    
    print("\n【事件类型分布】")
    for ann_type, count in report['event_coverage'].items():
        print("  %s: %d 条" % (ann_type, count))
    
    print("\n【优化建议】")
    for i, rec in enumerate(report['recommendations'], 1):
        print("  %d. %s" % (i, rec))
    
    print("\n" + "=" * 60)
    print("完整报告已保存到: %s" % output_path)
    print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description='自动化评估脚本')
    parser.add_argument('--input', type=str, default='outputs/extract_results/structured_data.json',
                        help='抽取结果文件路径')
    parser.add_argument('--errors', type=str, default='outputs/logs/validation_errors.jsonl',
                        help='校验错误文件路径')
    parser.add_argument('--output', type=str, default='outputs/eval/auto_eval_report.json',
                        help='评估报告输出路径')
    args = parser.parse_args()
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    print("[INFO] 开始自动化评估...")
    
    records = load_extract_results(args.input)
    errors = load_validation_errors(args.errors)
    
    if not records:
        print("警告: 未找到抽取结果数据")
    
    report = generate_evaluation_report(records, errors, args.output)
    print_report_summary(report, args.output)

if __name__ == '__main__':
    main()
