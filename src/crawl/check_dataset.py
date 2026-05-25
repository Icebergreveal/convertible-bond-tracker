import os
import csv
from collections import Counter
from typing import Dict, List
import argparse
from .load_config import load_config, parse_args

def check_dataset(config: Dict):
    metadata_path = config['output']['metadata']
    pdf_dir = config['output']['pdf_dir']
    report_path = "outputs/logs/dataset_quality.log"
    
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    records = []
    with open(metadata_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        records = list(reader)
    
    total_records = len(records)
    
    ann_type_counts = Counter()
    stock_counts = Counter()
    download_status_counts = Counter()
    missing_pdf = []
    duplicate_docs = []
    
    seen_docs = set()
    for record in records:
        ann_type_counts[record['ann_type']] += 1
        stock_counts[record['stock_code']] += 1
        download_status_counts[record['download_status']] += 1
        
        if record['doc_id'] in seen_docs:
            duplicate_docs.append(record['doc_id'])
        seen_docs.add(record['doc_id'])
        
        if record['download_status'] == 'success':
            pdf_path = os.path.join(pdf_dir, f"{record['doc_id']}.pdf")
            if not os.path.exists(pdf_path):
                missing_pdf.append(record['doc_id'])
    
    success_count = download_status_counts.get('success', 0)
    failed_count = download_status_counts.get('failed', 0)
    skipped_count = download_status_counts.get('skipped', 0)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Dataset Quality Report\n\n")
        f.write("## Summary\n")
        f.write(f"- Total records: {total_records}\n")
        f.write(f"- Unique stocks: {len(stock_counts)}\n")
        f.write(f"- Download success: {success_count}\n")
        f.write(f"- Download failed: {failed_count}\n")
        f.write(f"- Already exists: {skipped_count}\n")
        f.write(f"- Duplicate doc_ids: {len(duplicate_docs)}\n")
        
        f.write("\n## Announcement Type Distribution\n")
        for ann_type, count in sorted(ann_type_counts.items()):
            percentage = (count / total_records) * 100
            f.write(f"- {ann_type}: {count} ({percentage:.1f}%)\n")
        
        f.write("\n## Top 10 Stocks by Record Count\n")
        for stock, count in stock_counts.most_common(10):
            f.write(f"- {stock}: {count} records\n")
        
        f.write("\n## Download Status Breakdown\n")
        for status, count in download_status_counts.items():
            f.write(f"- {status}: {count}\n")
        
        if missing_pdf:
            f.write(f"\n## Missing PDF Files ({len(missing_pdf)})\n")
            for doc_id in missing_pdf[:10]:
                f.write(f"- {doc_id}\n")
            if len(missing_pdf) > 10:
                f.write(f"- ... and {len(missing_pdf) - 10} more\n")
        
        if duplicate_docs:
            f.write(f"\n## Duplicate doc_ids ({len(duplicate_docs)})\n")
            for doc_id in duplicate_docs[:10]:
                f.write(f"- {doc_id}\n")
            if len(duplicate_docs) > 10:
                f.write(f"- ... and {len(duplicate_docs) - 10} more\n")
        
        f.write("\n## Quality Assessment\n")
        issues = []
        
        if total_records < 150:
            issues.append(f"WARNING: Total records ({total_records}) below target (150)")
        else:
            issues.append(f"PASS: Total records meets target")
        
        required_types = ['下修触发提示', '下修提议', '下修决议', '下修实施', 
                         '强赎触发提示', '强赎决议', '强赎实施', '强赎结果']
        missing_types = [t for t in required_types if ann_type_counts.get(t, 0) == 0]
        if missing_types:
            issues.append(f"WARNING: Missing announcement types: {', '.join(missing_types)}")
        else:
            issues.append(f"PASS: All 8 announcement types present")
        
        if success_count < 150:
            issues.append(f"WARNING: Downloaded PDFs ({success_count}) below target (150)")
        else:
            issues.append(f"PASS: Downloaded PDFs meets target")
        
        if duplicate_docs:
            issues.append(f"WARNING: Found {len(duplicate_docs)} duplicate records")
        else:
            issues.append(f"PASS: No duplicates found")
        
        for issue in issues:
            f.write(f"- {issue}\n")
    
    print(f"Dataset quality report saved to {report_path}")
    return {
        'total_records': total_records,
        'success_count': success_count,
        'ann_types': dict(ann_type_counts),
        'issues': issues
    }

if __name__ == '__main__':
    args = parse_args()
    config = load_config(args.config)
    
    print("Checking dataset quality...")
    result = check_dataset(config)
    
    print("\nQuality Assessment:")
    for issue in result['issues']:
        print(f"  {issue}")