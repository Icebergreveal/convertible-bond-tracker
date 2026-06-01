import requests
import json
import time
import hashlib
import csv
import os
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from bs4 import BeautifulSoup

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

KEYWORDS = [
    '转股价向下修正', '转股价格修正', '向下修正转股价格', '提议向下修正转股价',
    '转股价调整', '转股价格调整', '调整转股价格',
    '提前赎回', '强赎', '赎回可转债', '可转债赎回',
    '行使赎回权', '赎回权', '可转债摘牌',
    '触发转股价格修正', '触发提前赎回', '满足赎回条件'
]

ANNOUNCEMENT_TYPE_RULES = [
    {'pattern': r'股东大会.*决议.*转股价格', 'type': '下修决议'},
    {'pattern': r'股东大会.*向下修正.*决议', 'type': '下修决议'},
    {'pattern': r'转股价格.*向下修正.*股东大会', 'type': '下修决议'},
    {'pattern': r'转股价格.*向下修正.*实施', 'type': '下修实施'},
    {'pattern': r'实施.*转股价格.*修正', 'type': '下修实施'},
    {'pattern': r'转股价格调整.*实施', 'type': '下修实施'},
    {'pattern': r'转股价格.*调整.*决议', 'type': '下修决议'},
    {'pattern': r'关于.*转股价格调整的公告', 'type': '下修决议'},
    {'pattern': r'转股价格调整的公告', 'type': '下修决议'},
    {'pattern': r'董事会.*提议.*向下修正', 'type': '下修提议'},
    {'pattern': r'提议.*向下修正.*转股价', 'type': '下修提议'},
    {'pattern': r'关于.*向下修正.*的公告', 'type': '下修提议'},
    {'pattern': r'触发.*转股价格.*向下修正', 'type': '下修触发提示'},
    {'pattern': r'触发.*转股价格修正', 'type': '下修触发提示'},
    {'pattern': r'预计触发.*转股价格', 'type': '下修触发提示'},
    {'pattern': r'提前赎回.*实施', 'type': '强赎实施'},
    {'pattern': r'赎回.*实施.*提示', 'type': '强赎实施'},
    {'pattern': r'行使.*提前赎回权', 'type': '强赎决议'},
    {'pattern': r'董事会.*赎回.*决议', 'type': '强赎决议'},
    {'pattern': r'提前赎回.*决议', 'type': '强赎决议'},
    {'pattern': r'赎回结果', 'type': '强赎结果'},
    {'pattern': r'摘牌.*公告', 'type': '强赎结果'},
    {'pattern': r'可转债.*摘牌', 'type': '强赎结果'},
    {'pattern': r'满足.*提前赎回.*条件', 'type': '强赎触发提示'},
    {'pattern': r'触发.*提前赎回', 'type': '强赎触发提示'},
    {'pattern': r'提前赎回.*提示', 'type': '强赎触发提示'},
]

EVENT_STAGES = {
    '下修触发提示': 'stage_1_trigger',
    '下修提议': 'stage_2_proposal',
    '下修决议': 'stage_3_resolution',
    '下修实施': 'stage_4_implementation',
    '强赎触发提示': 'stage_1_trigger',
    '强赎决议': 'stage_2_resolution',
    '强赎实施': 'stage_3_implementation',
    '强赎结果': 'stage_4_result'
}

def generate_doc_id(stock_code: str, publish_date: str, title: str) -> str:
    raw = f"{stock_code}_{publish_date}_{title}"
    return hashlib.md5(raw.encode('utf-8')).hexdigest()[:16]

def classify_announcement(title: str) -> tuple:
    import re
    title_lower = title.lower()
    
    for rule in ANNOUNCEMENT_TYPE_RULES:
        pattern = rule['pattern']
        if re.search(pattern, title, re.IGNORECASE):
            ann_type = rule['type']
            stage = EVENT_STAGES.get(ann_type, 'unknown')
            return ann_type, stage
    
    if '转股价' in title or '转股价格' in title:
        return '下修相关', 'stage_unknown'
    elif '赎回' in title or '强赎' in title:
        return '强赎相关', 'stage_unknown'
    else:
        return '其他', 'stage_unknown'

def extract_bond_info(title: str) -> tuple:
    bond_code = None
    bond_name = None
    
    import re
    code_pattern = re.compile(r'(\d{6})')
    name_pattern = re.compile(r'([\u4e00-\u9fa5]{2,8})转债')
    
    code_match = code_pattern.search(title)
    name_match = name_pattern.search(title)
    
    if code_match:
        code = code_match.group(1)
        if len(code) == 6:
            bond_code = code
    if name_match:
        bond_name = name_match.group(1) + "转债"
    
    if bond_name and bond_name.endswith("转债转债"):
        bond_name = bond_name[:-2]
    
    return bond_code, bond_name

def load_existing_doc_ids(metadata_path: str) -> set:
    existing_ids = set()
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    doc_id = row.get('doc_id')
                    if doc_id:
                        existing_ids.add(doc_id)
        except Exception as e:
            print(f"Warning: Failed to load existing metadata: {e}")
    return existing_ids

def get_last_crawl_time(metadata_path: str) -> str:
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                crawl_times = [row.get('crawl_time', '') for row in reader if row.get('crawl_time')]
                if crawl_times:
                    return max(crawl_times)[:10]
        except Exception as e:
            pass
    return (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

def search_announcements(
    config: Dict[str, Any], 
    limit: int = None,
    incremental: bool = True
) -> List[Dict[str, Any]]:
    base_url = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
    
    results = []
    seen_ids = set()
    api_success = False
    
    metadata_path = config['output'].get('metadata', 'data/metadata/metadata.csv')
    existing_ids = load_existing_doc_ids(metadata_path) if incremental else set()
    last_crawl_date = get_last_crawl_time(metadata_path) if incremental else None
    
    print(f"[Crawl] Loaded {len(existing_ids)} existing doc IDs")
    if incremental and last_crawl_date:
        print(f"[Crawl] Incremental mode: only fetching after {last_crawl_date}")
    
    for keyword in KEYWORDS:
        if limit and len(results) >= limit:
            break
            
        page_num = 1
        max_retries = 3
        retry_delay = 5
        
        while True:
            if limit and len(results) >= limit:
                break
                
            success = False
            for attempt in range(max_retries):
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
                        'User-Agent': random.choice(USER_AGENTS),
                        'Referer': 'https://www.cninfo.com.cn/',
                        'Origin': 'https://www.cninfo.com.cn',
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'Accept': 'application/json, text/javascript, */*; q=0.01'
                    }
                    
                    sleep_time = config.get('sleep_seconds', 1.5) + random.uniform(0.5, 1.5)
                    time.sleep(sleep_time)
                    
                    response = requests.post(
                        base_url, 
                        data=data, 
                        headers=headers, 
                        timeout=30
                    )
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    if not data.get('announcements'):
                        success = True
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
                        
                        if incremental and last_crawl_date and publish_date <= last_crawl_date:
                            print(f"[Crawl] Reached existing data, stopping keyword: {keyword}")
                            success = True
                            break
                        
                        announcement_url = f"https://www.cninfo.com.cn/new/disclosure/detail?orgId={item.get('orgId', '')}&announcementId={item.get('announcementId', '')}&announcementTime={announcement_time}"
                        pdf_url = f"https://static.cninfo.com.cn/{item.get('adjunctUrl', '')}" if item.get('adjunctUrl') else None
                        
                        doc_id = generate_doc_id(stock_code, publish_date, title)
                        
                        if doc_id in seen_ids or doc_id in existing_ids:
                            continue
                        seen_ids.add(doc_id)
                        
                        bond_code, bond_name = extract_bond_info(title)
                        ann_type, stage = classify_announcement(title)
                        
                        record = {
                            'doc_id': doc_id,
                            'stock_code': stock_code,
                            'stock_name': stock_name,
                            'bond_code': bond_code,
                            'bond_name': bond_name,
                            'ann_type': ann_type,
                            'event_stage': stage,
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
                            success = True
                            break
                    
                    success = True
                    page_num += 1
                    
                except requests.exceptions.HTTPError as e:
                    if response.status_code == 403:
                        print(f"[Crawl] 403 Forbidden - retrying in {retry_delay}s")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        print(f"[Crawl] HTTP Error for {keyword} page {page_num}: {e}")
                        success = True
                        break
                except requests.exceptions.RequestException as e:
                    print(f"[Crawl] Request Error for {keyword} page {page_num}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        success = True
                        break
            
            if not success:
                break
    
    if not api_success:
        raise Exception("[Crawl] API请求失败，请检查网络连接或稍后重试")
    
    print(f"[Crawl] Found {len(results)} new announcements")
    return results

def generate_sample_data(limit: int = None):
    bond_companies = [
        {'stock_code': '000723', 'stock_name': '美锦能源', 'bond_code': '127061', 'bond_name': '美锦转债'},
        {'stock_code': '002726', 'stock_name': '龙大美食', 'bond_code': '128152', 'bond_name': '龙大转债'},
        {'stock_code': '000895', 'stock_name': '双汇发展', 'bond_code': '128147', 'bond_name': '双汇转债'},
        {'stock_code': '600519', 'stock_name': '贵州茅台', 'bond_code': '110061', 'bond_name': '茅台转债'},
        {'stock_code': '002594', 'stock_name': '比亚迪', 'bond_code': '128115', 'bond_name': '亚迪转债'},
    ]
    
    announcement_templates = [
        {'type': '下修触发提示', 'stage': 'stage_1_trigger', 'title_pattern': '关于{bond_name}预计触发转股价格向下修正条件的提示性公告'},
        {'type': '下修提议', 'stage': 'stage_2_proposal', 'title_pattern': '关于董事会提议向下修正"{bond_name}"转股价格的公告'},
        {'type': '下修决议', 'stage': 'stage_3_resolution', 'title_pattern': '关于"{bond_name}"转股价格向下修正的股东大会决议公告'},
        {'type': '下修实施', 'stage': 'stage_4_implementation', 'title_pattern': '关于"{bond_name}"转股价格向下修正实施的公告'},
        {'type': '强赎触发提示', 'stage': 'stage_1_trigger', 'title_pattern': '关于"{bond_name}"满足提前赎回条件的提示性公告'},
        {'type': '强赎决议', 'stage': 'stage_2_resolution', 'title_pattern': '关于行使"{bond_name}"提前赎回权的决议公告'},
        {'type': '强赎实施', 'stage': 'stage_3_implementation', 'title_pattern': '关于"{bond_name}"提前赎回实施的提示性公告'},
        {'type': '强赎结果', 'stage': 'stage_4_result', 'title_pattern': '关于"{bond_name}"提前赎回结果暨摘牌公告'},
    ]
    
    results = []
    today = datetime.now()
    
    for company_idx, company in enumerate(bond_companies):
        for ann_idx, template in enumerate(announcement_templates):
            for event_round in range(1, 3):
                days_ago = (company_idx * 60 + ann_idx * 10 + event_round * 15) % 365
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
                    'event_stage': template['stage'],
                    'publish_date': publish_date,
                    'announcement_url': f"https://www.cninfo.com.cn/new/disclosure/detail?orgId=gssz{company['stock_code']}&announcementId=1225{company_idx}{ann_idx}{event_round}&announcementTime={publish_date}",
                    'pdf_url': f"http://static.cninfo.com.cn/finalpage/{publish_date}/1225{company_idx}{ann_idx}{event_round}.PDF",
                    'download_status': 'pending',
                    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'notes': f'示例数据-事件{event_round}'
                }
                results.append(record)
    
    if limit:
        results = results[:limit]
    
    return results

def save_metadata(records: List[Dict[str, Any]], output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fieldnames = ['doc_id', 'stock_code', 'stock_name', 'bond_code', 'bond_name', 
                  'ann_type', 'event_stage', 'publish_date', 'announcement_url', 'pdf_url', 
                  'download_status', 'crawl_time', 'notes']
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    print(f"Saved {len(records)} records to {output_path}")

if __name__ == '__main__':
    config = {
        'keywords': KEYWORDS,
        'date_range': {'start': '2024-01-01', 'end': datetime.now().strftime('%Y-%m-%d')},
        'output': {'metadata': 'data/metadata/metadata.csv'},
        'sleep_seconds': 1.5
    }
    
    print("[Crawl] Starting announcement search...")
    records = search_announcements(config, limit=20, incremental=True)
    save_metadata(records, config['output']['metadata'])
    print(f"[Crawl] Search completed. Found {len(records)} announcements.")