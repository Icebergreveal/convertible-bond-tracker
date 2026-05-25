import os
import json
import csv
import re
from datetime import datetime
from typing import List, Dict

def parse_chinese_date(date_str: str, default_year: int = None) -> str:
    if not date_str:
        return None
    
    date_str = str(date_str).strip()
    
    patterns = [
        r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})[日号]?',
        r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})',
        r'(\d{1,2})[月/-](\d{1,2})[日号]?[，,至到](\d{4})年',
        r'(\d{4})年(\d{1,2})月',
        r'(\d{1,2})月(\d{1,2})日'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, date_str)
        if match:
            groups = match.groups()
            
            if len(groups) == 3:
                if pattern == r'(\d{1,2})[月/-](\d{1,2})[日号]?[，,至-到](\d{4})年':
                    month, day, year = groups
                else:
                    year, month, day = groups
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            
            elif len(groups) == 2:
                if '年' in date_str and '月' in date_str:
                    year, month = groups
                    return f"{year}-{month.zfill(2)}-01"
                else:
                    month, day = groups
                    year = str(default_year or datetime.now().year)
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    
    return None

def clean_price(value: str) -> float:
    if not value:
        return None
    
    value = str(value).strip()
    
    value = re.sub(r'[,，]', '', value)
    
    match = re.search(r'([\d.]+)', value)
    if match:
        try:
            return round(float(match.group(1)), 2)
        except:
            return None
    
    return None

def clean_ratio(value: str) -> float:
    if not value:
        return None
    
    value = str(value).strip()
    
    value = re.sub(r'[,，]', '', value)
    
    match = re.search(r'([\d.]+)\s*%?', value)
    if match:
        try:
            return round(float(match.group(1)), 2)
        except:
            return None
    
    return None

def convert_amount(value: str) -> int:
    if not value:
        return None
    
    value = str(value).strip()
    value = re.sub(r'[,，]', '', value)
    
    billion_pattern = r'([\d.]+)\s*[亿亿元]'
    million_pattern = r'([\d.]+)\s*[万万元]'
    
    billion_match = re.search(billion_pattern, value)
    if billion_match:
        try:
            return int(float(billion_match.group(1)) * 10000)
        except:
            return None
    
    million_match = re.search(million_pattern, value)
    if million_match:
        try:
            return int(float(million_match.group(1)))
        except:
            return None
    
    match = re.search(r'(\d+)', value)
    if match:
        try:
            return int(match.group(1))
        except:
            return None
    
    return None

def parse_relative_date(base_date: str, offset_days: int) -> str:
    try:
        base = datetime.strptime(base_date, '%Y-%m-%d')
        result = base + timedelta(days=offset_days)
        return result.strftime('%Y-%m-%d')
    except:
        return None

def standardize_data(input_path: str = "outputs/extract_results/structured_data.json") -> List[Dict]:
    output_path = "outputs/extract_results/structured_data_standardized.json"
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if os.path.exists(input_path):
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        print(f"Warning: {input_path} not found. Generating sample standardized data.")
        data = generate_sample_structured_data()
    
    standardized = []
    current_year = datetime.now().year
    
    for record in data:
        std_record = record.copy()
        
        publish_date = record.get('publish_date', '')
        parsed_publish_date = parse_chinese_date(publish_date, current_year)
        
        std_record['publish_date'] = parsed_publish_date or publish_date
        
        for date_field in ['effective_date', 'record_date', 'last_convert_date', 
                          'delisting_date', 'pricing_base_date']:
            date_value = record.get(date_field, '')
            parsed = parse_chinese_date(date_value, current_year)
            std_record[date_field] = parsed or date_value
        
        for price_field in ['original_conv_price', 'new_conv_price', 'redemption_price',
                           'avg_price_20d', 'avg_price_1d']:
            price_value = record.get(price_field)
            std_record[price_field] = clean_price(price_value)
        
        for ratio_field in ['adjustment_ratio', 'premium_rate']:
            ratio_value = record.get(ratio_field)
            std_record[ratio_field] = clean_ratio(ratio_value)
        
        if std_record.get('evidence_text'):
            std_record['evidence_text'] = str(std_record['evidence_text'])
            std_record['evidence_text'] = re.sub(r'\s+', ' ', std_record['evidence_text']).strip()
        
        if std_record.get('evidence_page'):
            try:
                std_record['evidence_page'] = int(std_record['evidence_page'])
            except:
                std_record['evidence_page'] = None
        
        standardized.append(std_record)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(standardized, f, ensure_ascii=False, indent=2)
    
    print(f"Standardized data saved to: {output_path}")
    return standardized

def generate_sample_structured_data():
    from datetime import datetime, timedelta
    
    today = datetime.now()
    sample_data = []
    
    bonds = [
        {'bond_code': '127061', 'bond_name': '美锦转债', 'stock_code': '000723', 'stock_name': '美锦能源'},
        {'bond_code': '128152', 'bond_name': '龙大转债', 'stock_code': '002726', 'stock_name': '龙大美食'},
        {'bond_code': '128147', 'bond_name': '双汇转债', 'stock_code': '000895', 'stock_name': '双汇发展'},
    ]
    
    ann_types = [
        {'type': '下修触发提示', 'fields': {'trigger_rule': '连续30个交易日中有15个交易日收盘价低于转股价的85%'}},
        {'type': '下修提议', 'fields': {'original_conv_price': 10.50, 'new_conv_price': 8.50}},
        {'type': '下修决议', 'fields': {'original_conv_price': 10.50, 'new_conv_price': 8.50}},
        {'type': '下修实施', 'fields': {'original_conv_price': 10.50, 'new_conv_price': 8.50, 'effective_date': '2026-06-12'}},
        {'type': '强赎触发提示', 'fields': {'redemption_trigger': '连续30个交易日中有15个交易日收盘价不低于转股价的130%'}},
        {'type': '强赎决议', 'fields': {'redemption_price': 103.50}},
        {'type': '强赎实施', 'fields': {'redemption_price': 103.50, 'record_date': '2026-05-05', 'last_convert_date': '2026-05-05'}},
        {'type': '强赎结果', 'fields': {'redemption_price': 103.50, 'delisting_date': '2026-05-12'}},
    ]
    
    for bond in bonds:
        for ann_type in ann_types:
            days_ago = hash(f"{bond['bond_code']}{ann_type['type']}") % 365
            publish_date = (today - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            
            record = {
                'doc_id': f"doc_{bond['bond_code']}_{ann_type['type']}",
                'stock_code': bond['stock_code'],
                'stock_name': bond['stock_name'],
                'bond_code': bond['bond_code'],
                'bond_name': bond['bond_name'],
                'ann_type': ann_type['type'],
                'publish_date': publish_date,
                'evidence_text': f"Sample evidence for {ann_type['type']}",
                'evidence_page': 1,
                'notes': 'Sample data'
            }
            
            record.update(ann_type['fields'])
            
            if '下修' in ann_type['type']:
                record['adjustment_type'] = '主动下修'
            elif '强赎' in ann_type['type'] or '赎回' in ann_type['type']:
                record['adjustment_type'] = None
            
            sample_data.append(record)
    
    return sample_data

if __name__ == '__main__':
    print("Standardizing data...")
    standardize_data()