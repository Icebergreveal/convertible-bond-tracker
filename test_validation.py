import json
from src.extract.validate_results import validate_record

test_records = [
    {
        "doc_id": "test001",
        "stock_code": "002726",
        "stock_name": "龙大美食",
        "bond_code": "128130",
        "bond_name": "龙大转债",
        "ann_type": "董事会提议向下修正转股价格公告",
        "publish_date": "2026-05-07",
        "original_conv_price": 12.34,
        "new_conv_price": 9.87,
        "effective_date": "2026-05-10",
        "evidence_page": 2,
        "evidence_text": "董事会提议向下修正转股价格"
    },
    {
        "doc_id": "test002",
        "stock_code": "",
        "stock_name": "美锦能源",
        "bond_code": "127061",
        "ann_type": "关于提前赎回可转债的提示性公告",
        "publish_date": "2026-04-15",
        "redemption_price": 103.50,
        "record_date": "2026-04-25"
    },
    {
        "doc_id": "test003",
        "stock_code": "002507",
        "stock_name": "涪陵榨菜",
        "ann_type": "关于可转债转股价格调整的公告",
        "publish_date": "2026/03/20",
        "original_conv_price": "15.60",
        "new_conv_price": "12.48"
    },
    {
        "doc_id": "test004",
        "stock_code": "603288",
        "stock_name": "海天味业",
        "ann_type": "可转债赎回结果暨摘牌公告",
        "publish_date": "2026-02-28",
        "redemption_price": 102.80,
        "delisting_date": "2026-03-02"
    }
]

print("=== Pydantic校验测试 ===")
for i, record in enumerate(test_records, 1):
    print("\n--- 测试记录 %d ---" % i)
    print("ann_type: %s" % record['ann_type'])
    result = validate_record(record)
    
    if result['valid']:
        print("[PASS] 通过校验")
        if result['warnings']:
            print("[WARN] 警告:")
            for warn in result['warnings']:
                print("  - %s" % warn)
    else:
        print("[FAIL] 校验失败")
        print("错误详情:")
        for err in result['errors']:
            print("  - %s" % err)
    
    parsed_str = json.dumps(result.get('parsed', {}), ensure_ascii=False)[:100]
    print("解析后数据: %s..." % parsed_str)

print("\n=== 测试完成 ===")
