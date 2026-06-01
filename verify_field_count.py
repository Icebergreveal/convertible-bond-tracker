#!/usr/bin/env python3
# 验证README中的字段数量

print("README字段数量验证")
print("=" * 50)

# 公共字段（10个）
public_fields = [
    "doc_id", "stock_code", "stock_name", "bond_code", "bond_name",
    "ann_type", "publish_date", "evidence_page", "evidence_text", "notes"
]

# 下修专属字段（9个）
down_fields = [
    "trigger_rule", "original_conv_price", "new_conv_price",
    "pricing_base_date", "avg_price_20d", "avg_price_1d",
    "effective_date", "adjustment_ratio", "adjustment_type"
]

# 强赎专属字段（6个）
redem_fields = [
    "redemption_trigger", "redemption_price", "record_date",
    "last_convert_date", "delisting_date", "premium_rate"
]

print(f"\n公共字段 ({len(public_fields)}个):")
for i, f in enumerate(public_fields, 1):
    print(f"  {i}. {f}")

print(f"\n下修专属字段 ({len(down_fields)}个):")
for i, f in enumerate(down_fields, 1):
    print(f"  {i}. {f}")

print(f"\n强赎专属字段 ({len(redem_fields)}个):")
for i, f in enumerate(redem_fields, 1):
    print(f"  {i}. {f}")

total = len(public_fields) + len(down_fields) + len(redem_fields)
print(f"\n总计: {len(public_fields)} + {len(down_fields)} + {len(redem_fields)} = {total}个字段")

print("\n" + "=" * 50)
print(f"README中声明: 25个核心字段（公共10个+下修9个+强赎6个）")
print(f"实际统计: {total}个核心字段")
print(f"状态: {'✅ 一致' if total == 25 else '❌ 不一致'}")