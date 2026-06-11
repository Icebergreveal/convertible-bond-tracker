import csv
from typing import Dict, List

CNINFO_HOSTS = ("cninfo.com.cn", "static.cninfo.com.cn")
FORBIDDEN_MARKERS = (
    "sample",
    "synthetic",
    "generated",
    "random",
    "示例",
    "合成",
    "虚构",
    "随机",
    "Generated from parsed files",
)
PLACEHOLDER_VALUES = ("未知公司", "未知转债")


def is_cninfo_url(value: str) -> bool:
    if not value:
        return False
    return any(host in str(value).lower() for host in CNINFO_HOSTS)


def validate_real_metadata_record(record: Dict[str, str]) -> List[str]:
    errors = []
    doc_id = record.get("doc_id", "")

    if not doc_id:
        errors.append("missing doc_id")
    if not record.get("announcement_url") or not is_cninfo_url(record.get("announcement_url", "")):
        errors.append("announcement_url is not a CNINFO URL")
    if record.get("pdf_url") and not is_cninfo_url(record.get("pdf_url", "")):
        errors.append("pdf_url is not a CNINFO URL")

    text = " ".join(str(record.get(field, "")) for field in ("notes", "data_source", "source"))
    if any(marker.lower() in text.lower() for marker in FORBIDDEN_MARKERS):
        errors.append("record contains sample/synthetic marker")

    for field in ("stock_name", "bond_name"):
        if record.get(field) in PLACEHOLDER_VALUES:
            errors.append(f"{field} uses placeholder value")

    return errors


def assert_real_metadata_records(records: List[Dict[str, str]]) -> None:
    failures = []
    for index, record in enumerate(records, 1):
        errors = validate_real_metadata_record(record)
        if errors:
            failures.append(f"row {index} ({record.get('doc_id', '')}): {', '.join(errors)}")

    if failures:
        preview = "\n".join(failures[:10])
        raise ValueError(f"metadata contains non-real or non-CNINFO records:\n{preview}")


def read_metadata_csv(path: str) -> List[Dict[str, str]]:
    last_error = None
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            with open(path, "r", encoding=encoding, newline="") as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError as exc:
            last_error = exc

    raise UnicodeDecodeError(
        last_error.encoding,
        last_error.object,
        last_error.start,
        last_error.end,
        f"failed to read metadata CSV with utf-8-sig, utf-8, or gb18030: {last_error.reason}",
    )
