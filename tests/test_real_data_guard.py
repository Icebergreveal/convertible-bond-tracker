import csv
import os
import shutil
import tempfile
import unittest

from generate_metadata import extract_review_info
from src.crawl.real_data_guard import read_metadata_csv, validate_real_metadata_record
from src.crawl.search_announcements import save_metadata


class TestRealDataGuard(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def real_record(self):
        return {
            'doc_id': 'real_001',
            'stock_code': '002726',
            'stock_name': '龙大美食',
            'bond_code': '128130',
            'bond_name': '龙大转债',
            'title': '关于龙大转债转股价格调整公告',
            'ann_type': '下修决议',
            'event_stage': 'stage_3_resolution',
            'publish_date': '2026-05-07',
            'announcement_url': 'https://www.cninfo.com.cn/new/disclosure/detail?announcementId=1',
            'pdf_url': 'https://static.cninfo.com.cn/finalpage/2026-05-07/1.PDF',
            'download_status': 'pending',
            'crawl_time': '2026-06-11 17:00:00',
            'data_source': 'cninfo',
            'notes': 'Real data from CNINFO',
        }

    def test_real_cninfo_record_passes(self):
        self.assertEqual(validate_real_metadata_record(self.real_record()), [])

    def test_sample_record_is_rejected(self):
        record = self.real_record()
        record['data_source'] = 'sample'
        record['notes'] = '示例数据'

        self.assertTrue(validate_real_metadata_record(record))

        output_path = os.path.join(self.temp_dir, 'metadata.csv')
        with self.assertRaises(ValueError):
            save_metadata([record], output_path)

    def test_save_metadata_writes_source_fields(self):
        output_path = os.path.join(self.temp_dir, 'metadata.csv')
        save_metadata([self.real_record()], output_path)

        with open(output_path, 'r', encoding='utf-8') as f:
            row = next(csv.DictReader(f))

        self.assertEqual(row['data_source'], 'cninfo')
        self.assertIn('cninfo.com.cn', row['announcement_url'])

    def test_review_info_does_not_randomly_fill_missing_values(self):
        result = extract_review_info('普通公告，无可转债元数据。', 'doc_missing', 'data/parsed/doc_missing.md')

        self.assertEqual(result['doc_id'], 'doc_missing')
        self.assertIsNone(result['stock_code'])
        self.assertIsNone(result['bond_code'])
        self.assertIsNone(result['publish_date_guess'])
        self.assertEqual(result['review_status'], 'pending')

    def test_read_metadata_csv_supports_gb18030(self):
        output_path = os.path.join(self.temp_dir, 'gb_metadata.csv')
        content = 'doc_id,announcement_url,pdf_url,stock_name,bond_name,notes\n'
        content += 'doc_gbk,https://www.cninfo.com.cn/x,https://static.cninfo.com.cn/y,测试公司,测试转债,Real data from CNINFO\n'
        with open(output_path, 'w', encoding='gb18030') as f:
            f.write(content)

        rows = read_metadata_csv(output_path)

        self.assertEqual(rows[0]['stock_name'], '测试公司')
        self.assertEqual(validate_real_metadata_record(rows[0]), [])


if __name__ == '__main__':
    unittest.main()
