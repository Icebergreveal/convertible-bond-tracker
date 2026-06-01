import pandas as pd
import re
from collections import Counter

df = pd.read_csv('data/metadata/metadata_new.csv')

bond_codes = df['bond_code'].dropna().unique()
bond_names = df['bond_name'].dropna().unique()

print("=== 合成数据中的转债列表 ===\n")
print(f"转债代码 ({len(bond_codes)} 个):")
for code in sorted(bond_codes):
    print(f"  {code}")

print(f"\n转债名称 ({len(bond_names)} 个):")
for name in sorted(set(bond_names)):
    print(f"  {name}")

fake_bonds = []
for _, row in df[['bond_code', 'bond_name', 'stock_name']].drop_duplicates().iterrows():
    fake_bonds.append({
        'stock_code': row.get('stock_code', ''),
        'stock_name': row['stock_name'],
        'bond_code': row['bond_code'],
        'bond_name': row['bond_name']
    })

print("\n=== 可用于搜索的转债公司 ===")
unique_companies = df[['stock_code', 'stock_name', 'bond_code', 'bond_name']].drop_duplicates()
print(unique_companies.to_string())
