"""Create units and leases files with the exact column names expected by the system.

Units required columns:
- unit_id
- building_name
- address_line_1
- city
- postcode

Leases required columns:
- unit_id
- tenant_name
- lease_start
- lease_end (optional)
"""

import pandas as pd
from pathlib import Path

# Ensure test_data directory exists
test_data_dir = Path("test_data")
test_data_dir.mkdir(exist_ok=True)

print("Creating units and leases files with correct column names...")

# 1. Create units_fixed.xlsx with required columns
print("Creating units_fixed.xlsx...")
units_data = {
    "unit_id": ["UNIT001"],
    "building_name": ["Test Building"],
    "address_line_1": ["123 Test Street"],
    "city": ["Test City"],
    "postcode": ["TE1 1ST"],
    "address_line_2": ["Floor 1"]
}

units_df = pd.DataFrame(units_data)
with pd.ExcelWriter(test_data_dir / "units_fixed.xlsx", engine="openpyxl") as writer:
    units_df.to_excel(writer, index=False)

# 2. Create leases for different scenarios
print("Creating leases_valid_fixed.xlsx (lease covers invoice period)...")
leases_valid_data = {
    "unit_id": ["UNIT001"],
    "tenant_name": ["Test Tenant"],
    "lease_start": ["2016-01-01"],  # Before invoice period
    "lease_end": ["2016-03-31"]     # After invoice period
}

leases_valid_df = pd.DataFrame(leases_valid_data)
with pd.ExcelWriter(test_data_dir / "leases_valid_fixed.xlsx", engine="openpyxl") as writer:
    leases_valid_df.to_excel(writer, index=False)

print("Creating leases_invalid_fixed.xlsx (lease ends before invoice period)...")
leases_invalid_data = {
    "unit_id": ["UNIT001"],
    "tenant_name": ["Test Tenant"],
    "lease_start": ["2015-01-01"],
    "lease_end": ["2016-01-15"]     # Before Feb 2016 invoice
}

leases_invalid_df = pd.DataFrame(leases_invalid_data)
with pd.ExcelWriter(test_data_dir / "leases_invalid_fixed.xlsx", engine="openpyxl") as writer:
    leases_invalid_df.to_excel(writer, index=False)

print("Creating leases_partial_fixed.xlsx (lease starts during invoice period)...")
leases_partial_data = {
    "unit_id": ["UNIT001"],
    "tenant_name": ["Test Tenant"],
    "lease_start": ["2016-02-15"],  # Mid-February 2016
    "lease_end": ["2016-12-31"]
}

leases_partial_df = pd.DataFrame(leases_partial_data)
with pd.ExcelWriter(test_data_dir / "leases_partial_fixed.xlsx", engine="openpyxl") as writer:
    leases_partial_df.to_excel(writer, index=False)

print("All files created successfully with the correct column names!")