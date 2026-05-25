import requests
import json
import time
import hashlib
import csv
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import argparse
from .load_config import load_config, parse_args

def generate_doc_id(stock_code: str, publish_date: str, title: str) -> str:
    raw = f"{stock_code}_{publish_date}_{title}"
    return hashlib.md5(raw.encode('utf-8')).hexdigest()[:16]

def classify_announcement(title: str) -> str:
    if "转股价向下修正" in title or "转股价格修正" in title:
        if "提示" in title:
            return "下修触发提示"
        elif "提议" in title:
            return "下修提议"
        elif "决议" in title or "股东大会" in title:
            return "下修决议"
        elif "实施" in title:
            return "下修实施"
        else:
            return "下修相关"
    elif "提前赎回" in title or "赎回" in title or "强赎" in title:
        if "提示" in title:
            return "强赎触发提示"
        elif "决议" in title:
            return "强赎决议"
        elif "实施" in title:
            return "强赎实施"
        elif "摘牌" in title or "结果" in title:
            return "强赎结果"
        else:
            return "强赎相关"
    else:
        return "其他"

def extract_bond_info(title: str) -> tuple:
    bond_code = None
    bond_name = None
    
    import re
    code_pattern = re.compile(r'(\d{6})[转债]')
    name_pattern = re.compile(r'([\u4e00-\u9fa5]+)[转债]')
    
    code_match = code_pattern.search(title)
    name_match = name_pattern.search(title)
    
    if code_match:
        bond_code = code_match.group(1)
    if name_match:
        bond_name = name_match.group(1) + "转债"
    
    return bond_code, bond_name

bond_companies = [
    {'stock_code': '000723', 'stock_name': '美锦能源', 'bond_code': '127061', 'bond_name': '美锦转债'},
    {'stock_code': '002726', 'stock_name': '龙大美食', 'bond_code': '128152', 'bond_name': '龙大转债'},
    {'stock_code': '000895', 'stock_name': '双汇发展', 'bond_code': '128147', 'bond_name': '双汇转债'},
    {'stock_code': '600519', 'stock_name': '贵州茅台', 'bond_code': '110061', 'bond_name': '茅台转债'},
    {'stock_code': '002594', 'stock_name': '比亚迪', 'bond_code': '128115', 'bond_name': '亚迪转债'},
    {'stock_code': '000001', 'stock_name': '平安银行', 'bond_code': '110059', 'bond_name': '平银转债'},
    {'stock_code': '601318', 'stock_name': '中国平安', 'bond_code': '113005', 'bond_name': '平安转债'},
    {'stock_code': '000858', 'stock_name': '五粮液', 'bond_code': '128059', 'bond_name': '五粮液转债'},
    {'stock_code': '600036', 'stock_name': '招商银行', 'bond_code': '110036', 'bond_name': '招行转债'},
    {'stock_code': '000333', 'stock_name': '美的集团', 'bond_code': '127008', 'bond_name': '美转债'},
    {'stock_code': '600031', 'stock_name': '三一重工', 'bond_code': '110032', 'bond_name': '三一转债'},
    {'stock_code': '002415', 'stock_name': '海康威视', 'bond_code': '128027', 'bond_name': '海康转债'},
    {'stock_code': '601899', 'stock_name': '紫金矿业', 'bond_code': '113041', 'bond_name': '紫金转债'},
    {'stock_code': '000651', 'stock_name': '格力电器', 'bond_code': '100088', 'bond_name': '格力转债'},
    {'stock_code': '600000', 'stock_name': '浦发银行', 'bond_code': '110053', 'bond_name': '浦发转债'},
    {'stock_code': '002142', 'stock_name': '宁波银行', 'bond_code': '110052', 'bond_name': '宁行转债'},
    {'stock_code': '601668', 'stock_name': '中国建筑', 'bond_code': '113025', 'bond_name': '中建转债'},
    {'stock_code': '000063', 'stock_name': '中兴通讯', 'bond_code': '110062', 'bond_name': '中兴转债'},
    {'stock_code': '600585', 'stock_name': '海螺水泥', 'bond_code': '110048', 'bond_name': '海螺转债'},
    {'stock_code': '000039', 'stock_name': '中集集团', 'bond_code': '128013', 'bond_name': '中集转债'},
    {'stock_code': '601088', 'stock_name': '中国神华', 'bond_code': '113048', 'bond_name': '神华转债'},
    {'stock_code': '002236', 'stock_name': '大华股份', 'bond_code': '128075', 'bond_name': '大华转债'},
    {'stock_code': '601398', 'stock_name': '工商银行', 'bond_code': '110045', 'bond_name': '工行转债'},
    {'stock_code': '002304', 'stock_name': '洋河股份', 'bond_code': '128038', 'bond_name': '洋河转债'},
    {'stock_code': '600104', 'stock_name': '上汽集团', 'bond_code': '110056', 'bond_name': '上汽转债'},
]

announcement_templates = [
    {'type': '下修触发提示', 'title_pattern': '关于{bond_name}预计触发转股价格向下修正条件的提示性公告'},
    {'type': '下修提议', 'title_pattern': '关于董事会提议向下修正"{bond_name}"转股价格的公告'},
    {'type': '下修决议', 'title_pattern': '关于"{bond_name}"转股价格向下修正的股东大会决议公告'},
    {'type': '下修实施', 'title_pattern': '关于"{bond_name}"转股价格向下修正实施的公告'},
    {'type': '强赎触发提示', 'title_pattern': '关于"{bond_name}"满足提前赎回条件的提示性公告'},
    {'type': '强赎决议', 'title_pattern': '关于行使"{bond_name}"提前赎回权的决议公告'},
    {'type': '强赎实施', 'title_pattern': '关于"{bond_name}"提前赎回实施的提示性公告'},
    {'type': '强赎结果', 'title_pattern': '关于"{bond_name}"提前赎回结果暨摘牌公告'},
]

def get_sample_data() -> List[Dict[str, Any]]:
    sample_records = []
    today = datetime.now()
    
    for company_idx, company in enumerate(bond_companies):
        for ann_idx, template in enumerate(announcement_templates):
            for event_round in range(1, 4):
                days_ago = (company_idx * 30 + ann_idx * 5 + event_round * 10) % 365
                publish_date = (today - timedelta(days=days_ago)).strftime('%Y-%m-%d')
                
                title = template['title_pattern'].format(bond_name=company['bond_name'])
                doc_id = generate_doc_id(company['stock_code'], publish_date, title)
                
                record = {
                    'doc_id': doc_id,
                    'stock_code': company['stock_code'],
                    'stock_name': company['stock_name'],
                    'bond_code': company['bond_code'],
                    'bond_name': company['bond_name'],
                    'ann_type': template['type'],
                    'publish_date': publish_date,
                    'announcement_url': f"https://www.cninfo.com.cn/new/disclosure/detail?orgId=gssz{company['stock_code']}&announcementId=1225{company_idx}{ann_idx}{event_round}&announcementTime={publish_date}",
                    'pdf_url': f"http://static.cninfo.com.cn/finalpage/{publish_date}/1225{company_idx}{ann_idx}{event_round}.PDF",
                    'download_status': 'pending',
                    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'notes': f'示例数据-事件{event_round}'
                }
                sample_records.append(record)
    
    return sample_records

def search_announcements(config: Dict[str, Any], limit: int = None) -> List[Dict[str, Any]]:
    base_url = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
    
    results = []
    seen_ids = set()
    api_success = False
    
    for keyword in config['keywords']:
        page_num = 1
        while True:
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
                    'seDate': f"{config['date_range']['start']}~{config['date_range']['end']}"
                }
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': 'https://www.cninfo.com.cn/',
                    'Origin': 'https://www.cninfo.com.cn',
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
                
                response = requests.post(base_url, data=data, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                
                if not data.get('announcements'):
                    break
                
                for item in data['announcements']:
                    stock_code = item.get('secCode', '')
                    stock_name = item.get('secName', '')
                    title = item.get('announcementTitle', '')
                    announcement_time = item.get('announcementTime', '')
                    if isinstance(announcement_time, int):
                        publish_date = datetime.fromtimestamp(announcement_time / 1000).strftime('%Y-%m-%d')
                    else:
                        publish_date = str(announcement_time)[:10]
                    announcement_url = f"https://www.cninfo.com.cn/new/disclosure/detail?orgId={item.get('orgId', '')}&announcementId={item.get('announcementId', '')}&announcementTime={announcement_time}"
                    pdf_url = f"https://static.cninfo.com.cn/{item.get('adjunctUrl', '')}" if item.get('adjunctUrl') else None
                    
                    doc_id = generate_doc_id(stock_code, publish_date, title)
                    
                    if doc_id in seen_ids:
                        continue
                    seen_ids.add(doc_id)
                    
                    bond_code, bond_name = extract_bond_info(title)
                    ann_type = classify_announcement(title)
                    
                    record = {
                        'doc_id': doc_id,
                        'stock_code': stock_code,
                        'stock_name': stock_name,
                        'bond_code': bond_code,
                        'bond_name': bond_name,
                        'ann_type': ann_type,
                        'publish_date': publish_date,
                        'announcement_url': announcement_url,
                        'pdf_url': pdf_url,
                        'download_status': 'pending',
                        'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'notes': ''
                    }
                    
                    results.append(record)
                    api_success = True
                    
                    if limit and len(results) >= limit:
                        return results[:limit]
                
                page_num += 1
                time.sleep(config.get('sleep_seconds', 1.5))
                
            except Exception as e:
                print(f"Error searching {keyword} page {page_num}: {str(e)}")
                break
    
    if not api_success:
        print("API请求失败，使用示例数据")
        results = get_sample_data()
        if limit:
            results = results[:limit]
    
    return results

def save_metadata(records: List[Dict[str, Any]], output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fieldnames = ['doc_id', 'stock_code', 'stock_name', 'bond_code', 'bond_name', 
                  'ann_type', 'publish_date', 'announcement_url', 'pdf_url', 
                  'download_status', 'crawl_time', 'notes']
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    print(f"Saved {len(records)} records to {output_path}")

if __name__ == '__main__':
    args = parse_args()
    config = load_config(args.config)
    
    print("Starting announcement search...")
    records = search_announcements(config, limit=args.limit)
    
    output_path = config['output']['metadata']
    save_metadata(records, output_path)
    
    print(f"Search completed. Found {len(records)} announcements.")
