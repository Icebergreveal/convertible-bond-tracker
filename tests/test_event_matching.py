import csv
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.process.event_matching import match_events


class TestEventMatching(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.metadata_path = os.path.join(self.temp_dir, 'metadata.csv')
        self.extract_path = os.path.join(self.temp_dir, 'structured_data_standardized.json')
        self.output_path = os.path.join(self.temp_dir, 'event_chains.csv')

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def write_metadata(self):
        fieldnames = [
            'doc_id', 'stock_code', 'stock_name', 'bond_code', 'bond_name',
            'ann_type', 'event_stage', 'publish_date'
        ]
        rows = [
            ['doc_trigger', '002726', '龙大美食', '128130', '龙大转债', '下修触发提示', 'stage_1_trigger', '2026-05-01'],
            ['doc_proposal', '002726', '龙大美食', '128130', '龙大转债', '下修提议', 'stage_2_proposal', '2026-05-03'],
            ['doc_resolution', '002726', '龙大美食', '128130', '龙大转债', '下修决议', 'stage_3_resolution', '2026-05-07'],
            ['doc_impl', '002726', '龙大美食', '128130', '龙大转债', '下修实施', 'stage_4_implementation', '2026-05-10'],
        ]
        with open(self.metadata_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(fieldnames)
            writer.writerows(rows)

    def write_extract_records(self):
        records = [
            {
                'doc_id': 'doc_trigger',
                'stock_code': '002726',
                'stock_name': '龙大美食',
                'bond_code': '128130',
                'bond_name': '龙大转债',
                'ann_type': '下修类公告',
                'publish_date': '2026-05-01',
                'trigger_rule': '连续30个交易日中有15个交易日收盘价低于转股价的85%',
            },
            {
                'doc_id': 'doc_proposal',
                'bond_code': '128130',
                'bond_name': '龙大转债',
                'ann_type': '下修类公告',
                'publish_date': '2026-05-03',
                'original_conv_price': 12.34,
            },
            {
                'doc_id': 'doc_resolution',
                'bond_code': '128130',
                'bond_name': '龙大转债',
                'ann_type': '下修类公告',
                'publish_date': '2026-05-07',
            },
            {
                'doc_id': 'doc_impl',
                'bond_code': '128130',
                'bond_name': '龙大转债',
                'ann_type': '下修类公告',
                'publish_date': '2026-05-10',
                'new_conv_price': 9.87,
                'effective_date': '2026-05-11',
            },
        ]
        with open(self.extract_path, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False)

    def test_build_complete_adjustment_chain_from_main_entry(self):
        self.write_metadata()
        self.write_extract_records()

        chains = match_events(self.metadata_path, self.extract_path, self.output_path)

        self.assertEqual(len(chains), 1)
        self.assertTrue(chains[0]['complete'])
        self.assertEqual(chains[0]['event_type'], 'adjustment')
        self.assertEqual(chains[0]['nodes'], ['trigger', 'proposal', 'resolution', 'implementation'])
        self.assertEqual(chains[0]['missing_nodes'], [])
        self.assertEqual(chains[0]['original_conv_price'], 12.34)
        self.assertEqual(chains[0]['new_conv_price'], 9.87)
        self.assertTrue(os.path.exists(self.output_path))

        with open(self.output_path, 'r', encoding='utf-8-sig') as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(rows[0]['nodes'], 'trigger,proposal,resolution,implementation')


if __name__ == '__main__':
    unittest.main()
