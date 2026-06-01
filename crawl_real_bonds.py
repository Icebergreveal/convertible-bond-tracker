#!/usr/bin/env python3
import os
import sys
import csv
import time
import random
import hashlib
import requests
from datetime import datetime
from bs4 import BeautifulSoup

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0',
]

TARGET_BONDS = [
    ('000723', '美锦能源', '127061', '美锦转债'),
    ('002726', '龙大美食', '128152', '龙大转债'),
    ('000895', '双汇发展', '128147', '双汇转债'),
    ('600519', '贵州茅台', '110061', '茅台转债'),
    ('002594', '比亚迪', '128115', '亚迪转债'),
    ('000001', '平安银行', '110059', '平银转债'),
    ('601318', '中国平安', '113005', '平安转债'),
    ('000858', '五粮液', '127059', '五粮液转债'),
    ('600036', '招商银行', '110036', '招行转债'),
    ('000333', '美的集团', '127008', '美的转债'),
    ('600031', '三一重工', '110032', '三一转债'),
    ('002415', '海康威视', '128027', '海康转债'),
    ('601899', '紫金矿业', '113041', '紫金转债'),
    ('000651', '格力电器', '110048', '格力转债'),
    ('600000', '浦发银行', '110053', '浦发转债'),
    ('002142', '宁波银行', '110052', '宁行转债'),
]

KEYWORDS = [
    '转股价向下修正',
    '转股价格修正',
    '转债赎回',
    '提前赎回',
    '强赎',
    '触发转股价格向下修正',
    '行使提前赎回权',
]

def generate_doc_id(stock_code: str, publish_date: str, title: str) -> str:
    raw = f"{stock_code}_{publish_date}_{title}"
    return hashlib.md5(raw.encode('utf-8')).hexdigest()[:16]

def search_by_bond_name(bond_name: str, stock_code: str = None) -> list:
    base_url = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
    results = []
    
    for keyword in KEYWORDS:
        search_keyword = f"{bond_name} {keyword}" if bond_name else keyword
        
        page_num = 1
        found_in_page = False
        
        while page_num <= 10:
            try:
                data = {
                    'stock': stock_code if stock_code else '',
                    'searchkey': search_keyword,
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
                    'seDate': '2023-01-01~2026-12-31'
                }
                
                headers = {
                    'User-Agent': random.choice(USER_AGENTS),
                    'Referer': 'https://www.cninfo.com.cn/',
                    'Origin': 'https://www.cninfo.com.cn',
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json, text/javascript, */*; q=0.01'
                }
                
                time.sleep(1.5 + random.uniform(0.5, 1.0))
                
                response = requests.post(
                    base_url, 
                    data=data, 
                    headers=headers, 
                    timeout=30
                )
                response.raise_for_status()
                
                json_data = response.json()
                
                if not json_data.get('announcements'):
                    break
                
                for item in json_data['announcements']:
                    title = item.get('announcementTitle', '')
                    if bond_name and bond_name not in title:
                        continue
                    
                    stock_code_item = item.get('secCode', '')
                    stock_name = item.get('secName', '')
                    announcement_time = item.get('announcementTime', '')
                    
                    if isinstance(announcement_time, int):
                        publish_date = datetime.fromtimestamp(announcement_time / 1000).strftime('%Y-%m-%d')
                    else:
                        publish_date = str(announcement_time)[:10]
                    
                    announcement_url = f"https://www.cninfo.com.cn/new/disclosure/detail?orgId={item.get('orgId', '')}&announcementId={item.get('announcementId', '')}"
                    pdf_url = f"https://static.cninfo.com.cn/{item.get('adjunctUrl', '')}" if item.get('adjunctUrl') else None
                    
                    doc_id = generate_doc_id(stock_code_item, publish_date, title)
                    
                    results.append({
                        'doc_id': doc_id,
                        'stock_code': stock_code_item,
                        'stock_name': stock_name,
                        'bond_code': '',
                        'bond_name': bond_name,
                        'title': title,
                        'ann_type': classify_announcement(title),
                        'event_stage': get_event_stage(title),
                        'publish_date': publish_date,
                        'announcement_url': announcement_url,
                        'pdf_url': pdf_url,
                        'download_status': 'pending',
                        'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'notes': 'Real data from CNINFO'
                    })
                    found_in_page = True
                
                page_num += 1
                
            except Exception as e:
                print(f"  Error searching '{search_keyword}' page {page_num}: {e}")
                break
    
    return results

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
    all_results = []
    
    print("=== 开始从巨潮资讯网爬取真实可转债公告 ===\n")
    
    for stock_code, stock_name, bond_code, bond_name in TARGET_BONDS:
        print(f"搜索: {stock_name} ({bond_name})")
        
        results = search_by_bond_name(bond_name, stock_code)
        
        if results:
            print(f"  找到 {len(results)} 条公告")
            for r in results[:3]:
                print(f"    - {r['publish_date']}: {r['ann_type']}")
            all_results.extend(results)
        else:
            print(f"  未找到相关公告")
        
        time.sleep(1)
    
    print(f"\n=== 爬取完成 ===")
    print(f"总共找到 {len(all_results)} 条公告")
    
    if all_results:
        new_count = save_to_metadata(all_results, output_path)
        print(f"新增 {new_count} 条记录到 {output_path}")
        
        ann_type_counts = {}
        for r in all_results:
            ann_type = r['ann_type']
            ann_type_counts[ann_type] = ann_type_counts.get(ann_type, 0) + 1
        
        print("\n公告类型分布:")
        for ann_type, count in sorted(ann_type_counts.items()):
            print(f"  {ann_type}: {count}")
    else:
        print("未找到任何公告，请检查网络连接或API是否可用")

if __name__ == '__main__':
    main()
