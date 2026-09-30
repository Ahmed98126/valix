# Testing Guide - Validation Logic & Filtering

## Test Excel File Generated

✅ **File Created**: `test_validation_batch.xlsx` (30 invoices)

### Test Scenarios Included:

1. **TEST-OCC-* invoices** (Occupied Periods)
   - Invoices during lease periods
   - **Expected**: Status = "Valid"
   - **Expected**: Determination = "OK TO PAY" (if daily rate < £4)

2. **TEST-VAC-* invoices** (Vacancy Periods)
   - Invoices during vacancy periods
   - **Expected**: Status = "Invalid"
   - **Expected**: Determination = "COT" (Check on This)

3. **TEST-LS-* invoices** (Landlord Supply)
   - Invoices for units ending in '00' (SHOP-100)
   - **Expected**: Determination = "Landlord Supply - OK TO PAY"

4. **TEST-RATE-* invoices** (Different Daily Rates)
   - Various daily rates to test determination logic
   - **Expected**: Different determinations based on rate

## How to Test

### Step 1: Upload Test File
1. Go to `/upload` page
2. Upload `test_validation_batch.xlsx`
3. Wait for processing to complete

### Step 2: Check Results
1. Go to `/invoices` page
2. Review the validation results:
   - Check that TEST-OCC invoices show "Valid" status
   - Check that TEST-VAC invoices show "Invalid" status
   - Check that TEST-LS invoices show "Landlord Supply - OK TO PAY"
   - Check that determinations match expected logic

### Step 3: Test Filtering
1. **Filter by Status:**
   - Select "Valid" → Should show only TEST-OCC invoices
   - Select "Invalid" → Should show only TEST-VAC invoices
   - Select "Needs Review" → Should show invoices with partial overlap

2. **Filter by Determination:**
   - Select "COT" → Should show Invalid invoices
   - Select "OK TO PAY" → Should show Valid invoices with low daily rate
   - Select "Landlord Supply - OK TO PAY" → Should show TEST-LS invoices

3. **Filter by Batch:**
   - Select the test batch → Should show only test invoices

4. **Test Export:**
   - Apply filters
   - Click "Export to CSV"
   - Verify exported file matches filtered results

## Current Database State

### Units & Leases
- **4 Units**: SHOP-001, SHOP-002, OFFICE-101, SHOP-100
- **5 Leases**: Various lease periods creating occupied/vacant periods

### Unit Timeline (Vacancy Calculation)
The system automatically calculates:
- **Occupied periods**: From lease start to lease end
- **Vacancy periods**: Gaps between leases, pre-first-lease, never-leased

**Example (SHOP-002):**
- 🔴 Vacant: 2000-01-01 to 2023-12-01
- 🟢 Occupied: 2023-12-02 to 2025-09-02 (Bakery Corp)
- 🔴 Vacant: 2025-09-03 to 2025-12-30
- 🟢 Occupied: 2025-12-31 to ongoing (Tech Store Inc)

## Validation Logic Flow

1. **Duplicate Check**: invoice_number + gross_amount
2. **Calculate Invoice Days**: billing_period_end - billing_period_start + 1
3. **Calculate Daily Rate**: gross_amount / invoice_days
4. **Check Vacancy Overlap**: Query UnitTimeline for overlap days
5. **Determine Status**:
   - `total_overlap == 0` → "Invalid"
   - `total_overlap == invoice_days` → "Valid"
   - `total_overlap < invoice_days` → "Needs Review"
6. **Generate Determination**: Based on status + daily_rate + unit_id

## Filtering Implementation

### Fixed Issues:
- ✅ Filters now use proper JOIN syntax
- ✅ Status filter works correctly
- ✅ Determination filter works correctly
- ✅ Batch filter works correctly
- ✅ Export respects filters

### How It Works:
- **Status Filter**: Inner join with InvoiceValidation table
- **Determination Filter**: Inner join with InvoiceValidation table
- **Batch Filter**: Direct filter on Invoice.source_batch
- **Export**: Uses same query logic as page filters

## Expected Results Summary

After uploading `test_validation_batch.xlsx`:

| Invoice Type | Expected Status | Expected Determination | Reason |
|-------------|----------------|----------------------|--------|
| TEST-OCC-* | Valid | OK TO PAY / OK TO PAY, SUBMIT METER READING | During occupied period |
| TEST-VAC-* | Invalid | COT | During vacancy period |
| TEST-LS-* | Valid/Invalid | Landlord Supply - OK TO PAY | Unit ends in '00' |
| TEST-RATE-* | Varies | Varies by daily rate | Different rate scenarios |

## Commands

```bash
# Generate new test file
python scripts/generate_test_excel.py --output=my_test.xlsx --count=50

# Inspect database
python scripts/inspect_database.py

# Check validation results
python scripts/validate_invoices.py
```




