# Testing Workflow Guide

## Overview

This guide explains how to test the invoice validation system with comprehensive dummy data before moving to production.

## Understanding the Real-World Migration Phase

**In production**, clients will need to supply:
1. **Units Data**: All property units (shops, offices, etc.)
2. **Leases Data**: Historical and current lease periods for each unit

This data will be loaded once during the initial setup/migration phase, then invoices will be validated against it.

## Current Testing Setup

We've created tools to simulate this with comprehensive dummy data:

### 1. **Sample Data Generator** (`scripts/load_sample_data.py`)

Creates dummy units and leases for testing.

**Basic Portfolio** (4 units, 5 leases):
```bash
python scripts/load_sample_data.py
```

**Comprehensive Portfolio** (20+ units, 30+ leases):
```bash
python scripts/load_sample_data.py --comprehensive
```

**What it creates:**
- Units across multiple buildings
- Leases with various scenarios:
  - Active leases (ongoing)
  - Expired leases (past)
  - Future leases (upcoming)
  - Gaps between leases (vacancy periods)
  - Never-leased units (ongoing vacancy)
  - Units ending in '00' (Landlord Supply)

### 2. **Test Excel Generator** (`scripts/generate_test_excel.py`)

Creates test Excel files with invoices matching your format.

```bash
# Generate 50 invoices
python scripts/generate_test_excel.py

# Generate 100 invoices
python scripts/generate_test_excel.py --count 100

# Custom output file
python scripts/generate_test_excel.py --output my_test_batch.xlsx --count 75
```

**What it creates:**
- Invoices during occupied periods (TEST-OCC-*)
- Invoices during vacancy periods (TEST-VAC-*)
- Invoices for landlord supply units (TEST-LS-*)
- Invoices with various daily rates (TEST-RATE-*)

### 3. **Comprehensive Test Workflow** (`scripts/test_workflow.py`)

**One command to set up everything:**

```bash
# Basic setup (4 units, 3 Excel files with 50 invoices each)
python scripts/test_workflow.py

# Comprehensive setup (20+ units, 5 Excel files with 100 invoices each)
python scripts/test_workflow.py --comprehensive --excel-count 5 --invoices-per-file 100
```

This script:
1. Initializes the database
2. Loads sample units/leases
3. Generates multiple test Excel files
4. Provides step-by-step testing instructions

## Step-by-Step Testing Workflow

### Step 1: Set Up Test Data

```bash
# Option A: Use comprehensive workflow (recommended)
python scripts/test_workflow.py --comprehensive

# Option B: Manual setup
python scripts/load_sample_data.py --comprehensive
python scripts/generate_test_excel.py --count 50 --output test_batch_01.xlsx
python scripts/generate_test_excel.py --count 50 --output test_batch_02.xlsx
python scripts/generate_test_excel.py --count 50 --output test_batch_03.xlsx
```

### Step 2: Start the Web Server

```bash
python main.py
```

Server will start at: `http://localhost:8000`

### Step 3: Access the Web Interface

1. **Login** (or signup if first time)
   - Default test user: `admin@test.com` / `admin123`
   - Or create new user via signup

2. **Dashboard** (`http://localhost:8000/dashboard`)
   - View KPIs
   - See recent invoices
   - Check system status

### Step 4: Upload Test Files

1. Go to **Upload Page** (`http://localhost:8000/upload`)
2. Drag and drop test Excel files (or click to browse)
3. Watch the progress bar
4. Check for:
   - ✅ Success messages
   - ⚠️ Warnings (duplicates, missing data)
   - ❌ Errors (format issues, missing columns)

### Step 5: View and Verify Results

1. **Invoice List** (`http://localhost:8000/invoices`)
   - See all uploaded invoices
   - Use filters:
     - **Status**: Valid, Invalid, Needs Review
     - **Determination**: OK TO PAY, DO NOT PAY, COT, etc.
     - **Batch**: Filter by upload batch
   - Export filtered results to CSV

2. **Verify Validation Logic:**
   - **TEST-OCC-*** invoices → Should be **Invalid** (tenant liable)
   - **TEST-VAC-*** invoices → Should be **Valid** (landlord liable)
   - **TEST-LS-*** invoices → Should be **Landlord Supply - OK TO PAY**
   - **TEST-RATE-*** invoices → Check daily rate determinations

3. **Check Individual Invoices:**
   - Click on any invoice to see details
   - View validation breakdown
   - See vacancy overlap calculations
   - Check duplicate status

### Step 6: Test Duplicate Detection

1. Try uploading the **same file twice**
2. Should see duplicate warnings
3. Duplicates should be skipped (not saved)
4. Check duplicate batch numbers in results

### Step 7: Test Filtering and Export

1. **Filter by Status:**
   - Select "Valid" → Should show TEST-VAC-* invoices
   - Select "Invalid" → Should show TEST-OCC-* invoices

2. **Filter by Determination:**
   - Select "OK TO PAY" → Should show valid invoices with low daily rates
   - Select "COT" → Should show invalid/needs review invoices

3. **Export to CSV:**
   - Apply filters
   - Click "Export to CSV"
   - Verify exported file matches filters

## What to Validate

### ✅ Validation Logic

1. **Vacancy Overlap:**
   - Invoices during vacant periods → Valid
   - Invoices during occupied periods → Invalid
   - Partial overlap → Needs Review

2. **Determinations:**
   - Valid + Unpaid + Daily Rate < £4 → "OK TO PAY"
   - Valid + Unpaid + Daily Rate £4-£10 → "OK TO PAY, SUBMIT METER READING"
   - Valid + Unpaid + Daily Rate >= £10 → "DO NOT PAY, SUBMIT METER READING"
   - Invalid/Needs Review → "COT"
   - Unit ending in '00' → "Landlord Supply - OK TO PAY"

3. **Duplicate Detection:**
   - Same invoice_number + gross_amount → Detected as duplicate
   - Checks against all historical invoices

### ✅ System Performance

1. **File Upload:**
   - Small files (< 100 invoices) → Should process quickly
   - Large files (500+ invoices) → Should show progress, complete successfully

2. **Database:**
   - All invoices stored
   - All validation results stored
   - Unit timeline generated correctly

3. **UI Responsiveness:**
   - Filters work correctly
   - Export works
   - Navigation is smooth

## Expected Test Results

### Test File: `test_batch_01.xlsx` (50 invoices)

**Expected Distribution:**
- ~17 TEST-OCC-* invoices → Invalid (during occupied periods)
- ~17 TEST-VAC-* invoices → Valid (during vacancy periods)
- ~5 TEST-LS-* invoices → Landlord Supply - OK TO PAY
- ~11 TEST-RATE-* invoices → Various determinations based on daily rate

**Validation Checks:**
- All invoices processed
- No errors (only warnings for duplicates if re-uploaded)
- Status and determinations match expected logic
- Filters work correctly

## Troubleshooting

### No Units Found
```bash
# Reload sample data
python scripts/load_sample_data.py --comprehensive
```

### Excel File Not Uploading
- Check file format (.xlsx or .xls)
- Verify column names match expected format
- Check file size (should be < 10MB)

### Validation Results Don't Match Expected
- Check unit timeline: `python scripts/inspect_database.py`
- Verify lease periods cover invoice dates
- Check for gaps in lease data

### Duplicate Detection Not Working
- Try uploading same file twice
- Check duplicate_batch field in results
- Verify invoice_number + gross_amount match

## Next Steps After Testing

Once you're satisfied with testing:

1. **Prepare Real Data:**
   - Export Units from your system
   - Export Leases from your system
   - Format as CSV/Excel

2. **Create Import Script:**
   - Based on your data format
   - Load units and leases
   - Verify data integrity

3. **Production Deployment:**
   - Set up production environment
   - Load real data
   - Configure for client
   - Go live!

## Quick Reference

```bash
# Full testing workflow
python scripts/test_workflow.py --comprehensive

# Generate single test file
python scripts/generate_test_excel.py --count 100

# Check database
python scripts/inspect_database.py

# Start server
python main.py
```

## Questions?

- Check `QUICK_RECAP.md` for system overview
- Check `PROJECT_STATUS_AND_NEXT_STEPS.md` for current status
- Check `VALIDATION_RESULTS_EXPLANATION.md` for validation logic details


