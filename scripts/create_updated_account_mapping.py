"""Create account mapping file with the updated column names.

Now that we've modified the source code, we need to create a new account mapping file
with the correct column names: supplier_account_number, unit_id, supplier_name, notes
"""

import pandas as pd
from pathlib import Path

# Ensure test_data directory exists
test_data_dir = Path("test_data")
test_data_dir.mkdir(exist_ok=True)

print("Creating account mapping file with updated column names...")

# Create account mapping for E.ON invoice with the new column names
mapping_data = {
    "supplier_account_number": ["0123 4567 89"],  # Account number from the E.ON invoice
    "unit_id": ["UNIT001"],
    "supplier_name": ["E.ON"],
    "notes": ["Test mapping for E.ON invoice"]
}

mapping_df = pd.DataFrame(mapping_data)
with pd.ExcelWriter(test_data_dir / "account_mapping_updated.xlsx", engine="openpyxl") as writer:
    mapping_df.to_excel(writer, index=False)

print("Account mapping file created successfully with the updated column names!")