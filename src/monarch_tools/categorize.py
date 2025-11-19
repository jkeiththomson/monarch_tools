"""Categorize command implementation for monarch_tools.

This version is intentionally simple and text-based. It:

- Reads:
  - data/categories.txt
  - data/groups.txt
  - data/rules.json
  - an <stem>.activity.csv file (from the `activity` command; columns: Date, Description, Amount)
- Walks each row of the activity file.
- For each row, ensures:
  - There is a canonical merchant name for the raw Description.
  - There is a category assigned to that canonical name.
- Writes back updated:
  - categories.txt
  - groups.txt
  - rules.json

The rules.json format is:

{
  "exact": {
    "<canonical_merchant>": {
      "category": "<category_name>"
    }
  },
  "patterns": [
    {
      "pattern": "<regex>",
      "canonical": "<canonical_merchant>"
    }
  ],
  "raw_to_canonical": {
    "<raw_description>": "<canonical_merchant>"
  },
  "rules_version": 1
}

"""

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple


def _load_categories(path: Path) -> List[str]:
    cats: List[str] = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            cats.append(s)
    return cats


def _save_categories(path: Path, categories: List[str]) -> None:
    text = "\n".join(categories) + "\n"
    path.write_text(text, encoding="utf-8")


def _load_groups(path: Path) -> Tuple[List[str], Dict[str, str], Dict[str, List[str]]]:
    """Return (groups_in_order, category_to_group, group_to_categories)."""
    groups: List[str] = []
    category_to_group: Dict[str, str] = {}
    group_to_categories: Dict[str, List[str]] = {}

    if not path.exists():
        return groups, category_to_group, group_to_categories

    current_group: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("*"):
            current_group = line.lstrip("*").strip()
            if current_group not in groups:
                groups.append(current_group)
            group_to_categories.setdefault(current_group, [])
        else:
            cat = line
            if current_group is None:
                # Ungrouped category; create a default group bucket.
                current_group = "Ungrouped"
                if current_group not in groups:
                    groups.append(current_group)
                group_to_categories.setdefault(current_group, [])
            category_to_group[cat] = current_group
            group_to_categories.setdefault(current_group, []).append(cat)

    return groups, category_to_group, group_to_categories


def _save_groups(path: Path, groups: List[str], group_to_categories: Dict[str, List[str]]) -> None:
    lines: List[str] = []
    for grp in groups:
        lines.append(f"*{grp}")
        for cat in group_to_categories.get(grp, []):
            lines.append(cat)
        lines.append("")  # blank line between groups
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _load_rules(path: Path) -> Dict:
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = {}
    # Normalize structure
    data.setdefault("exact", {})
    data.setdefault("patterns", [])
    data.setdefault("raw_to_canonical", {})
    data.setdefault("rules_version", 1)
    return data


def _save_rules(path: Path, rules: Dict) -> None:
    path.write_text(json.dumps(rules, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _pick_canonical(raw_desc: str, existing_canonical: str | None) -> str:
    print()
    print(f"Raw merchant: {raw_desc}")
    if existing_canonical:
        prompt = f"Canonical merchant name [{existing_canonical}]: "
        entered = input(prompt).strip()
        return existing_canonical if entered == "" else entered
    else:
        entered = input("Canonical merchant name (leave blank to use raw): ").strip()
        return raw_desc if entered == "" else entered


def _pick_category(
    canonical: str,
    categories: List[str],
    category_to_group: Dict[str, str],
    groups: List[str],
    group_to_categories: Dict[str, List[str]],
) -> Tuple[str, str]:
    print()
    print(f"Assign category for merchant: {canonical}")
    if categories:
        print("Existing categories:")
        for idx, cat in enumerate(categories, start=1):
            grp = category_to_group.get(cat, "(no group)")
            print(f"  {idx:2d}. {cat} [{grp}]")
    else:
        print("No categories defined yet.")

    while True:
        entered = input("Category name (existing or new): ").strip()
        if entered == "":
            print("Please enter a category name (or Ctrl+C to abort).")
            continue
        category = entered
        break

    if category not in categories:
        categories.append(category)

    grp = category_to_group.get(category)
    if grp:
        return category, grp

    # Need a group.
    print()
    print(f"Choose group for category '{category}':")
    if groups:
        for idx, g in enumerate(groups, start=1):
            print(f"  {idx:2d}. {g}")
    else:
        print("No groups defined yet.")

    entered = input("Group name (existing or new) [Other]: ").strip()
    if entered == "":
        entered = "Other"
    group = entered

    if group not in groups:
        groups.append(group)
    group_to_categories.setdefault(group, [])
    if category not in group_to_categories[group]:
        group_to_categories[group].append(category)
    category_to_group[category] = group

    return category, group


def _iter_activity_rows(activity_csv: Path):
    with activity_csv.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        if "Description" not in headers:
            raise SystemExit(
                f"activity CSV {activity_csv} does not have a 'Description' column; "
                f"headers={headers}"
            )
        for row in reader:
            yield row


def cmd_categorize(ns: argparse.Namespace) -> int:
    categories_path = Path(ns.categories_txt)
    groups_path = Path(ns.groups_txt)
    rules_path = Path(ns.rules_json)
    activity_path = Path(ns.activity_csv)

    categories = _load_categories(categories_path)
    groups, category_to_group, group_to_categories = _load_groups(groups_path)
    rules = _load_rules(rules_path)

    raw_to_canonical: Dict[str, str] = rules.setdefault("raw_to_canonical", {})
    exact: Dict[str, Dict[str, str]] = rules.setdefault("exact", {})
    patterns = rules.setdefault("patterns", [])

    print(f"Loaded {len(categories)} categories, {len(groups)} groups, "
          f"{len(raw_to_canonical)} raw→canonical mappings, {len(exact)} canonical rules.")

    seen_canonical: Dict[str, str] = {}  # canonical -> category

    for row in _iter_activity_rows(activity_path):
        raw_desc = (row.get("Description") or "").strip()
        if not raw_desc:
            continue

        # First, see if we already have a canonical + category fully defined.
        canonical = raw_to_canonical.get(raw_desc)

        # Try patterns only if no explicit mapping.
        if not canonical and patterns:
            for rule in patterns:
                pat = rule.get("pattern")
                if not pat:
                    continue
                try:
                    if re.search(pat, raw_desc, flags=re.IGNORECASE):
                        canonical = rule.get("canonical") or raw_desc
                        break
                except re.error:
                    # Ignore bad patterns
                    continue

        # If still no canonical, interact with the user.
        canonical = _pick_canonical(raw_desc, canonical)

        raw_to_canonical[raw_desc] = canonical

        # If we have already assigned a category for this canonical in this run, reuse it.
        if canonical in seen_canonical:
            continue

        info = exact.get(canonical)
        category = info.get("category") if info else None

        if category is None:
            cat, grp = _pick_category(
                canonical,
                categories,
                category_to_group,
                groups,
                group_to_categories,
            )
            category = cat
            exact[canonical] = {"category": category}
        else:
            # Ensure the category appears in our category/group structures.
            if category not in categories:
                categories.append(category)
            grp = category_to_group.get(category)
            if grp is None:
                # Put into a default group.
                grp = "Other"
                if grp not in groups:
                    groups.append(grp)
                group_to_categories.setdefault(grp, []).append(category)
                category_to_group[category] = grp

        seen_canonical[canonical] = category

    # Persist files.
    _save_categories(categories_path, categories)
    _save_groups(groups_path, groups, group_to_categories)
    _save_rules(rules_path, rules)

    print()
    print("Updated:")
    print(f"  {categories_path}")
    print(f"  {groups_path}")
    print(f"  {rules_path}")
    return 0
