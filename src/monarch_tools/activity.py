"""
Activity extraction command for monarch_tools.

Usage:
    monarch_tools activity <statement_type> <pdf_path>

This command looks for an extractor function with the signature:

    extract_activity(pdf_path: str, out_dir: str) -> str

First it tries:
    monarch_tools.extractors.<statement_type>.extract_activity

Then it tries:
    process_<statement_type>_statement.extract_activity

If no extractor is found, it writes a placeholder CSV to the out/ directory.
"""

import importlib
from pathlib import Path
from typing import Callable, Optional


ExtractorFn = Callable[[str, str], str]


def _try_import(module_name: str, func_name: str) -> Optional[ExtractorFn]:
    """Try to import module_name.func_name, return the function or None."""
    try:
        module = importlib.import_module(module_name)
    except ImportError:
        return None

    func = getattr(module, func_name, None)
    if not callable(func):
        return None
    return func  # type: ignore[return-value]


def _find_extractor(statement_type: str) -> Optional[ExtractorFn]:
    """
    Try to find an extractor function for the given statement_type.

    1. monarch_tools.extractors.<statement_type>.extract_activity
    2. process_<statement_type>_statement.extract_activity
    """
    stype = statement_type.lower()

    # 1) Package-based extractor: monarch_tools.extractors.<stype>
    pkg_module = f"monarch_tools.extractors.{stype}"
    func = _try_import(pkg_module, "extract_activity")
    if func is not None:
        return func

    # 2) Standalone module: process_<stype>_statement.py
    standalone_module = f"process_{stype}_statement"
    func = _try_import(standalone_module, "extract_activity")
    if func is not None:
        return func

    return None


def activity_command(args) -> int:
    """
    Command entry point used by console.py.

    Expects args.statement_type and args.pdf_path.
    """
    statement_type = args.statement_type
    pdf_path = args.pdf_path

    pdf_path_obj = Path(pdf_path)
    if not pdf_path_obj.exists():
        print(f"Error: PDF not found: {pdf_path}")
        return 1

    out_dir = Path("out")
    out_dir.mkdir(parents=True, exist_ok=True)

    extractor = _find_extractor(statement_type)

    if extractor is None:
        # Match the style of your earlier message and write a placeholder.
        print(
            f"No activity extractor found for type '{statement_type}'. "
            "Provide monarch_tools.extractors."
            f"{statement_type}.extract_activity(pdf_path, out_dir) "
            "or a module 'process_chase_statement.py' with 'extract_activity'."
        )

        placeholder = out_dir / f"{pdf_path_obj.stem}.activity.csv"
        if not placeholder.exists():
            # Minimal placeholder header; you can adjust columns later.
            placeholder.write_text(
                "transaction_date,post_date,description,amount,balance,raw\n"
            )
        print(f"Wrote placeholder file: {placeholder}")
        return 2

    # We have an extractor; run it.
    try:
        csv_path_str = extractor(str(pdf_path_obj), str(out_dir))
    except Exception as e:
        print(f"Error while running extractor for '{statement_type}': {e}")
        return 1

    if csv_path_str is None:
        # In case the extractor returns nothing; be defensive.
        csv_path = out_dir / f"{pdf_path_obj.stem}.activity.csv"
        print(
            "Extractor did not return a CSV path. "
            f"Assuming output at: {csv_path}"
        )
    else:
        csv_path = Path(csv_path_str)

    print(f"Wrote activity CSV: {csv_path}")
    return 0