import io
import csv
import re
import pandas as pd
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
    """
    try:
        # Load CSV into pandas DataFrame
        # decode with utf-8, fallback to latin-1
        try:
            content = csv_bytes.decode('utf-8')
        except UnicodeDecodeError:
            content = csv_bytes.decode('latin-1')

        # Use StringIO to read CSV
        df = pd.read_csv(io.StringIO(content))
        
        # Clean column names (strip whitespace and lowercase)
        df.columns = [col.strip().lower() for col in df.columns]
        
        # Detect target columns
        date_col = None
        desc_col = None
        amt_col = None
        
        for col in df.columns:
            if col in DATE_COLS:
                date_col = col
            elif col in DESC_COLS:
                desc_col = col
            elif col in AMT_COLS:
                amt_col = col
                
        # Fallbacks if exact matches not found
        if not date_col:
            # Look for any column containing 'date'
            for col in df.columns:
                if 'date' in col:
                    date_col = col
                    break
        if not desc_col:
            # Look for description keywords
            for col in df.columns:
                if 'desc' in col or 'particular' in col or 'narrat' in col or 'remark' in col or 'payee' in col:
                    desc_col = col
                    break
        if not amt_col:
            # Look for amount keywords
            for col in df.columns:
                if 'amount' in col or 'debit' in col or 'withdraw' in col or 'spent' in col:
                    amt_col = col
                    break

        # Absolute fallback: use column indexes 0, 1, 2 if we still don't find them
        if len(df.columns) >= 3:
            if not date_col: date_col = df.columns[0]
            if not desc_col: desc_col = df.columns[1]
            if not amt_col: amt_col = df.columns[2]
        else:
            raise ValueError("CSV statement must have at least 3 columns (Date, Description, Amount).")

        parsed_expenses = []
        
        for _, row in df.iterrows():
            raw_date = str(row[date_col]).strip()
            raw_desc = str(row[desc_col]).strip()
            raw_amt = str(row[amt_col]).strip()
            
            # Skip empty or NaN rows
            if pd.isna(row[date_col]) or pd.isna(row[desc_col]) or pd.isna(row[amt_col]):
                continue
                
            # Parse amount
            # Remove currency symbols, commas, and extra spaces
            clean_amt_str = re.sub(r'[^\d\.\-]', '', raw_amt)
            try:
                amt = abs(float(clean_amt_str))
            except ValueError:
                continue
                
            if amt <= 0:
                continue
                
            # Parse Date
            parsed_date = None
            date_formats = [
                '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%m/%d/%Y', 
                '%d %b %Y', '%Y/%m/%d', '%d-%b-%y', '%d-%b-%Y'
            ]
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(raw_date, fmt).strftime('%Y-%m-%d')
                    break
                except ValueError:
                    continue
                    
            if not parsed_date:
                # If date parsing fails, default to today's date
                parsed_date = datetime.today().strftime('%Y-%m-%d')
                
            # Categorize the description
            category = categorize_expense(raw_desc)
            
            parsed_expenses.append({
                "date": parsed_date,
                "description": raw_desc,
                "amount": round(amt, 2),
                "category": category
            })
            
        return parsed_expenses
        
    except Exception as e:
        # If anything fails, raise a custom exception that can be caught by the FastAPI handler
        raise ValueError(f"Error parsing CSV file: {str(e)}")
