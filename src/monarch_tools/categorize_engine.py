from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


def normalize_merchant(s: str) -> str:
    return " ".join((s or "").strip().split())


def load_categories(path: Path) -> set[str]:
    cats: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            cats.add(s)
    return cats


@dataclass(frozen=True)
class PatternRule:
    regex: str
    category: str
    _compiled: re.Pattern[str]

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "PatternRule":
        rx = str(d["regex"])
        cat = str(d["category"])
        return PatternRule(regex=rx, category=cat, _compiled=re.compile(rx))


@dataclass
class Rules:
    version: int
    merchants: Dict[str, str]
    patterns: List[PatternRule]


def load_rules(path: Path) -> Rules:
    data = json.loads(path.read_text(encoding="utf-8"))
    version = int(data.get("version", 1))
    merchants = {
        normalize_merchant(k): str(v)
        for k, v in (data.get("merchants", {}) or {}).items()
    }
    patterns = [PatternRule.from_dict(x) for x in (data.get("patterns", []) or [])]
    return Rules(version=version, merchants=merchants, patterns=patterns)


def categorize_merchant(merchant: str, rules: Rules) -> Optional[str]:
    m = normalize_merchant(merchant)

    cat = rules.merchants.get(m)
    if cat:
        return cat

    for pr in rules.patterns:
        if pr._compiled.search(m):
            return pr.category

    return None
