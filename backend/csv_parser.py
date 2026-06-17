import io
import csv
import re
from datetime import datetime
from typing import List, Dict, Any
from ml_engine import categorize_expense

# Keywords to match column names in the CSV file
DATE_COLS = ['date', 'transaction date', 'tx date', 'value date', 'date of transaction', 'posting date']
DESC_COLS = ['description', 'particulars', 'narration', 'details', 'remarks', 'payee', 'transaction details']
AMT_COLS = ['amount', 'debit', 'value', 'transaction amount', 'withdrawal', 'outflow', 'debit amount']

def parse_bank_statement_csv(csv_bytes: bytes) -> List[Dict[str, Any]]:
    """
    Parses a CSV bank statement. Auto-detects columns for date, description, and amount.
    Applies auto-categorization to each transaction.
    Returns a list of structured expense dictionaries.
    Uses only stdlib csv module (replaces pandas dependency).
    """
    try:
        # Decode with utf-8, fallback to latin-1
        try:
            content = csv_bytes.decode('utf-8')
        except UnicodeDecodeError:
            content = csv_bytes.decode('latin-1')

        reader = csv.DictReader(io.StringIO(content))

        if reader.fieldnames is None:
            raise ValueError("CSV file appears to be empty or has no headers.")

        # Clean column names (strip whitespace and lowercase)
        raw_fieldnames = list(reader.fieldnames)
        cleaned_to_raw: Dict[str, str] = {col.strip().lower(): col for col in raw_fieldnames}
        columns = list(cleaned_to_raw.keys())

        # Detect target columns
        date_col = None
        desc_col = None
        amt_col = None

        for col in columns:
            if col in DATE_COLS:
                date_col = col
            elif col in DESC_COLS:
                desc_col = col
            elif col in AMT_COLS:
                amt_col = col

        # Fallbacks if exact matches not found
        if not date_col:
            for col in columns:
                if 'date' in col:
                    date_col = col
                    break
        if not desc_col:
            for col in columns:
                if 'desc' in col or 'particular' in col or 'narrat' in col or 'remark' in col or 'payee' in col:
                    desc_col = col
                    break
        if not amt_col:
            for col in columns:
                if 'amount' in col or 'debit' in col or 'withdraw' in col or 'spent' in col:
                    amt_col = col
                    break

        # Absolute fallback: use column indexes 0, 1, 2
        if len(columns) >= 3:
            if not date_col: date_col = columns[0]
            if not desc_col: desc_col = columns[1]
            if not amt_col:  amt_col  = columns[2]
        else:
            raise ValueError("CSV statement must have at least 3 columns (Date, Description, Amount).")

        # Map cleaned column names back to raw header names for DictReader lookup
        raw_date_col = cleaned_to_raw[date_col]
        raw_desc_col = cleaned_to_raw[desc_col]
        raw_amt_col  = cleaned_to_raw[amt_col]

        date_formats = [
            '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%m/%d/%Y',
            '%d %b %Y', '%Y/%m/%d', '%d-%b-%y', '%d-%b-%Y'
        ]

        parsed_expenses = []

        for row in reader:
            raw_date = (row.get(raw_date_col) or "").strip()
            raw_desc = (row.get(raw_desc_col) or "").strip()
            raw_amt  = (row.get(raw_amt_col)  or "").strip()

            # Skip empty rows
            if not raw_date or not raw_desc or not raw_amt:
                continue

            # Parse amount — remove currency symbols, commas, spaces
            clean_amt_str = re.sub(r'[^\d.\-]', '', raw_amt)
            try:
                amt = abs(float(clean_amt_str))
            except ValueError:
                continue

            if amt <= 0:
                continue

            # Parse date
            parsed_date = None
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(raw_date, fmt).strftime('%Y-%m-%d')
                    break
                except ValueError:
                    continue

            if not parsed_date:
                parsed_date = datetime.today().strftime('%Y-%m-%d')

            # Categorize
            category = categorize_expense(raw_desc)

            parsed_expenses.append({
                "date": parsed_date,
                "description": raw_desc,
                "amount": round(amt, 2),
                "category": category
            })

        return parsed_expenses

    except Exception as e:
        raise ValueError(f"Error parsing CSV file: {str(e)}")
