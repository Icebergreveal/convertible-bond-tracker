import os
import yaml
from dotenv import load_dotenv
from typing import Dict, Any
import argparse

def load_config(config_path: str = "configs/crawl.yaml") -> Dict[str, Any]:
    load_dotenv()
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    config['env'] = {
        'LLM_API_KEY': os.getenv('LLM_API_KEY'),
        'MINERU_API_KEY': os.getenv('MINERU_API_KEY'),
        'LLM_BASE_URL': os.getenv('LLM_BASE_URL'),
        'LLM_MODEL': os.getenv('LLM_MODEL', 'Qwen/Qwen3-8B')
    }
    
    return config

def parse_args():
    parser = argparse.ArgumentParser(description='Crawl CNINFO convertible bond announcements')
    parser.add_argument('--config', type=str, default='configs/crawl.yaml', help='Config file path')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of records')
    parser.add_argument('--keyword', type=str, default=None, help='Filter by keyword')
    parser.add_argument('--market', type=str, default=None, help='Filter by market (sz/sh)')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    config = load_config(args.config)
    print(f"Loaded config from {args.config}")
    print(f"Project: {config['project_name']}")
    print(f"Max records: {config['max_records']}")
    print(f"Date range: {config['date_range']['start']} to {config['date_range']['end']}")