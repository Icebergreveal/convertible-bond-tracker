import csv
import os
from typing import Any, Dict, List, Optional


DEFAULT_BOND_LIST_PATH = os.path.join("data", "bonds", "bond_list.csv")
BOND_FIELDNAMES = ["bond_code", "bond_name", "stock_code", "stock_name", "issue_date"]


def _parse_issue_year(issue_date: str) -> Optional[int]:
    if not issue_date:
        return None
    try:
        return int(issue_date[:4])
    except ValueError:
        return None


def fetch_convertible_bonds(
    start_year: int = 2015,
    end_year: int = 2025,
    bond_list_path: str = DEFAULT_BOND_LIST_PATH,
) -> List[Dict[str, Any]]:
    """Load convertible bond reference data from the checked real-data list."""
    if not os.path.exists(bond_list_path):
        raise FileNotFoundError(
            f"Bond list not found: {bond_list_path}. Run the real CNINFO crawl pipeline first."
        )

    bonds: List[Dict[str, Any]] = []
    with open(bond_list_path, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            bond = {field: (row.get(field) or "").strip() for field in BOND_FIELDNAMES}
            issue_year = _parse_issue_year(bond["issue_date"])
            if issue_year is not None and not (start_year <= issue_year <= end_year):
                continue
            bonds.append(bond)

    return bonds


def save_bond_data(bonds: List[Dict[str, Any]], output_path: str = DEFAULT_BOND_LIST_PATH):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=BOND_FIELDNAMES)
        writer.writeheader()
        writer.writerows(bonds)

    print(f"Saved {len(bonds)} convertible bonds to {output_path}")


if __name__ == "__main__":
    print("Loading convertible bond reference data from data/bonds/bond_list.csv...")
    loaded_bonds = fetch_convertible_bonds(2015, 2025)
    print(f"Loaded {len(loaded_bonds)} convertible bonds")
    save_bond_data(loaded_bonds)
