import os
import json
import csv
import requests
from datetime import datetime
from typing import List, Dict

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

def parse_pdf_with_mineru_api(pdf_path: str, output_dir: str, api_key: str) -> bool:
    try:
        doc_id = os.path.splitext(os.path.basename(pdf_path))[0]
        md_path = os.path.join(output_dir, f"{doc_id}.md")
        json_path = os.path.join(output_dir, f"{doc_id}.json")
        
        if os.path.exists(md_path) and os.path.exists(json_path):
            return True
        
        url = "https://api.mineru.cn/v1/parse"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "file_path": pdf_path,
            "output_format": "markdown",
            "language": "zh"
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=300)
        
        if response.status_code == 200:
            result = response.json()
            if "content" in result:
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(result["content"])
                
                parse_info = {
                    "doc_id": doc_id,
                    "pdf_path": pdf_path,
                    "md_path": md_path,
                    "parse_time": datetime.now().isoformat(),
                    "status": "success",
                    "parser": "MinerU_API",
                    "pages": result.get("pages", 0)
                }
                
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(parse_info, f, ensure_ascii=False, indent=2)
                
                return True
            else:
                print(f"MinerU API returned no content for {pdf_path}")
                return False
        else:
            print(f"MinerU API failed for {pdf_path}: {response.status_code} - {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"MinerU API exception for {pdf_path}: {str(e)[:200]}")
        return False

def parse_pdf(pdf_path: str, output_dir: str, api_key: str = None) -> bool:
    if api_key:
        if parse_pdf_with_mineru_api(pdf_path, output_dir, api_key):
            return True
        print(f"MinerU API failed, falling back to PyPDF2 for {pdf_path}")
    
    return parse_pdf_with_pypdf2(pdf_path, output_dir)

def batch_parse_pdfs(config: Dict, limit: int = None):
    metadata_path = config['output']['metadata']
    pdf_dir = config['output']['pdf_dir']
    parsed_dir = "data/parsed"
    log_path = "outputs/logs/parse_quality.log"
    
    api_key = config.get('mineru', {}).get('api_key')
    
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
        log_file.write(f"Total PDFs to parse: {len(records)}\n")
        log_file.write(f"Using MinerU API: {api_key is not None}\n\n")
        
        for i, record in enumerate(records, 1):
            doc_id = record['doc_id']
            pdf_path = os.path.join(pdf_dir, f"{doc_id}.pdf")
            
            print(f"Parsing [{i}/{len(records)}] {doc_id}")
            
            if parse_pdf(pdf_path, parsed_dir, api_key):
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
    config = {
        'output': {
            'metadata': 'data/metadata/metadata.csv',
            'pdf_dir': 'data/pdf'
        },
        'mineru': {
            'api_key': 'eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiIzMDUwMDc5MSIsInJvbCI6IlJPTEVfUkVHSVNURVIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc3OTY3NzA5NCwiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiZTYyYjMwYjUtMTYxZi00ZDJmLThlMjYtM2U1ODUwMWE0YmIxIiwiZW1haWwiOiIiLCJleHAiOjE3ODc0NTMwOTR9.S1FD2biZpChXqlhiTGNk5wXTIyXjoW2E74Jipt_VyWLmGGTiVbTsGWoHPO3zv1AgIpRDQdrmoYlATu8qDFCEng'
        }
    }
    batch_parse_pdfs(config)
