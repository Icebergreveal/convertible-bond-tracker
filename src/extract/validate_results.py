import os
import json
import csv
from datetime import datetime
from typing import List, Dict
from src.schema.schemas import ConversionPriceAdjustment, EarlyRedemption
from src.crawl.load_config import load_config, parse_args

def validate_results(input_path: str = "outputs/extract_results/structured_data.json"):
    output_path = "outputs/extract_results/records_validated.csv"
    error_path = "outputs/logs/validation_errors.jsonl"
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    os.makedirs(os.path.dirname(error_path), exist_ok=True)
    
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    valid_records = []
    errors = []
    
    for record in data:
        ann_type = record.get('ann_type', '')
        
        try:
            if '下修' in ann_type:
                parsed = ConversionPriceAdjustment(**record)
            elif '强赎' in ann_type or '赎回' in ann_type:
                parsed = EarlyRedemption(**record)
            else:
                parsed = record
            
            valid_records.append(record)
            
        except Exception as e:
            errors.append({
                "doc_id": record.get('doc_id'),
                "ann_type": ann_type,
                "error": str(e),
                "record": record
            })
    
    fieldnames = ['doc_id', 'stock_code', 'stock_name', 'bond_code', 'bond_name',
                  'ann_type', 'publish_date', 'trigger_rule', 'original_conv_price',
                  'new_conv_price', 'effective_date', 'redemption_trigger',
                  'redemption_price', 'record_date', 'last_convert_date',
                  'evidence_page', 'evidence_text']
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in valid_records:
            row = {k: record.get(k, '') for k in fieldnames}
            writer.writerow(row)
    
    with open(error_path, 'w', encoding='utf-8') as f:
        for error in errors:
            f.write(json.dumps(error, ensure_ascii=False) + '\n')
    
    print(f"Validation completed:")
    print(f"  Total records: {len(data)}")
    print(f"  Valid: {len(valid_records)}")
    print(f"  Errors: {len(errors)}")
    print(f"Validated records saved to: {output_path}")
    print(f"Errors saved to: {error_path}")
    
    return {
        'total': len(data),
        'valid': len(valid_records),
        'errors': len(errors)
    }

if __name__ == '__main__':
    args = parse_args()
    config = load_config(args.config)
    
    print("Validating extraction results...")
    validate_results()