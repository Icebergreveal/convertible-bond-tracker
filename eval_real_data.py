import pandas as pd
from datetime import datetime
import os

print("=" * 70)
print("可转债事件分析 - 真实数据质量评估报告")
print("=" * 70)
print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

metadata_df = pd.read_csv('data/metadata/metadata.csv')

existing_pdfs = [f for f in os.listdir('data/pdf') if f.endswith('.pdf')]
pdf_count = len(existing_pdfs)

print("=" * 70)
print("1. 数据规模统计")
print("=" * 70)
print(f"元数据记录总数: {len(metadata_df)}")
print(f"已下载PDF文件数: {pdf_count}")
print(f"未下载记录数: {len(metadata_df) - pdf_count}")

print("\n" + "=" * 70)
print("2. 公告类型分布 (真实数据)")
print("=" * 70)
ann_type_counts = metadata_df['ann_type'].value_counts()
for ann_type, count in ann_type_counts.items():
    pct = count / len(metadata_df) * 100
    print(f"  {ann_type}: {count} ({pct:.1f}%)")

print("\n" + "=" * 70)
print("3. 公司覆盖情况")
print("=" * 70)
unique_stocks = metadata_df['stock_name'].nunique()
print(f"涉及不同公司数: {unique_stocks}")

top_companies = metadata_df['stock_name'].value_counts().head(10)
print("\n公告数量前10的公司:")
for company, count in top_companies.items():
    print(f"  {company}: {count}")

print("\n" + "=" * 70)
print("4. 数据类型覆盖")
print("=" * 70)

required_types = [
    '下修触发提示',
    '下修提议',
    '下修决议',
    '下修实施',
    '强赎触发提示',
    '强赎决议',
    '强赎实施',
    '强赎结果'
]

covered_types = [t for t in required_types if t in ann_type_counts.index]
missing_types = [t for t in required_types if t not in ann_type_counts.index]

print("已覆盖的公告类型:")
for t in covered_types:
    print(f"  [OK] {t}")

if missing_types:
    print("\n缺失的公告类型:")
    for t in missing_types:
        print(f"  [!!] {t}")
else:
    print("\n所有8种公告类型都已覆盖!")

print("\n" + "=" * 70)
print("5. 下修事件 vs 强赎事件")
print("=" * 70)

adjustment_count = len(metadata_df[metadata_df['ann_type'].str.contains('下修', na=False)])
redemption_count = len(metadata_df[metadata_df['ann_type'].str.contains('强赎|赎回', na=False)])

print(f"下修类公告: {adjustment_count} ({adjustment_count/len(metadata_df)*100:.1f}%)")
print(f"强赎类公告: {redemption_count} ({redemption_count/len(metadata_df)*100:.1f}%)")

print("\n" + "=" * 70)
print("6. 与合成数据的对比")
print("=" * 70)
print(f"原合成数据量: 600条")
print(f"新真实数据量: {len(metadata_df)}条")
print(f"变化: 替换为100%真实数据")

print("\n" + "=" * 70)
print("7. 结论与建议")
print("=" * 70)

issues = []
if len(metadata_df) < 150:
    issues.append(f"数据量不足: {len(metadata_df)} < 150")
if missing_types:
    issues.append(f"缺失公告类型: {', '.join(missing_types)}")
if pdf_count < len(metadata_df) * 0.8:
    issues.append(f"PDF下载率偏低: {pdf_count}/{len(metadata_df)} ({pdf_count/len(metadata_df)*100:.1f}%)")

if not issues:
    print("\n评估结果: PASS")
    print("\n数据质量满足挑战档要求:")
    print(f"  - 数据量: {len(metadata_df)} >= 150")
    print(f"  - 公告类型覆盖: {len(covered_types)}/8")
    print(f"  - PDF文件数: {pdf_count}")
    print(f"  - 公司覆盖数: {unique_stocks}")
else:
    print("\n评估结果: NEED_IMPROVEMENT")
    print("\n需要改进的问题:")
    for issue in issues:
        print(f"  - {issue}")

print("\n建议:")
if len(metadata_df) < 300:
    print("1. 建议爬取更多数据，目标300+条记录")
if missing_types:
    print(f"2. 建议搜索'{missing_types[0]}'相关关键词以覆盖缺失类型")
if pdf_count < len(metadata_df):
    print("3. 继续下载剩余PDF文件")

print("\n" + "=" * 70)
print("报告结束")
print("=" * 70)
