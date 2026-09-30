"""Script to load invoice CSV files into the database.
    
Expected CSV columns:
    - invoice_number (required)
    - supplier_name (required)
    - unit_id (required)
    - billing_period_start (required, date format: YYYY-MM-DD or DD/MM/YYYY)
    - billing_period_end (required, date format: YYYY-MM-DD or DD/MM/YYYY)
    - invoice_date (optional, date format: YYYY-MM-DD or DD/MM/YYYY)
    - gross_amount (required, numeric)
    - net_amount (optional, numeric)
    - vat_amount (optional, numeric)
    - utility_type (required, e.g., 'Electricity', 'Gas', 'Water')
    - currency (optional, defaults to 'GBP')
    - source_batch (optional, string identifier)
    
Usage:
    python scripts/load_invoices.py [path_to_csv_file]
    
If no path is provided, defaults to data/sample_invoices.csv
"""

import sys
import csv
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_session, init_db
from app.models import Invoice


def parse_date(date_str: str) -> datetime.date:
    """
    Parse a date string, supporting multiple formats.
    
    Supports:
    - YYYY-MM-DD (ISO format)
    - YYYY-MM-DD HH:MM:SS (datetime string - time is ignored)
    - DD/MM/YYYY
    - DD-MM-YYYY
    
    Returns a date object.
    """
    if not date_str or date_str.strip() == "":
        return None
    
    date_str = date_str.strip()
    
    # First, try to handle datetime strings (with time component)
    # Strip time component if present
    if ' ' in date_str and len(date_str) > 10:
        # Likely has time component, try to parse as datetime first
        try:
            # Try YYYY-MM-DD HH:MM:SS
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").date()
        except ValueError:
            try:
                # Try YYYY-MM-DD HH:MM:SS.microseconds
                return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S.%f").date()
            except ValueError:
                # If datetime parsing fails, just take the date part
                date_str = date_str.split(' ')[0]
    
    # Try ISO format first (YYYY-MM-DD)
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        pass
    
    # Try DD/MM/YYYY
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").date()
    except ValueError:
        pass
    
    # Try DD-MM-YYYY
    try:
        return datetime.strptime(date_str, "%d-%m-%Y").date()
    except ValueError:
        pass
    
    # If all fail, raise an error
    raise ValueError(f"Unable to parse date: {date_str}. Expected formats: YYYY-MM-DD, DD/MM/YYYY, or DD-MM-YYYY")


def parse_decimal(value_str: str) -> Decimal:
    """Parse a decimal value from string, handling empty strings."""
    if not value_str or value_str.strip() == "":
        return None
    # Remove any currency symbols or commas
    cleaned = value_str.strip().replace(",", "").replace("£", "").replace("$", "").replace("€", "")
    return Decimal(cleaned)


def load_invoices_from_csv(csv_path: Path, source_batch: str = None):
    """
    Load invoices from a CSV file into the database.
    
    Args:
        csv_path: Path to the CSV file
        source_batch: Optional batch identifier for this import
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    # Initialize database if tables don't exist
    init_db()
    
    invoices_loaded = 0
    errors = []
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        # Validate required columns
        required_columns = [
            "invoice_number",
            "supplier_name",
            "unit_id",
            "billing_period_start",
            "billing_period_end",
            "gross_amount",
            "utility_type",
        ]
        
        missing_columns = [col for col in required_columns if col not in reader.fieldnames]
        if missing_columns:
            raise ValueError(f"CSV is missing required columns: {', '.join(missing_columns)}")
        
        with get_session() as session:
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (row 1 is header)
                try:
                    # Parse dates
                    billing_period_start = parse_date(row["billing_period_start"])
                    billing_period_end = parse_date(row["billing_period_end"])
                    invoice_date = parse_date(row.get("invoice_date", ""))
                    
                    # Parse amounts
                    gross_amount = parse_decimal(row["gross_amount"])
                    if gross_amount is None:
                        raise ValueError("gross_amount is required and cannot be empty")
                    
                    net_amount = parse_decimal(row.get("net_amount", ""))
                    vat_amount = parse_decimal(row.get("vat_amount", ""))
                    
                    # Create invoice record
                    invoice = Invoice(
                        invoice_number=row["invoice_number"].strip(),
                        supplier_name=row["supplier_name"].strip(),
                        unit_id=row["unit_id"].strip(),
                        billing_period_start=billing_period_start,
                        billing_period_end=billing_period_end,
                        invoice_date=invoice_date,
                        gross_amount=gross_amount,
                        net_amount=net_amount,
                        vat_amount=vat_amount,
                        utility_type=row["utility_type"].strip(),
                        currency=row.get("currency", "GBP").strip() or "GBP",
                        source_batch=source_batch or row.get("source_batch", "").strip() or None,
                    )
                    
                    session.add(invoice)
                    invoices_loaded += 1
                    
                except Exception as e:
                    error_msg = f"Row {row_num}: {str(e)}"
                    errors.append(error_msg)
                    print(f"ERROR: {error_msg}", file=sys.stderr)
            
            # Commit all invoices
            if invoices_loaded > 0:
                session.commit()
                print(f"\n✓ Successfully loaded {invoices_loaded} invoice(s) into the database.")
            else:
                print("\n⚠ No invoices were loaded.")
            
            if errors:
                print(f"\n⚠ {len(errors)} error(s) encountered during loading.")


def main():
    """Main entry point for the script."""
    # Determine CSV file path
    if len(sys.argv) > 1:
        csv_path = Path(sys.argv[1])
    else:
        # Default to data/sample_invoices.csv
        csv_path = Path(__file__).parent.parent / "data" / "sample_invoices.csv"
    
    # Optional source batch identifier
    source_batch = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        load_invoices_from_csv(csv_path, source_batch)
    except Exception as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

