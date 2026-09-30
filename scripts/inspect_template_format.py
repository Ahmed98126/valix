"""
Inspect the format of the account mapping template directly from the system.
This will help us understand exactly what the system expects.
"""

import pandas as pd
import requests
import tempfile
import os
from pathlib import Path

# Create test_data directory if it doesn't exist
test_data_dir = Path("test_data")
test_data_dir.mkdir(exist_ok=True)

# Let's create a template with every possible column name variation we can think of
print("Creating template with multiple column name variations...")

# Create a DataFrame with various column name formats
df = pd.DataFrame({
    # Original format from code
    "Supplier Name": ["British Gas"],
    "Account Number": ["1234567890"],
    "Unit ID": ["SHOP-001"],
    "Notes": ["Main electricity account"],
    
    # Alternative formats
    "supplier_name": ["E.ON"],
    "supplier_account_number": ["0987654321"],
    "unit_id": ["OFFICE-101"],
    "notes": ["Office building"],
    
    # More variations
    "SupplierName": ["Thames Water"],
    "AccountNumber": ["WATER001"],
    "UnitID": ["UNIT-A5"],
    "Note": ["Water supply"],
})

# Save the template with all variations
variations_path = test_data_dir / "column_variations.xlsx"
with pd.ExcelWriter(variations_path, engine="openpyxl") as writer:
    df.to_excel(writer, index=False)

print(f"Template with variations saved to {variations_path}")

# Create a simplified E.ON mapping with just the required columns
print("Creating simplified E.ON mapping...")
eon_simple = pd.DataFrame({
    "Account Number": ["0123 4567 89"],
    "Unit ID": ["UNIT001"]
})

simple_path = test_data_dir / "eon_mapping_simple.xlsx"
with pd.ExcelWriter(simple_path, engine="openpyxl") as writer:
    eon_simple.to_excel(writer, index=False)

print(f"Simplified E.ON mapping saved to {simple_path}")

print("Done! Try importing these different templates to see which format works.")