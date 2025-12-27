from typing import List
from pathlib import Path
import argparse
import sys

def cmd_extract(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m monarch_tools extract",
        description="Extract data from a statement PDF (stub)",
    )
    parser.add_argument("--pdf", required=True, help="Path to input PDF")
    parser.add_argument("--out", required=True, help="Output directory")

    args = parser.parse_args(argv)

    pdf_path = Path(args.pdf)
    out_dir = Path(args.out)

    if not pdf_path.exists():
        print(f"ERROR: PDF not found: {pdf_path}", file=sys.stderr)
        return 2

    if not pdf_path.is_file():
        print(f"ERROR: Not a file: {pdf_path}", file=sys.stderr)
        return 2

    out_dir.mkdir(parents=True, exist_ok=True)

    print("extract (stub)")
    print(f"  pdf: {pdf_path}")
    print(f"  out: {out_dir}")
    print("  status: OK (no extraction performed yet)")

    return 0
