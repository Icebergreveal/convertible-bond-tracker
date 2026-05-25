import unittest
import os
import sys
import tempfile
import json
import csv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestPipelineIntegration(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.temp_dir, 'data', 'metadata'), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, 'outputs', 'extract_results'), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, 'outputs', 'event_chain'), exist_ok=True)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_end_to_end_pipeline(self):
        """测试端到端工作流"""
        from src.extract.validate_results import validate_record
        from src.indicator.calc_indicators import calculate_indicators
        
        test_record = {
            "doc_id": "test_end_to_end",
            "stock_code": "002726",
            "stock_name": "龙大美食",
            "bond_code": "128130",
            "bond_name": "龙大转债",
            "ann_type": "董事会提议向下修正转股价格公告",
            "publish_date": "2026-05-07",
            "original_conv_price": 12.34,
            "new_conv_price": 9.87,
            "effective_date": "2026-05-10",
            "adjustment_ratio": 20.02,
            "evidence_page": 2,
            "evidence_text": "董事会提议向下修正转股价格"
        }
        
        validation_result = validate_record(test_record)
        self.assertTrue(validation_result['valid'], f"校验失败: {validation_result.get('errors')}")
        
        event_chain_path = os.path.join(self.temp_dir, 'outputs', 'event_chain', 'event_chains.csv')
        fieldnames = ['bond_code', 'bond_name', 'event_type', 'complete',
                      'original_conv_price', 'new_conv_price', 'redemption_price',
                      'total_days']
        with open(event_chain_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow({
                'bond_code': '128130',
                'bond_name': '龙大转债',
                'event_type': 'adjustment',
                'complete': 'True',
                'original_conv_price': '12.34',
                'new_conv_price': '9.87',
                'redemption_price': '',
                'total_days': '30'
            })
        
        indicators = calculate_indicators(event_chain_path)
        self.assertEqual(len(indicators), 1)
        self.assertEqual(indicators[0]['adjustment_ratio_calc'], 20.02)
    
    def test_data_flow_consistency(self):
        """测试数据流转一致性"""
        from src.extract.validate_results import validate_record
        
        test_records = [
            {
                "doc_id": "test_001",
                "stock_code": "002726",
                "stock_name": "龙大美食",
                "bond_code": "128130",
                "bond_name": "龙大转债",
                "ann_type": "董事会提议向下修正转股价格公告",
                "publish_date": "2026-05-07",
                "original_conv_price": 12.34,
                "new_conv_price": 9.87
            },
            {
                "doc_id": "test_002",
                "stock_code": "603288",
                "stock_name": "海天味业",
                "bond_code": "113595",
                "bond_name": "海天转债",
                "ann_type": "可转债赎回结果暨摘牌公告",
                "publish_date": "2026-02-28",
                "redemption_price": 102.80,
                "delisting_date": "2026-03-02"
            }
        ]
        
        all_valid = True
        for record in test_records:
            result = validate_record(record)
            if not result['valid']:
                all_valid = False
                print(f"校验失败: {record['doc_id']} - {result['errors']}")
        
        self.assertTrue(all_valid)
    
    def test_metadata_format(self):
        """测试metadata格式"""
        metadata_path = os.path.join(self.temp_dir, 'data', 'metadata', 'metadata.csv')
        
        fieldnames = ['doc_id', 'stock_code', 'stock_name', 'bond_code', 'bond_name',
                      'ann_title', 'publish_date', 'ann_type', 'download_status', 'pdf_path']
        
        with open(metadata_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow({
                'doc_id': 'test_doc_001',
                'stock_code': '002726',
                'stock_name': '龙大美食',
                'bond_code': '128130',
                'bond_name': '龙大转债',
                'ann_title': '董事会提议向下修正转股价格公告',
                'publish_date': '2026-05-07',
                'ann_type': '董事会提议向下修正转股价格公告',
                'download_status': 'success',
                'pdf_path': 'data/pdf/test_doc_001.pdf'
            })
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            records = list(reader)
        
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['doc_id'], 'test_doc_001')
        self.assertEqual(records[0]['stock_code'], '002726')
        self.assertEqual(records[0]['download_status'], 'success')
    
    def test_empty_input_handling(self):
        """测试空输入处理"""
        from src.indicator.calc_indicators import calculate_indicators
        from src.extract.validate_results import validate_record
        
        result = calculate_indicators('nonexistent_file.csv')
        self.assertEqual(result, [])
        
        empty_record = {}
        validation = validate_record(empty_record)
        self.assertFalse(validation['valid'])
        self.assertIn('必填字段', str(validation['errors']))

if __name__ == '__main__':
    unittest.main()
