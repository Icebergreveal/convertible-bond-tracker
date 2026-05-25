import os
import json
import csv
from datetime import datetime, timedelta
from typing import List, Dict

def parse_date(date_str: str) -> datetime:
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except (ValueError, TypeError):
        return None

def match_events(input_path: str = "outputs/extract_results/structured_data_standardized.json"):
    output_path = "outputs/event_chain/event_chains.csv"
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    if os.path.exists(input_path):
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error reading {input_path}: {e}")
            data = generate_sample_data()
    else:
        print(f"Warning: {input_path} not found. Generating sample event chains.")
        data = generate_sample_data()
    
    bond_groups = {}
    for record in data:
        bond_code = record.get('bond_code') or record.get('bond_name')
        if bond_code:
            if bond_code not in bond_groups:
                bond_groups[bond_code] = []
            bond_groups[bond_code].append(record)
    
    event_chains = []
    
    for bond_code, records in bond_groups.items():
        records.sort(key=lambda x: x.get('publish_date', ''))
        
        adjustment_records = [r for r in records if '下修' in r.get('ann_type', '') and r.get('adjustment_type') != '被动调整']
        redemption_records = [r for r in records if ('强赎' in r.get('ann_type', '') or '赎回' in r.get('ann_type', ''))]
        
        if adjustment_records:
            chains = match_adjustment_chains(adjustment_records, bond_code)
            event_chains.extend(chains)
        
        if redemption_records:
            chains = match_redemption_chains(redemption_records, bond_code)
            event_chains.extend(chains)
    
    fieldnames = ['bond_code', 'bond_name', 'event_type', 'complete', 'nodes', 'missing_nodes',
                  'trigger_date', 'proposal_date', 'resolution_date', 'implementation_date',
                  'total_days', 'cycle_status', 'original_conv_price', 'new_conv_price', 
                  'adjustment_ratio', 'redemption_price', 'premium_rate', 'notes']
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for chain in event_chains:
            row = {k: chain.get(k, '') for k in fieldnames}
            writer.writerow(row)
    
    complete_count = sum(1 for c in event_chains if c.get('complete'))
    print(f"Event chains saved to: {output_path}")
    print(f"Total event chains: {len(event_chains)}")
    print(f"Complete chains: {complete_count}")
    print(f"Incomplete chains: {len(event_chains) - complete_count}")
    
    return event_chains

def generate_sample_data():
    sample_data = [
        {'bond_code': '127061', 'bond_name': '美锦转债', 'stock_code': '000723', 'stock_name': '美锦能源',
         'ann_type': '下修触发提示', 'publish_date': '2026-05-12', 'adjustment_type': '主动下修',
         'trigger_rule': '连续30个交易日中有15个交易日收盘价低于转股价的85%', 'evidence_text': '触发条件说明', 'evidence_page': 2},
        {'bond_code': '127061', 'bond_name': '美锦转债', 'stock_code': '000723', 'stock_name': '美锦能源',
         'ann_type': '下修提议', 'publish_date': '2026-05-18', 'adjustment_type': '主动下修',
         'original_conv_price': 10.50, 'new_conv_price': 8.50, 'evidence_text': '提议内容', 'evidence_page': 3},
        {'bond_code': '127061', 'bond_name': '美锦转债', 'stock_code': '000723', 'stock_name': '美锦能源',
         'ann_type': '下修决议', 'publish_date': '2026-06-02', 'adjustment_type': '主动下修',
         'original_conv_price': 10.50, 'new_conv_price': 8.50, 'evidence_text': '决议内容', 'evidence_page': 4},
        {'bond_code': '127061', 'bond_name': '美锦转债', 'stock_code': '000723', 'stock_name': '美锦能源',
         'ann_type': '下修实施', 'publish_date': '2026-06-10', 'adjustment_type': '主动下修',
         'original_conv_price': 10.50, 'new_conv_price': 8.50, 'effective_date': '2026-06-12',
         'evidence_text': '实施内容', 'evidence_page': 2},
        {'bond_code': '128152', 'bond_name': '龙大转债', 'stock_code': '002726', 'stock_name': '龙大美食',
         'ann_type': '强赎触发提示', 'publish_date': '2026-04-15',
         'redemption_trigger': '连续30个交易日中有15个交易日收盘价不低于转股价的130%', 'evidence_text': '强赎触发说明', 'evidence_page': 1},
        {'bond_code': '128152', 'bond_name': '龙大转债', 'stock_code': '002726', 'stock_name': '龙大美食',
         'ann_type': '强赎决议', 'publish_date': '2026-04-20',
         'redemption_price': 103.50, 'evidence_text': '强赎决议内容', 'evidence_page': 2},
        {'bond_code': '128152', 'bond_name': '龙大转债', 'stock_code': '002726', 'stock_name': '龙大美食',
         'ann_type': '强赎实施', 'publish_date': '2026-04-25',
         'redemption_price': 103.50, 'record_date': '2026-05-05', 'last_convert_date': '2026-05-05',
         'evidence_text': '强赎实施内容', 'evidence_page': 3},
        {'bond_code': '128152', 'bond_name': '龙大转债', 'stock_code': '002726', 'stock_name': '龙大美食',
         'ann_type': '强赎结果', 'publish_date': '2026-05-10',
         'redemption_price': 103.50, 'delisting_date': '2026-05-12',
         'evidence_text': '强赎结果内容', 'evidence_page': 1},
    ]
    return sample_data

def match_adjustment_chains(records: List[Dict], bond_code: str) -> List[Dict]:
    chains = []
    sorted_records = sorted(records, key=lambda x: x.get('publish_date', ''))
    
    while sorted_records:
        chain_records = []
        first_date = parse_date(sorted_records[0].get('publish_date'))
        
        for i, record in enumerate(sorted_records):
            record_date = parse_date(record.get('publish_date'))
            if record_date and first_date and (record_date - first_date).days <= 90:
                chain_records.append(record)
            else:
                break
        
        chain = build_adjustment_chain(chain_records, bond_code)
        if chain:
            chains.append(chain)
        
        sorted_records = sorted_records[len(chain_records):]
    
    return chains

def build_adjustment_chain(records: List[Dict], bond_code: str) -> Dict:
    if not records:
        return {}
    
    trigger = None
    proposal = None
    resolution = None
    implementation = None
    
    for record in records:
        ann_type = record.get('ann_type', '')
        if not trigger and '触发提示' in ann_type:
            trigger = record
        elif not proposal and '提议' in ann_type:
            proposal = record
        elif not resolution and '决议' in ann_type:
            resolution = record
        elif not implementation and '实施' in ann_type:
            implementation = record
    
    all_nodes = ['trigger', 'proposal', 'resolution', 'implementation']
    present_nodes = []
    missing_nodes = []
    
    if trigger:
        present_nodes.append('trigger')
    else:
        missing_nodes.append('trigger')
    if proposal:
        present_nodes.append('proposal')
    else:
        missing_nodes.append('proposal')
    if resolution:
        present_nodes.append('resolution')
    else:
        missing_nodes.append('resolution')
    if implementation:
        present_nodes.append('implementation')
    else:
        missing_nodes.append('implementation')
    
    dates = []
    if trigger:
        dates.append(parse_date(trigger.get('publish_date')))
    if proposal:
        dates.append(parse_date(proposal.get('publish_date')))
    if resolution:
        dates.append(parse_date(resolution.get('publish_date')))
    if implementation:
        dates.append(parse_date(implementation.get('publish_date')))
    
    dates = [d for d in dates if d]
    total_days = (max(dates) - min(dates)).days if len(dates) >= 2 else None
    cycle_status = 'NORMAL'
    notes = []
    
    if total_days is not None:
        if total_days > 90:
            cycle_status = 'LONG'
            notes.append(f'周期{total_days}天超过90天限制')
        elif total_days < 7:
            cycle_status = 'SHORT'
            notes.append('周期过短，可能存在异常')
    
    original_price = None
    new_price = None
    ratio = None
    
    if implementation:
        original_price = implementation.get('original_conv_price')
        new_price = implementation.get('new_conv_price')
    elif resolution:
        original_price = resolution.get('original_conv_price')
        new_price = resolution.get('new_conv_price')
    elif proposal:
        original_price = proposal.get('original_conv_price')
        new_price = proposal.get('new_conv_price')
    
    if original_price is not None and new_price is not None:
        try:
            original_price = float(original_price)
            new_price = float(new_price)
            if original_price > 0:
                ratio = round((original_price - new_price) / original_price * 100, 2)
                if ratio > 100:
                    notes.append('下修幅度超过100%，可能存在数据错误')
                elif ratio < 0:
                    notes.append('下修幅度为负，可能是溢价调整')
        except (ValueError, TypeError):
            pass
    
    return {
        'bond_code': bond_code,
        'bond_name': records[0].get('bond_name', ''),
        'event_type': 'adjustment',
        'complete': len(present_nodes) == 4,
        'nodes': ','.join(present_nodes),
        'missing_nodes': ','.join(missing_nodes),
        'trigger_date': trigger.get('publish_date') if trigger else '',
        'proposal_date': proposal.get('publish_date') if proposal else '',
        'resolution_date': resolution.get('publish_date') if resolution else '',
        'implementation_date': implementation.get('publish_date') if implementation else '',
        'total_days': total_days,
        'cycle_status': cycle_status,
        'original_conv_price': original_price,
        'new_conv_price': new_price,
        'adjustment_ratio': ratio,
        'notes': '; '.join(notes)
    }

def match_redemption_chains(records: List[Dict], bond_code: str) -> List[Dict]:
    chains = []
    sorted_records = sorted(records, key=lambda x: x.get('publish_date', ''))
    
    while sorted_records:
        chain_records = []
        first_date = parse_date(sorted_records[0].get('publish_date'))
        
        for i, record in enumerate(sorted_records):
            record_date = parse_date(record.get('publish_date'))
            if record_date and first_date and (record_date - first_date).days <= 60:
                chain_records.append(record)
            else:
                break
        
        chain = build_redemption_chain(chain_records, bond_code)
        if chain:
            chains.append(chain)
        
        sorted_records = sorted_records[len(chain_records):]
    
    return chains

def build_redemption_chain(records: List[Dict], bond_code: str) -> Dict:
    if not records:
        return {}
    
    trigger = None
    resolution = None
    implementation = None
    result = None
    
    for record in records:
        ann_type = record.get('ann_type', '')
        if not trigger and ('触发提示' in ann_type or '满足' in ann_type):
            trigger = record
        elif not resolution and '决议' in ann_type:
            resolution = record
        elif not implementation and '实施' in ann_type:
            implementation = record
        elif not result and ('结果' in ann_type or '摘牌' in ann_type):
            result = record
    
    all_nodes = ['trigger', 'resolution', 'implementation', 'result']
    present_nodes = []
    missing_nodes = []
    
    if trigger:
        present_nodes.append('trigger')
    else:
        missing_nodes.append('trigger')
    if resolution:
        present_nodes.append('resolution')
    else:
        missing_nodes.append('resolution')
    if implementation:
        present_nodes.append('implementation')
    else:
        missing_nodes.append('implementation')
    if result:
        present_nodes.append('result')
    else:
        missing_nodes.append('result')
    
    dates = []
    if trigger:
        dates.append(parse_date(trigger.get('publish_date')))
    if resolution:
        dates.append(parse_date(resolution.get('publish_date')))
    if implementation:
        dates.append(parse_date(implementation.get('publish_date')))
    if result:
        dates.append(parse_date(result.get('publish_date')))
    
    dates = [d for d in dates if d]
    total_days = (max(dates) - min(dates)).days if len(dates) >= 2 else None
    cycle_status = 'NORMAL'
    notes = []
    
    if total_days is not None:
        if total_days > 60:
            cycle_status = 'LONG'
            notes.append(f'周期{total_days}天超过60天限制')
        elif total_days < 7:
            cycle_status = 'SHORT'
            notes.append('周期过短，可能存在异常')
    
    redemption_price = None
    premium_rate = None
    
    if implementation:
        redemption_price = implementation.get('redemption_price')
    elif result:
        redemption_price = result.get('redemption_price')
    elif resolution:
        redemption_price = resolution.get('redemption_price')
    
    if redemption_price is not None:
        try:
            redemption_price = float(redemption_price)
            premium_rate = round((redemption_price - 100) / 100 * 100, 2)
            if redemption_price < 100:
                notes.append('赎回价格低于面值100元，可能存在数据错误')
        except (ValueError, TypeError):
            pass
    
    return {
        'bond_code': bond_code,
        'bond_name': records[0].get('bond_name', ''),
        'event_type': 'redemption',
        'complete': len(present_nodes) == 4,
        'nodes': ','.join(present_nodes),
        'missing_nodes': ','.join(missing_nodes),
        'trigger_date': trigger.get('publish_date') if trigger else '',
        'proposal_date': '',
        'resolution_date': resolution.get('publish_date') if resolution else '',
        'implementation_date': implementation.get('publish_date') if implementation else '',
        'total_days': total_days,
        'cycle_status': cycle_status,
        'redemption_price': redemption_price,
        'premium_rate': premium_rate,
        'notes': '; '.join(notes)
    }

if __name__ == '__main__':
    print("Matching event chains...")
    match_events()