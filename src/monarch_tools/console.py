import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pdfplumber

from .hello import cmd_hello
from .name import cmd_name
from .help import cmd_help
from .activity import cmd_activity
from .categorize import cmd_categorize




def build_parser():
    parser = argparse.ArgumentParser(
        prog="monarch-tools",
        description="Monarch Money toolbox CLI",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # --- hello ---
    p_hello = sub.add_parser("hello", help="Say hello")
    p_hello.set_defaults(func=cmd_hello)

    # --- name ---
    p_name = sub.add_parser("name", help="Print your name")
    p_name.add_argument("who", help="Name to greet")
    p_name.set_defaults(func=cmd_name)

    # --- help ---
    p_help = sub.add_parser("help", help="Show available commands and usage")
    p_help.set_defaults(func=cmd_help)

    # --- activity (real, positional) ---
    p_activity = sub.add_parser(
        "activity",
        help="Extract account activity from a statement PDF and write <stem>.activity.csv",
        description=(
            "Parse a statement PDF for the given account type and emit <stem>.activity.csv "
            "in the same folder as the PDF."
        ),
    )
    p_activity.add_argument(
        "account_type",
        choices=["chase", "citi", "amex"],
        help="Which account type parser to use.",
    )
    p_activity.add_argument(
        "statement_pdf",
        help="Statement PDF path (absolute) or a path/filename under ./statements.",
    )
    p_activity.add_argument(
        "--debug",
        action="store_true",
        help="Print diagnostic info (counts and a few sample lines).",
    )
    p_activity.set_defaults(func=cmd_activity)



    # --- categorize ---
    p_categorize = sub.add_parser(
        "categorize",
        help="Interactively assign categories to activity rows",
        description=(
            "Walk an activity CSV file and interactively build/update rules.json, "
            "categories.txt, and groups.txt."
        ),
    )
    p_categorize.add_argument(
        "categories_txt",
        help="Path to categories.txt",
    )
    p_categorize.add_argument(
        "groups_txt",
        help="Path to groups.txt",
    )
    p_categorize.add_argument(
        "rules_json",
        help="Path to rules.json",
    )
    p_categorize.add_argument(
        "activity_csv",
        help="Path to <stem>.activity.csv produced by the 'activity' command.",
    )
    p_categorize.set_defaults(func=cmd_categorize)



    return parser






def main():
    parser = build_parser()
    ns = parser.parse_args()
    return ns.func(ns)


if __name__ == "__main__":
    raise SystemExit(main())
