import os
import json
import csv
import re
from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import ValidationError
from src.schema.schemas import ConversionPriceAdjustment, EarlyRedemption

import math

DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')

def is_nan(value) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, str) and value.lower() in ['nan', 'none', 'null', '']:
        return True
    return False

def validate_date_format(date_str: Optional[str]) -> bool:
    if is_nan(date_str):
        return True
    if not isinstance(date_str, str):
        return False
    if not DATE_PATTERN.match(date_str):
        return False
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def validate_numeric(value: Any, field_name: str) -> List[str]:
    errors = []
    if is_nan(value):
        return errors
    
    numeric_fields = [
        'original_conv_price', 'new_conv_price', 'avg_price_20d', 'avg_price_1d',
        'adjustment_ratio', 'redemption_price', 'premium_rate', 'evidence_page'
    ]
    
    if field_name in numeric_fields:
        try:
            float(value)
        except (ValueError, TypeError):
            errors.append(f"{field_name} 必须是数字类型，当前值: {value}")
    
    return errors

def validate_required_fields(record: Dict) -> List[str]:
    errors = []
    required_fields = ['doc_id', 'stock_code', 'stock_name', 'ann_type']
    
    for field in required_fields:
        value = record.get(field)
        if is_nan(value):
            errors.append(f"必填字段 {field} 为空")
    
    return errors

def clean_nan_values(record: Dict) -> Dict:
    cleaned = {}
    for key, value in record.items():
        if is_nan(value):
            cleaned[key] = None
        else:
            cleaned[key] = value
    return cleaned

def validate_record(record: Dict) -> dict:
    result = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'parsed': None
    }
    
    cleaned_record = clean_nan_values(record)
    
    result['errors'].extend(validate_required_fields(cleaned_record))
    
    date_fields = ['publish_date', 'pricing_base_date', 'effective_date', 
                   'record_date', 'last_convert_date', 'delisting_date']
    for field in date_fields:
        date_value = cleaned_record.get(field)
        if not validate_date_format(date_value):
            result['errors'].append(f"日期格式错误: {field} = {date_value} (期望格式: YYYY-MM-DD)")
    
    numeric_fields_to_check = ['original_conv_price', 'new_conv_price', 'avg_price_20d', 
                               'avg_price_1d', 'adjustment_ratio', 'redemption_price', 
                               'premium_rate', 'evidence_page']
    for field in numeric_fields_to_check:
        value = cleaned_record.get(field)
        result['errors'].extend(validate_numeric(value, field))
    
    if result['errors']:
        result['valid'] = False
        return result
    
    ann_type = cleaned_record.get('ann_type', '')
    
    try:
        if '下修' in ann_type:
            parsed = ConversionPriceAdjustment(**cleaned_record)
            result['parsed'] = parsed.dict()
        elif '强赎' in ann_type or '赎回' in ann_type:
            parsed = EarlyRedemption(**cleaned_record)
            result['parsed'] = parsed.dict()
        else:
            result['warnings'].append(f"未知公告类型: {ann_type}，未进行Pydantic校验")
            result['parsed'] = cleaned_record
            
    except ValidationError as e:
        for err in e.errors():
            field_path = '.'.join(str(p) for p in err['loc'])
            result['errors'].append(f"Pydantic校验失败 [{field_path}]: {err['msg']}")
        result['valid'] = False
    
    if result['parsed']:
        if result['parsed'].get('new_conv_price') and result['parsed'].get('original_conv_price'):
            if result['parsed']['new_conv_price'] > result['parsed']['original_conv_price']:
                result['warnings'].append("新转股价高于原转股价，可能存在异常")
    
    return result

def validate_results(input_path: str = "outputs/extract_results/structured_data.json"):
    output_path = "outputs/extract_results/records_validated.csv"
    error_path = "outputs/logs/validation_errors.jsonl"
    warning_path = "outputs/logs/validation_warnings.jsonl"
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    os.makedirs(os.path.dirname(error_path), exist_ok=True)
    
    if not os.path.exists(input_path):
        print(f"错误: 输入文件不存在 {input_path}")
        return {
            'total': 0,
            'valid': 0,
            'errors': 0,
            'warnings': 0
        }
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    valid_records = []
    errors = []
    warnings = []
    
    for record in data:
        validation = validate_record(record)
        
        if validation['errors']:
            errors.append({
                "doc_id": record.get('doc_id'),
                "ann_type": record.get('ann_type'),
                "errors": validation['errors'],
                "record": record,
                "timestamp": datetime.now().isoformat()
            })
        else:
            valid_records.append(validation['parsed'] if validation['parsed'] else record)
        
        if validation['warnings']:
            warnings.append({
                "doc_id": record.get('doc_id'),
                "ann_type": record.get('ann_type'),
                "warnings": validation['warnings'],
                "timestamp": datetime.now().isoformat()
            })
    
    fieldnames = [
        'doc_id', 'stock_code', 'stock_name', 'bond_code', 'bond_name',
        'ann_type', 'publish_date', 'trigger_rule', 'original_conv_price',
        'new_conv_price', 'pricing_base_date', 'avg_price_20d', 'avg_price_1d',
        'effective_date', 'adjustment_ratio', 'adjustment_type',
        'redemption_trigger', 'redemption_price', 'record_date',
        'last_convert_date', 'delisting_date', 'premium_rate',
        'evidence_page', 'evidence_text', 'notes'
    ]
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in valid_records:
            row = {k: record.get(k, '') for k in fieldnames}
            writer.writerow(row)
    
    with open(error_path, 'w', encoding='utf-8') as f:
        for error in errors:
            f.write(json.dumps(error, ensure_ascii=False) + '\n')
    
    with open(warning_path, 'w', encoding='utf-8') as f:
        for warning in warnings:
            f.write(json.dumps(warning, ensure_ascii=False) + '\n')
    
    print("=== 校验完成 ===")
    print(f"  总记录数: {len(data)}")
    print(f"  通过校验: {len(valid_records)}")
    print(f"  校验失败: {len(errors)}")
    print(f"  警告: {len(warnings)}")
    print(f"  验证结果保存到: {output_path}")
    print(f"  错误记录保存到: {error_path}")
    print(f"  警告记录保存到: {warning_path}")
    
    if errors:
        print("\n=== 错误详情 ===")
        for i, error in enumerate(errors[:5], 1):
            print(f"\n错误 {i}:")
            print(f"  doc_id: {error['doc_id']}")
            print(f"  ann_type: {error['ann_type']}")
            print(f"  错误信息: {', '.join(error['errors'])}")
    
    return {
        'total': len(data),
        'valid': len(valid_records),
        'errors': len(errors),
        'warnings': len(warnings)
    }

if __name__ == '__main__':
    print("🚀 开始Pydantic校验...")
    result = validate_results()
    print("\n✅ 校验完成")
