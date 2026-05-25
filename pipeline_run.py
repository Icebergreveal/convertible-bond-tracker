#!/usr/bin/env python3
import argparse
import yaml
import json
from datetime import datetime
from src.crawl import load_config, search_announcements, download_pdfs, check_dataset
from src.parse import batch_parse_pdfs, check_parse_quality
from src.section import route_sections
from src.extract import extract_fields, validate_results
from src.process import standardize_data, match_events
from src.indicator import calculate_indicators
from src.eval import generate_eval_template

def log_step(step_name, status, message=""):
    log_entry = {
        "time": datetime.now().isoformat(),
        "step": step_name,
        "status": status,
        "message": message
    }
    with open("outputs/logs/workflow.log", "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    print(f"[{status}] {step_name}: {message}")

def run_crawl(config, args):
    log_step("crawl", "started")
    records = search_announcements(config, limit=args.limit)
    from src.crawl.search_announcements import save_metadata
    save_metadata(records, config['output']['metadata'])
    log_step("crawl", "completed", f"Found {len(records)} announcements")
    
    log_step("download", "started")
    download_pdfs(config, limit=args.limit)
    log_step("download", "completed")
    
    log_step("check_dataset", "started")
    check_dataset(config)
    log_step("check_dataset", "completed")

def run_parse(config, args):
    log_step("parse", "started")
    batch_parse_pdfs(config, limit=args.limit)
    log_step("parse", "completed")
    
    log_step("parse_check", "started")
    check_parse_quality(config)
    log_step("parse_check", "completed")

def run_section(config, args):
    log_step("section_routing", "started")
    route_sections(config)
    log_step("section_routing", "completed")

def run_extract(config, args):
    log_step("extract", "started")
    extract_fields(config, limit=args.limit)
    log_step("extract", "completed")
    
    log_step("validate", "started")
    validate_results()
    log_step("validate", "completed")

def run_process(config, args):
    log_step("standardize", "started")
    standardize_data()
    log_step("standardize", "completed")
    
    log_step("match_events", "started")
    match_events()
    log_step("match_events", "completed")

def run_indicator(config, args):
    log_step("calculate_indicators", "started")
    calculate_indicators()
    log_step("calculate_indicators", "completed")

def run_eval(config, args):
    log_step("generate_eval", "started")
    generate_eval_template()
    log_step("generate_eval", "completed")

def run_all(config, args):
    run_crawl(config, args)
    run_parse(config, args)
    run_section(config, args)
    run_extract(config, args)
    run_process(config, args)
    run_indicator(config, args)
    run_eval(config, args)
    log_step("all", "completed", "End-to-end workflow finished")

def main():
    parser = argparse.ArgumentParser(description='Convertible Bond Event Analysis Pipeline')
    parser.add_argument('--config', type=str, default='configs/crawl.yaml', help='Config file path')
    parser.add_argument('--step', type=str, required=True, 
                        choices=['crawl', 'parse', 'section', 'extract', 'process', 'indicator', 'eval', 'all'],
                        help='Step to run')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of records')
    
    args = parser.parse_args()
    config = load_config(args.config)
    
    import os
    os.makedirs("outputs/logs", exist_ok=True)
    
    log_step("workflow", "started", f"Running step: {args.step}")
    
    if args.step == 'crawl':
        run_crawl(config, args)
    elif args.step == 'parse':
        run_parse(config, args)
    elif args.step == 'section':
        run_section(config, args)
    elif args.step == 'extract':
        run_extract(config, args)
    elif args.step == 'process':
        run_process(config, args)
    elif args.step == 'indicator':
        run_indicator(config, args)
    elif args.step == 'eval':
        run_eval(config, args)
    elif args.step == 'all':
        run_all(config, args)
    
    log_step("workflow", "finished")

if __name__ == '__main__':
    main()