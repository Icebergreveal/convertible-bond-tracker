import argparse
import csv
import os
import re
from datetime import datetime
from typing import Dict, List, Optional

REVIEW_FIELDNAMES = [
    "doc_id",
    "stock_code",
    "stock_name",
    "bond_code",
    "bond_name",
    "ann_type_guess",
    "publish_date_guess",
    "source_md_path",
    "review_status",
    "review_comment",
]


def first_match(patterns: List[str], text: str) -> Optional[str]:
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


def normalize_date(match: Optional[re.Match]) -> Optional[str]:
    if not match:
        return None
    try:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        return datetime(year, month, day).strftime("%Y-%m-%d")
    except ValueError:
        return None


def infer_announcement_type(text: str) -> Optional[str]:
    if "下修" in text or "修正" in text:
        if "触发" in text or "条件" in text:
            return "触发转股价格向下修正条件的提示性公告"
        if "提议" in text or "建议" in text:
            return "董事会提议向下修正转股价格公告"
        if "决议" in text or "审议" in text or "通过" in text:
            return "关于可转债转股价格调整的公告"
        if "实施" in text or "生效" in text or "调整" in text:
            return "可转债转股价格向下修正实施公告"
        return "关于可转债转股价格调整的公告"

    if "赎回" in text or "强赎" in text:
        if "结果" in text or "摘牌" in text or "完成" in text:
            return "可转债赎回结果暨摘牌公告"
        if "实施" in text or "提示" in text or "登记" in text:
            return "可转债提前赎回实施提示公告"
        if "决议" in text or "审议" in text or "通过" in text or "行使" in text:
            return "关于行使可转债提前赎回权的公告"
        if "触发" in text or "条件" in text:
            return "关于提前赎回可转债的提示性公告"
        return "关于提前赎回可转债的提示性公告"

    return None


def extract_review_info(md_content: str, doc_id: str, md_path: str) -> Dict[str, Optional[str]]:
    header = md_content[:3000]
    date_match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", header) or re.search(
        r"(\d{4})-(\d{1,2})-(\d{1,2})", header
    )

    return {
        "doc_id": doc_id,
        "stock_code": first_match([r"股票代码[：:]\s*(\d{6})", r"证券代码[：:]\s*(\d{6})"], header),
        "stock_name": first_match([r"股票简称[：:]\s*([^\s\n,，]+)", r"公司简称[：:]\s*([^\s\n,，]+)"], header),
        "bond_code": first_match([r"转债代码[：:]\s*(\d{6})", r"可转债代码[：:]\s*(\d{6})"], header),
        "bond_name": first_match([r"转债简称[：:]\s*([^\s\n,，]+)", r"可转债简称[：:]\s*([^\s\n,，]+)"], header),
        "ann_type_guess": infer_announcement_type(md_content),
        "publish_date_guess": normalize_date(date_match),
        "source_md_path": md_path,
        "review_status": "pending",
        "review_comment": "Derived from parsed text; not formal metadata until manually verified against CNINFO.",
    }


def build_review_queue(parsed_dir: str) -> List[Dict[str, Optional[str]]]:
    records = []
    for filename in sorted(os.listdir(parsed_dir)):
        if not filename.endswith(".md"):
            continue
        doc_id = filename[:-3]
        md_path = os.path.join(parsed_dir, filename)
        with open(md_path, "r", encoding="utf-8") as f:
            records.append(extract_review_info(f.read(), doc_id, md_path))
    return records


def save_review_queue(records: List[Dict[str, Optional[str]]], output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_FIELDNAMES)
        writer.writeheader()
        writer.writerows(records)
    print(f"Saved review queue with {len(records)} records to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a manual metadata review queue from parsed Markdown. Does not write formal metadata.csv."
    )
    parser.add_argument("--parsed-dir", default="data/parsed", help="Parsed Markdown directory")
    parser.add_argument("--output", default="outputs/review/metadata_review_queue.csv", help="Review queue CSV path")
    args = parser.parse_args()

    if not os.path.isdir(args.parsed_dir):
        raise FileNotFoundError(f"Parsed directory not found: {args.parsed_dir}")

    records = build_review_queue(args.parsed_dir)
    save_review_queue(records, args.output)


if __name__ == "__main__":
    main()
