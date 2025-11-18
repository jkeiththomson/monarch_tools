"""Name command implementation for monarch_tools."""

import argparse


def cmd_name(ns: argparse.Namespace) -> int:
    print(f"Hello, {ns.who}!")
    return 0
