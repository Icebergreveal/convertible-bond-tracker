import csv
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.process.event_matching import match_events, detect_event_types, infer_nodes, stage_to_node

class TestEventChainNodes(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.metadata_path = os.path.join(self.temp_dir, 'metadata.csv')
        self.extract_path = os.path.join(self.temp_dir, 'structured_data_standardized.json')
        self.output_path = os.path.join(self.temp_dir, 'event_chains.csv')

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def write_metadata(self, rows):
        fieldnames = [
            'doc_id', 'stock_code', 'stock_name', 'bond_code', 'bond_name',
            'ann_type', 'event_stage', 'publish_date'
        ]
        with open(self.metadata_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    def write_extract_records(self, records):
        with open(self.extract_path, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False)

    def test_adjustment_complete_chain(self):
        """测试下修事件完整链（4个节点）"""
        self.write_metadata([
            {'doc_id': 'doc_trigger', 'stock_code': '002726', 'stock_name': '龙大美食',
             'bond_code': '128130', 'bond_name': '龙大转债', 'ann_type': '下修触发提示',
             'event_stage': 'stage_1_trigger', 'publish_date': '2026-05-01'},
            {'doc_id': 'doc_proposal', 'stock_code': '002726', 'stock_name': '龙大美食',
             'bond_code': '128130', 'bond_name': '龙大转债', 'ann_type': '下修提议',
             'event_stage': 'stage_2_proposal', 'publish_date': '2026-05-03'},
            {'doc_id': 'doc_resolution', 'stock_code': '002726', 'stock_name': '龙大美食',
             'bond_code': '128130', 'bond_name': '龙大转债', 'ann_type': '下修决议',
             'event_stage': 'stage_3_resolution', 'publish_date': '2026-05-07'},
            {'doc_id': 'doc_impl', 'stock_code': '002726', 'stock_name': '龙大美食',
             'bond_code': '128130', 'bond_name': '龙大转债', 'ann_type': '下修实施',
             'event_stage': 'stage_4_implementation', 'publish_date': '2026-05-10'},
        ])
        
        self.write_extract_records([
            {'doc_id': 'doc_trigger', 'bond_code': '128130', 'ann_type': '下修类公告',
             'publish_date': '2026-05-01', 'trigger_rule': '连续30日中有15日低于85%'},
            {'doc_id': 'doc_proposal', 'bond_code': '128130', 'ann_type': '下修类公告',
             'publish_date': '2026-05-03', 'original_conv_price': 12.34},
            {'doc_id': 'doc_resolution', 'bond_code': '128130', 'ann_type': '下修类公告',
             'publish_date': '2026-05-07'},
            {'doc_id': 'doc_impl', 'bond_code': '128130', 'ann_type': '下修类公告',
             'publish_date': '2026-05-10', 'new_conv_price': 9.87, 'effective_date': '2026-05-11'},
        ])

        chains = match_events(self.metadata_path, self.extract_path, self.output_path)

        self.assertEqual(len(chains), 1)
        self.assertTrue(chains[0]['complete'])
        self.assertEqual(chains[0]['event_type'], 'adjustment')
        self.assertEqual(chains[0]['nodes'], ['trigger', 'proposal', 'resolution', 'implementation'])
        self.assertEqual(chains[0]['missing_nodes'], [])

    def test_adjustment_missing_proposal(self):
        """测试下修事件链缺失提议节点"""
        self.write_metadata([
            {'doc_id': 'doc_trigger', 'stock_code': '002726', 'stock_name': '龙大美食',
             'bond_code': '128130', 'bond_name': '龙大转债', 'ann_type': '下修触发提示',
             'event_stage': 'stage_1_trigger', 'publish_date': '2026-05-01'},
            {'doc_id': 'doc_resolution', 'stock_code': '002726', 'stock_name': '龙大美食',
             'bond_code': '128130', 'bond_name': '龙大转债', 'ann_type': '下修决议',
             'event_stage': 'stage_3_resolution', 'publish_date': '2026-05-07'},
            {'doc_id': 'doc_impl', 'stock_code': '002726', 'stock_name': '龙大美食',
             'bond_code': '128130', 'bond_name': '龙大转债', 'ann_type': '下修实施',
             'event_stage': 'stage_4_implementation', 'publish_date': '2026-05-10'},
        ])
        
        self.write_extract_records([
            {'doc_id': 'doc_trigger', 'bond_code': '128130', 'ann_type': '下修类公告',
             'publish_date': '2026-05-01'},
            {'doc_id': 'doc_resolution', 'bond_code': '128130', 'ann_type': '下修类公告',
             'publish_date': '2026-05-07'},
            {'doc_id': 'doc_impl', 'bond_code': '128130', 'ann_type': '下修类公告',
             'publish_date': '2026-05-10', 'new_conv_price': 9.87},
        ])

        chains = match_events(self.metadata_path, self.extract_path, self.output_path)

        self.assertEqual(len(chains), 1)
        self.assertFalse(chains[0]['complete'])
        self.assertEqual(set(chains[0]['nodes']), {'resolution', 'trigger', 'implementation'})
        self.assertEqual(chains[0]['missing_nodes'], ['proposal'])

    def test_adjustment_missing_multiple_nodes(self):
        """测试下修事件链缺失多个节点"""
        self.write_metadata([
            {'doc_id': 'doc_trigger', 'stock_code': '002726', 'stock_name': '龙大美食',
             'bond_code': '128130', 'bond_name': '龙大转债', 'ann_type': '下修触发提示',
             'event_stage': 'stage_1_trigger', 'publish_date': '2026-05-01'},
            {'doc_id': 'doc_impl', 'stock_code': '002726', 'stock_name': '龙大美食',
             'bond_code': '128130', 'bond_name': '龙大转债', 'ann_type': '下修实施',
             'event_stage': 'stage_4_implementation', 'publish_date': '2026-05-10'},
        ])
        
        self.write_extract_records([
            {'doc_id': 'doc_trigger', 'bond_code': '128130', 'ann_type': '下修类公告',
             'publish_date': '2026-05-01'},
            {'doc_id': 'doc_impl', 'bond_code': '128130', 'ann_type': '下修类公告',
             'publish_date': '2026-05-10', 'new_conv_price': 9.87},
        ])

        chains = match_events(self.metadata_path, self.extract_path, self.output_path)

        self.assertEqual(len(chains), 1)
        self.assertFalse(chains[0]['complete'])
        self.assertEqual(sorted(chains[0]['nodes']), ['implementation', 'trigger'])
        self.assertEqual(chains[0]['missing_nodes'], ['proposal', 'resolution'])

    def test_redemption_complete_chain(self):
        """测试强赎事件完整链（4个节点）"""
        self.write_metadata([
            {'doc_id': 'doc_trigger', 'stock_code': '603288', 'stock_name': '海天味业',
             'bond_code': '113595', 'bond_name': '海天转债', 'ann_type': '强赎触发提示',
             'event_stage': 'stage_1_trigger', 'publish_date': '2026-02-01'},
            {'doc_id': 'doc_resolution', 'stock_code': '603288', 'stock_name': '海天味业',
             'bond_code': '113595', 'bond_name': '海天转债', 'ann_type': '强赎决议',
             'event_stage': 'stage_2_resolution', 'publish_date': '2026-02-10'},
            {'doc_id': 'doc_impl', 'stock_code': '603288', 'stock_name': '海天味业',
             'bond_code': '113595', 'bond_name': '海天转债', 'ann_type': '强赎实施',
             'event_stage': 'stage_3_implementation', 'publish_date': '2026-02-20'},
            {'doc_id': 'doc_result', 'stock_code': '603288', 'stock_name': '海天味业',
             'bond_code': '113595', 'bond_name': '海天转债', 'ann_type': '强赎结果',
             'event_stage': 'stage_4_result', 'publish_date': '2026-02-28'},
        ])
        
        self.write_extract_records([
            {'doc_id': 'doc_trigger', 'bond_code': '113595', 'ann_type': '强赎类公告',
             'publish_date': '2026-02-01', 'redemption_trigger': '连续15日高于130%'},
            {'doc_id': 'doc_resolution', 'bond_code': '113595', 'ann_type': '强赎类公告',
             'publish_date': '2026-02-10', 'redemption_price': 103.50},
            {'doc_id': 'doc_impl', 'bond_code': '113595', 'ann_type': '强赎类公告',
             'publish_date': '2026-02-20', 'record_date': '2026-02-25', 'last_convert_date': '2026-02-27'},
            {'doc_id': 'doc_result', 'bond_code': '113595', 'ann_type': '强赎类公告',
             'publish_date': '2026-02-28', 'delisting_date': '2026-03-01'},
        ])

        chains = match_events(self.metadata_path, self.extract_path, self.output_path)

        self.assertEqual(len(chains), 1)
        self.assertTrue(chains[0]['complete'])
        self.assertEqual(chains[0]['event_type'], 'redemption')
        self.assertEqual(chains[0]['nodes'], ['trigger', 'resolution', 'implementation', 'result'])
        self.assertEqual(chains[0]['missing_nodes'], [])

    def test_redemption_missing_result(self):
        """测试强赎事件链缺失结果节点"""
        self.write_metadata([
            {'doc_id': 'doc_trigger', 'stock_code': '603288', 'stock_name': '海天味业',
             'bond_code': '113595', 'bond_name': '海天转债', 'ann_type': '强赎触发提示',
             'event_stage': 'stage_1_trigger', 'publish_date': '2026-02-01'},
            {'doc_id': 'doc_resolution', 'stock_code': '603288', 'stock_name': '海天味业',
             'bond_code': '113595', 'bond_name': '海天转债', 'ann_type': '强赎决议',
             'event_stage': 'stage_2_resolution', 'publish_date': '2026-02-10'},
            {'doc_id': 'doc_impl', 'stock_code': '603288', 'stock_name': '海天味业',
             'bond_code': '113595', 'bond_name': '海天转债', 'ann_type': '强赎实施',
             'event_stage': 'stage_3_implementation', 'publish_date': '2026-02-20'},
        ])
        
        self.write_extract_records([
            {'doc_id': 'doc_trigger', 'bond_code': '113595', 'ann_type': '强赎类公告',
             'publish_date': '2026-02-01'},
            {'doc_id': 'doc_resolution', 'bond_code': '113595', 'ann_type': '强赎类公告',
             'publish_date': '2026-02-10', 'redemption_price': 103.50},
            {'doc_id': 'doc_impl', 'bond_code': '113595', 'ann_type': '强赎类公告',
             'publish_date': '2026-02-20'},
        ])

        chains = match_events(self.metadata_path, self.extract_path, self.output_path)

        self.assertEqual(len(chains), 1)
        self.assertFalse(chains[0]['complete'])
        self.assertEqual(chains[0]['missing_nodes'], ['result'])

    def test_single_node_chain(self):
        """测试单节点事件链"""
        self.write_metadata([
            {'doc_id': 'doc_only_impl', 'stock_code': '002726', 'stock_name': '龙大美食',
             'bond_code': '128130', 'bond_name': '龙大转债', 'ann_type': '下修实施',
             'event_stage': 'stage_4_implementation', 'publish_date': '2026-05-10'},
        ])
        
        self.write_extract_records([
            {'doc_id': 'doc_only_impl', 'bond_code': '128130', 'ann_type': '下修类公告',
             'publish_date': '2026-05-10', 'new_conv_price': 9.87},
        ])

        chains = match_events(self.metadata_path, self.extract_path, self.output_path)

        self.assertEqual(len(chains), 1)
        self.assertFalse(chains[0]['complete'])
        self.assertEqual(chains[0]['nodes'], ['implementation'])
        self.assertEqual(chains[0]['missing_nodes'], ['trigger', 'proposal', 'resolution'])

    def test_detect_event_types_adjustment(self):
        """测试事件类型检测-下修"""
        record = {'ann_type': '下修实施', 'original_conv_price': 12.34, 'new_conv_price': 9.87}
        event_types = detect_event_types(record)
        self.assertIn('adjustment', event_types)

    def test_detect_event_types_redemption(self):
        """测试事件类型检测-强赎"""
        record = {'ann_type': '强赎决议', 'redemption_price': 103.50}
        event_types = detect_event_types(record)
        self.assertIn('redemption', event_types)

    def test_stage_to_node_mapping(self):
        """测试阶段到节点的映射"""
        self.assertEqual(stage_to_node('stage_1_trigger'), 'trigger')
        self.assertEqual(stage_to_node('stage_2_proposal'), 'proposal')
        self.assertEqual(stage_to_node('stage_3_resolution'), 'resolution')
        self.assertEqual(stage_to_node('stage_4_implementation'), 'implementation')
        self.assertEqual(stage_to_node('stage_4_result'), 'result')
        self.assertIsNone(stage_to_node('unknown'))

    def test_infer_adjustment_nodes_from_text(self):
        """测试从文本推断下修节点"""
        record = {'ann_type': '董事会提议向下修正转股价格', 'evidence_text': '董事会审议通过'}
        nodes = infer_nodes(record, 'adjustment')
        self.assertIn('proposal', nodes)

    def test_infer_redemption_nodes_from_text(self):
        """测试从文本推断强赎节点"""
        record = {'ann_type': '行使提前赎回权', 'evidence_text': '最后转股日期为2026-02-27'}
        nodes = infer_nodes(record, 'redemption')
        self.assertIn('implementation', nodes)

    def test_multiple_bonds_multiple_chains(self):
        """测试多个转债多个事件链"""
        self.write_metadata([
            {'doc_id': 'bond1_trigger', 'stock_code': '002726', 'stock_name': '龙大美食',
             'bond_code': '128130', 'bond_name': '龙大转债', 'ann_type': '下修触发提示',
             'event_stage': 'stage_1_trigger', 'publish_date': '2026-05-01'},
            {'doc_id': 'bond1_impl', 'stock_code': '002726', 'stock_name': '龙大美食',
             'bond_code': '128130', 'bond_name': '龙大转债', 'ann_type': '下修实施',
             'event_stage': 'stage_4_implementation', 'publish_date': '2026-05-10'},
            {'doc_id': 'bond2_trigger', 'stock_code': '603288', 'stock_name': '海天味业',
             'bond_code': '113595', 'bond_name': '海天转债', 'ann_type': '强赎触发提示',
             'event_stage': 'stage_1_trigger', 'publish_date': '2026-02-01'},
            {'doc_id': 'bond2_result', 'stock_code': '603288', 'stock_name': '海天味业',
             'bond_code': '113595', 'bond_name': '海天转债', 'ann_type': '强赎结果',
             'event_stage': 'stage_4_result', 'publish_date': '2026-02-28'},
        ])
        
        self.write_extract_records([
            {'doc_id': 'bond1_trigger', 'bond_code': '128130', 'ann_type': '下修类公告',
             'publish_date': '2026-05-01'},
            {'doc_id': 'bond1_impl', 'bond_code': '128130', 'ann_type': '下修类公告',
             'publish_date': '2026-05-10', 'new_conv_price': 9.87},
            {'doc_id': 'bond2_trigger', 'bond_code': '113595', 'ann_type': '强赎类公告',
             'publish_date': '2026-02-01'},
            {'doc_id': 'bond2_result', 'bond_code': '113595', 'ann_type': '强赎类公告',
             'publish_date': '2026-02-28', 'delisting_date': '2026-03-01'},
        ])

        chains = match_events(self.metadata_path, self.extract_path, self.output_path)

        self.assertEqual(len(chains), 2)
        bond1_chain = [c for c in chains if c['bond_code'] == '128130'][0]
        bond2_chain = [c for c in chains if c['bond_code'] == '113595'][0]
        
        self.assertEqual(bond1_chain['event_type'], 'adjustment')
        self.assertEqual(bond2_chain['event_type'], 'redemption')

if __name__ == '__main__':
    unittest.main()