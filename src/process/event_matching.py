import csv
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Set
from src.crawl.real_data_guard import read_metadata_csv

EVENT_STAGE_ORDER = {
    "adjustment": ["trigger", "proposal", "resolution", "implementation"],
    "redemption": ["trigger", "resolution", "implementation", "result"],
}

CSV_FIELDNAMES = [
    "bond_code",
    "bond_name",
    "stock_code",
    "stock_name",
    "event_type",
    "complete",
    "nodes",
    "missing_nodes",
    "trigger_date",
    "proposal_date",
    "resolution_date",
    "implementation_date",
    "result_date",
    "total_days",
    "cycle_status",
    "original_conv_price",
    "new_conv_price",
    "adjustment_ratio",
    "redemption_price",
    "premium_rate",
    "avg_price_1d",
    "notes",
    "events",
]


def is_empty(value) -> bool:
    return value is None or str(value).strip().lower() in {"", "nan", "none", "null"}


def first_value(*values):
    for value in values:
        if not is_empty(value):
            return value
    return None


def parse_date(value: Optional[str]) -> Optional[datetime]:
    if is_empty(value):
        return None

    text = str(value).strip().replace("/", "-")
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text[:19], fmt)
        except ValueError:
            continue
    return None


def format_date(value: Optional[str]) -> Optional[str]:
    parsed = parse_date(value)
    return parsed.strftime("%Y-%m-%d") if parsed else value


def load_json_records(path: str) -> List[Dict]:
    if not os.path.exists(path):
        print(f"[EventMatch] warning: extract file not found: {path}")
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else []


def load_metadata_map(path: str) -> Dict[str, Dict]:
    if not os.path.exists(path):
        print(f"[EventMatch] warning: metadata file not found: {path}")
        return {}

    return {row.get("doc_id"): row for row in read_metadata_csv(path) if row.get("doc_id")}


def stage_to_node(stage: Optional[str]) -> Optional[str]:
    stage_map = {
        "stage_1_trigger": "trigger",
        "stage_2_proposal": "proposal",
        "stage_2_resolution": "resolution",
        "stage_3_resolution": "resolution",
        "stage_3_implementation": "implementation",
        "stage_4_implementation": "implementation",
        "stage_4_result": "result",
    }
    return stage_map.get(stage or "")


def detect_event_types(record: Dict) -> Set[str]:
    ann_type = str(record.get("ann_type") or "")
    text = " ".join(str(record.get(k) or "") for k in ("ann_type", "title", "evidence_text"))
    event_types: Set[str] = set()

    if any(keyword in text for keyword in ("下修", "向下修正", "转股价格调整")):
        event_types.add("adjustment")
    if any(keyword in text for keyword in ("强赎", "赎回", "摘牌")):
        event_types.add("redemption")
    if any(not is_empty(record.get(k)) for k in ("trigger_rule", "original_conv_price", "new_conv_price")):
        event_types.add("adjustment")
    if any(not is_empty(record.get(k)) for k in ("redemption_trigger", "redemption_price", "delisting_date")):
        event_types.add("redemption")
    if ann_type == "下修类公告":
        event_types.add("adjustment")
    if ann_type == "强赎类公告":
        event_types.add("redemption")

    return event_types


def infer_nodes(record: Dict, event_type: str) -> Set[str]:
    nodes: Set[str] = set()
    stage_node = stage_to_node(record.get("event_stage"))
    if stage_node:
        nodes.add(stage_node)

    text = " ".join(str(record.get(k) or "") for k in ("ann_type", "title", "evidence_text"))
    if event_type == "adjustment":
        nodes.update(infer_adjustment_nodes(record, text))
    elif event_type == "redemption":
        nodes.update(infer_redemption_nodes(record, text))
    return nodes


def infer_adjustment_nodes(record: Dict, text: str) -> Set[str]:
    nodes: Set[str] = set()
    if "触发" in text or not is_empty(record.get("trigger_rule")):
        nodes.add("trigger")
    if "提议" in text or "董事会" in text:
        nodes.add("proposal")
    if any(keyword in text for keyword in ("决议", "股东大会", "审议通过")):
        nodes.add("resolution")
    if any(keyword in text for keyword in ("实施", "生效")) or not is_empty(record.get("effective_date")):
        nodes.add("implementation")
    return nodes


def infer_redemption_nodes(record: Dict, text: str) -> Set[str]:
    nodes: Set[str] = set()
    if "触发" in text or "满足" in text or not is_empty(record.get("redemption_trigger")):
        nodes.add("trigger")
    if any(keyword in text for keyword in ("决议", "行使")):
        nodes.add("resolution")
    if any(keyword in text for keyword in ("实施", "登记", "最后转股")):
        nodes.add("implementation")
    if not is_empty(record.get("record_date")) or not is_empty(record.get("last_convert_date")):
        nodes.add("implementation")
    if any(keyword in text for keyword in ("结果", "摘牌")) or not is_empty(record.get("delisting_date")):
        nodes.add("result")
    return nodes


def merge_record(record: Dict, metadata: Dict) -> Dict:
    merged = dict(record)
    for key, value in metadata.items():
        if is_empty(merged.get(key)):
            merged[key] = value
    if "title" not in merged:
        merged["title"] = metadata.get("title") or metadata.get("ann_title")
    return merged


def node_date(record: Dict, node: str) -> Optional[str]:
    field_map = {
        "trigger": ["publish_date"],
        "proposal": ["publish_date"],
        "resolution": ["publish_date", "pricing_base_date"],
        "implementation": ["effective_date", "record_date", "last_convert_date", "publish_date"],
        "result": ["delisting_date", "publish_date"],
    }
    for field in field_map.get(node, []):
        value = format_date(record.get(field))
        if not is_empty(value):
            return value
    return None


def build_empty_chain(record: Dict, event_type: str) -> Dict:
    return {
        "bond_code": record.get("bond_code"),
        "bond_name": record.get("bond_name"),
        "stock_code": record.get("stock_code"),
        "stock_name": record.get("stock_name"),
        "event_type": event_type,
        "complete": False,
        "nodes": [],
        "missing_nodes": [],
        "trigger_date": None,
        "proposal_date": None,
        "resolution_date": None,
        "implementation_date": None,
        "result_date": None,
        "total_days": 0,
        "cycle_status": "NORMAL",
        "original_conv_price": None,
        "new_conv_price": None,
        "adjustment_ratio": None,
        "redemption_price": None,
        "premium_rate": None,
        "avg_price_1d": None,
        "notes": "",
        "events": [],
    }


def update_chain(chain: Dict, record: Dict, nodes: Set[str]) -> None:
    chain["events"].append(compact_event(record, nodes))
    chain["nodes"] = sorted(set(chain["nodes"]).union(nodes), key=node_sort_key)

    for node in nodes:
        date_key = f"{node}_date"
        date_value = node_date(record, node)
        if date_key in chain and is_empty(chain.get(date_key)):
            chain[date_key] = date_value

    for field in (
        "original_conv_price",
        "new_conv_price",
        "adjustment_ratio",
        "redemption_price",
        "premium_rate",
        "avg_price_1d",
    ):
        if is_empty(chain.get(field)) and not is_empty(record.get(field)):
            chain[field] = record.get(field)

    for field in ("bond_name", "stock_code", "stock_name"):
        if is_empty(chain.get(field)) and not is_empty(record.get(field)):
            chain[field] = record.get(field)


def compact_event(record: Dict, nodes: Set[str]) -> Dict:
    return {
        "doc_id": record.get("doc_id"),
        "ann_type": record.get("ann_type"),
        "event_stage": record.get("event_stage"),
        "publish_date": format_date(record.get("publish_date")),
        "nodes": sorted(nodes, key=node_sort_key),
    }


def node_sort_key(node: str) -> int:
    order = ["trigger", "proposal", "resolution", "implementation", "result"]
    return order.index(node) if node in order else len(order)


def finalize_chain(chain: Dict) -> Dict:
    expected = EVENT_STAGE_ORDER[chain["event_type"]]
    nodes = chain["nodes"]
    chain["missing_nodes"] = [node for node in expected if node not in nodes]
    chain["complete"] = len(chain["missing_nodes"]) == 0
    chain["total_days"] = calculate_total_days(chain)
    chain["cycle_status"] = cycle_status(chain["event_type"], chain["total_days"])
    return chain


def calculate_total_days(chain: Dict) -> int:
    dates = [
        parse_date(chain.get(field))
        for field in ("trigger_date", "proposal_date", "resolution_date", "implementation_date", "result_date")
    ]
    dates = [date for date in dates if date]
    if len(dates) < 2:
        return 0
    return (max(dates) - min(dates)).days


def cycle_status(event_type: str, total_days: int) -> str:
    if total_days <= 0:
        return "NORMAL"
    threshold = 90 if event_type == "adjustment" else 60
    return "NORMAL" if total_days <= threshold else "LONG"


class BondEventMatcher:
    def load_records(self, metadata_path: str, extract_path: str) -> List[Dict]:
        extracted = load_json_records(extract_path)
        metadata_map = load_metadata_map(metadata_path)

        if extracted:
            return [merge_record(record, metadata_map.get(record.get("doc_id"), {})) for record in extracted]

        print("[EventMatch] warning: using metadata only because extract data is empty")
        return list(metadata_map.values())

    def build_event_chains(self, records: List[Dict]) -> List[Dict]:
        chain_map: Dict[tuple, Dict] = {}

        for record in records:
            bond_code = record.get("bond_code")
            if is_empty(bond_code):
                continue

            for event_type in detect_event_types(record):
                key = (bond_code, event_type)
                if key not in chain_map:
                    chain_map[key] = build_empty_chain(record, event_type)
                update_chain(chain_map[key], record, infer_nodes(record, event_type))

        chains = [finalize_chain(chain) for chain in chain_map.values()]
        return sorted(chains, key=lambda row: (row.get("bond_code") or "", row.get("event_type") or ""))

    def save_chains(self, chains: List[Dict], output_path: str) -> None:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES, extrasaction="ignore")
            writer.writeheader()
            for chain in chains:
                writer.writerow(serialize_chain(chain))

        print(f"[EventMatch] event chains saved to: {output_path}")

    def match_events(self, metadata_path: str, extract_path: str, output_path: str) -> List[Dict]:
        print("[EventMatch] start event matching")
        records = self.load_records(metadata_path, extract_path)
        chains = self.build_event_chains(records)
        self.save_chains(chains, output_path)
        self.print_summary(chains)
        return chains

    def print_summary(self, chains: List[Dict]) -> None:
        complete_count = sum(1 for chain in chains if chain["complete"])
        print("[EventMatch] summary:")
        print(f"  total chains: {len(chains)}")
        print(f"  complete chains: {complete_count}")
        print(f"  incomplete chains: {len(chains) - complete_count}")


def serialize_chain(chain: Dict) -> Dict:
    row = dict(chain)
    row["nodes"] = ",".join(chain.get("nodes", []))
    row["missing_nodes"] = ",".join(chain.get("missing_nodes", []))
    row["events"] = json.dumps(chain.get("events", []), ensure_ascii=False)
    return row


def match_events(
    metadata_path: str = "data/metadata/metadata.csv",
    extract_path: str = "outputs/extract_results/structured_data_standardized.json",
    output_path: str = "outputs/event_chain/event_chains.csv",
) -> List[Dict]:
    matcher = BondEventMatcher()
    return matcher.match_events(metadata_path, extract_path, output_path)


if __name__ == "__main__":
    match_events()
