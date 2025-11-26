# src/monarch_tools/extractors/chase.py
"""
Chase activity extractor for monarch_tools.

This implementation:
- Opens the Chase PDF with pdfplumber
- First tries to extract transactions from table structures
- If none are found, falls back to parsing the raw text lines with a regex
- Treats rows starting with a date (MM/DD/YY or MM/DD/YYYY) as transactions
- Writes a normalized CSV with columns:
    transaction_date, post_date, description, amount, balance, raw

You can refine the heuristics over time as we see more statement layouts.
"""

from pathlib import Path
import csv
import re
from typing import List, Optional


DATE_RE = re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}$")
MONEY_RE = re.compile(r"^-?\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?$")

# For fallback line-based parsing:
LINE_TXN_RE = re.compile(
    r"""
    ^\s*
    (?P<tran_date>\d{1,2}/\d{1,2}/\d{2,4})      # transaction date
    \s+
    (?:                                       
        (?P<post_date>\d{1,2}/\d{1,2}/\d{2,4})  # optional post date
        \s+
    )?
    (?P<desc>.*?)                              # description (lazy)
    \s+
    (?P<amount>-?\(?\$?\d[\d,]*\.\d{2}\)?)      # amount
    (?:\s+
        (?P<balance>-?\(?\$?\d[\d,]*\.\d{2}\)?) # optional balance
    )?
    \s*$
    """,
    re.VERBOSE,
)


def _parse_money(s: str) -> Optional[float]:
    """
    Parse a money string like:
      '123.45', '1,234.56', '-123.45', '$123.45', '-$1,234.56', '(123.45)'
    into a float. Returns None if it doesn't look like money.
    """
    if s is None:
        return None
    s = s.strip()
    if not s:
        return None

    # Handle parentheses for negatives: (123.45)
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()

    # Strip dollar sign
    if s.startswith("$"):
        s = s[1:].strip()

    # Remove commas
    s = s.replace(",", "")

    # After cleaning, must match a number
    if not re.match(r"^-?\d+(?:\.\d{2})?$", s):
        return None

    try:
        value = float(s)
    except ValueError:
        return None

    if negative:
        value = -value
    return value


def _looks_like_date(s: str) -> bool:
    if s is None:
        return False
    s = s.strip()
    return bool(DATE_RE.match(s))


def _looks_like_money(s: str) -> bool:
    if s is None:
        return False
    s = s.strip()
    return bool(MONEY_RE.match(s))


def _clean_cell(cell) -> str:
    if cell is None:
        return ""
    return str(cell).strip()


def _extract_transactions_from_table(table: List[List[Optional[str]]]) -> List[List[str]]:
    """
    Given one table from pdfplumber (list of rows, each row a list of cells),
    extract transaction-like rows.

    Heuristic:
    - First cell must be a date (transaction_date)
    - Second cell may be a date (post_date)
    - Description is the next non-empty, non-date cell(s)
    - Amount is the *last* cell that looks like money
    - Balance is an optional other money-looking cell to the right of description
    """
    rows_out: List[List[str]] = []

    for raw_row in table:
        if not raw_row:
            continue

        # Normalize to list of strings
        row = [_clean_cell(c) for c in raw_row]

        # Skip header rows containing 'date' and 'description'
        joined_lower = " ".join(row).lower()
        if "date" in joined_lower and "description" in joined_lower:
            continue

        if not row:
            continue

        # Must start with a date to be considered a transaction
        first = row[0]
        if not _looks_like_date(first):
            continue

        transaction_date = first
        idx = 1

        # Optional post_date if the next cell is also a date
        post_date = ""
        if idx < len(row) and _looks_like_date(row[idx]):
            post_date = row[idx]
            idx += 1

        # Next non-empty cell is description (possibly spanning multiple cells)
        description_parts: List[str] = []
        while idx < len(row) and not row[idx]:
            idx += 1

        desc_idx = idx
        while desc_idx < len(row) and not _looks_like_money(row[desc_idx]):
            if row[desc_idx]:
                description_parts.append(row[desc_idx])
            desc_idx += 1

        description = " ".join(description_parts).strip()
        if not description:
            # Fallback: join any middle cells
            middle = [c for c in row[1:-1] if c]
            description = " ".join(middle).strip()

        # Find all money-like cells in the row
        money_indices: List[int] = [
            i for i, val in enumerate(row) if _looks_like_money(val)
        ]

        amount_str = ""
        balance_str = ""

        if money_indices:
            # Heuristic:
            # - Last money-looking cell is amount
            # - If there are at least two, the second-to-last may be balance
            last_idx = money_indices[-1]
            amount_str = row[last_idx]

            if len(money_indices) >= 2:
                balance_idx = money_indices[-2]
                if balance_idx != last_idx:
                    balance_str = row[balance_idx]

        amount_val = _parse_money(amount_str)
        if amount_val is None:
            # If we can't parse amount, skip this row
            continue

        amount_norm = f"{amount_val:.2f}"

        balance_val = _parse_money(balance_str)
        balance_norm = ""
        if balance_val is not None:
            balance_norm = f"{balance_val:.2f}"

        raw_joined = " | ".join(row)

        rows_out.append(
            [
                transaction_date,
                post_date,
                description,
                amount_norm,
                balance_norm,
                raw_joined,
            ]
        )

    return rows_out


def _extract_transactions_from_lines(lines: List[str]) -> List[List[str]]:
    """
    Fallback: parse raw text lines using a regex.

    Each matching line is turned into:
        [transaction_date, post_date, description, amount, balance, raw_line]
    """
    rows_out: List[List[str]] = []

    for line in lines:
        s = line.strip()
        if not s:
            continue

        m = LINE_TXN_RE.match(s)
        if not m:
            continue

        tran_date = m.group("tran_date") or ""
        post_date = m.group("post_date") or ""
        desc = (m.group("desc") or "").strip()
        amount_str = (m.group("amount") or "").strip()
        balance_str = (m.group("balance") or "").strip()

        amount_val = _parse_money(amount_str)
        if amount_val is None:
            # If we can't parse amount, skip
            continue
        amount_norm = f"{amount_val:.2f}"

        balance_norm = ""
        balance_val = _parse_money(balance_str) if balance_str else None
        if balance_val is not None:
            balance_norm = f"{balance_val:.2f}"

        rows_out.append(
            [
                tran_date,
                post_date,
                desc,
                amount_norm,
                balance_norm,
                s,  # raw line
            ]
        )

    return rows_out


def extract_activity(pdf_path: str, out_dir: str) -> str:
    """
    Parse a Chase statement PDF and write an .activity.csv file into out_dir.

    Returns:
        The absolute path to the written CSV as a string.

    If pdfplumber is not available or parsing fails, writes a header-only file.
    """
    pdf = Path(pdf_path)
    out_dir_path = Path(out_dir)
    out_dir_path.mkdir(parents=True, exist_ok=True)

    out_csv = out_dir_path / f"{pdf.stem}.activity.csv"

    # Try to import pdfplumber at runtime
    try:
        import pdfplumber  # type: ignore
    except ImportError:
        print(
            "[chase extractor] pdfplumber is not installed. "
            "Writing header-only CSV."
        )
        with out_csv.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["transaction_date", "post_date", "description", "amount", "balance", "raw"]
            )
        return str(out_csv)

    all_transactions: List[List[str]] = []

    try:
        with pdfplumber.open(str(pdf)) as doc:
            # ---------- First pass: tables ----------
            for page_num, page in enumerate(doc.pages, start=1):
                try:
                    tables = page.extract_tables()
                except Exception as e:
                    print(f"[chase extractor] Failed to extract tables from page {page_num}: {e}")
                    continue

                if not tables:
                    continue

                for t in tables:
                    if not t:
                        continue
                    txns = _extract_transactions_from_table(t)
                    if txns:
                        all_transactions.extend(txns)

            # ---------- Second pass: raw text lines (if tables found nothing) ----------
            if not all_transactions:
                print("[chase extractor] No transactions found via tables; trying line-based parsing.")
                for page_num, page in enumerate(doc.pages, start=1):
                    try:
                        text = page.extract_text()
                    except Exception as e:
                        print(f"[chase extractor] Failed to extract text from page {page_num}: {e}")
                        continue

                    if not text:
                        continue

                    lines = text.splitlines()
                    txns = _extract_transactions_from_lines(lines)
                    if txns:
                        all_transactions.extend(txns)

    except Exception as e:
        print(f"[chase extractor] Error reading PDF: {e}")
        # Fallback to header-only CSV
        with out_csv.open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["transaction_date", "post_date", "description", "amount", "balance", "raw"]
            )
        return str(out_csv)

    # Always write at least a header so downstream tools don't choke
    with out_csv.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["transaction_date", "post_date", "description", "amount", "balance", "raw"]
        )
        for row in all_transactions:
            writer.writerow(row)

    print(f"[chase extractor] Wrote activity CSV with {len(all_transactions)} rows: {out_csv}")
    return str(out_csv)