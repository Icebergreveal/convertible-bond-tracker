#!/usr/bin/env python3
# 重新计算赎回溢价率

import sys
sys.stdout.reconfigure(encoding='utf-8')

from src.indicator.calc_indicators import calculate_indicators

print('=' * 70)
print('重新计算赎回溢价率')
print('=' * 70)

results = calculate_indicators()
print(f'\n处理了 {len(results)} 条记录')

# 统计赎回溢价率计算情况
has_premium = [r for r in results if r.get('premium_rate_calc')]
print(f'有赎回溢价率计算的记录: {len(has_premium)}')

if has_premium:
    print('\n样本数据:')
    for r in has_premium[:5]:
        print(f"  - {r.get('bond_name')} ({r.get('bond_code')})")
        print(f"    redemption_price: {r.get('redemption_price')}")
        print(f"    premium_rate_calc: {r.get('premium_rate_calc')}")
        print(f"    calc_method: {r.get('calc_method')}")
        print()
else:
    print('\n没有赎回溢价率数据')
    print('检查事件链数据...')

    import csv
    with open('outputs/event_chain/event_chains.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        records = list(reader)

    print(f'事件链总记录: {len(records)}')

    redemption_records = [r for r in records if r.get('redemption_price')]
    print(f'有redemption_price的记录: {len(redemption_records)}')

    if redemption_records:
        print('\n事件链中的赎回数据样本:')
        for r in redemption_records[:3]:
            print(f"  - {r.get('bond_name')} ({r.get('bond_code')})")
            print(f"    redemption_price: {r.get('redemption_price')}")
            print(f"    event_type: {r.get('event_type')}")
            print()

print('\n' + '=' * 70)
print('结论')
print('=' * 70)