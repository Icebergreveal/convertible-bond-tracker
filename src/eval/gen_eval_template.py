import os
import json
import csv
import random
from typing import List, Dict

def generate_eval_template(
    input_path: str = "outputs/extract_results/structured_data.json",
    output_path: str = "outputs/eval/eval_manual_sample.csv",
    sample_ratio: float = 0.1
):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if os.path.exists(input_path):
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        print(f"Warning: {input_path} not found. Generating empty evaluation template.")
        data = []
    
    sample_size = max(10, int(len(data) * sample_ratio)) if data else 0
    sample = random.sample(data, min(sample_size, len(data))) if data else []
    
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
