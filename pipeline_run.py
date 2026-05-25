#!/usr/bin/env python3
import argparse
import yaml
import json
import time
from datetime import datetime
from src.crawl import load_config, search_announcements, download_pdfs, check_dataset
from src.parse import batch_parse_pdfs, check_parse_quality
from src.section import route_sections
from src.extract import extract_fields, validate_results
from src.process import standardize_data, match_events
from src.indicator import calculate_indicators
from src.eval import generate_eval_template
from src.utils.logger_config import setup_logger, log_step_start, log_step_complete, log_step_error, log_data_quality

logger = setup_logger()

def run_crawl(config, args):
    start_time = time.time()
    log_step_start("crawl", limit=args.limit)
    
    try:
        records = search_announcements(config, limit=args.limit)
        from src.crawl.search_announcements import save_metadata
        save_metadata(records, config['output']['metadata'])
        duration = time.time() - start_time
        log_step_complete("crawl", duration=duration, records_found=len(records))
        log_data_quality("crawl", len(records), len(records), 0)
        
        log_step_start("download", limit=args.limit)
        download_pdfs(config, limit=args.limit)
        log_step_complete("download", duration=time.time() - start_time)
        
        log_step_start("check_dataset")
        check_dataset(config)
        log_step_complete("check_dataset", duration=time.time() - start_time)
        
    except Exception as e:
        log_step_error("crawl", e)
        raise

def run_parse(config, args):
    start_time = time.time()
    log_step_start("parse", limit=args.limit)
    
    try:
        batch_parse_pdfs(config, limit=args.limit)
        duration = time.time() - start_time
        log_step_complete("parse", duration=duration)
        
        log_step_start("parse_check")
        check_parse_quality(config)
        log_step_complete("parse_check", duration=time.time() - start_time)
        
    except Exception as e:
        log_step_error("parse", e)
        raise

def run_section(config, args):
    start_time = time.time()
    log_step_start("section_routing")
    
    try:
        route_sections(config)
        duration = time.time() - start_time
        log_step_complete("section_routing", duration=duration)
    except Exception as e:
        log_step_error("section_routing", e)
        raise

def run_extract(config, args):
    start_time = time.time()
    log_step_start("extract", limit=args.limit)
    
    try:
        extract_fields(config, limit=args.limit)
        duration = time.time() - start_time
        log_step_complete("extract", duration=duration)
        
        log_step_start("validate")
        result = validate_results()
        log_step_complete("validate", duration=time.time() - start_time, **result)
        log_data_quality("validate", result['total'], result['valid'], result['errors'])
        
    except Exception as e:
        log_step_error("extract", e)
        raise

def run_process(config, args):
    start_time = time.time()
    log_step_start("standardize")
    
    try:
        standardize_data()
        duration = time.time() - start_time
        log_step_complete("standardize", duration=duration)
        
        log_step_start("match_events")
        match_events()
        log_step_complete("match_events", duration=time.time() - start_time)
        
    except Exception as e:
        log_step_error("process", e)
        raise

def run_indicator(config, args):
    start_time = time.time()
    log_step_start("calculate_indicators")
    
    try:
        calculate_indicators()
        duration = time.time() - start_time
        log_step_complete("calculate_indicators", duration=duration)
    except Exception as e:
        log_step_error("indicator", e)
        raise

def run_eval(config, args):
    start_time = time.time()
    log_step_start("generate_eval")
    
    try:
        generate_eval_template()
        duration = time.time() - start_time
        log_step_complete("generate_eval", duration=duration)
    except Exception as e:
        log_step_error("eval", e)
        raise

def run_all(config, args):
    total_start = time.time()
    
    run_crawl(config, args)
    run_parse(config, args)
    run_section(config, args)
    run_extract(config, args)
    run_process(config, args)
    run_indicator(config, args)
    run_eval(config, args)
    
    total_duration = time.time() - total_start
    log_step_complete("all", duration=total_duration, message="End-to-end workflow finished")

def main():
    parser = argparse.ArgumentParser(description='Convertible Bond Event Analysis Pipeline')
    parser.add_argument('--config', type=str, default='configs/crawl.yaml', help='Config file path')
    parser.add_argument('--step', type=str, required=True, 
                        choices=['crawl', 'parse', 'section', 'extract', 'process', 'indicator', 'eval', 'all'],
                        help='Step to run')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of records')
    parser.add_argument('--log-level', type=str, default='INFO', 
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Logging level')
    
    args = parser.parse_args()
    config = load_config(args.config)
    
    logger.info("=" * 60)
    logger.info(f"可转债事件分析工作流启动")
    logger.info(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"执行步骤: {args.step}")
    logger.info(f"记录限制: {args.limit if args.limit else '全部'}")
    logger.info("=" * 60)
    
    try:
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
        
        logger.info("=" * 60)
        logger.info("工作流执行完成")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.exception(f"工作流执行失败: {str(e)}")
        raise

if __name__ == '__main__':
    main()
