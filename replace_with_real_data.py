import pandas as pd
import os
import shutil

print("=" * 60)
print("替换合成数据为真实数据")
print("=" * 60)

real_df = pd.read_csv('data/metadata/metadata_real.csv')
fake_df = pd.read_csv('data/metadata/metadata_new.csv')

print(f"\n1. 备份原metadata.csv -> metadata_synthetic_backup.csv")
if os.path.exists('data/metadata/metadata.csv'):
    shutil.copy('data/metadata/metadata.csv', 'data/metadata/metadata_synthetic_backup.csv')
    print("   备份完成")

print(f"\n2. 将metadata_real.csv复制为metadata.csv")
shutil.copy('data/metadata/metadata_real.csv', 'data/metadata/metadata.csv')
print("   复制完成")

print(f"\n3. 移动合成数据文件到backups")
os.makedirs('data/metadata/backups', exist_ok=True)
shutil.move('data/metadata/metadata_new.csv', 'data/metadata/backups/metadata_new_backup.csv')
shutil.move('data/metadata/metadata_backup.csv', 'data/metadata/backups/metadata_backup_backup.csv')
print("   移动完成")

print("\n" + "=" * 60)
print("更新后的数据统计")
print("=" * 60)

updated_df = pd.read_csv('data/metadata/metadata.csv')
print(f"\n主数据文件: data/metadata/metadata.csv")
print(f"总记录数: {len(updated_df)}")

print(f"\n公告类型分布:")
for ann_type, count in updated_df['ann_type'].value_counts().items():
    print(f"  {ann_type}: {count}")

print(f"\n不同公司数: {updated_df['stock_name'].nunique() if 'stock_name' in updated_df.columns else 'N/A'}")

print("\n✅ 替换完成！")
