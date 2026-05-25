import unittest
import os
import sys
import tempfile
import csv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.indicator.calc_indicators import calculate_indicators

class TestCalculateIndicators(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.input_path = os.path.join(self.temp_dir, 'event_chains.csv')
        self.output_path = os.path.join(self.temp_dir, 'quantitative_indicators.csv')
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def create_test_csv(self, rows):
        fieldnames = ['bond_code', 'bond_name', 'event_type', 'complete',
                      'original_conv_price', 'new_conv_price', 'redemption_price',
                      'total_days', 'adjustment_ratio', 'premium_rate']
        with open(self.input_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    
    def test_adjustment_ratio_calculation(self):
        """测试下修幅度计算"""
        self.create_test_csv([{
            'bond_code': '128130',
            'bond_name': '龙大转债',
            'event_type': 'adjustment',
            'complete': 'True',
            'original_conv_price': '12.34',
            'new_conv_price': '9.87',
            'redemption_price': '',
            'total_days': '30'
        }])
        
        result = calculate_indicators(self.input_path)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['adjustment_ratio_calc'], 20.02)
        self.assertEqual(result[0]['adjustment_ratio_check'], 'NO_EXISTING')
    
    def test_adjustment_ratio_with_existing(self):
        """测试下修幅度与已有值比对"""
        self.create_test_csv([{
            'bond_code': '128130',
            'bond_name': '龙大转债',
            'event_type': 'adjustment',
            'complete': 'True',
            'original_conv_price': '12.34',
            'new_conv_price': '9.87',
            'redemption_price': '',
            'total_days': '30',
            'adjustment_ratio': '20.02'
        }])
        
        result = calculate_indicators(self.input_path)
        
        self.assertEqual(result[0]['adjustment_ratio_check'], 'OK')
    
    def test_adjustment_ratio_mismatch(self):
        """测试下修幅度不匹配情况"""
        self.create_test_csv([{
            'bond_code': '128130',
            'bond_name': '龙大转债',
            'event_type': 'adjustment',
            'complete': 'True',
            'original_conv_price': '12.34',
            'new_conv_price': '9.87',
            'redemption_price': '',
            'total_days': '30',
            'adjustment_ratio': '15.00'
        }])
        
        result = calculate_indicators(self.input_path)
        
        self.assertEqual(result[0]['adjustment_ratio_check'], 'MISMATCH')
    
    def test_premium_rate_calculation(self):
        """测试赎回溢价率计算"""
        self.create_test_csv([{
            'bond_code': '113595',
            'bond_name': '海天转债',
            'event_type': 'redemption',
            'complete': 'True',
            'original_conv_price': '',
            'new_conv_price': '',
            'redemption_price': '103.50',
            'total_days': '20'
        }])
        
        result = calculate_indicators(self.input_path)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['premium_rate_calc'], 3.5)
        self.assertEqual(result[0]['premium_rate_check'], 'NO_EXISTING')
    
    def test_cycle_check_adjustment_normal(self):
        """测试下修事件周期检查-正常"""
        self.create_test_csv([{
            'bond_code': '128130',
            'bond_name': '龙大转债',
            'event_type': 'adjustment',
            'complete': 'True',
            'original_conv_price': '12.34',
            'new_conv_price': '9.87',
            'redemption_price': '',
            'total_days': '60'
        }])
        
        result = calculate_indicators(self.input_path)
        
        self.assertEqual(result[0]['cycle_check'], 'NORMAL')
    
    def test_cycle_check_adjustment_long(self):
        """测试下修事件周期检查-过长"""
        self.create_test_csv([{
            'bond_code': '128130',
            'bond_name': '龙大转债',
            'event_type': 'adjustment',
            'complete': 'True',
            'original_conv_price': '12.34',
            'new_conv_price': '9.87',
            'redemption_price': '',
            'total_days': '100'
        }])
        
        result = calculate_indicators(self.input_path)
        
        self.assertEqual(result[0]['cycle_check'], 'LONG')
    
    def test_cycle_check_redemption_normal(self):
        """测试强赎事件周期检查-正常"""
        self.create_test_csv([{
            'bond_code': '113595',
            'bond_name': '海天转债',
            'event_type': 'redemption',
            'complete': 'True',
            'original_conv_price': '',
            'new_conv_price': '',
            'redemption_price': '103.50',
            'total_days': '45'
        }])
        
        result = calculate_indicators(self.input_path)
        
        self.assertEqual(result[0]['cycle_check'], 'NORMAL')
    
    def test_cycle_check_redemption_long(self):
        """测试强赎事件周期检查-过长"""
        self.create_test_csv([{
            'bond_code': '113595',
            'bond_name': '海天转债',
            'event_type': 'redemption',
            'complete': 'True',
            'original_conv_price': '',
            'new_conv_price': '',
            'redemption_price': '103.50',
            'total_days': '70'
        }])
        
        result = calculate_indicators(self.input_path)
        
        self.assertEqual(result[0]['cycle_check'], 'LONG')
    
    def test_missing_values(self):
        """测试缺失值处理"""
        self.create_test_csv([{
            'bond_code': '128130',
            'bond_name': '龙大转债',
            'event_type': 'adjustment',
            'complete': 'True',
            'original_conv_price': '',
            'new_conv_price': '',
            'redemption_price': '',
            'total_days': ''
        }])
        
        result = calculate_indicators(self.input_path)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['adjustment_ratio_calc'], '')
        self.assertEqual(result[0]['premium_rate_calc'], '')
        self.assertEqual(result[0]['cycle_check'], '')
    
    def test_zero_original_price(self):
        """测试原转股价为0的情况"""
        self.create_test_csv([{
            'bond_code': '128130',
            'bond_name': '龙大转债',
            'event_type': 'adjustment',
            'complete': 'True',
            'original_conv_price': '0',
            'new_conv_price': '9.87',
            'redemption_price': '',
            'total_days': '30'
        }])
        
        result = calculate_indicators(self.input_path)
        
        self.assertEqual(result[0]['adjustment_ratio_calc'], '')
    
    def test_empty_input(self):
        """测试空输入"""
        result = calculate_indicators(os.path.join(self.temp_dir, 'nonexistent.csv'))
        
        self.assertEqual(result, [])
    
    def test_multiple_records(self):
        """测试多条记录处理"""
        self.create_test_csv([
            {
                'bond_code': '128130',
                'bond_name': '龙大转债',
                'event_type': 'adjustment',
                'complete': 'True',
                'original_conv_price': '12.34',
                'new_conv_price': '9.87',
                'redemption_price': '',
                'total_days': '30'
            },
            {
                'bond_code': '113595',
                'bond_name': '海天转债',
                'event_type': 'redemption',
                'complete': 'True',
                'original_conv_price': '',
                'new_conv_price': '',
                'redemption_price': '102.80',
                'total_days': '15'
            }
        ])
        
        result = calculate_indicators(self.input_path)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['adjustment_ratio_calc'], 20.02)
        self.assertEqual(result[1]['premium_rate_calc'], 2.8)

if __name__ == '__main__':
    unittest.main()
