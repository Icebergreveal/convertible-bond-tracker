#!/usr/bin/env python3
import os
import csv
import time
import random
import hashlib
import requests
from datetime import datetime

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0',
]

KEYWORDS = [
    '转股价向下修正',
    '转股价格修正条件',
    '转债赎回提示',
    '提前赎回可转债',
    '行使赎回权',
    '触发转股价格',
]

def generate_doc_id(stock_code: str, publish_date: str, title: str) -> str:
    raw = f"{stock_code}_{publish_date}_{title}"
    return hashlib.md5(raw.encode('utf-8')).hexdigest()[:16]

def classify_announcement(title: str) -> str:
    if '向下修正' in title or '下修' in title:
        if '触发' in title:
            return '下修触发提示'
        elif '提议' in title:
            return '下修提议'
        elif '决议' in title or '调整' in title:
            return '下修决议'
        elif '实施' in title:
            return '下修实施'
    elif '赎回' in title or '强赎' in title:
        if '触发' in title or '提示' in title:
            return '强赎触发提示'
        elif '决议' in title or '行使' in title:
            return '强赎决议'
        elif '实施' in title:
            return '强赎实施'
        elif '结果' in title or '摘牌' in title:
            return '强赎结果'
    return '其他'

def get_event_stage(title: str) -> str:
    if '下修触发提示' in title:
        return 'stage_1_trigger'
    elif '下修提议' in title:
        return 'stage_2_proposal'
    elif '下修决议' in title:
        return 'stage_3_resolution'
    elif '下修实施' in title:
        return 'stage_4_implementation'
    elif '强赎触发提示' in title:
        return 'stage_1_trigger'
    elif '强赎决议' in title:
        return 'stage_2_resolution'
    elif '强赎实施' in title:
        return 'stage_3_implementation'
    elif '强赎结果' in title:
        return 'stage_4_result'
    return 'stage_unknown'

def extract_bond_info(title: str) -> tuple:
    import re
    bond_code = None
    bond_name = None
    
    code_pattern = re.compile(r'[\u4e00-\u9fa5]*[\uff08\(]*([12]\d{5})[\uff09\)]*[\u4e00-\u9fa5]*转债')
    name_pattern = re.compile(r'([\u4e00-\u9fa5]{2,8})转债')
    
    code_match = code_pattern.search(title)
    name_match = name_pattern.search(title)
    
    if code_match:
        code = code_match.group(1)
        if len(code) == 6 and code.startswith(('1', '2')):
            bond_code = code
    
    if name_match:
        possible_name = name_match.group(1)
        if possible_name not in ['可转债', '本转债']:
            bond_name = possible_name + '转债'
    
    return bond_code, bond_name

def search_announcements(keyword: str, limit_per_keyword: int = 50) -> list:
    base_url = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
    results = []
    
    for page_num in range(1, 6):
        try:
            data = {
                'stock': '',
                'searchkey': keyword,
                'plate': '',
                'category': 'category_bnd',
                'trade': '',
                'column': '',
                'columnTitle': '历史公告',
                'pageNum': page_num,
                'pageSize': 30,
                'tabName': 'fulltext',
                'sortName': 'time',
                'sortType': 'desc',
                'limit': '',
                'showTitle': '',
                'seDate': '2024-01-01~2026-12-31'
            }
            
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Referer': 'https://www.cninfo.com.cn/',
                'Origin': 'https://www.cninfo.com.cn',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json, text/javascript, */*; q=0.01'
            }
            
            print(f"  搜索关键词: '{keyword}' 页码: {page_num}")
            time.sleep(2 + random.uniform(0.5, 1.5))
            
            response = requests.post(
                base_url, 
                data=data, 
                headers=headers, 
                timeout=30
            )
            response.raise_for_status()
            
            json_data = response.json()
            
            if not json_data.get('announcements'):
                print(f"    没有更多数据")
                break
            
            for item in json_data['announcements']:
                title = item.get('announcementTitle', '')
                stock_code = item.get('secCode', '')
                stock_name = item.get('secName', '')
                announcement_time = item.get('announcementTime', '')
                
                if isinstance(announcement_time, int):
                    publish_date = datetime.fromtimestamp(announcement_time / 1000).strftime('%Y-%m-%d')
                else:
                    publish_date = str(announcement_time)[:10]
                
                bond_code, bond_name = extract_bond_info(title)
                
                announcement_url = f"https://www.cninfo.com.cn/new/disclosure/detail?orgId={item.get('orgId', '')}&announcementId={item.get('announcementId', '')}"
                pdf_url = f"https://static.cninfo.com.cn/{item.get('adjunctUrl', '')}" if item.get('adjunctUrl') else None
                
                doc_id = generate_doc_id(stock_code, publish_date, title)
                
                ann_type = classify_announcement(title)
                if ann_type == '其他':
                    continue
                
                results.append({
                    'doc_id': doc_id,
                    'stock_code': stock_code,
                    'stock_name': stock_name,
                    'bond_code': bond_code or '',
                    'bond_name': bond_name or '',
                    'title': title,
                    'ann_type': ann_type,
                    'event_stage': get_event_stage(title),
                    'publish_date': publish_date,
                    'announcement_url': announcement_url,
                    'pdf_url': pdf_url,
                    'download_status': 'pending',
                    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'notes': 'Real data from CNINFO'
                })
            
            print(f"    本页找到 {len(json_data['announcements'])} 条")
            
            if len(results) >= limit_per_keyword:
                break
                
        except Exception as e:
            print(f"    Error: {e}")
            break
    
    return results

def save_to_metadata(records: list, output_path: str):
    fieldnames = ['doc_id', 'stock_code', 'stock_name', 'bond_code', 'bond_name', 
                  'title', 'ann_type', 'event_stage', 'publish_date', 
                  'announcement_url', 'pdf_url', 'download_status', 'crawl_time', 'notes']
    
    existing_ids = set()
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('doc_id'):
                    existing_ids.add(row['doc_id'])
    
    new_records = [r for r in records if r['doc_id'] not in existing_ids]
    
    if new_records:
        with open(output_path, 'a', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if os.path.getsize(output_path) == 0:
                writer.writeheader()
            writer.writerows(new_records)
    
    return len(new_records)

def main():
    output_path = 'data/metadata/metadata_real.csv'
    
    if os.path.exists(output_path):
        os.remove(output_path)
    
    all_results = []
    
    print("=== 开始从巨潮资讯网爬取真实可转债公告 ===\n")
    
    for keyword in KEYWORDS:
        print(f"\n[关键词] {keyword}")
        results = search_announcements(keyword, limit_per_keyword=100)
        all_results.extend(results)
        print(f"  已累计 {len(all_results)} 条公告")
        time.sleep(2)
    
    print(f"\n=== 爬取完成 ===")
    print(f"总共找到 {len(all_results)} 条公告")
    
    if all_results:
        new_count = save_to_metadata(all_results, output_path)
        print(f"已保存 {new_count} 条记录到 {output_path}")
        
        ann_type_counts = {}
        for r in all_results:
            ann_type = r['ann_type']
            ann_type_counts[ann_type] = ann_type_counts.get(ann_type, 0) + 1
        
        print("\n公告类型分布:")
        for ann_type, count in sorted(ann_type_counts.items()):
            print(f"  {ann_type}: {count}")
        
        bond_counts = {}
        for r in all_results:
            bond_name = r.get('bond_name') or '未知'
            bond_counts[bond_name] = bond_counts.get(bond_name, 0) + 1
        
        print("\n转债分布 (Top 20):")
        for bond_name, count in sorted(bond_counts.items(), key=lambda x: -x[1])[:20]:
            print(f"  {bond_name}: {count}")
    else:
        print("未找到任何公告，请检查网络连接")

if __name__ == '__main__':
    main()
