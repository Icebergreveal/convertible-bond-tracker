#!/usr/bin/env python3
# 检查metadata和PDF数量差异

import os
import pandas as pd
import sys

sys.stdout.reconfigure(encoding='utf-8')

print('=' * 70)
print('Metadata与PDF数量差异分析')
print('=' * 70)

# 1. 检查metadata.csv
metadata_path = 'data/metadata/metadata.csv'
if os.path.exists(metadata_path):
    df = pd.read_csv(metadata_path, encoding='utf-8')
    print(f'\n1. metadata.csv 统计')
    print(f'   总记录数: {len(df)}')

    # 检查download_status分布
    print(f'\n   下载状态分布:')
    status_counts = df['download_status'].value_counts()
    for status, count in status_counts.items():
        print(f'   - {status}: {count}')

    # 检查pending数量
    pending_count = len(df[df['download_status'] == 'pending'])
    downloaded_count = len(df[df['download_status'] == 'downloaded'])

    print(f'\n   待下载: {pending_count}')
    print(f'   已下载: {downloaded_count}')

# 2. 检查PDF数量
pdf_dir = 'data/pdf'
if os.path.exists(pdf_dir):
    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
    print(f'\n2. PDF文件统计')
    print(f'   PDF文件数: {len(pdf_files)}')

# 3. 检查parsed数量
parsed_dir = 'data/parsed'
if os.path.exists(parsed_dir):
    md_files = [f for f in os.listdir(parsed_dir) if f.endswith('.md')]
    print(f'\n3. Markdown文件统计')
    print(f'   Markdown文件数: {len(md_files)}')

# 4. 分析差异原因
print('\n' + '=' * 70)
print('差异分析')
print('=' * 70)

if os.path.exists(metadata_path):
    print(f'''
差异原因:

1. 下载状态分布:
   - pending (待下载): {pending_count}条
   - downloaded (已下载): {downloaded_count}条

2. 实际PDF数量: {len(pdf_files)}个

3. 差异说明:
   - metadata.csv 记录总数: {len(df)}条
   - 实际下载的PDF: {len(pdf_files)}个
   - 差异: {len(df) - len(pdf_files)}条

4. 可能原因:
   - ① 部分公告还未下载（pending状态）
   - ② 下载失败或被跳过
   - ③ PDF已删除或移动

5. 解决方案:
   - 运行下载: python pipeline_run.py --step download --limit {pending_count}
''')