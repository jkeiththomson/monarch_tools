from typing import List

HELP_TEXT = """\
monarch-tools

Usage:
  python -m monarch_tools <command> [args...]

Commands:
  hello       Sanity check the CLI wiring
  version     Print package version
  help        Show this help
"""

def cmd_help(argv: List[str]) -> int:
    print(HELP_TEXT)
    return 0