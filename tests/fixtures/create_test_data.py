"""Script to create test data fixtures for E2E testing."""

import pandas as pd
from pathlib import Path
from datetime import date, timedelta
import random

# Create fixtures directory
fixtures_dir = Path(__file__).parent
fixtures_dir.mkdir(exist_ok=True)

def create_test_units():
    """Create test units Excel file."""
    units_data = {
        "unit_id": ["SHOP-001", "SHOP-002", "SHOP-003", "OFFICE-001", "OFFICE-002"],
        "building_name": ["Main Building", "Main Building", "Annex Building", "Office Tower", "Office Tower"],
        "address_line_1": ["123 High Street", "123 High Street", "125 High Street", "456 Business Park", "456 Business Park"],
        "address_line_2": ["", "Unit 2", "", "Floor 5", "Floor 6"],
        "city": ["London", "London", "London", "Manchester", "Manchester"],
        "postcode": ["SW1A 1AA", "SW1A 1AA", "SW1A 1AB", "M1 1AA", "M1 1AA"]
    }
    
    df = pd.DataFrame(units_data)
    output_file = fixtures_dir / "test_units.xlsx"
    df.to_excel(output_file, index=False, engine='openpyxl')
    print(f"[OK] Created {output_file}")
    return output_file

def create_test_leases():
    """Create test leases Excel file."""
    leases_data = {
        "unit_id": ["SHOP-001", "SHOP-002", "SHOP-003", "OFFICE-001", "OFFICE-002"],
        "tenant_name": ["ABC Retail Ltd", "XYZ Services", "Quick Mart", "Tech Corp", "Finance Inc"],
        "lease_start": [
            date(2024, 1, 1),
            date(2024, 2, 1),
            date(2024, 3, 1),
            date(2024, 1, 15),
            date(2024, 2, 15)
        ],
        "lease_end": [
            date(2024, 12, 31),
            date(2024, 12, 31),
            date(2025, 2, 28),
            date(2024, 12, 31),
            date(2025, 1, 31)
        ]
    }
    
    df = pd.DataFrame(leases_data)
    # Convert dates to strings for Excel
    df['lease_start'] = df['lease_start'].astype(str)
    df['lease_end'] = df['lease_end'].astype(str)
    
    output_file = fixtures_dir / "test_leases.xlsx"
    df.to_excel(output_file, index=False, engine='openpyxl')
    print(f"[OK] Created {output_file}")
    return output_file

def create_test_invoices():
    """Create test invoices Excel file."""
    invoices_data = {
        "invoice_number": ["INV-001", "INV-002", "INV-003", "INV-004", "INV-005"],
        "supplier_account_number": ["1234567890", "9876543210", "5555555555", "1111111111", "2222222222"],
        "supplier_name": ["British Gas", "EDF Energy", "E.ON", "Scottish Power", "Octopus Energy"],
        "unit_id": ["SHOP-001", "SHOP-002", "SHOP-003", "OFFICE-001", "OFFICE-002"],
        "billing_period_start": [
            date(2024, 1, 1),
            date(2024, 2, 1),
            date(2024, 3, 1),
            date(2024, 1, 15),
            date(2024, 2, 15)
        ],
        "billing_period_end": [
            date(2024, 1, 31),
            date(2024, 2, 29),
            date(2024, 3, 31),
            date(2024, 2, 14),
            date(2024, 3, 14)
        ],
        "gross_amount": ["300.00", "350.50", "275.75", "450.00", "320.25"],
        "utility_type": ["Electricity", "Electricity", "Electricity", "Electricity", "Electricity"],
        "invoice_date": [
            date(2024, 2, 5),
            date(2024, 3, 5),
            date(2024, 4, 5),
            date(2024, 2, 20),
            date(2024, 3, 20)
        ]
    }
    
    df = pd.DataFrame(invoices_data)
    # Convert dates to strings for Excel
    df['billing_period_start'] = df['billing_period_start'].astype(str)
    df['billing_period_end'] = df['billing_period_end'].astype(str)
    df['invoice_date'] = df['invoice_date'].astype(str)
    
    output_file = fixtures_dir / "test_invoices.xlsx"
    df.to_excel(output_file, index=False, engine='openpyxl')
    print(f"[OK] Created {output_file}")
    return output_file

def create_test_invoices_csv():
    """Create test invoices CSV file (alternative format)."""
    invoices_data = {
        "invoice_number": ["INV-CSV-001", "INV-CSV-002"],
        "supplier_account_number": ["3333333333", "4444444444"],
        "supplier_name": ["British Gas", "EDF Energy"],
        "unit_id": ["SHOP-001", "SHOP-002"],
        "billing_period_start": ["2024-04-01", "2024-05-01"],
        "billing_period_end": ["2024-04-30", "2024-05-31"],
        "gross_amount": ["400.00", "375.50"],
        "utility_type": ["Electricity", "Electricity"]
    }
    
    df = pd.DataFrame(invoices_data)
    output_file = fixtures_dir / "test_invoices.csv"
    df.to_csv(output_file, index=False)
    print(f"[OK] Created {output_file}")
    return output_file

def create_invalid_test_file():
    """Create an invalid test file for error handling tests."""
    invalid_file = fixtures_dir / "invalid.txt"
    invalid_file.write_text("This is not a valid invoice file.\nIt should cause an error when uploaded.")
    print(f"[OK] Created {invalid_file}")
    return invalid_file

if __name__ == "__main__":
    print("Creating test data fixtures...")
    print("=" * 50)
    
    create_test_units()
    create_test_leases()
    create_test_invoices()
    create_test_invoices_csv()
    create_invalid_test_file()
    
    print("=" * 50)
    print("[OK] All test data fixtures created!")
    print(f"\nLocation: {fixtures_dir}")
    print("\nFiles created:")
    print("  - test_units.xlsx")
    print("  - test_leases.xlsx")
    print("  - test_invoices.xlsx")
    print("  - test_invoices.csv")
    print("  - invalid.txt")

