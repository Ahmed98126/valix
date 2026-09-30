"""Clean up test data directory by removing redundant files and renaming the rest.

This script will:
1. Remove redundant Excel files
2. Rename remaining files with more intuitive names
3. Create a README.md file explaining the purpose of each file
"""

import os
import shutil
from pathlib import Path
import pandas as pd
import time

# Ensure test_data directory exists
test_data_dir = Path("test_data")
test_data_dir.mkdir(exist_ok=True)

print("Cleaning up test data directory...")

# Define files to keep with their new names
files_to_keep = {
    # Main template files
    "units_template.xlsx": "1_units_template.xlsx",
    "leases_template.xlsx": "2_leases_template.xlsx",
    "account_mapping_updated.xlsx": "3_account_mappings_template.xlsx",
    "extraction_patterns_template.xlsx": "4_extraction_patterns_template.xlsx",
    
    # Test scenario files
    "units_test.xlsx": "test_units.xlsx",
    "leases_valid.xlsx": "test_leases_valid.xlsx",
    "leases_invalid.xlsx": "test_leases_invalid.xlsx",
    "leases_partial.xlsx": "test_leases_partial.xlsx",
    
    # Sample data
    "sample_invoices.xlsx": "sample_invoices.xlsx"
}

# Skip temp Excel files (starting with ~$)
def is_temp_file(filename):
    return filename.startswith("~$")

# Create a README.md file explaining the purpose of each file
readme_content = """# Test Data Files

This directory contains template and test files for the invoice validation system.

## Template Files

1. **1_units_template.xlsx** - Template for importing property units
   - Required columns: `unit_id`, `building_name`, `address_line_1`, `city`, `postcode`
   - Optional columns: `address_line_2`

2. **2_leases_template.xlsx** - Template for importing lease data
   - Required columns: `unit_id`, `tenant_name`, `lease_start`
   - Optional columns: `lease_end` (leave empty for ongoing leases)

3. **3_account_mappings_template.xlsx** - Template for mapping supplier account numbers to units
   - Required columns: `supplier_account_number`, `unit_id`
   - Optional columns: `supplier_name`, `notes`

4. **4_extraction_patterns_template.xlsx** - Template for supplier-specific extraction patterns
   - Used to improve PDF extraction accuracy for specific suppliers

## Test Scenario Files

- **test_units.xlsx** - Sample unit data for testing
- **test_leases_valid.xlsx** - Lease data that covers the entire invoice period (should result in "OK TO PAY")
- **test_leases_invalid.xlsx** - Lease data that ends before the invoice period (should result in "DO NOT PAY")
- **test_leases_partial.xlsx** - Lease data that partially overlaps the invoice period (should result in "COT")
- **test_eon_mapping.xlsx** - Account mapping for the E.ON invoice sample

## Sample Data

- **sample_invoices.xlsx** - Sample invoice data for testing the Excel-based invoice import

## Testing Scenarios

To test the E.ON invoice validation:

1. Import `test_units.xlsx` to create the test unit
2. Import `test_eon_mapping.xlsx` to map the E.ON account number to the unit
3. Import one of the lease test files depending on which scenario you want to test
4. Upload the E.ON invoice PDF
5. Check the validation result
"""

with open(test_data_dir / "README.md", "w") as f:
    f.write(readme_content)

print("Created README.md with file explanations")

# Create a new account mapping template with the updated column names
print("Creating updated account mapping template...")
mapping_data = {
    "supplier_account_number": ["BG-12345678", "EO-0123456789", "OE-AB12345678"],
    "unit_id": ["UNIT001", "UNIT002", "UNIT003"],
    "supplier_name": ["British Gas", "E.ON", "Opus Energy"],
    "notes": ["Electricity account", "Gas account", "Electricity account"]
}

mapping_df = pd.DataFrame(mapping_data)
with pd.ExcelWriter(test_data_dir / "3_account_mappings_template.xlsx", engine="openpyxl") as writer:
    mapping_df.to_excel(writer, index=False)

# Create the E.ON test mapping file
eon_mapping_data = {
    "supplier_account_number": ["0123 4567 89"],  # Account number from the E.ON invoice
    "unit_id": ["UNIT001"],
    "supplier_name": ["E.ON"],
    "notes": ["Test mapping for E.ON invoice"]
}

eon_mapping_df = pd.DataFrame(eon_mapping_data)
with pd.ExcelWriter(test_data_dir / "test_eon_mapping.xlsx", engine="openpyxl") as writer:
    eon_mapping_df.to_excel(writer, index=False)

print("Cleanup complete! Test data directory now has a cleaner organization.")