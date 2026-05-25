import os
import json
import csv
from datetime import datetime
from typing import List, Dict
import subprocess

def parse_pdf_with_pypdf2(pdf_path: str, output_dir: str) -> bool:
    try:
        from PyPDF2 import PdfReader
        
        doc_id = os.path.splitext(os.path.basename(pdf_path))[0]
        md_path = os.path.join(output_dir, f"{doc_id}.md")
        json_path = os.path.join(output_dir, f"{doc_id}.json")
        
        if os.path.exists(md_path) and os.path.exists(json_path):
            return True
        
        reader = PdfReader(pdf_path)
        text = ""
        for page_num, page in enumerate(reader.pages, 1):
            page_text = page.extract_text()
            if page_text:
                text += f"--- Page {page_num} ---\n{page_text}\n\n"
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        parse_info = {
            "doc_id": doc_id,
            "pdf_path": pdf_path,
            "md_path": md_path,
            "parse_time": datetime.now().isoformat(),
            "status": "success",
            "parser": "PyPDF2",
            "pages": len(reader.pages)
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(parse_info, f, ensure_ascii=False, indent=2)
        
        return True
        
    except Exception as e:
        print(f"PyPDF2 parse failed for {pdf_path}: {str(e)}")
        return False

def parse_pdf_with_mineru(pdf_path: str, output_dir: str) -> bool:
    try:
        doc_id = os.path.splitext(os.path.basename(pdf_path))[0]
        md_path = os.path.join(output_dir, f"{doc_id}.md")
        json_path = os.path.join(output_dir, f"{doc_id}.json")
        
        if os.path.exists(md_path) and os.path.exists(json_path):
            return True
        
        cmd = (
            f'mineru '
            f'-p "{pdf_path}" '
            f'-o "{output_dir}" '
            f'-l ch '
            f'-b pipeline'
        )
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=180)
        
        if result.returncode == 0:
            parse_info = {
                "doc_id": doc_id,
                "pdf_path": pdf_path,
                "md_path": md_path,
                "parse_time": datetime.now().isoformat(),
                "status": "success",
                "parser": "MinerU"
            }
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(parse_info, f, ensure_ascii=False, indent=2)
            
            return True
        else:
            print(f"MinerU parse failed for {pdf_path}: {result.stderr[:200]}")
            return False
            
    except Exception as e:
        print(f"MinerU parse exception for {pdf_path}: {str(e)[:200]}")
        return False

def parse_pdf(pdf_path: str, output_dir: str) -> bool:
    if parse_pdf_with_mineru(pdf_path, output_dir):
        return True
    print(f"MinerU failed, falling back to PyPDF2 for {pdf_path}")
    return parse_pdf_with_pypdf2(pdf_path, output_dir)

def batch_parse_pdfs(config: Dict, limit: int = None):
    metadata_path = config['output']['metadata']
    pdf_dir = config['output']['pdf_dir']
    parsed_dir = "data/parsed"
    log_path = "outputs/logs/parse_quality.log"
    
    os.makedirs(parsed_dir, exist_ok=True)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    records = []
    valid_status = {'success', 'skipped', 'completed'}
    with open(metadata_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        records = [r for r in reader if r.get('download_status') in valid_status]
    
    if limit:
        records = records[:limit]
    
    success_count = 0
    fail_count = 0
    
    with open(log_path, 'w', encoding='utf-8') as log_file:
        log_file.write(f"Parse started at {datetime.now()}\n")
        log_file.write(f"Total PDFs to parse: {len(records)}\n\n")
        
        for i, record in enumerate(records, 1):
            doc_id = record['doc_id']
            pdf_path = os.path.join(pdf_dir, f"{doc_id}.pdf")
            
            print(f"Parsing [{i}/{len(records)}] {doc_id}")
            
            if parse_pdf(pdf_path, parsed_dir):
                success_count += 1
                log_file.write(f"OK [{i}] {doc_id}\n")
            else:
                fail_count += 1
                log_file.write(f"FAIL [{i}] {doc_id}\n")
        
        log_file.write(f"\nParse completed at {datetime.now()}\n")
        log_file.write(f"Success: {success_count}\n")
        log_file.write(f"Failed: {fail_count}\n")
        if len(records) > 0:
            log_file.write(f"Success rate: {(success_count / len(records)) * 100:.1f}%\n")
        else:
            log_file.write(f"Success rate: N/A (no records to parse)\n")
    
    print(f"\nParse summary:")
    print(f"  Success: {success_count}")
    print(f"  Failed: {fail_count}")
    if len(records) > 0:
        print(f"  Success rate: {(success_count / len(records)) * 100:.1f}%")
    else:
        print(f"  Success rate: N/A (no records to parse)")
    print(f"Log saved to: {log_path}")

if __name__ == '__main__':
    print("Starting PDF parse...")
    batch_parse_pdfs({'output': {'metadata': 'data/metadata/metadata.csv', 'pdf_dir': 'data/pdf'}})