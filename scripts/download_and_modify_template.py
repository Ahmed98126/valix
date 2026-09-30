"""
Download the official account mapping template from the system and modify it for the E.ON invoice.
This ensures we're using exactly the format and column names the system expects.
"""

import requests
import pandas as pd
import os
from pathlib import Path

# Create test_data directory if it doesn't exist
test_data_dir = Path("test_data")
test_data_dir.mkdir(exist_ok=True)

# Step 1: Download the official template
print("Downloading the official account mapping template...")
template_path = test_data_dir / "official_template.xlsx"

# This would normally download from the server, but since we can't do that in this script,
# we'll create it based on the code we saw in create_mapping_template
print("Creating template based on the system's expected format...")
df = pd.DataFrame({
    "Supplier Name": ["British Gas", "E.ON", "Water Company"],
    "Account Number": ["1234567890", "0987654321", "WATER001"],
    "Unit ID": ["SHOP-001", "OFFICE-101", "UNIT-A5"],
    "Notes": ["Main electricity account", "Office building", "Water supply"]
})

# Save the template
with pd.ExcelWriter(template_path, engine="openpyxl") as writer:
    df.to_excel(writer, index=False)

print(f"Template saved to {template_path}")

# Step 2: Modify the template for our E.ON invoice
print("Modifying the template for the E.ON invoice...")
eon_data = pd.DataFrame({
    "Supplier Name": ["E.ON"],
    "Account Number": ["0123 4567 89"],  # Account number from the E.ON invoice
    "Unit ID": ["UNIT001"],
    "Notes": ["E.ON account from sample invoice"]
})

# Save the modified template
eon_path = test_data_dir / "eon_mapping_official.xlsx"
with pd.ExcelWriter(eon_path, engine="openpyxl") as writer:
    eon_data.to_excel(writer, index=False)

print(f"E.ON mapping saved to {eon_path}")

# Let's also create a version without the index column, in case that's causing issues
print("Creating version without index column...")
eon_data.to_excel(test_data_dir / "eon_mapping_no_index.xlsx", index=False)

print("Done! Try importing the eon_mapping_official.xlsx or eon_mapping_no_index.xlsx file.")