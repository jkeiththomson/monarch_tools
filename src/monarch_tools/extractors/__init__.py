# src/monarch_tools/extractors/__init__.py
"""
Extractor plugins for monarch_tools.

Each module in this package implements one or more functions like:

    extract_activity(pdf_path: str, out_dir: str) -> str

The activity command will look up:
    monarch_tools.extractors.<statement_type>.extract_activity
based on the statement type passed on the CLI (e.g., "chase").
"""