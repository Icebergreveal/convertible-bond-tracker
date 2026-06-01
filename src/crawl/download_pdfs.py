import os
import requests
import csv
import time
from datetime import datetime
from typing import List, Dict
import argparse
from .load_config import load_config, parse_args

def load_metadata(input_path: str) -> List[Dict[str, str]]:
    records = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records

def download_pdf(url: str, save_path: str, retries: int = 3) -> bool:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'http://www.cninfo.com.cn/'
    }
    
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            if os.path.getsize(save_path) < 100:
                os.remove(save_path)
                return False
            
            return True
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
                continue
            return False

def download_pdfs(config: Dict, limit: int = None):
    metadata_path = config['output']['metadata']
    pdf_dir = config['output']['pdf_dir']
    log_path = "outputs/logs/crawl_download.log"
    
    os.makedirs(pdf_dir, exist_ok=True)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    records = load_metadata(metadata_path)
    
    if limit:
        records = records[:limit]
    
    downloaded = 0
    skipped = 0
    failed = 0
    
    with open(log_path, 'w', encoding='utf-8') as log_file:
        log_file.write(f"Download started at {datetime.now()}\n")
        log_file.write(f"Total records to process: {len(records)}\n\n")
        
        for i, record in enumerate(records, 1):
            doc_id = record['doc_id']
            pdf_url = record['pdf_url']
            save_path = os.path.join(pdf_dir, f"{doc_id}.pdf")
            
            if not pdf_url:
                record['download_status'] = 'failed'
                record['notes'] = 'No PDF URL'
                failed += 1
                log_file.write(f"FAIL [{i}] {doc_id}: No PDF URL\n")
                continue
            
            if os.path.exists(save_path):
                record['download_status'] = 'skipped'
                record['notes'] = 'File already exists'
                skipped += 1
                log_file.write(f"SKIP [{i}] {doc_id}: File exists\n")
                continue
            
            print(f"Downloading [{i}/{len(records)}] {doc_id}")
            
            if download_pdf(pdf_url, save_path):
                record['download_status'] = 'success'
                downloaded += 1
                log_file.write(f"OK [{i}] {doc_id}: Downloaded\n")
            else:
                record['download_status'] = 'failed'
                record['notes'] = 'Download failed'
                failed += 1
                log_file.write(f"FAIL [{i}] {doc_id}: Download failed\n")
            
            time.sleep(config.get('sleep_seconds', 1.0))
        
        log_file.write(f"\nDownload completed at {datetime.now()}\n")
        log_file.write(f"Downloaded: {downloaded}\n")
        log_file.write(f"Skipped: {skipped}\n")
        log_file.write(f"Failed: {failed}\n")
    
    with open(metadata_path, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['doc_id', 'stock_code', 'stock_name', 'bond_code', 'bond_name', 
                      'ann_type', 'event_stage', 'publish_date', 'announcement_url', 'pdf_url', 
                      'download_status', 'crawl_time', 'notes']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    print(f"\nDownload summary:")
    print(f"  Downloaded: {downloaded}")
    print(f"  Skipped: {skipped}")
    print(f"  Failed: {failed}")
    print(f"Log saved to: {log_path}")

if __name__ == '__main__':
    args = parse_args()
    config = load_config(args.config)
    
    print("Starting PDF download...")
    download_pdfs(config, limit=args.limit)