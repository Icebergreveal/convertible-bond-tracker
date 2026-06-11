import unittest
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.schema.schemas import ConversionPriceAdjustment, EarlyRedemption
from src.extract.validate_results import validate_record
from pydantic import ValidationError

class TestPydanticSchemas(unittest.TestCase):
    
    def test_conversion_price_adjustment_valid(self):
        """测试下修Schema正常校验"""
        data = {
            "doc_id": "test_doc_001",
            "stock_code": "002726",
            "stock_name": "龙大美食",
            "bond_code": "128130",
            "bond_name": "龙大转债",
            "ann_type": "下修实施",
            "publish_date": "2026-05-10",
            "original_conv_price": 12.34,
            "new_conv_price": 9.87,
            "adjustment_ratio": 20.02,
            "evidence_text": "董事会同意向下修正转股价格"
        }
        
        model = ConversionPriceAdjustment(**data)
        self.assertEqual(model.doc_id, "test_doc_001")
        self.assertEqual(model.stock_code, "002726")
        self.assertEqual(model.original_conv_price, 12.34)
        self.assertEqual(model.new_conv_price, 9.87)
    
    def test_conversion_price_adjustment_missing_required(self):
        """测试下修Schema必填字段缺失"""
        data = {
            "doc_id": "test_doc_001",
            "stock_code": "002726",
            "stock_name": "龙大美食",
            "ann_type": "下修实施"
        }
        
        model = ConversionPriceAdjustment(**data)
        self.assertIsNone(model.bond_code)
        self.assertIsNone(model.bond_name)
    
    def test_conversion_price_adjustment_invalid_price(self):
        """测试下修Schema无效价格（负数）"""
        data = {
            "doc_id": "test_doc_001",
            "stock_code": "002726",
            "stock_name": "龙大美食",
            "ann_type": "下修实施",
            "original_conv_price": -10.0,
            "new_conv_price": 9.87
        }
        
        with self.assertRaises(ValidationError):
            ConversionPriceAdjustment(**data)
    
    def test_conversion_price_adjustment_with_avg_prices(self):
        """测试包含均价字段的下修Schema校验"""
        data = {
            "doc_id": "test_doc_001",
            "stock_code": "002726",
            "stock_name": "龙大美食",
            "ann_type": "下修实施",
            "new_conv_price": 10.0,
            "avg_price_20d": 8.0,
            "avg_price_1d": 8.5
        }
        
        model = ConversionPriceAdjustment(**data)
        self.assertEqual(model.new_conv_price, 10.0)
        self.assertEqual(model.avg_price_20d, 8.0)
    
    def test_early_redemption_valid(self):
        """测试强赎Schema正常校验"""
        data = {
            "doc_id": "test_doc_002",
            "stock_code": "603288",
            "stock_name": "海天味业",
            "bond_code": "113595",
            "bond_name": "海天转债",
            "ann_type": "强赎实施",
            "publish_date": "2026-02-28",
            "redemption_price": 103.50,
            "evidence_text": "行使提前赎回权"
        }
        
        model = EarlyRedemption(**data)
        self.assertEqual(model.redemption_price, 103.50)
    
    def test_early_redemption_invalid_price(self):
        """测试强赎Schema无效赎回价格（低于100）"""
        data = {
            "doc_id": "test_doc_002",
            "stock_code": "603288",
            "stock_name": "海天味业",
            "ann_type": "强赎实施",
            "redemption_price": 99.0
        }
        
        with self.assertRaises(ValidationError):
            EarlyRedemption(**data)
    
    def test_adjustment_ratio_range(self):
        """测试下修幅度超出范围"""
        data = {
            "doc_id": "test_doc_001",
            "stock_code": "002726",
            "stock_name": "龙大美食",
            "ann_type": "下修实施",
            "adjustment_ratio": 150.0
        }
        
        with self.assertRaises(ValidationError):
            ConversionPriceAdjustment(**data)
    
    def test_validate_record_success(self):
        """测试validate_record成功校验"""
        record = {
            "doc_id": "test_doc_001",
            "stock_code": "002726",
            "stock_name": "龙大美食",
            "bond_code": "128130",
            "bond_name": "龙大转债",
            "ann_type": "下修实施",
            "publish_date": "2026-05-10",
            "original_conv_price": 12.34,
            "new_conv_price": 9.87,
            "evidence_text": "董事会同意向下修正转股价格"
        }
        
        result = validate_record(record)
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)
        self.assertIsNotNone(result['parsed'])
    
    def test_validate_record_missing_required(self):
        """测试validate_record必填字段缺失"""
        record = {
            "doc_id": "",
            "stock_code": "",
            "stock_name": "",
            "ann_type": "下修实施"
        }
        
        result = validate_record(record)
        self.assertFalse(result['valid'])
        self.assertIn("必填字段", str(result['errors']))
    
    def test_validate_record_invalid_date(self):
        """测试validate_record日期格式错误"""
        record = {
            "doc_id": "test_doc_001",
            "stock_code": "002726",
            "stock_name": "龙大美食",
            "ann_type": "下修实施",
            "publish_date": "2026/05/10"
        }
        
        result = validate_record(record)
        self.assertFalse(result['valid'])
        self.assertIn("日期格式错误", str(result['errors']))
    
    def test_validate_record_invalid_numeric(self):
        """测试validate_record数值格式错误"""
        record = {
            "doc_id": "test_doc_001",
            "stock_code": "002726",
            "stock_name": "龙大美食",
            "ann_type": "下修实施",
            "original_conv_price": "invalid"
        }
        
        result = validate_record(record)
        self.assertFalse(result['valid'])
        self.assertIn("必须是数字类型", str(result['errors']))
    
    def test_validate_record_new_price_higher(self):
        """测试validate_record新转股价高于原转股价警告"""
        record = {
            "doc_id": "test_doc_001",
            "stock_code": "002726",
            "stock_name": "龙大美食",
            "ann_type": "下修实施",
            "original_conv_price": 9.87,
            "new_conv_price": 12.34,
            "evidence_text": "test"
        }
        
        result = validate_record(record)
        self.assertTrue(result['valid'])
        self.assertIn("新转股价高于原转股价", str(result['warnings']))
    
    def test_validate_record_unknown_ann_type(self):
        """测试validate_record未知公告类型"""
        record = {
            "doc_id": "test_doc_001",
            "stock_code": "002726",
            "stock_name": "龙大美食",
            "ann_type": "未知公告类型",
            "evidence_text": "test"
        }
        
        result = validate_record(record)
        self.assertTrue(result['valid'])
        self.assertIn("未知公告类型", str(result['warnings']))

if __name__ == '__main__':
    unittest.main()