import pandas as pd
import os

print("=" * 60)
print("真实数据 vs 合成数据分析")
print("=" * 60)

real_df = pd.read_csv('data/metadata/metadata_real.csv')
fake_df = pd.read_csv('data/metadata/metadata_new.csv')

print(f"\n【metadata_real.csv (真实爬取数据)】")
print(f"  总记录数: {len(real_df)}")
print(f"  有PDF的记录: {len(real_df[real_df['download_status'] == 'completed'])}")

if 'ann_type' in real_df.columns:
    print(f"\n  公告类型分布:")
    for ann_type, count in real_df['ann_type'].value_counts().items():
        print(f"    {ann_type}: {count}")

if 'stock_name' in real_df.columns:
    unique_stocks = real_df['stock_name'].nunique()
    print(f"\n  不同公司数: {unique_stocks}")

print(f"\n【metadata_new.csv (合成数据)】")
print(f"  总记录数: {len(fake_df)}")

if 'notes' in fake_df.columns:
    synthetic_count = len(fake_df[fake_df['notes'].str.contains('示例数据|Synthetic', na=False)])
    print(f"  标记为合成的: {synthetic_count}")

if 'ann_type' in fake_df.columns:
    print(f"\n  公告类型分布:")
    for ann_type, count in fake_df['ann_type'].value_counts().items():
        print(f"    {ann_type}: {count}")

print("\n" + "=" * 60)
print("结论")
print("=" * 60)
print(f"\n真实数据: {len(real_df)} 条")
print(f"合成数据: {len(fake_df)} 条")
print(f"\n【推荐操作】:")
print("1. 使用 metadata_real.csv 作为主数据文件")
print("2. 删除 metadata_new.csv 或将其移到 backups/ 目录")
print("3. 只用真实数据计算准确率")
