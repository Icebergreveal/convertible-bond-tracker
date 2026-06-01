import os
import json
import csv
import requests
from datetime import datetime
from typing import List, Dict

def parse_pdf_with_pypdf2(pdf_path: str, output_dir: str) -> dict:
    try:
        from PyPDF2 import PdfReader
        
        doc_id = os.path.splitext(os.path.basename(pdf_path))[0]
        md_path = os.path.join(output_dir, f"{doc_id}.md")
        json_path = os.path.join(output_dir, f"{doc_id}.json")
        
        if os.path.exists(md_path) and os.path.exists(json_path):
            return {"status": "success", "parser": "PyPDF2 (cached)"}
        
        reader = PdfReader(pdf_path)
        text = ""
        for page_num, page in enumerate(reader.pages, 1):
            page_text = page.extract_text()
            if page_text:
                text += f"--- Page {page_num} ---\n{page_text}\n\n"
        
        if not text.strip():
            return {"status": "failed", "parser": "PyPDF2", "error": "PDF contains no extractable text (possibly scanned/image-based)"}
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        parse_info = {
            "doc_id": doc_id,
            "pdf_path": pdf_path,
            "md_path": md_path,
            "parse_time": datetime.now().isoformat(),
            "status": "success",
            "parser": "PyPDF2",
            "pages": len(reader.pages),
            "char_count": len(text)
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(parse_info, f, ensure_ascii=False, indent=2)
        
        return {"status": "success", "parser": "PyPDF2", "pages": len(reader.pages)}
        
    except Exception as e:
        return {"status": "failed", "parser": "PyPDF2", "error": str(e)}

def parse_pdf_with_mineru_api(pdf_path: str, output_dir: str, api_key: str) -> dict:
    try:
        doc_id = os.path.splitext(os.path.basename(pdf_path))[0]
        md_path = os.path.join(output_dir, f"{doc_id}.md")
        json_path = os.path.join(output_dir, f"{doc_id}.json")
        
        if os.path.exists(md_path) and os.path.exists(json_path):
            return {"status": "success", "parser": "MinerU_API (cached)"}
        
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
            if "content" in result and result["content"].strip():
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(result["content"])
                
                parse_info = {
                    "doc_id": doc_id,
                    "pdf_path": pdf_path,
                    "md_path": md_path,
                    "parse_time": datetime.now().isoformat(),
                    "status": "success",
                    "parser": "MinerU_API",
                    "pages": result.get("pages", 0),
                    "char_count": len(result["content"])
                }
                
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(parse_info, f, ensure_ascii=False, indent=2)
                
                return {"status": "success", "parser": "MinerU_API", "pages": result.get("pages", 0)}
            else:
                return {"status": "failed", "parser": "MinerU_API", "error": "API returned empty content"}
        else:
            error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
            return {"status": "failed", "parser": "MinerU_API", "error": error_msg}
            
    except requests.exceptions.Timeout:
        return {"status": "failed", "parser": "MinerU_API", "error": "Request timed out"}
    except requests.exceptions.RequestException as e:
        return {"status": "failed", "parser": "MinerU_API", "error": f"Network error: {str(e)[:100]}"}
    except Exception as e:
        return {"status": "failed", "parser": "MinerU_API", "error": str(e)[:200]}

def parse_pdf(pdf_path: str, output_dir: str, api_key: str = None) -> dict:
    if not os.path.exists(pdf_path):
        return {"status": "failed", "parser": "N/A", "error": f"PDF file not found: {pdf_path}"}
    
    if api_key:
        result = parse_pdf_with_mineru_api(pdf_path, output_dir, api_key)
        if result["status"] == "success":
            return result
        print(f"MinerU API failed ({result.get('error', 'unknown')}), falling back to PyPDF2")
    
    return parse_pdf_with_pypdf2(pdf_path, output_dir)

def batch_parse_pdfs(config: Dict, limit: int = None):
    metadata_path = config['output']['metadata']
    pdf_dir = config['output']['pdf_dir']
    parsed_dir = "data/parsed"
    log_path = "outputs/logs/parse_quality.log"
    failed_records_path = "outputs/logs/parse_failed_records.csv"
    review_queue_path = "outputs/logs/manual_review_queue.csv"
    
    api_key = config.get('mineru', {}).get('api_key')
    
    os.makedirs(parsed_dir, exist_ok=True)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    records = []
    valid_status = {'success', 'skipped', 'completed', 'pending'}
    with open(metadata_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        records = [r for r in reader if r.get('download_status') in valid_status]
    
    if limit:
        records = records[:limit]
    
    success_count = 0
    fail_count = 0
    failed_records = []
    review_queue = []
    
    with open(log_path, 'w', encoding='utf-8') as log_file:
        log_file.write(f"Parse started at {datetime.now()}\n")
        log_file.write(f"Total PDFs to parse: {len(records)}\n")
        log_file.write(f"Using MinerU API: {api_key is not None}\n\n")
        
        for i, record in enumerate(records, 1):
            doc_id = record['doc_id']
            pdf_path = os.path.join(pdf_dir, f"{doc_id}.pdf")
            
            print(f"Parsing [{i}/{len(records)}] {doc_id}")
            
            result = parse_pdf(pdf_path, parsed_dir, api_key)
            
            if result["status"] == "success":
                success_count += 1
                log_file.write(f"OK [{i}] {doc_id} - {result['parser']}")
                if 'pages' in result:
                    log_file.write(f" ({result['pages']} pages)")
                log_file.write("\n")
            else:
                fail_count += 1
                error_msg = result.get('error', 'Unknown error')
                log_file.write(f"FAIL [{i}] {doc_id} - {result['parser']}: {error_msg}\n")
                
                failed_record = {
                    "doc_id": doc_id,
                    "stock_code": record.get('stock_code', ''),
                    "stock_name": record.get('stock_name', ''),
                    "ann_title": record.get('ann_title', ''),
                    "publish_date": record.get('publish_date', ''),
                    "pdf_path": pdf_path,
                    "parser_attempted": result['parser'],
                    "error_message": error_msg,
                    "parse_time": datetime.now().isoformat(),
                    "review_status": "pending",
                    "review_comment": ""
                }
                failed_records.append(failed_record)
                
                if "scanned" in error_msg.lower() or "image" in error_msg.lower():
                    review_queue.append({
                        "doc_id": doc_id,
                        "reason": "Image-based PDF - requires manual review",
                        "priority": "high"
                    })
                elif "network" in error_msg.lower() or "timeout" in error_msg.lower():
                    review_queue.append({
                        "doc_id": doc_id,
                        "reason": "Network error - retry recommended",
                        "priority": "medium"
                    })
                else:
                    review_queue.append({
                        "doc_id": doc_id,
                        "reason": f"Parse failed: {error_msg}",
                        "priority": "low"
                    })
        
        log_file.write(f"\nParse completed at {datetime.now()}\n")
        log_file.write(f"Success: {success_count}\n")
        log_file.write(f"Failed: {fail_count}\n")
        if len(records) > 0:
            log_file.write(f"Success rate: {(success_count / len(records)) * 100:.1f}%\n")
        else:
            log_file.write(f"Success rate: N/A (no records to parse)\n")
    
    if failed_records:
        with open(failed_records_path, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ["doc_id", "stock_code", "stock_name", "ann_title", "publish_date", 
                         "pdf_path", "parser_attempted", "error_message", "parse_time", 
                         "review_status", "review_comment"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(failed_records)
        print(f"\nFailed records saved to: {failed_records_path}")
    
    if review_queue:
        with open(review_queue_path, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ["doc_id", "reason", "priority", "review_status", "reviewer", "review_date", "review_note"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for item in review_queue:
                writer.writerow({
                    "doc_id": item["doc_id"],
                    "reason": item["reason"],
                    "priority": item["priority"],
                    "review_status": "pending",
                    "reviewer": "",
                    "review_date": "",
                    "review_note": ""
                })
        print(f"Manual review queue saved to: {review_queue_path}")
    
    print(f"\nParse summary:")
    print(f"  Success: {success_count}")
    print(f"  Failed: {fail_count}")
    if len(records) > 0:
        print(f"  Success rate: {(success_count / len(records)) * 100:.1f}%")
    else:
        print(f"  Success rate: N/A (no records to parse)")
    print(f"Log saved to: {log_path}")
    
    return {
        'total': len(records),
        'success': success_count,
        'failed': fail_count,
        'failed_records': failed_records
    }

def retry_failed_parses(config: Dict):
    failed_records_path = "outputs/logs/parse_failed_records.csv"
    
    if not os.path.exists(failed_records_path):
        print("No failed records found to retry")
        return
    
    api_key = config.get('mineru', {}).get('api_key')
    parsed_dir = "data/parsed"
    
    with open(failed_records_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        failed_records = list(reader)
    
    retry_success = 0
    retry_fail = 0
    
    for record in failed_records:
        if record.get('review_status') == 'completed':
            continue
        
        doc_id = record['doc_id']
        pdf_path = record['pdf_path']
        
        print(f"Retrying parse for {doc_id}")
        
        result = parse_pdf(pdf_path, parsed_dir, api_key)
        
        if result["status"] == "success":
            retry_success += 1
            record['review_status'] = 'completed'
            record['review_comment'] = f"Retry succeeded with {result['parser']}"
            print(f"  ✅ Success")
        else:
            retry_fail += 1
            print(f"  ❌ Failed: {result.get('error', 'unknown')}")
    
    with open(failed_records_path, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ["doc_id", "stock_code", "stock_name", "ann_title", "publish_date", 
                     "pdf_path", "parser_attempted", "error_message", "parse_time", 
                     "review_status", "review_comment"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(failed_records)
    
    print(f"\nRetry summary:")
    print(f"  Total retried: {len(failed_records)}")
    print(f"  Success: {retry_success}")
    print(f"  Failed: {retry_fail}")

if __name__ == '__main__':
    print("Starting PDF parse...")
    config = {
        'output': {
            'metadata': 'data/metadata/metadata.csv',
            'pdf_dir': 'data/pdf'
        },
        'mineru': {
            'api_key': os.getenv('MINERU_API_KEY', '')
        }
    }
    batch_parse_pdfs(config)