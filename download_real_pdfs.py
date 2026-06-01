#!/usr/bin/env python3
import os
import csv
import time
import random
import requests
from pathlib import Path

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0',
]

def download_pdf(pdf_url: str, output_dir: str, doc_id: str) -> tuple:
    if not pdf_url or not pdf_url.endswith('.PDF'):
        return False, 'Invalid PDF URL'
    
    headers = {
        'User-Agent': random.choice(USER_AGENTS),
        'Referer': 'https://www.cninfo.com.cn/',
    }
    
    try:
        response = requests.get(pdf_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        if response.status_code == 200 and len(response.content) > 1000:
            output_path = os.path.join(output_dir, f"{doc_id}.pdf")
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True, len(response.content)
        else:
            return False, f'Small file: {len(response.content)} bytes'
    except Exception as e:
        return False, str(e)

def main():
    input_path = 'data/metadata/metadata_real.csv'
    output_dir = 'data/pdf'
    
    os.makedirs(output_dir, exist_ok=True)
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    records = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        records = list(reader)
    
    print(f"=== 开始下载PDF文件 ===")
    print(f"总记录数: {len(records)}")
    print(f"保存目录: {output_dir}\n")
    
    success_count = 0
    fail_count = 0
    skip_count = 0
    
    for i, record in enumerate(records):
        doc_id = record.get('doc_id', '')
        pdf_url = record.get('pdf_url', '')
        stock_name = record.get('stock_name', 'Unknown')
        ann_type = record.get('ann_type', 'Unknown')
        
        existing_pdf = os.path.join(output_dir, f"{doc_id}.pdf")
        if os.path.exists(existing_pdf):
            skip_count += 1
            continue
        
        if i % 10 == 0:
            print(f"[进度] {i+1}/{len(records)}")
        
        success, info = download_pdf(pdf_url, output_dir, doc_id)
        
        if success:
            success_count += 1
            record['download_status'] = 'completed'
        else:
            fail_count += 1
            record['download_status'] = f'failed: {info}'
        
        time.sleep(1 + random.uniform(0.5, 1.0))
    
    with open(input_path, 'w', encoding='utf-8', newline='') as f:
        fieldnames = list(records[0].keys()) if records else []
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    print(f"\n=== 下载完成 ===")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print(f"跳过: {skip_count}")
    print(f"总文件数: {success_count + fail_count}")
    
    existing_pdfs = [f for f in os.listdir(output_dir) if f.endswith('.pdf')]
    print(f"\n目录中现有PDF文件: {len(existing_pdfs)}")

if __name__ == '__main__':
    main()
