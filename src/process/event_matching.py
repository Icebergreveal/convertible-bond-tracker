import os
import json
import csv
from datetime import datetime
from typing import List, Dict, Optional

EVENT_STAGE_ORDER = {
    '下修': ['stage_1_trigger', 'stage_2_proposal', 'stage_3_resolution', 'stage_4_implementation'],
    '强赎': ['stage_1_trigger', 'stage_2_resolution', 'stage_3_implementation', 'stage_4_result']
}

class BondEventMatcher:
    def __init__(self):
        self.bond_map = {}
        self.event_chains = []
    
    def load_bond_info(self, metadata_path: str):
        """从metadata加载可转债信息并建立映射"""
        if not os.path.exists(metadata_path):
            print(f"[EventMatch] 警告: metadata文件不存在 {metadata_path}")
            return
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                bond_code = row.get('bond_code')
                bond_name = row.get('bond_name')
                stock_code = row.get('stock_code')
                stock_name = row.get('stock_name')
                
                if bond_code:
                    if bond_code not in self.bond_map:
                        self.bond_map[bond_code] = {
                            'bond_code': bond_code,
                            'bond_name': bond_name,
                            'stock_code': stock_code,
                            'stock_name': stock_name,
                            'events': []
                        }
                    
                    self.bond_map[bond_code]['events'].append({
                        'doc_id': row.get('doc_id'),
                        'ann_type': row.get('ann_type'),
                        'event_stage': row.get('event_stage'),
                        'publish_date': row.get('publish_date'),
                        'download_status': row.get('download_status')
                    })
        
        print(f"[EventMatch] 加载了 {len(self.bond_map)} 个可转债")
    
    def load_extracted_data(self, extract_path: str) -> List[Dict]:
        """加载LLM抽取结果"""
        if not os.path.exists(extract_path):
            print(f"[EventMatch] 警告: 抽取结果文件不存在 {extract_path}")
            return []
        
        try:
            with open(extract_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"[EventMatch] 警告: JSON解析失败 {extract_path}")
            return []
    
    def build_event_chains(self, extracted_data: List[Dict]) -> List[Dict]:
        """为每个可转债构建事件链"""
        chains = []
        
        for bond_code, bond_info in self.bond_map.items():
            events = bond_info['events']
            if len(events) < 2:
                continue
            
            sorted_events = sorted(events, key=lambda x: x['publish_date'])
            
            event_type = self._determine_event_type(sorted_events[0]['ann_type'])
            if event_type not in EVENT_STAGE_ORDER:
                continue
            
            chain = self._build_chain_for_bond(bond_info, sorted_events, event_type)
            if chain:
                chains.append(chain)
        
        print(f"[EventMatch] 构建了 {len(chains)} 条事件链")
        return chains
    
    def _determine_event_type(self, ann_type: str) -> str:
        """确定事件类型"""
        if '下修' in ann_type:
            return '下修'
        elif '强赎' in ann_type or '赎回' in ann_type:
            return '强赎'
        return 'unknown'
    
    def _build_chain_for_bond(self, bond_info: Dict, events: List[Dict], event_type: str) -> Optional[Dict]:
        """为单个可转债构建事件链"""
        chain = {
            'bond_code': bond_info['bond_code'],
            'bond_name': bond_info['bond_name'],
            'stock_code': bond_info['stock_code'],
            'stock_name': bond_info['stock_name'],
            'event_type': event_type,
            'stages': {},
            'complete': False,
            'total_days': 0,
            'original_conv_price': None,
            'new_conv_price': None,
            'redemption_price': None,
            'adjustment_ratio': None,
            'premium_rate': None,
            'events': []
        }
        
        stage_order = EVENT_STAGE_ORDER[event_type]
        stage_info = {}
        
        for event in events:
            stage = event.get('event_stage')
            if stage in stage_order:
                stage_info[stage] = event
        
        chain['stages'] = stage_info
        
        has_all_stages = all(stage in stage_info for stage in stage_order)
        chain['complete'] = has_all_stages
        
        if stage_info:
            first_event = events[0]
            last_event = events[-1]
            try:
                first_date = datetime.strptime(first_event['publish_date'], '%Y-%m-%d')
                last_date = datetime.strptime(last_event['publish_date'], '%Y-%m-%d')
                chain['total_days'] = (last_date - first_date).days
            except:
                chain['total_days'] = 0
        
        chain['events'] = events
        
        return chain
    
    def enrich_chains_with_extracted_data(self, chains: List[Dict], extracted_data: List[Dict]):
        """用抽取数据丰富事件链"""
        doc_id_map = {item['doc_id']: item for item in extracted_data if 'doc_id' in item}
        
        for chain in chains:
            for event in chain['events']:
                doc_id = event.get('doc_id')
                if doc_id in doc_id_map:
                    extracted = doc_id_map[doc_id]
                    
                    if chain['event_type'] == '下修':
                        if chain['original_conv_price'] is None:
                            chain['original_conv_price'] = extracted.get('original_conv_price')
                        if chain['new_conv_price'] is None:
                            chain['new_conv_price'] = extracted.get('new_conv_price')
                        if chain['adjustment_ratio'] is None:
                            chain['adjustment_ratio'] = extracted.get('adjustment_ratio')
                    
                    elif chain['event_type'] == '强赎':
                        if chain['redemption_price'] is None:
                            chain['redemption_price'] = extracted.get('redemption_price')
                        if chain['premium_rate'] is None:
                            chain['premium_rate'] = extracted.get('premium_rate')
        
        return chains
    
    def save_chains(self, chains: List[Dict], output_path: str):
        """保存事件链到文件"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            fieldnames = [
                'bond_code', 'bond_name', 'stock_code', 'stock_name', 'event_type',
                'complete', 'total_days', 'original_conv_price', 'new_conv_price',
                'redemption_price', 'adjustment_ratio', 'premium_rate', 'stages', 'events'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for chain in chains:
                row = {k: chain.get(k) for k in fieldnames}
                row['stages'] = json.dumps(chain.get('stages', {}), ensure_ascii=False)
                row['events'] = json.dumps(chain.get('events', []), ensure_ascii=False)
                writer.writerow(row)
        
        print(f"[EventMatch] 事件链已保存到 {output_path}")
    
    def match_events(self, metadata_path: str, extract_path: str, output_path: str):
        """完整的事件链匹配流程"""
        print("[EventMatch] 开始事件链匹配...")
        
        self.load_bond_info(metadata_path)
        extracted_data = self.load_extracted_data(extract_path)
        chains = self.build_event_chains(extracted_data)
        chains = self.enrich_chains_with_extracted_data(chains, extracted_data)
        self.save_chains(chains, output_path)
        
        self._print_summary(chains)
        
        return chains
    
    def _print_summary(self, chains: List[Dict]):
        """打印事件链摘要"""
        complete_chains = [c for c in chains if c['complete']]
        incomplete_chains = [c for c in chains if not c['complete']]
        
        print(f"\n[EventMatch] 事件链匹配摘要:")
        print(f"  总事件链数: {len(chains)}")
        print(f"  完整事件链: {len(complete_chains)}")
        print(f"  不完整事件链: {len(incomplete_chains)}")
        
        print("\n[EventMatch] 事件链详情:")
        for chain in chains:
            status = "✅" if chain['complete'] else "⚡"
            print(f"  {status} {chain['bond_name']} ({chain['bond_code']}) - {chain['event_type']}")
            print(f"     阶段: {list(chain['stages'].keys())}")
            print(f"     周期: {chain['total_days']} 天")
            if chain['event_type'] == '下修':
                print(f"     转股价: {chain['original_conv_price']} → {chain['new_conv_price']}")
            elif chain['event_type'] == '强赎':
                print(f"     赎回价: {chain['redemption_price']}")

def match_events(
    metadata_path: str = "data/metadata/metadata.csv",
    extract_path: str = "outputs/extract_results/structured_data.json",
    output_path: str = "outputs/event_chain/event_chains.csv"
):
    """事件链匹配入口函数"""
    matcher = BondEventMatcher()
    return matcher.match_events(metadata_path, extract_path, output_path)

if __name__ == '__main__':
    match_events()