"""Fix Excel template files.

This script recreates the Excel template files in the test_data directory
using the openpyxl engine to ensure they are valid Excel files.
"""

import pandas as pd
import os
from pathlib import Path

# Ensure test_data directory exists
test_data_dir = Path("test_data")
test_data_dir.mkdir(exist_ok=True)

print("Fixing Excel template files...")

# 1. Fix units_template.xlsx
print("Creating units_template.xlsx...")
units_data = {
    "unit_id": ["UNIT001", "UNIT002", "UNIT003", "UNIT004", "UNIT005", 
                "UNIT006", "UNIT007", "UNIT008", "UNIT009", "UNIT010"],
    "address": ["123 Main Street, London, SW1A 1AA", "456 High Street, Manchester, M1 1AB", 
                "789 Market Square, Birmingham, B1 1CD", "101 River Road, Glasgow, G1 1DE", 
                "202 Park Lane, Edinburgh, EH1 1FG", "303 Bridge Street, Leeds, LS1 1GH", 
                "404 Church Road, Bristol, BS1 1IJ", "505 Station Avenue, Liverpool, L1 1KL", 
                "606 Queen's Drive, Newcastle, NE1 1MN", "707 King's Road, Cardiff, CF1 1OP"],
    "property_type": ["Commercial Office", "Retail", "Commercial Office", "Warehouse", "Retail", 
                      "Commercial Office", "Retail", "Warehouse", "Commercial Office", "Retail"],
    "is_currently_vacant": [False, True, False, True, False, True, False, False, True, False],
    "vacancy_start_date": [None, "2025-12-01", None, "2026-01-15", None, "2025-11-01", None, None, "2026-02-01", None],
    "vacancy_end_date": [None, None, None, "2026-04-15", None, None, None, None, "2026-05-01", None]
}

units_df = pd.DataFrame(units_data)
with pd.ExcelWriter(test_data_dir / "units_template.xlsx", engine="openpyxl") as writer:
    units_df.to_excel(writer, index=False)

# 2. Fix leases_template.xlsx
print("Creating leases_template.xlsx...")
leases_data = {
    "unit_id": ["UNIT001", "UNIT003", "UNIT005", "UNIT007", "UNIT008", "UNIT010", 
                "UNIT002", "UNIT004", "UNIT006", "UNIT009"],
    "lease_start_date": ["2025-01-01", "2025-06-01", "2024-09-01", "2025-03-15", "2025-05-01", 
                         "2025-02-01", "2024-01-01", "2024-03-01", "2024-05-01", "2025-01-01"],
    "lease_end_date": ["2026-12-31", "2027-05-31", "2026-08-31", "2027-03-14", "2026-04-30", 
                       "2027-01-31", "2025-11-30", "2026-01-14", "2025-10-31", "2026-01-31"],
    "tenant_name": ["Acme Corporation", "Global Enterprises", "Retail Solutions Ltd", "Fashion Outlet Co", 
                    "Logistics Partners", "City Retail Group", "Tech Innovations", "Storage Solutions", 
                    "Office Space Inc", "Business Center Ltd"],
    "lease_reference": ["LEASE-ACME-2025", "LEASE-GE-2025", "LEASE-RSL-2024", "LEASE-FOC-2025", 
                        "LEASE-LP-2025", "LEASE-CRG-2025", "LEASE-TI-2024", "LEASE-SS-2024", 
                        "LEASE-OSI-2024", "LEASE-BCL-2025"]
}

leases_df = pd.DataFrame(leases_data)
with pd.ExcelWriter(test_data_dir / "leases_template.xlsx", engine="openpyxl") as writer:
    leases_df.to_excel(writer, index=False)

# 3. Fix account_mappings_template.xlsx
print("Creating account_mappings_template.xlsx...")
mappings_data = {
    "supplier_account_number": ["BG-12345678", "BG-23456789", "BG-34567890", "BG-45678901", "BG-56789012",
                               "EO-12345678", "EO-23456789", "EO-34567890", "EO-45678901", "EO-56789012",
                               "TW-12345678", "TW-23456789", "TW-34567890", "TW-45678901", "TW-56789012",
                               "OE-12345678", "OE-23456789", "OE-34567890", "OE-45678901", "OE-56789012"],
    "unit_id": ["UNIT001", "UNIT002", "UNIT003", "UNIT004", "UNIT005",
               "UNIT001", "UNIT002", "UNIT003", "UNIT004", "UNIT005",
               "UNIT001", "UNIT002", "UNIT003", "UNIT004", "UNIT005",
               "UNIT006", "UNIT007", "UNIT008", "UNIT009", "UNIT010"],
    "supplier_name": ["British Gas", "British Gas", "British Gas", "British Gas", "British Gas",
                     "E.ON", "E.ON", "E.ON", "E.ON", "E.ON",
                     "Thames Water", "Thames Water", "Thames Water", "Thames Water", "Thames Water",
                     "Opus Energy", "Opus Energy", "Opus Energy", "Opus Energy", "Opus Energy"],
    "notes": ["Electricity account", "Electricity account", "Electricity account", "Electricity account", "Electricity account",
             "Gas account", "Gas account", "Gas account", "Gas account", "Gas account",
             "Water account", "Water account", "Water account", "Water account", "Water account",
             "Electricity account", "Electricity account", "Electricity account", "Electricity account", "Electricity account"]
}

mappings_df = pd.DataFrame(mappings_data)
with pd.ExcelWriter(test_data_dir / "account_mappings_template.xlsx", engine="openpyxl") as writer:
    mappings_df.to_excel(writer, index=False)

# 4. Fix extraction_patterns_template.xlsx
print("Creating extraction_patterns_template.xlsx...")
patterns_data = {
    "Supplier Name": ["British Gas", "British Gas", "British Gas", "British Gas",
                     "E.ON", "E.ON", "E.ON", "E.ON",
                     "Opus Energy", "Thames Water", "Thames Water"],
    "Field Name": ["supplier_account_number", "supplier_account_number", "billing_period_start", "billing_period_end",
                  "supplier_account_number", "supplier_account_number", "billing_period_start", "billing_period_end",
                  "supplier_account_number", "supplier_account_number", "supplier_account_number"],
    "Pattern Type": ["regex", "regex", "regex", "regex",
                    "regex", "regex", "regex", "regex",
                    "regex", "regex", "regex"],
    "Pattern Value": [
        r'customer\s+reference\s+number[\s:]+([0-9\s-]{6,})',
        r'customer\s+reference[\s:]+([0-9\s-]{6,})',
        r'bill\s+period[\s:]+(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})\s*[-–]\s*\d{1,2}\s+[A-Za-z]{3}\s+\d{2}',
        r'bill\s+period[\s:]+\d{1,2}\s+[A-Za-z]{3}\s+\d{2}\s*[-–]\s*(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})',
        r'account\s+number[\s:]+([0-9\s-]{6,})',
        r'your\s+account\s+number[\s:]+([0-9\s-]{6,})',
        r'billing\s+period[\s:]+(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})\s*[-–]\s*\d{1,2}\s+[A-Za-z]{3}\s+\d{2}',
        r'billing\s+period[\s:]+\d{1,2}\s+[A-Za-z]{3}\s+\d{2}\s*[-–]\s*(\d{1,2}\s+[A-Za-z]{3}\s+\d{2})',
        r'account\s+number\s*\n(?:[^\n]*\n){0,2}\s*([0-9]{6,})',
        r'account\s+number[\s:]+([0-9\s-]{6,})',
        r'customer\s+reference[\s:]+([0-9\s-]{6,})'
    ],
    "Priority": [100, 90, 100, 100, 100, 90, 100, 100, 100, 100, 90],
    "Notes": [
        "British Gas account number pattern",
        "British Gas alternative account pattern",
        "British Gas billing period start pattern",
        "British Gas billing period end pattern",
        "E.ON account number pattern",
        "E.ON account number pattern (with 'your')",
        "E.ON billing period start pattern",
        "E.ON billing period end pattern",
        "Opus Energy account number pattern (multi-line)",
        "Thames Water account number pattern",
        "Thames Water alternative account pattern"
    ]
}

patterns_df = pd.DataFrame(patterns_data)
with pd.ExcelWriter(test_data_dir / "extraction_patterns_template.xlsx", engine="openpyxl") as writer:
    patterns_df.to_excel(writer, index=False)

# 5. Fix sample_invoices.xlsx
print("Creating sample_invoices.xlsx...")
invoices_data = {
    "invoice_number": ["INV-BG-001", "INV-BG-002", "INV-BG-003", "INV-EO-001", "INV-EO-002",
                      "INV-TW-001", "INV-TW-002", "INV-OE-001", "INV-OE-002", "INV-OE-003"],
    "supplier_name": ["British Gas", "British Gas", "British Gas", "E.ON", "E.ON",
                     "Thames Water", "Thames Water", "Opus Energy", "Opus Energy", "Opus Energy"],
    "supplier_account_number": ["BG-12345678", "BG-23456789", "BG-34567890", "EO-12345678", "EO-23456789",
                               "TW-12345678", "TW-23456789", "OE-12345678", "OE-23456789", "OE-34567890"],
    "unit_id": ["UNIT001", "UNIT002", "UNIT003", "UNIT001", "UNIT002",
               "UNIT001", "UNIT002", "UNIT006", "UNIT007", "UNIT008"],
    "address": ["123 Main Street, London, SW1A 1AA", "456 High Street, Manchester, M1 1AB",
               "789 Market Square, Birmingham, B1 1CD", "123 Main Street, London, SW1A 1AA",
               "456 High Street, Manchester, M1 1AB", "123 Main Street, London, SW1A 1AA",
               "456 High Street, Manchester, M1 1AB", "303 Bridge Street, Leeds, LS1 1GH",
               "404 Church Road, Bristol, BS1 1IJ", "505 Station Avenue, Liverpool, L1 1KL"],
    "billing_period_start": ["2025-12-01", "2025-12-01", "2025-12-01", "2025-12-01", "2025-12-01",
                            "2025-12-01", "2025-12-01", "2025-12-01", "2025-12-01", "2025-12-01"],
    "billing_period_end": ["2025-12-31", "2025-12-31", "2025-12-31", "2025-12-31", "2025-12-31",
                          "2026-01-31", "2026-01-31", "2025-12-31", "2025-12-31", "2025-12-31"],
    "invoice_date": ["2026-01-05", "2026-01-05", "2026-01-05", "2026-01-07", "2026-01-07",
                    "2026-01-10", "2026-01-10", "2026-01-08", "2026-01-08", "2026-01-08"],
    "gross_amount": [120.00, 85.50, 210.60, 95.40, 65.80, 45.60, 32.40, 145.20, 98.70, 187.50],
    "net_amount": [100.00, 71.25, 175.50, 79.50, 54.83, 45.60, 32.40, 121.00, 82.25, 156.25],
    "vat_amount": [20.00, 14.25, 35.10, 15.90, 10.97, 0.00, 0.00, 24.20, 16.45, 31.25],
    "utility_type": ["Electricity", "Electricity", "Electricity", "Gas", "Gas",
                    "Water", "Water", "Electricity", "Electricity", "Electricity"],
    "currency": ["GBP", "GBP", "GBP", "GBP", "GBP", "GBP", "GBP", "GBP", "GBP", "GBP"]
}

invoices_df = pd.DataFrame(invoices_data)
with pd.ExcelWriter(test_data_dir / "sample_invoices.xlsx", engine="openpyxl") as writer:
    invoices_df.to_excel(writer, index=False)

print("All Excel template files have been fixed!")