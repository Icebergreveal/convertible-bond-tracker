import os
import csv
from typing import List, Dict

def calculate_indicators(input_path: str = "outputs/event_chain/event_chains.csv"):
    output_path = "outputs/indicators/quantitative_indicators.csv"
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    records = []
    if os.path.exists(input_path):
        with open(input_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            records = list(reader)
    
    if not records:
        print("No records to process")
        return []
    
    results = []
    
    for record in records:
        result = record.copy()
        
        original_price = None
        new_price = None
        redemption_price = None
        
        try:
            original_price = float(record.get('original_conv_price')) if record.get('original_conv_price') else None
        except (ValueError, TypeError):
            original_price = None
        
        try:
            new_price = float(record.get('new_conv_price')) if record.get('new_conv_price') else None
        except (ValueError, TypeError):
            new_price = None
        
        try:
            redemption_price = float(record.get('redemption_price')) if record.get('redemption_price') else None
        except (ValueError, TypeError):
            redemption_price = None
        
        if original_price is not None and original_price > 0 and new_price is not None:
            adjustment_ratio = round((original_price - new_price) / original_price * 100, 2)
            result['adjustment_ratio_calc'] = adjustment_ratio
            
            existing_ratio = float(record.get('adjustment_ratio')) if record.get('adjustment_ratio') else None
            if existing_ratio is not None:
                result['adjustment_ratio_check'] = 'OK' if abs(adjustment_ratio - existing_ratio) < 0.01 else 'MISMATCH'
            else:
                result['adjustment_ratio_check'] = 'NO_EXISTING'
        else:
            result['adjustment_ratio_calc'] = ''
            result['adjustment_ratio_check'] = ''
        
        if redemption_price is not None and redemption_price > 0:
            try:
                avg_price_1d = float(record.get('avg_price_1d')) if record.get('avg_price_1d') else None
                conv_price = float(record.get('new_conv_price')) if record.get('new_conv_price') else None
                
                if avg_price_1d is not None and avg_price_1d > 0 and conv_price is not None and conv_price > 0:
                    conversion_value = round(avg_price_1d / conv_price * 100, 2)
                    premium_rate = round((redemption_price - conversion_value) / conversion_value * 100, 2)
                    result['premium_rate_calc'] = premium_rate
                    result['conversion_value'] = conversion_value
                    result['calc_method'] = '精确计算(使用avg_price_1d)'
                else:
                    premium_rate = round((redemption_price - 100) / 100 * 100, 2)
                    result['premium_rate_calc'] = premium_rate
                    result['conversion_value'] = 100
                    result['calc_method'] = '简化计算(假设转股价值=100)'
            except (ValueError, TypeError):
                premium_rate = round((redemption_price - 100) / 100 * 100, 2)
                result['premium_rate_calc'] = premium_rate
                result['conversion_value'] = 100
                result['calc_method'] = '简化计算(假设转股价值=100)'
            
            existing_premium = float(record.get('premium_rate')) if record.get('premium_rate') else None
            if existing_premium is not None:
                result['premium_rate_check'] = 'OK' if abs(premium_rate - existing_premium) < 0.01 else 'MISMATCH'
            else:
                result['premium_rate_check'] = 'NO_EXISTING'
        else:
            result['premium_rate_calc'] = ''
            result['conversion_value'] = ''
            result['calc_method'] = ''
            result['premium_rate_check'] = ''
        
        try:
            total_days = int(record.get('total_days')) if record.get('total_days') else None
        except (ValueError, TypeError):
            total_days = None
        
        if total_days is not None and total_days > 0:
            if record.get('event_type') == 'adjustment':
                result['cycle_check'] = 'NORMAL' if total_days <= 90 else 'LONG'
            else:
                result['cycle_check'] = 'NORMAL' if total_days <= 60 else 'LONG'
        else:
            result['cycle_check'] = ''
        
        results.append(result)
    
    fieldnames = list(results[0].keys()) if results else []
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"Quantitative indicators saved to: {output_path}")
    print(f"Processed {len(results)} records")
    return results

if __name__ == '__main__':
    print("Calculating indicators...")
    calculate_indicators()