# console.py
"""
Main command dispatcher for monarch_tools.

Each command’s "business logic" lives in its own module:
hello.py, name.py, help.py, activity.py, categorize.py, etc.

This file is defensive: if a given command function is missing,
the CLI will print a helpful message instead of crashing.
"""

import argparse
import sys


# ---- Safe imports with fallbacks -------------------------------------------

# hello
try:
    from .hello import hello_command as _hello_command  # type: ignore
except Exception:  # ImportError, AttributeError, etc.
    def _hello_command(args):
        print("hello command is not implemented yet.")


# name
try:
    from .name import name_command as _name_command  # type: ignore
except Exception:
    def _name_command(args):
        print("name command is not implemented yet.")


# help
try:
    from .help import help_command as _help_command  # type: ignore
except Exception:
    def _help_command(args):
        print("help command is not implemented yet.")


# activity
try:
    from .activity import activity_command as _activity_command  # type: ignore
except Exception:
    def _activity_command(args):
        print("activity command is not implemented yet.")


# categorize (new implementation)
try:
    from .categorize import categorize_command as _categorize_command  # type: ignore
except Exception:
    def _categorize_command(args):
        print("categorize command is not implemented yet.")


# ---- Parser setup ----------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="monarch_tools",
        description="Monarch Tools Command Line Interface",
    )

    subparsers = parser.add_subparsers(dest="command")
    try:
        subparsers.required = True  # Python 3.7+
    except AttributeError:
        pass

    # ---- hello ----
    hello_p = subparsers.add_parser("hello", help="Say hello")
    hello_p.set_defaults(func=_hello_command)

    # ---- name ----
    name_p = subparsers.add_parser("name", help="Print your name")
    name_p.add_argument("your_name", help="Your name")
    name_p.set_defaults(func=_name_command)

    # ---- help ----
    help_p = subparsers.add_parser("help", help="Show help for monarch_tools")
    help_p.set_defaults(func=_help_command)

    # ---- activity ----
    activity_p = subparsers.add_parser(
        "activity",
        help="Extract account activity from a statement PDF",
    )
    activity_p.add_argument(
        "statement_type",
        help="Statement type (e.g., 'chase')",
    )
    activity_p.add_argument(
        "pdf_path",
        help="Path to the PDF statement",
    )
    activity_p.set_defaults(func=_activity_command)

    # ---- categorize ----
    categorize_p = subparsers.add_parser(
        "categorize",
        help="Categorize merchants using categories, groups, and rules",
    )
    categorize_p.add_argument(
        "activity_csv",
        help="Input CSV file (activity extracted file)",
    )
    categorize_p.add_argument(
        "--categories",
        default="data/categories.txt",
        help="Path to category list (default: data/categories.txt)",
    )
    categorize_p.add_argument(
        "--groups",
        default="data/groups.txt",
        help="Path to group→category mapping (default: data/groups.txt)",
    )
    categorize_p.add_argument(
        "--rules",
        default="data/rules.json",
        help="Path to categorization rules (default: data/rules.json)",
    )
    categorize_p.add_argument(
        "--output",
        help="Output CSV; default is <stem>.categorized.csv",
    )
    categorize_p.set_defaults(func=_categorize_command)

    return parser


# ---- Main entry point ------------------------------------------------------


def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = args.func(args)
        if isinstance(result, int):
            return result
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
