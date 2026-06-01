import pandas as pd
import os

print("=" * 70)
print("检验数据真实性")
print("=" * 70)

metadata_path = 'data/metadata/metadata.csv'

if not os.path.exists(metadata_path):
    print("metadata.csv 不存在!")
else:
    df = pd.read_csv(metadata_path)
    
    print(f"\n文件: data/metadata/metadata.csv")
    print(f"总记录数: {len(df)}")
    
    synthetic_markers = ['示例数据', 'Synthetic', 'fake', '合成', '示例']
    found_synthetic = []
    
    for col in df.columns:
        if df[col].dtype == 'object':
            for marker in synthetic_markers:
                mask = df[col].astype(str).str.contains(marker, na=False)
                if mask.any():
                    count = mask.sum()
                    found_synthetic.append(f"  - 列 '{col}' 中有 {count} 条包含 '{marker}'")
    
    if found_synthetic:
        print("\n检测到合成数据标记:")
        for item in found_synthetic:
            print(item)
        print("\n结论: 存在合成数据")
    else:
        print("\n未检测到任何合成数据标记")
        print("结论: 数据是真实的")
    
    if 'notes' in df.columns:
        notes_with_data = df['notes'].dropna()
        if len(notes_with_data) > 0:
            print("\nnotes列内容样例:")
            for i, note in enumerate(notes_with_data.head(5)):
                print(f"  {i+1}. {note}")
        else:
            print("\nnotes列为空")
    
    print("\n" + "=" * 70)
    print("公告类型分布 (验证数据真实性)")
    print("=" * 70)
    for ann_type, count in df['ann_type'].value_counts().items():
        print(f"  {ann_type}: {count}")

print("\n" + "=" * 70)
print("检验完成")
print("=" * 70)
