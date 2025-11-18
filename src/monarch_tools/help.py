"""Help command implementation for monarch_tools."""

import argparse


def cmd_help(ns: argparse.Namespace) -> int:
    print("Available commands:")
    print("  hello                        Say hello")
    print("  name <who>                   Print your name")
    print("  activity <type> <pdf>        Extract account activity from a statement PDF")
    print("  help                         Show this help message")
    print("\nUse 'monarch-tools <command> --help' for detailed options.")
    return 0
