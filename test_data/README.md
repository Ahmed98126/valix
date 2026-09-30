# Test Data Files

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
