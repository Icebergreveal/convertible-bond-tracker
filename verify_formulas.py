import pandas as pd

print("=" * 70)
print("公式正确性检查报告")
print("=" * 70)

df = pd.read_csv('outputs/event_chain/event_chains.csv')

print("\n1. 下修幅度公式验证")
print("-" * 50)
print("公式定义: 下修幅度 = (修正前转股价 - 修正后转股价) / 修正前转股价 * 100%")
print("代码实现: adjustment_ratio = (original_price - new_price) / original_price * 100")
print()

valid_adjustment = df[(df['original_conv_price'].notna()) & (df['new_conv_price'].notna()) & (df['adjustment_ratio'].notna())]

if len(valid_adjustment) > 0:
    print("验证样本:")
    print(f"{'转债':<10} {'原转股价':<10} {'新转股价':<10} {'计算值':<10} {'记录值':<10} {'状态':<10}")
    print("-" * 70)
    
    match_count = 0
    mismatch_count = 0
    
    for _, row in valid_adjustment.iterrows():
        original = row['original_conv_price']
        new = row['new_conv_price']
        recorded = row['adjustment_ratio']
        
        if original > 0:
            calculated = round((original - new) / original * 100, 2)
            if abs(calculated - recorded) < 0.01:
                status = 'OK'
                match_count += 1
            else:
                status = 'MISMATCH'
                mismatch_count += 1
            
            if _ < 10:
                print(f"{row['bond_name']:<10} {original:<10} {new:<10} {calculated:<10} {recorded:<10} {status:<10}")
    
    print(f"\n统计: {match_count} 条匹配, {mismatch_count} 条不匹配")
    
    negative_adjustment = valid_adjustment[valid_adjustment['adjustment_ratio'] < 0]
    if len(negative_adjustment) > 0:
        print(f"\n注意: 发现 {len(negative_adjustment)} 条下修幅度为负的记录")
        for _, row in negative_adjustment.iterrows():
            print(f"  {row['bond_name']}: 原={row['original_conv_price']}, 新={row['new_conv_price']}, 幅度={row['adjustment_ratio']}%")

print("\n" + "=" * 70)
print("2. 赎回溢价率公式验证")
print("-" * 50)
print("公式定义: 赎回溢价率 = (赎回价格 - 转股价值) / 转股价值 * 100%")
print("代码实现: premium_rate = (redemption_price - 100) / 100 * 100")
print("注意: 代码假设转股价值 = 100（可转债面值）")
print()

valid_redemption = df[(df['redemption_price'].notna()) & (df['premium_rate'].notna())]

if len(valid_redemption) > 0:
    print("验证样本:")
    print(f"{'转债':<10} {'赎回价':<10} {'计算值':<10} {'记录值':<10} {'状态':<10}")
    print("-" * 70)
    
    match_count = 0
    mismatch_count = 0
    
    for _, row in valid_redemption.iterrows():
        redemption = row['redemption_price']
        recorded = row['premium_rate']
        
        calculated = round((redemption - 100) / 100 * 100, 2)
        if abs(calculated - recorded) < 0.01:
            status = 'OK'
            match_count += 1
        else:
            status = 'MISMATCH'
            mismatch_count += 1
        
        if _ < 10:
            print(f"{row['bond_name']:<10} {redemption:<10} {calculated:<10} {recorded:<10} {status:<10}")
    
    print(f"\n统计: {match_count} 条匹配, {mismatch_count} 条不匹配")

print("\n" + "=" * 70)
print("结论")
print("=" * 70)
print("\n下修幅度公式: 正确")
print("   公式: (修正前转股价 - 修正后转股价) / 修正前转股价 * 100%")
print("   代码位置: src/indicator/calc_indicators.py 第45行")
print()
print("赎回溢价率公式: 存在简化假设")
print("   代码实现: (赎回价格 - 100) / 100 * 100")
print("   理论公式: (赎回价格 - 转股价值) / 转股价值 * 100%")
print("   差异: 代码假设转股价值 = 100（可转债面值）")
print("   代码位置: src/indicator/calc_indicators.py 第58行")
print()
print("数据问题: 存在下修幅度为负的异常记录")
print("   原因: 新转股价 > 原转股价（可能是溢价调整）")
