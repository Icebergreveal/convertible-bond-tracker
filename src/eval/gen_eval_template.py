import os
import json
import csv
import random
from typing import List, Dict

def generate_eval_template(input_path: str = "outputs/extract_results/structured_data.json", sample_ratio: float = 0.1):
    output_path = "outputs/eval/eval_manual_sample.csv"
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if os.path.exists(input_path):
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        print(f"Warning: {input_path} not found. Generating template with sample data.")
        data = [
            {'doc_id': 'abc1234567890123', 'stock_code': '000723', 'stock_name': '美锦能源', 
             'bond_code': '127061', 'bond_name': '美锦转债', 'ann_type': '下修触发提示',
             'trigger_rule': '连续30个交易日中有15个交易日收盘价低于转股价格的85%',
             'original_conv_price': 10.50, 'publish_date': '2026-05-12'},
            {'doc_id': 'def4567890123456', 'stock_code': '002726', 'stock_name': '龙大美食',
             'bond_code': '128152', 'bond_name': '龙大转债', 'ann_type': '下修提议',
             'trigger_rule': '连续30个交易日中有20个交易日收盘价低于转股价格的90%',
             'original_conv_price': 8.20, 'new_conv_price': 6.50, 'publish_date': '2026-05-07'},
            {'doc_id': 'ghi7890123456789', 'stock_code': '000895', 'stock_name': '双汇发展',
             'bond_code': '128147', 'bond_name': '双汇转债', 'ann_type': '强赎触发提示',
             'redemption_trigger': '连续15个交易日收盘价不低于转股价格的130%',
             'publish_date': '2026-04-28'},
            {'doc_id': 'jkl0123456789012', 'stock_code': '600519', 'stock_name': '贵州茅台',
             'bond_code': '110061', 'bond_name': '茅台转债', 'ann_type': '强赎决议',
             'redemption_price': 103.50, 'publish_date': '2026-04-20'},
            {'doc_id': 'mno3456789012345', 'stock_code': '002594', 'stock_name': '比亚迪',
             'bond_code': '128115', 'bond_name': '亚迪转债', 'ann_type': '下修实施',
             'original_conv_price': 250.00, 'new_conv_price': 180.00, 'effective_date': '2026-03-15'}
        ]
    
    sample_size = max(10, int(len(data) * sample_ratio))
    sample = random.sample(data, min(sample_size, len(data)))
    
    fieldnames = [
        'doc_id', 'stock_code', 'stock_name', 'bond_code', 'bond_name', 'ann_type',
        'predicted_trigger_rule', 'gold_trigger_rule', 'trigger_correct',
        'predicted_price', 'gold_price', 'price_correct',
        'predicted_date', 'gold_date', 'date_correct',
        'evidence_correct', 'evidence_complete',
        'error_type', 'notes'
    ]
    
    eval_records = []
    for record in sample:
        eval_record = {
            'doc_id': record.get('doc_id', ''),
            'stock_code': record.get('stock_code', ''),
            'stock_name': record.get('stock_name', ''),
            'bond_code': record.get('bond_code', ''),
            'bond_name': record.get('bond_name', ''),
            'ann_type': record.get('ann_type', ''),
            'predicted_trigger_rule': record.get('trigger_rule', '') or record.get('redemption_trigger', ''),
            'gold_trigger_rule': '',
            'trigger_correct': '',
            'predicted_price': record.get('original_conv_price', '') or record.get('redemption_price', ''),
            'gold_price': '',
            'price_correct': '',
            'predicted_date': record.get('publish_date', '') or record.get('effective_date', ''),
            'gold_date': '',
            'date_correct': '',
            'evidence_correct': '',
            'evidence_complete': '',
            'error_type': '',
            'notes': ''
        }
        eval_records.append(eval_record)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(eval_records)
    
    print(f"Evaluation template saved to: {output_path}")
    print(f"Sample size: {len(eval_records)}")
    return eval_records

if __name__ == '__main__':
    print("Generating evaluation template...")
    generate_eval_template()