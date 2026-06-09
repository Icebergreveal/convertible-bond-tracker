#!/usr/bin/env python3
import json

# 读取重试结果
with open('outputs/extract_results/retry_chunk_0/structured_data_retry_chunk_0.json', 'r', encoding='utf-8') as f:
    retry_data = json.load(f)

retry_ids = {item['doc_id'] for item in retry_data}
print("retry_chunk_0 记录数:", len(retry_data))

# 未抽取列表中的文件
unextracted_list = [
    '60dd6f5d7a842203',
    '60ec7680640eb727',
    '0652e5fe91444bad'
]

print("\n检查未抽取列表中的文件是否在重试结果中:")
for doc_id in unextracted_list:
    if doc_id in retry_ids:
        print("[OK] ", doc_id, " 在重试结果中")
    else:
        print("[NO] ", doc_id, " 不在重试结果中")

# 检查第一条数据是否是之前未抽取的
first_doc_id = retry_data[0]['doc_id']
print("\n重试结果第一条数据的doc_id:", first_doc_id)
if first_doc_id in unextracted_list:
    print("是否在未抽取列表中: 是")
else:
    print("是否在未抽取列表中: 否")