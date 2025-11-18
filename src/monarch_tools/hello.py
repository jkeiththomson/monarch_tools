"""Hello command implementation for monarch_tools."""

import argparse


def cmd_hello(ns: argparse.Namespace) -> int:
    print("Hello from monarch-tools!")
    return 0
