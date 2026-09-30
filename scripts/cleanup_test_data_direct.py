"""Clean up test data directory by directly creating the files we need.

This script will:
1. Create a backup of all existing Excel files
2. Create new files with intuitive names
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

# Create backup directory
backup_dir = test_data_dir / "old_files"
backup_dir.mkdir(exist_ok=True)

# Move all Excel files to backup except temporary Excel files
for file_path in test_data_dir.glob("*.xlsx"):
    if not file_path.name.startswith("~$"):
        try:
            # Copy to backup
            shutil.copy2(file_path, backup_dir / file_path.name)
            print(f"Backed up: {file_path.name}")
            
            # Delete original
            os.remove(file_path)
            print(f"Removed: {file_path.name}")
        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")

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

# 1. Create units template
print("Creating units template...")
units_data = {
    "unit_id": ["UNIT001", "UNIT002", "UNIT003", "UNIT004", "UNIT005"],
    "building_name": ["Main Street Office", "High Street Retail", "Market Square Office", 
                     "River Road Warehouse", "Park Lane Shop"],
    "address_line_1": ["123 Main Street", "456 High Street", "789 Market Square", 
                      "101 River Road", "202 Park Lane"],
    "city": ["London", "Manchester", "Birmingham", "Glasgow", "Edinburgh"],
    "postcode": ["SW1A 1AA", "M1 1AB", "B1 1CD", "G1 1DE", "EH1 1FG"],
    "address_line_2": ["Floor 1", "Suite 2", "Unit 3A", "Building B", "Floor 2"]
}

units_df = pd.DataFrame(units_data)
with pd.ExcelWriter(test_data_dir / "1_units_template.xlsx", engine="openpyxl") as writer:
    units_df.to_excel(writer, index=False)

# 2. Create leases template
print("Creating leases template...")
leases_data = {
    "unit_id": ["UNIT001", "UNIT002", "UNIT003", "UNIT004", "UNIT005"],
    "tenant_name": ["Acme Corporation", "Global Enterprises", "Retail Solutions Ltd", 
                   "Logistics Partners", "City Retail Group"],
    "lease_start": ["2025-01-01", "2025-06-01", "2024-09-01", "2025-03-15", "2025-05-01"],
    "lease_end": ["2026-12-31", "2027-05-31", "2026-08-31", "2027-03-14", "2026-04-30"]
}

leases_df = pd.DataFrame(leases_data)
with pd.ExcelWriter(test_data_dir / "2_leases_template.xlsx", engine="openpyxl") as writer:
    leases_df.to_excel(writer, index=False)

# 3. Create account mappings template
print("Creating account mappings template...")
mapping_data = {
    "supplier_account_number": ["BG-12345678", "EO-0123456789", "OE-AB12345678", "TW-12345", "SW-98765"],
    "unit_id": ["UNIT001", "UNIT002", "UNIT003", "UNIT004", "UNIT005"],
    "supplier_name": ["British Gas", "E.ON", "Opus Energy", "Thames Water", "Southern Water"],
    "notes": ["Electricity account", "Gas account", "Electricity account", "Water account", "Water account"]
}

mapping_df = pd.DataFrame(mapping_data)
with pd.ExcelWriter(test_data_dir / "3_account_mappings_template.xlsx", engine="openpyxl") as writer:
    mapping_df.to_excel(writer, index=False)

# 4. Create extraction patterns template (reuse existing one if possible)
print("Creating extraction patterns template...")
try:
    # Try to copy from backup if it exists
    if (backup_dir / "extraction_patterns_template.xlsx").exists():
        shutil.copy2(backup_dir / "extraction_patterns_template.xlsx", test_data_dir / "4_extraction_patterns_template.xlsx")
    else:
        # Create a simple one
        patterns_data = {
            "supplier_name": ["British Gas", "E.ON", "Opus Energy"],
            "field_name": ["supplier_account_number", "billing_period_start", "gross_amount"],
            "pattern_type": ["regex", "regex", "regex"],
            "pattern_value": ["Account:\\s*(\\d+)", "Period\\s+from\\s+(\\d{2}/\\d{2}/\\d{4})", "Total\\s+due[:\\s]*(£?\\d+\\.\\d{2})"],
            "priority": [10, 10, 10],
            "notes": ["Extract account number", "Extract billing period start date", "Extract total amount due"]
        }
        patterns_df = pd.DataFrame(patterns_data)
        with pd.ExcelWriter(test_data_dir / "4_extraction_patterns_template.xlsx", engine="openpyxl") as writer:
            patterns_df.to_excel(writer, index=False)
except Exception as e:
    print(f"Error creating extraction patterns template: {e}")

# 5. Create test units file
print("Creating test units file...")
test_units_data = {
    "unit_id": ["UNIT001"],
    "building_name": ["Test Building"],
    "address_line_1": ["123 Test Street"],
    "city": ["Test City"],
    "postcode": ["TE1 1ST"],
    "address_line_2": ["Floor 1"]
}

test_units_df = pd.DataFrame(test_units_data)
with pd.ExcelWriter(test_data_dir / "test_units.xlsx", engine="openpyxl") as writer:
    test_units_df.to_excel(writer, index=False)

# 6. Create test lease files for different scenarios
print("Creating test lease files...")
# Valid lease (covers invoice period)
leases_valid_data = {
    "unit_id": ["UNIT001"],
    "tenant_name": ["Test Tenant"],
    "lease_start": ["2016-01-01"],  # Before invoice period
    "lease_end": ["2016-03-31"]     # After invoice period
}

leases_valid_df = pd.DataFrame(leases_valid_data)
with pd.ExcelWriter(test_data_dir / "test_leases_valid.xlsx", engine="openpyxl") as writer:
    leases_valid_df.to_excel(writer, index=False)

# Invalid lease (ends before invoice period)
leases_invalid_data = {
    "unit_id": ["UNIT001"],
    "tenant_name": ["Test Tenant"],
    "lease_start": ["2015-01-01"],
    "lease_end": ["2016-01-15"]     # Before Feb 2016 invoice
}

leases_invalid_df = pd.DataFrame(leases_invalid_data)
with pd.ExcelWriter(test_data_dir / "test_leases_invalid.xlsx", engine="openpyxl") as writer:
    leases_invalid_df.to_excel(writer, index=False)

# Partial lease (starts during invoice period)
leases_partial_data = {
    "unit_id": ["UNIT001"],
    "tenant_name": ["Test Tenant"],
    "lease_start": ["2016-02-15"],  # Mid-February 2016
    "lease_end": ["2016-12-31"]
}

leases_partial_df = pd.DataFrame(leases_partial_data)
with pd.ExcelWriter(test_data_dir / "test_leases_partial.xlsx", engine="openpyxl") as writer:
    leases_partial_df.to_excel(writer, index=False)

# 7. Create E.ON test mapping file
print("Creating E.ON test mapping file...")
eon_mapping_data = {
    "supplier_account_number": ["0123 4567 89"],  # Account number from the E.ON invoice
    "unit_id": ["UNIT001"],
    "supplier_name": ["E.ON"],
    "notes": ["Test mapping for E.ON invoice"]
}

eon_mapping_df = pd.DataFrame(eon_mapping_data)
with pd.ExcelWriter(test_data_dir / "test_eon_mapping.xlsx", engine="openpyxl") as writer:
    eon_mapping_df.to_excel(writer, index=False)

# 8. Create sample invoices file (reuse existing one if possible)
print("Creating sample invoices file...")
try:
    # Try to copy from backup if it exists
    if (backup_dir / "sample_invoices.xlsx").exists():
        shutil.copy2(backup_dir / "sample_invoices.xlsx", test_data_dir / "sample_invoices.xlsx")
    else:
        # Create a simple one
        invoices_data = {
            "invoice_number": ["INV-001", "INV-002", "INV-003"],
            "supplier_account_number": ["BG-12345678", "EO-0123456789", "OE-AB12345678"],
            "supplier_name": ["British Gas", "E.ON", "Opus Energy"],
            "unit_id": ["UNIT001", "UNIT002", "UNIT003"],
            "billing_period_start": ["2026-01-01", "2026-01-01", "2026-01-01"],
            "billing_period_end": ["2026-01-31", "2026-01-31", "2026-01-31"],
            "invoice_date": ["2026-02-01", "2026-02-01", "2026-02-01"],
            "gross_amount": [100.00, 150.00, 200.00],
            "net_amount": [83.33, 125.00, 166.67],
            "vat_amount": [16.67, 25.00, 33.33],
            "utility_type": ["Electricity", "Gas", "Electricity"],
            "currency": ["GBP", "GBP", "GBP"]
        }
        invoices_df = pd.DataFrame(invoices_data)
        with pd.ExcelWriter(test_data_dir / "sample_invoices.xlsx", engine="openpyxl") as writer:
            invoices_df.to_excel(writer, index=False)
except Exception as e:
    print(f"Error creating sample invoices file: {e}")

print("Cleanup complete! Test data directory now has a cleaner organization.")