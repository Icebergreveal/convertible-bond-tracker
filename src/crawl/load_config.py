import os
from typing import Dict, Any
import argparse

try:
    import yaml
except ImportError:
    yaml = None

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        return False


def parse_scalar(value: str):
    value = value.strip().strip('"').strip("'")
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        return int(value)
    except ValueError:
        return value


def load_simple_yaml(config_text: str) -> Dict[str, Any]:
    config: Dict[str, Any] = {}
    current_section = None

    for raw_line in config_text.splitlines():
        line = raw_line.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        stripped = line.strip()

        if indent == 0 and stripped.endswith(":"):
            current_section = stripped[:-1]
            config[current_section] = {}
            continue

        if indent == 0 and ":" in stripped:
            key, value = stripped.split(":", 1)
            config[key.strip()] = parse_scalar(value)
            current_section = None
            continue

        if current_section and ":" in stripped:
            key, value = stripped.split(":", 1)
            config[current_section][key.strip()] = parse_scalar(value)

    return config


def load_config(config_path: str = "configs/crawl.yaml") -> Dict[str, Any]:
    load_dotenv()
    
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()

    config = yaml.safe_load(content) if yaml else load_simple_yaml(content)
    
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
