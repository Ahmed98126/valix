# Test Data Fixtures

This directory contains test data files for E2E testing.

## Files

- **test_units.xlsx** - Sample units/properties data
- **test_leases.xlsx** - Sample lease data
- **test_invoices.xlsx** - Sample invoice data (Excel format)
- **test_invoices.csv** - Sample invoice data (CSV format)
- **invalid.txt** - Invalid file for error handling tests
- **test_invoice.pdf** - Sample PDF invoice (if available)

## Creating Test Data

Run the fixture creation script:

```bash
python tests/fixtures/create_test_data.py
```

This will create all necessary test files.

## Test Data Structure

### Units (`test_units.xlsx`)
- unit_id: Unique identifier (e.g., "SHOP-001")
- building_name: Building name
- address_line_1: Street address
- address_line_2: Additional address info (optional)
- city: City name
- postcode: UK postcode

### Leases (`test_leases.xlsx`)
- unit_id: References unit
- tenant_name: Tenant company name
- lease_start: Lease start date (YYYY-MM-DD)
- lease_end: Lease end date (YYYY-MM-DD)

### Invoices (`test_invoices.xlsx` / `test_invoices.csv`)
- invoice_number: Unique invoice number
- supplier_account_number: Supplier account number (REQUIRED)
- supplier_name: Supplier company name
- unit_id: References unit
- billing_period_start: Billing period start (YYYY-MM-DD)
- billing_period_end: Billing period end (YYYY-MM-DD)
- gross_amount: Invoice amount (decimal)
- utility_type: Type of utility (e.g., "Electricity")
- invoice_date: Invoice date (YYYY-MM-DD, optional)

## Notes

- All dates are in YYYY-MM-DD format
- All amounts are in GBP (decimal format)
- supplier_account_number is REQUIRED and must be different from invoice_number
- Unit IDs must match between units, leases, and invoices files

