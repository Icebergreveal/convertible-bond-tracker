import unittest
import os
import sys
import tempfile
import csv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.crawl.search_announcements import classify_announcement, extract_bond_info, generate_doc_id

class TestCrawlFunctions(unittest.TestCase):
    
    def test_classify_announcement_lower_repair_trigger(self):
        """测试下修触发提示分类"""
        titles = [
            '关于美锦转债预计触发转股价格向下修正条件的提示性公告',
            '关于"龙大转债"触发转股价格向下修正条件的提示性公告',
            '预计触发转股价格向下修正条件的公告'
        ]
        
        for title in titles:
            ann_type, stage = classify_announcement(title)
            self.assertEqual(ann_type, '下修触发提示')
            self.assertEqual(stage, 'stage_1_trigger')
    
    def test_classify_announcement_lower_repair_proposal(self):
        """测试下修提议分类"""
        titles = [
            '关于董事会提议向下修正"龙大转债"转股价格的公告',
            '董事会提议向下修正转股价格公告',
            '关于向下修正转股价格的公告'
        ]
        
        for title in titles:
            ann_type, stage = classify_announcement(title)
            self.assertEqual(ann_type, '下修提议')
            self.assertEqual(stage, 'stage_2_proposal')
    
    def test_classify_announcement_lower_repair_resolution(self):
        """测试下修决议分类"""
        titles = [
            '关于"双汇转债"转股价格向下修正的股东大会决议公告',
            '转股价格调整决议公告',
            '关于转股价格调整的公告'
        ]
        
        for title in titles:
            ann_type, stage = classify_announcement(title)
            self.assertEqual(ann_type, '下修决议')
            self.assertEqual(stage, 'stage_3_resolution')
    
    def test_classify_announcement_lower_repair_implementation(self):
        """测试下修实施分类"""
        titles = [
            '关于"茅台转债"转股价格向下修正实施的公告',
            '转股价格向下修正实施公告',
            '实施转股价格修正公告'
        ]
        
        for title in titles:
            ann_type, stage = classify_announcement(title)
            self.assertEqual(ann_type, '下修实施')
            self.assertEqual(stage, 'stage_4_implementation')
    
    def test_classify_announcement_redemption_trigger(self):
        """测试强赎触发提示分类"""
        titles = [
            '关于"洋河转债"满足提前赎回条件的提示性公告',
            '触发提前赎回条件公告',
            '提前赎回条件满足提示公告'
        ]
        
        for title in titles:
            ann_type, stage = classify_announcement(title)
            self.assertEqual(ann_type, '强赎触发提示')
            self.assertEqual(stage, 'stage_1_trigger')
    
    def test_classify_announcement_redemption_resolution(self):
        """测试强赎决议分类"""
        titles = [
            '关于行使"平安转债"提前赎回权的决议公告',
            '行使提前赎回权公告',
            '董事会关于提前赎回的决议'
        ]
        
        for title in titles:
            ann_type, stage = classify_announcement(title)
            self.assertEqual(ann_type, '强赎决议')
            self.assertEqual(stage, 'stage_2_resolution')
    
    def test_classify_announcement_redemption_implementation(self):
        """测试强赎实施分类"""
        titles = [
            '关于"格力转债"提前赎回实施的提示性公告',
            '提前赎回实施公告',
            '赎回实施提示公告'
        ]
        
        for title in titles:
            ann_type, stage = classify_announcement(title)
            self.assertEqual(ann_type, '强赎实施')
            self.assertEqual(stage, 'stage_3_implementation')
    
    def test_classify_announcement_redemption_result(self):
        """测试强赎结果分类"""
        titles = [
            '关于"浦发转债"提前赎回结果暨摘牌公告',
            '可转债赎回结果公告',
            '转债摘牌公告'
        ]
        
        for title in titles:
            ann_type, stage = classify_announcement(title)
            self.assertEqual(ann_type, '强赎结果')
            self.assertEqual(stage, 'stage_4_result')
    
    def test_extract_bond_info(self):
        """测试可转债信息提取"""
        test_cases = [
            ('关于128152龙大转债转股价格调整公告', ('128152', '龙大转债')),
            ('关于"110061茅台转债"赎回公告', ('110061', '茅台转债')),
            ('美锦转债公告', (None, '美锦转债')),
            ('127061公告', ('127061', None)),
            ('普通公告', (None, None))
        ]
        
        for title, expected in test_cases:
            bond_code, bond_name = extract_bond_info(title)
            self.assertEqual((bond_code, bond_name), expected)
    
    def test_generate_doc_id(self):
        """测试文档ID生成"""
        id1 = generate_doc_id('002726', '2024-01-01', '测试公告')
        id2 = generate_doc_id('002726', '2024-01-01', '测试公告')
        id3 = generate_doc_id('002727', '2024-01-01', '测试公告')
        
        self.assertEqual(id1, id2)
        self.assertNotEqual(id1, id3)
        self.assertEqual(len(id1), 16)
    
    def test_classify_unknown_announcement(self):
        """测试未知公告类型"""
        title = '2024年第一季度报告'
        ann_type, stage = classify_announcement(title)
        self.assertEqual(ann_type, '其他')
        self.assertEqual(stage, 'stage_unknown')

if __name__ == '__main__':
    unittest.main()