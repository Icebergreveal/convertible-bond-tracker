from src.extract.validate_results import validate_record
import json

with open('outputs/extract_results/structured_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

failed_count = 0
for i, record in enumerate(data[:10]):
    result = validate_record(record)
    if not result['valid']:
        failed_count += 1
        print("记录 %d 失败:" % i)
        print("  doc_id: %s" % record.get("doc_id"))
        print("  errors: %s" % result["errors"])
        print()

print("前10条记录中失败: %d" % failed_count)
