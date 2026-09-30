"""Fix template columns to match required fields.

This script updates the Excel templates to match the exact column names
required by the Valix system, as shown in the UI.
"""

import pandas as pd
import os
from pathlib import Path

# Ensure test_data directory exists
test_data_dir = Path("test_data")
test_data_dir.mkdir(exist_ok=True)

print("Fixing template columns to match required fields...")

# 1. Fix units_template.xlsx with EXACT required columns
print("Creating units_template.xlsx with required columns...")
units_data = {
    "unit_id": ["UNIT001", "UNIT002", "UNIT003", "UNIT004", "UNIT005", 
                "UNIT006", "UNIT007", "UNIT008", "UNIT009", "UNIT010"],
    "building_name": ["Main Street Office", "High Street Retail", "Market Square Office", 
                     "River Road Warehouse", "Park Lane Shop", "Bridge Street Office", 
                     "Church Road Retail", "Station Avenue Warehouse", "Queen's Drive Office", 
                     "King's Road Retail"],
    "address_line_1": ["123 Main Street", "456 High Street", "789 Market Square", 
                      "101 River Road", "202 Park Lane", "303 Bridge Street", 
                      "404 Church Road", "505 Station Avenue", "606 Queen's Drive", 
                      "707 King's Road"],
    "city": ["London", "Manchester", "Birmingham", "Glasgow", "Edinburgh", 
            "Leeds", "Bristol", "Liverpool", "Newcastle", "Cardiff"],
    "postcode": ["SW1A 1AA", "M1 1AB", "B1 1CD", "G1 1DE", "EH1 1FG", 
                "LS1 1GH", "BS1 1IJ", "L1 1KL", "NE1 1MN", "CF1 1OP"],
    # Optional columns
    "address_line_2": ["Floor 1", "Suite 2", "Unit 3A", "Building B", "Floor 2", 
                      "Suite 101", "Unit 5", "Floor 3", "Suite 202", "Unit 7"]
}

units_df = pd.DataFrame(units_data)
with pd.ExcelWriter(test_data_dir / "units_template.xlsx", engine="openpyxl") as writer:
    units_df.to_excel(writer, index=False)

# 2. Fix leases_template.xlsx with EXACT required columns
print("Creating leases_template.xlsx with required columns...")
leases_data = {
    "unit_id": ["UNIT001", "UNIT003", "UNIT005", "UNIT007", "UNIT008", "UNIT010", 
                "UNIT002", "UNIT004", "UNIT006", "UNIT009"],
    "tenant_name": ["Acme Corporation", "Global Enterprises", "Retail Solutions Ltd", "Fashion Outlet Co", 
                    "Logistics Partners", "City Retail Group", "Tech Innovations", "Storage Solutions", 
                    "Office Space Inc", "Business Center Ltd"],
    "lease_start": ["2025-01-01", "2025-06-01", "2024-09-01", "2025-03-15", "2025-05-01", 
                   "2025-02-01", "2024-01-01", "2024-03-01", "2024-05-01", "2025-01-01"],
    "lease_end": ["2026-12-31", "2027-05-31", "2026-08-31", "2027-03-14", "2026-04-30", 
                 "2027-01-31", "2025-11-30", "2026-01-14", "2025-10-31", "2026-01-31"]
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

# 4. Create a specific E.ON account mapping for the sample invoice
print("Creating eon_account_mapping.xlsx for the sample E.ON invoice...")
eon_mapping_data = {
    "supplier_account_number": ["0123 4567 89"],  # Account number from the E.ON invoice
    "unit_id": ["UNIT001"],  # Map to a specific unit
    "supplier_name": ["E.ON"],
    "notes": ["E.ON account from sample invoice"]
}

eon_mapping_df = pd.DataFrame(eon_mapping_data)
with pd.ExcelWriter(test_data_dir / "eon_account_mapping.xlsx", engine="openpyxl") as writer:
    eon_mapping_df.to_excel(writer, index=False)

print("All template files have been fixed with the correct column names!")