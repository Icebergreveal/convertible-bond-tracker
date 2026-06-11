import unittest
import os
import sys
import tempfile
import subprocess
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestPipelineCLI(unittest.TestCase):
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_config_path = os.path.join(self.temp_dir, 'test_config.yaml')
        self.create_test_config()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def create_test_config(self):
        config_content = """
project_name: "Test Project"
max_records: 100
date_range:
  start: "2026-01-01"
  end: "2026-12-31"

crawl:
  base_url: "http://www.cninfo.com.cn"
  timeout: 30
  max_retries: 3

output:
  metadata: "{temp_dir}/metadata/metadata.csv"
  pdf: "{temp_dir}/pdf/"
  parsed: "{temp_dir}/parsed/"
  extract_results: "{temp_dir}/extract_results/"
  event_chain: "{temp_dir}/event_chain/"
  indicators: "{temp_dir}/indicators/"
  logs: "{temp_dir}/logs/"
  eval: "{temp_dir}/eval/"

llm:
  model: "gpt-4o-mini"
  temperature: 0.1
  max_tokens: 4096

section_rules:
  - name: "转股价格调整"
    keywords: ["转股价格", "向下修正", "调整"]
  - name: "提前赎回"
    keywords: ["提前赎回", "强赎", "摘牌"]
"""
        os.makedirs(os.path.join(self.temp_dir, 'metadata'), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, 'pdf'), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, 'parsed'), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, 'extract_results'), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, 'event_chain'), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, 'indicators'), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, 'logs'), exist_ok=True)
        os.makedirs(os.path.join(self.temp_dir, 'eval'), exist_ok=True)
        
        config_content = config_content.replace("{temp_dir}", self.temp_dir)
        with open(self.test_config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
    
    def run_pipeline_command(self, step, extra_args=None):
        cmd = [sys.executable, 'pipeline_run.py', '--step', step, '--config', self.test_config_path]
        if extra_args:
            cmd.extend(extra_args)
        
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(__file__) + '/..')
        return result
    
    def test_cli_help(self):
        """测试CLI帮助信息"""
        result = subprocess.run([sys.executable, 'pipeline_run.py', '--help'], 
                              capture_output=True, text=True, 
                              cwd=os.path.dirname(__file__) + '/..')
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('--step', result.stdout)
        self.assertIn('--config', result.stdout)
        self.assertIn('--limit', result.stdout)
    
    def test_cli_missing_step(self):
        """测试CLI缺少step参数"""
        result = subprocess.run([sys.executable, 'pipeline_run.py'], 
                              capture_output=True, text=True, 
                              cwd=os.path.dirname(__file__) + '/..')
        
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('error', result.stderr.lower())
    
    def test_cli_invalid_step(self):
        """测试CLI无效step参数"""
        result = subprocess.run([sys.executable, 'pipeline_run.py', '--step', 'invalid_step'], 
                              capture_output=True, text=True, 
                              cwd=os.path.dirname(__file__) + '/..')
        
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('invalid choice', result.stderr.lower())
    
    def test_cli_config_not_found(self):
        """测试配置文件不存在的情况"""
        result = subprocess.run([sys.executable, 'pipeline_run.py', '--step', 'validate', 
                                '--config', '/nonexistent/path/config.yaml'], 
                              capture_output=True, text=True, 
                              cwd=os.path.dirname(__file__) + '/..')
        
        self.assertNotEqual(result.returncode, 0)
    
    def test_cli_step_list(self):
        """测试所有有效step参数"""
        valid_steps = ['crawl', 'download', 'parse', 'section', 'extract', 
                      'validate', 'process', 'indicator', 'eval', 'all']
        
        for step in valid_steps:
            result = subprocess.run([sys.executable, 'pipeline_run.py', '--step', step, '--help'], 
                                  capture_output=True, text=True, 
                                  cwd=os.path.dirname(__file__) + '/..')
            self.assertNotIn('invalid choice', result.stderr.lower())

if __name__ == '__main__':
    unittest.main()