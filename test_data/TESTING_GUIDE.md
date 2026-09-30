# Valix MVP Testing Guide

This document provides step-by-step instructions for testing the Valix invoice validation system using the provided test data.

## Test Data Overview

The test data simulates a commercial real estate company with:
- 10 properties (units)
- Lease information for all units
- 20 utility account mappings (electricity, gas, water)
- 10 sample invoices in Excel format

## Testing Scenarios

### Scenario 1: Basic Onboarding and Excel Invoice Processing

#### Step 1: Create Account and Login
1. Register a new account
2. Verify email (if required)
3. Login to the system

#### Step 2: Import Units
1. Navigate to "Import Units" in the dashboard
2. Upload `units_template.xlsx`
3. Verify units are imported correctly

**Expected Result**: 10 units should be imported and visible in the units list.

#### Step 3: Import Leases
1. Navigate to "Import Leases" in the dashboard
2. Upload `leases_template.xlsx`
3. Verify leases are imported correctly

**Expected Result**: 10 leases should be imported. The system should generate unit timeline records.

#### Step 4: Import Account Mappings
1. Navigate to "Account Mappings" in the dashboard
2. Upload `account_mappings_template.xlsx`
3. Verify mappings are imported correctly

**Expected Result**: 20 account mappings should be imported and visible in the mappings list.

#### Step 5: Upload Excel Invoices
1. Navigate to "Upload Invoices" in the dashboard
2. Upload `sample_invoices.xlsx`
3. Verify invoices are processed

**Expected Result**: 10 invoices should be imported and validated.

#### Step 6: Check Validation Results
1. Navigate to "Invoices" in the dashboard
2. Check validation status for each invoice

**Expected Results**:
- Invoices for occupied units (UNIT001, UNIT003, UNIT005, UNIT007, UNIT008, UNIT010) should be "OK TO PAY"
- Invoices for vacant units (UNIT002, UNIT004, UNIT006, UNIT009) should be "DO NOT PAY" or "COT" depending on vacancy dates

### Scenario 2: PDF Invoice Processing

#### Step 1: Upload PDF Invoices
1. Navigate to "Upload Invoices" in the dashboard
2. Upload your PDF invoices
3. Monitor processing status

**Expected Results**:
- PDFs should be processed using Azure Document Intelligence and enhanced extraction
- Supplier-specific patterns should improve extraction accuracy
- Extracted data should be displayed for review

#### Step 2: Check Account Mapping
1. Navigate to "Invoices" in the dashboard
2. Verify if invoices were mapped to units correctly
3. Check "Unmapped Invoices" if any weren't mapped

**Expected Results**:
- Invoices with account numbers matching the mappings should be linked to units
- Invoices with unknown account numbers should appear in "Unmapped Invoices"

#### Step 3: Check Manual Review Queue
1. Navigate to "Manual Review" in the dashboard
2. Check if any invoices need manual review

**Expected Results**:
- Invoices with low confidence scores or missing fields should appear here
- You should be able to view and edit the extracted data

#### Step 4: Process Manual Reviews
1. Select an invoice in the Manual Review queue
2. Review and correct the extracted data
3. Submit for processing

**Expected Results**:
- Corrected invoice should be processed and validated
- It should appear in the main Invoices list with appropriate status

### Scenario 3: Special Cases

#### Test Case 1: Duplicate Invoice
1. Upload the same PDF invoice twice
2. Check how the system handles duplicates

**Expected Result**: Second invoice should be marked as duplicate.

#### Test Case 2: Invoice for Vacant Period
1. Upload an invoice for a period when the unit was vacant
2. Check validation result

**Expected Result**: Invoice should be marked "DO NOT PAY".

#### Test Case 3: Invoice Spanning Occupied and Vacant Periods
1. Upload an invoice with billing period spanning both occupied and vacant periods
2. Check validation result

**Expected Result**: Invoice should be marked "COT" (Change of Tenancy).

#### Test Case 4: Unknown Account Number
1. Upload an invoice with an account number not in the mappings
2. Check result

**Expected Result**: Invoice should appear in "Unmapped Invoices" queue.

## Evaluation Criteria

For each test scenario, evaluate:

1. **Functionality**: Does the feature work as expected?
2. **Usability**: Is the interface intuitive and easy to use?
3. **Performance**: Does the system respond in a reasonable time?
4. **Error Handling**: Are errors handled gracefully with clear messages?
5. **Data Integrity**: Is data stored and displayed correctly?

## Reporting Issues

For any issues found during testing, note:
1. The specific scenario and step where the issue occurred
2. Expected vs. actual behavior
3. Any error messages displayed
4. Steps to reproduce the issue

This information will be valuable for prioritizing fixes and improvements.