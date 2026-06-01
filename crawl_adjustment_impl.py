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
]

KEYWORDS = [
    '转股价格向下修正实施',
    '向下修正转股价格实施',
    '转股价修正实施',
    '下修转股价格生效',
    '转股价格调整实施',
]

def generate_doc_id(stock_code: str, publish_date: str, title: str) -> str:
    raw = f"{stock_code}_{publish_date}_{title}"
    return hashlib.md5(raw.encode('utf-8')).hexdigest()[:16]

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

def search_announcements(keyword: str) -> list:
    base_url = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
    results = []
    
    for page_num in range(1, 10):
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
            
            print(f"  搜索: '{keyword}' 页码: {page_num}")
            time.sleep(2 + random.uniform(0.5, 1.5))
            
            response = requests.post(base_url, data=data, headers=headers, timeout=30)
            response.raise_for_status()
            
            json_data = response.json()
            
            if not json_data.get('announcements'):
                print(f"    无更多数据")
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
                
                if '实施' not in title:
                    continue
                
                announcement_url = f"https://www.cninfo.com.cn/new/disclosure/detail?orgId={item.get('orgId', '')}&announcementId={item.get('announcementId', '')}"
                pdf_url = f"https://static.cninfo.com.cn/{item.get('adjunctUrl', '')}" if item.get('adjunctUrl') else None
                
                doc_id = generate_doc_id(stock_code, publish_date, title)
                
                results.append({
                    'doc_id': doc_id,
                    'stock_code': stock_code,
                    'stock_name': stock_name,
                    'bond_code': bond_code or '',
                    'bond_name': bond_name or '',
                    'title': title,
                    'ann_type': '下修实施',
                    'event_stage': 'stage_4_implementation',
                    'publish_date': publish_date,
                    'announcement_url': announcement_url,
                    'pdf_url': pdf_url,
                    'download_status': 'pending',
                    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'notes': 'Real data - 下修实施 type'
                })
            
            print(f"    本页找到 {len(results)} 条下修实施公告")
            
        except Exception as e:
            print(f"    Error: {e}")
            break
    
    return results

def main():
    output_path = 'data/metadata/metadata_adjustment_impl.csv'
    
    if os.path.exists(output_path):
        os.remove(output_path)
    
    all_results = []
    
    print("=== 爬取'下修实施'类型公告 ===\n")
    
    for keyword in KEYWORDS:
        print(f"\n[关键词] {keyword}")
        results = search_announcements(keyword)
        all_results.extend(results)
        print(f"  累计: {len(all_results)} 条")
        time.sleep(2)
    
    if all_results:
        df = pd.DataFrame(all_results)
        df_unique = df.drop_duplicates(subset=['doc_id'])
        
        fieldnames = list(df.columns)
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(df_unique.to_dict('records'))
        
        print(f"\n已保存 {len(df_unique)} 条到 {output_path}")
    else:
        print("未找到任何下修实施公告")
        print("注意: '下修实施'类型在现实中较为罕见，因为它是下修流程的最后一步")

if __name__ == '__main__':
    main()
