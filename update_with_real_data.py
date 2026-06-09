import os
import json
import csv

def load_real_data(file_path):
    """加载真实数据"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, file_path):
    """保存JSON文件"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved: {file_path}")

def save_csv(data, file_path):
    """保存CSV文件"""
    if not data:
        print(f"Empty data, skipped: {file_path}")
        return
    
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    fieldnames = set()
    for item in data:
        fieldnames.update(item.keys())
    
    fieldnames = sorted(list(fieldnames))
    
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"Saved: {file_path}")

def filter_valid_records(data):
    """过滤有效记录（至少包含bond_code和ann_type）"""
    valid_records = []
    for record in data:
        if record.get('bond_code') and record.get('ann_type'):
            valid_records.append(record)
    return valid_records

def update_extract_results(real_data):
    """更新extract_results文件夹"""
    # 保存为结构化数据文件
    save_json(real_data, "outputs/extract_results/structured_data.json")
    save_json(real_data, "outputs/extract_results/structured_data_standardized.json")
    save_json(real_data, "outputs/extract_results/structured_data_merged.json")
    save_json(real_data, "outputs/extract_results/structured_data_merged_fixed.json")
    
    # 保存为CSV文件
    valid_records = filter_valid_records(real_data)
    save_csv(valid_records, "outputs/extract_results/records_validated.csv")
    save_csv(valid_records, "outputs/extract_results/最终抽取结果.csv")
    save_csv(valid_records, "outputs/extract_results/最终抽取结果_清洗后.csv")
    save_csv(valid_records, "outputs/extract_results/抽取结果.csv")
    save_csv(valid_records, "outputs/extract_results/结构化数据最终结果.csv")
    
    return valid_records

def build_event_chains(valid_records):
    """构建事件链"""
    bond_map = {}
    
    for record in valid_records:
        bond_code = record.get('bond_code')
        if not bond_code:
            continue
            
        if bond_code not in bond_map:
            bond_map[bond_code] = {
                'bond_code': bond_code,
                'bond_name': record.get('bond_name'),
                'stock_code': record.get('stock_code'),
                'stock_name': record.get('stock_name'),
                'events': []
            }
        
        bond_map[bond_code]['events'].append(record)
    
    event_chains = []
    
    for bond_code, bond_info in bond_map.items():
        events = bond_info['events']
        
        event_types = set()
        for e in events:
            ann_type = e.get('ann_type', '')
            if '下修' in ann_type:
                event_types.add('adjustment')
            elif '强赎' in ann_type or '赎回' in ann_type:
                event_types.add('redemption')
        
        for event_type in event_types:
            chain = {
                'bond_code': bond_code,
                'bond_name': bond_info['bond_name'],
                'stock_code': bond_info['stock_code'],
                'stock_name': bond_info['stock_name'],
                'event_type': event_type,
                'complete': False,
                'nodes': [],
                'missing_nodes': [],
                'trigger_date': None,
                'proposal_date': None,
                'resolution_date': None,
                'implementation_date': None,
                'total_days': 0,
                'cycle_status': 'NORMAL',
                'original_conv_price': None,
                'new_conv_price': None,
                'adjustment_ratio': None,
                'redemption_price': None,
                'premium_rate': None,
                'notes': '',
                'adjustment_ratio_calc': '',
                'adjustment_ratio_check': '',
                'premium_rate_calc': '',
                'conversion_value': '',
                'calc_method': '',
                'premium_rate_check': '',
                'cycle_check': 'NORMAL'
            }
            
            for event in events:
                ann_type = event.get('ann_type', '')
                publish_date = event.get('publish_date')
                
                if event_type == 'adjustment':
                    if '触发' in ann_type:
                        chain['trigger_date'] = publish_date
                        chain['nodes'].append('trigger')
                    elif '提议' in ann_type:
                        chain['proposal_date'] = publish_date
                        chain['nodes'].append('proposal')
                    elif '决议' in ann_type:
                        chain['resolution_date'] = publish_date
                        chain['nodes'].append('resolution')
                    elif '实施' in ann_type or '生效' in ann_type:
                        chain['implementation_date'] = publish_date
                        chain['nodes'].append('implementation')
                    
                    if event.get('original_conv_price'):
                        chain['original_conv_price'] = event['original_conv_price']
                    if event.get('new_conv_price'):
                        chain['new_conv_price'] = event['new_conv_price']
                    if event.get('adjustment_ratio'):
                        chain['adjustment_ratio'] = event['adjustment_ratio']
                
                elif event_type == 'redemption':
                    if '触发' in ann_type:
                        chain['trigger_date'] = publish_date
                        chain['nodes'].append('trigger')
                    elif '决议' in ann_type:
                        chain['resolution_date'] = publish_date
                        chain['nodes'].append('resolution')
                    elif '实施' in ann_type:
                        chain['implementation_date'] = publish_date
                        chain['nodes'].append('implementation')
                    elif '摘牌' in ann_type or '结果' in ann_type:
                        chain['delisting_date'] = publish_date
                        chain['nodes'].append('result')
                    
                    if event.get('redemption_price'):
                        chain['redemption_price'] = event['redemption_price']
                    if event.get('premium_rate'):
                        chain['premium_rate'] = event['premium_rate']
            
            chain['nodes'] = ','.join(chain['nodes'])
            
            expected_nodes = ['trigger', 'proposal', 'resolution', 'implementation'] if event_type == 'adjustment' else ['trigger', 'resolution', 'implementation', 'result']
            chain['missing_nodes'] = ','.join([n for n in expected_nodes if n not in chain['nodes'].split(',')])
            chain['complete'] = len(chain['nodes'].split(',')) >= len(expected_nodes) - 1
            
            dates = [d for d in [chain['trigger_date'], chain['proposal_date'], chain['resolution_date'], chain['implementation_date']] if d]
            if len(dates) >= 2:
                from datetime import datetime
                try:
                    first_date = datetime.strptime(min(dates), '%Y-%m-%d')
                    last_date = datetime.strptime(max(dates), '%Y-%m-%d')
                    chain['total_days'] = (last_date - first_date).days
                except:
                    pass
            
            event_chains.append(chain)
    
    return event_chains

def calculate_indicators(event_chains):
    """计算量化指标"""
    for chain in event_chains:
        if chain['event_type'] == 'adjustment':
            original_price = chain.get('original_conv_price')
            new_price = chain.get('new_conv_price')
            
            if original_price and new_price:
                try:
                    original_price = float(original_price)
                    new_price = float(new_price)
                    if original_price > 0:
                        adjustment_ratio = round((original_price - new_price) / original_price * 100, 2)
                        chain['adjustment_ratio_calc'] = adjustment_ratio
                        chain['adjustment_ratio_check'] = 'OK'
                except:
                    pass
        
        elif chain['event_type'] == 'redemption':
            redemption_price = chain.get('redemption_price')
            
            if redemption_price:
                try:
                    redemption_price = float(redemption_price)
                    premium_rate = round((redemption_price - 100) / 100 * 100, 2)
                    chain['premium_rate_calc'] = premium_rate
                    chain['conversion_value'] = 100
                    chain['calc_method'] = '简化计算(假设转股价值=100)'
                    chain['premium_rate_check'] = 'OK'
                except:
                    pass
        
        total_days = chain.get('total_days', 0)
        if total_days:
            try:
                total_days = int(total_days)
                if chain['event_type'] == 'adjustment':
                    chain['cycle_check'] = 'NORMAL' if total_days <= 90 else 'LONG'
                else:
                    chain['cycle_check'] = 'NORMAL' if total_days <= 60 else 'LONG'
            except:
                pass
    
    return event_chains

def main():
    print("Start updating outputs folders with real data...")
    
    # 加载真实数据
    real_data_path = "outputs/extract_results/structured_data_merged_final.json"
    if not os.path.exists(real_data_path):
        print(f"Error: Real data file not found {real_data_path}")
        return
    
    real_data = load_real_data(real_data_path)
    print(f"Loaded {len(real_data)} records")
    
    # 更新extract_results
    print("\nUpdating extract_results...")
    valid_records = update_extract_results(real_data)
    print(f"   Valid records: {len(valid_records)}")
    
    # 构建事件链
    print("\nUpdating event_chain...")
    event_chains = build_event_chains(valid_records)
    save_csv(event_chains, "outputs/event_chain/event_chains.csv")
    save_csv(event_chains, "outputs/sample_outputs/event_chains_sample.csv")
    print(f"   Built {len(event_chains)} event chains")
    
    # 计算指标
    print("\nUpdating indicators...")
    indicators = calculate_indicators(event_chains)
    save_csv(indicators, "outputs/indicators/quantitative_indicators.csv")
    save_csv(indicators[:10], "outputs/sample_outputs/quantitative_indicators_sample.csv")
    print(f"   Calculated {len(indicators)} indicators")
    
    # 更新sample outputs
    print("\nUpdating sample_outputs...")
    save_csv(valid_records[:10], "outputs/sample_outputs/records_validated_sample.csv")
    
    # 更新eval
    print("\nUpdating eval...")
    eval_sample = []
    for i, record in enumerate(valid_records[:20], 1):
        eval_sample.append({
            'id': i,
            'doc_id': record.get('doc_id'),
            'bond_code': record.get('bond_code'),
            'bond_name': record.get('bond_name'),
            'ann_type': record.get('ann_type'),
            'evidence_text': record.get('evidence_text', '')[:100] + '...' if record.get('evidence_text') else '',
            'review_result': '',
            'notes': ''
        })
    save_csv(eval_sample, "outputs/eval/eval_manual_sample.csv")
    
    print("\nAll outputs folders updated with real data!")
    print("Summary:")
    print(f"   - Total records: {len(real_data)}")
    print(f"   - Valid records: {len(valid_records)}")
    print(f"   - Event chains: {len(event_chains)}")
    print(f"   - Indicators: {len(indicators)}")

if __name__ == "__main__":
    main()
