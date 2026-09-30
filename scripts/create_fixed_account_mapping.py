"""Create account mapping file with the exact column names expected by the system.

The system expects:
- "Account Number" (not "supplier_account_number")
- "Unit ID" (not "unit_id")
- "Supplier Name" (not "supplier_name")
- "Notes" (not "notes")
"""

import pandas as pd
from pathlib import Path

# Ensure test_data directory exists
test_data_dir = Path("test_data")
test_data_dir.mkdir(exist_ok=True)

print("Creating account mapping file with correct column names...")

# Create account mapping for E.ON invoice with EXACT column names
mapping_data = {
    "Account Number": ["0123 4567 89"],  # Account number from the E.ON invoice
    "Unit ID": ["UNIT001"],
    "Supplier Name": ["E.ON"],
    "Notes": ["Test mapping for E.ON invoice"]
}

mapping_df = pd.DataFrame(mapping_data)
with pd.ExcelWriter(test_data_dir / "account_mapping_fixed.xlsx", engine="openpyxl") as writer:
    mapping_df.to_excel(writer, index=False)

print("Account mapping file created successfully with the correct column names!")