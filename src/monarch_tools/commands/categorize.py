from __future__ import annotations

import argparse
import csv
from pathlib import Path

from monarch_tools.categorize_engine import (
    categorize_merchant,
    load_categories,
    load_rules,
    normalize_merchant,
)


def _default_out_path(in_csv: Path, suffix: str) -> Path:
    return in_csv.with_name(in_csv.name.replace(".monarch.csv", suffix))


def cmd_categorize(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="monarch-tools categorize")
    p.add_argument("--in", dest="in_csv", required=True, help="Input .monarch.csv")
    p.add_argument("--rules", required=True, help="Path to rules.json")
    p.add_argument("--categories", required=True, help="Path to categories.txt")
    p.add_argument("--out", dest="out_csv", default="", help="Output categorized CSV path (optional)")
    p.add_argument("--unmatched", default="", help="Output unmatched merchants CSV path (optional)")
    args = p.parse_args(argv)

    in_csv = Path(args.in_csv).expanduser()
    rules_path = Path(args.rules).expanduser()
    cats_path = Path(args.categories).expanduser()

    if not in_csv.exists():
        raise SystemExit(f"ERROR: input not found: {in_csv}")
    if not rules_path.exists():
        raise SystemExit(f"ERROR: rules not found: {rules_path}")
    if not cats_path.exists():
        raise SystemExit(f"ERROR: categories not found: {cats_path}")

    out_csv = Path(args.out_csv).expanduser() if args.out_csv else _default_out_path(in_csv, ".monarch.categorized.csv")
    unmatched_csv = Path(args.unmatched).expanduser() if args.unmatched else _default_out_path(in_csv, ".unmatched_merchants.csv")

    categories = load_categories(cats_path)
    rules = load_rules(rules_path)

    unmatched_counts: dict[str, int] = {}

    with in_csv.open("r", newline="", encoding="utf-8") as fin, out_csv.open("w", newline="", encoding="utf-8") as fout:
        r = csv.DictReader(fin)
        if not r.fieldnames:
            raise SystemExit("ERROR: input CSV has no header")

        fieldnames = list(r.fieldnames)
        if "Category" not in fieldnames:
            raise SystemExit("ERROR: input CSV missing 'Category' column")

        w = csv.DictWriter(fout, fieldnames=fieldnames)
        w.writeheader()

        for row in r:
            merchant = row.get("Merchant", "") or ""
            existing = (row.get("Category", "") or "").strip()

            if existing:
                w.writerow(row)
                continue

            cat = categorize_merchant(merchant, rules) or "Uncategorized"
            if cat not in categories:
                cat = "Uncategorized"

            row["Category"] = cat
            w.writerow(row)

            if cat == "Uncategorized":
                key = normalize_merchant(merchant)
                if key:
                    unmatched_counts[key] = unmatched_counts.get(key, 0) + 1

    with unmatched_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Merchant", "Count"])
        for merch, cnt in sorted(unmatched_counts.items(), key=lambda x: (-x[1], x[0])):
            w.writerow([merch, cnt])

    print("wrote:")
    print(f"  categorized: {out_csv}")
    print(f"  unmatched:   {unmatched_csv}")
    return 0
