import os
import json
import csv
from collections import Counter
from typing import Dict
import argparse
from src.crawl.load_config import load_config, parse_args

def check_parse_quality(config: Dict):
    metadata_path = config['output']['metadata']
    pdf_dir = config['output']['pdf_dir']
    parsed_dir = "data/parsed"
    report_path = "outputs/logs/parse_quality.log"
    
    records = []
    with open(metadata_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        records = [r for r in reader if r['download_status'] == 'success']
    
    parsed_count = 0
    empty_count = 0
    quality_issues = []
    
    for record in records:
        doc_id = record['doc_id']
        md_path = os.path.join(parsed_dir, f"{doc_id}.md")
        
        if os.path.exists(md_path):
            parsed_count += 1
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if len(content.strip()) < 50:
                    empty_count += 1
                    quality_issues.append((doc_id, "empty_content"))
        else:
            quality_issues.append((doc_id, "not_found"))
    
    success_rate = (parsed_count / len(records)) * 100 if records else 0
    empty_rate = (empty_count / parsed_count) * 100 if parsed_count else 0
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Parse Quality Report\n\n")
        f.write("## Summary\n")
        f.write(f"- Total PDFs: {len(records)}\n")
        f.write(f"- Successfully parsed: {parsed_count}\n")
        f.write(f"- Empty content: {empty_count}\n")
        f.write(f"- Parse success rate: {success_rate:.1f}%\n")
        f.write(f"- Empty content rate: {empty_rate:.1f}%\n")
        
        if quality_issues:
            f.write(f"\n## Quality Issues ({len(quality_issues)})\n")
            for doc_id, issue in quality_issues[:20]:
                f.write(f"- {doc_id}: {issue}\n")
            if len(quality_issues) > 20:
                f.write(f"- ... and {len(quality_issues) - 20} more\n")
        
        f.write("\n## Quality Assessment\n")
        if success_rate >= 95:
            f.write("- PASS: Parse success rate meets target (≥95%)\n")
        else:
            f.write(f"- WARNING: Parse success rate ({success_rate:.1f}%) below target\n")
        
        if empty_rate < 5:
            f.write("- PASS: Empty content rate is acceptable (<5%)\n")
        else:
            f.write(f"- WARNING: Empty content rate ({empty_rate:.1f}%) is high\n")
    
    print(f"Parse quality report saved to {report_path}")
    return {
        'total_pdfs': len(records),
        'parsed_count': parsed_count,
        'success_rate': success_rate,
        'empty_count': empty_count
    }

if __name__ == '__main__':
    args = parse_args()
    config = load_config(args.config)
    
    print("Checking parse quality...")
    result = check_parse_quality(config)
    
    print(f"\nQuality Summary:")
    print(f"  Total PDFs: {result['total_pdfs']}")
    print(f"  Parsed: {result['parsed_count']}")
    print(f"  Success rate: {result['success_rate']:.1f}%")