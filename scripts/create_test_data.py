"""Create test data for E.ON invoice validation scenarios.

This script creates Excel files with the correct column names for:
1. Units
2. Leases (with different scenarios)
3. Account mappings for the E.ON invoice
"""

import pandas as pd
from pathlib import Path

# Ensure test_data directory exists
test_data_dir = Path("test_data")
test_data_dir.mkdir(exist_ok=True)

print("Creating test data files for E.ON invoice validation...")

# 1. Create units_test.xlsx with required columns
print("Creating units_test.xlsx...")
units_data = {
    "unit_id": ["UNIT001"],
    "building_name": ["Test Building"],
    "address_line_1": ["123 Test Street"],
    "city": ["Test City"],
    "postcode": ["TE1 1ST"],
    "address_line_2": ["Floor 1"]
}

units_df = pd.DataFrame(units_data)
with pd.ExcelWriter(test_data_dir / "units_test.xlsx", engine="openpyxl") as writer:
    units_df.to_excel(writer, index=False)

# 2. Create leases for different scenarios
print("Creating leases_valid.xlsx (lease covers invoice period)...")
leases_valid_data = {
    "unit_id": ["UNIT001"],
    "tenant_name": ["Test Tenant"],
    "lease_start": ["2016-01-01"],  # Before invoice period
    "lease_end": ["2016-03-31"]     # After invoice period
}

leases_valid_df = pd.DataFrame(leases_valid_data)
with pd.ExcelWriter(test_data_dir / "leases_valid.xlsx", engine="openpyxl") as writer:
    leases_valid_df.to_excel(writer, index=False)

print("Creating leases_invalid.xlsx (lease ends before invoice period)...")
leases_invalid_data = {
    "unit_id": ["UNIT001"],
    "tenant_name": ["Test Tenant"],
    "lease_start": ["2015-01-01"],
    "lease_end": ["2016-01-15"]     # Before Feb 2016 invoice
}

leases_invalid_df = pd.DataFrame(leases_invalid_data)
with pd.ExcelWriter(test_data_dir / "leases_invalid.xlsx", engine="openpyxl") as writer:
    leases_invalid_df.to_excel(writer, index=False)

print("Creating leases_partial.xlsx (lease starts during invoice period)...")
leases_partial_data = {
    "unit_id": ["UNIT001"],
    "tenant_name": ["Test Tenant"],
    "lease_start": ["2016-02-15"],  # Mid-February 2016
    "lease_end": ["2016-12-31"]
}

leases_partial_df = pd.DataFrame(leases_partial_data)
with pd.ExcelWriter(test_data_dir / "leases_partial.xlsx", engine="openpyxl") as writer:
    leases_partial_df.to_excel(writer, index=False)

# 3. Create account mapping for E.ON invoice
print("Creating account_mapping_eon.xlsx...")
mapping_data = {
    "supplier_account_number": ["0123 4567 89"],  # Account number from the E.ON invoice
    "unit_id": ["UNIT001"],
    "supplier_name": ["E.ON"],
    "notes": ["Test mapping for E.ON invoice"]
}

mapping_df = pd.DataFrame(mapping_data)
with pd.ExcelWriter(test_data_dir / "account_mapping_eon.xlsx", engine="openpyxl") as writer:
    mapping_df.to_excel(writer, index=False)

print("All test data files created successfully!")