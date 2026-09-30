# Current System Status & Database Structure

## What We Currently Have

### ✅ Completed Features

1. **Authentication System**
   - User login/signup
   - Session management
   - Protected routes

2. **File Upload System**
   - Excel (.xlsx, .xls) and CSV support
   - Automatic header detection
   - Flexible column mapping
   - Duplicate prevention (checks before saving)
   - Background processing
   - Progress tracking

3. **Validation Engine**
   - Duplicate detection (invoice_number + gross_amount)
   - Vacancy overlap calculation
   - Validation status determination
   - Final determination generation
   - Daily rate calculation

4. **Web UI**
   - Dashboard with KPIs
   - Invoice list with filters
   - Upload page with drag-and-drop
   - Detailed invoice view
   - CSV export

5. **Database**
   - All historical invoices stored
   - Validation results stored
   - Unit timeline (vacancy/occupied periods)
   - Upload status tracking

## Database Structure

### Tables Overview

#### 1. **Units** (4 records)
Stores commercial property units (shops, offices, etc.)

**Fields:**
- `unit_id` (unique identifier, e.g., "SHOP-001")
- `building_name`
- `address_line_1`, `address_line_2`
- `city`, `postcode`

**Current Data:**
- SHOP-001, SHOP-002 (High Street Shopping Centre, London)
- OFFICE-101 (Business Park Tower, Manchester)
- SHOP-100 (Retail Complex, Birmingham)

#### 2. **Leases** (5 records)
Stores lease periods for units

**Fields:**
- `unit_id` (references Unit.unit_id)
- `tenant_name`
- `lease_start` (date)
- `lease_end` (date, NULL for ongoing)

**Current Data:**
- SHOP-001: Coffee Shop Ltd (2024-12-01 to ongoing)
- SHOP-002: Bakery Corp (2023-12-02 to 2025-09-02), Tech Store Inc (2025-12-31 to ongoing)
- OFFICE-101: Law Firm A (2022-12-02 to 2025-06-04), Law Firm B (2025-10-02 to ongoing)
- SHOP-100: No leases (never-leased unit)

#### 3. **UnitTimeline** (11 records)
**Derived table** showing occupied/vacant periods

**How It Works:**
- Generated from Units + Leases
- Calculates gaps between leases = vacancy periods
- Pre-first-lease periods = vacancy
- Never-leased units = ongoing vacancy

**Fields:**
- `unit_id`
- `period_start`, `period_end` (NULL = ongoing)
- `status` ('occupied' or 'vacant')
- `lease_id` (if occupied, NULL if vacant)
- `days_in_period`

**Current Timeline Example (SHOP-002):**
1. 🔴 Vacant: 2000-01-01 to 2023-12-01 (pre-first-lease)
2. 🟢 Occupied: 2023-12-02 to 2025-09-02 (Bakery Corp lease)
3. 🔴 Vacant: 2025-09-03 to 2025-12-30 (gap between leases)
4. 🟢 Occupied: 2025-12-31 to ongoing (Tech Store Inc lease)

#### 4. **Invoices** (441 records)
All historical invoices from uploads

**Fields:**
- `invoice_number`, `supplier_name`, `unit_id`
- `billing_period_start`, `billing_period_end`, `invoice_date`
- `gross_amount`, `net_amount`, `vat_amount`
- `utility_type`, `currency`
- `source_batch` (which upload batch it came from)
- `created_at`

**Current Data:**
- 441 invoices from multiple batches
- Latest batch: BATCH_20251203_190423_2b495ff2 (146 invoices)
- Units include: SBM027AP, VXH029AD, HAC028AE, LHS016AM (from your Excel file)

#### 5. **InvoiceValidation** (441 records)
Validation results for each invoice

**Fields:**
- `invoice_id` (references Invoice.id)
- `invoice_days` (days in billing period)
- `total_vacancy_overlap_days` (overlap with vacancy periods)
- `validation_status` ('Valid', 'Invalid', 'Needs Review')
- `is_duplicate` ('Yes' or 'No')
- `duplicate_batch` (which batch duplicate was found in)
- `daily_rate` (gross_amount / invoice_days)
- `determination` ('OK TO PAY', 'COT', 'DO NOT PAY', etc.)
- `validated_at`

**Current Statistics:**
- Invalid/COT: 408 invoices
- Invalid/LPI: 18 invoices
- Valid/OK TO CLAIM: 15 invoices
- Duplicates detected: 342 invoices

#### 6. **Users** (1 record)
User accounts for authentication

**Fields:**
- `email`, `hashed_password`, `full_name`
- `is_active`, `created_at`, `last_login`

## How Vacancy Calculation Works

### Step 1: Load Units and Leases
- Units define the property units
- Leases define when units were occupied

### Step 2: Generate Timeline
The `generate_unit_timeline()` function:

1. **For each unit:**
   - Gets all leases ordered by start date
   - If no leases: Creates ongoing vacancy from 2000-01-01
   - If has leases:
     - Creates occupied periods for each lease
     - Finds gaps between leases = vacancy periods
     - Pre-first-lease period = vacancy

2. **Example (SHOP-002):**
   - Lease 1: 2023-12-02 to 2025-09-02 (Bakery Corp)
   - Lease 2: 2025-12-31 to ongoing (Tech Store Inc)
   - Gap: 2025-09-03 to 2025-12-30 = **vacancy period**
   - Pre-lease: 2000-01-01 to 2023-12-01 = **vacancy period**

### Step 3: Check Invoice Overlap
When validating an invoice:
- Gets all vacancy periods for the invoice's unit_id
- Calculates overlap days between invoice period and vacancy periods
- Uses overlap to determine validation status

## Validation Logic Flow

1. **Duplicate Check**
   - Query: `invoice_number + gross_amount` already exists?
   - If yes: Mark as duplicate, skip saving

2. **Calculate Invoice Days**
   - `billing_period_end - billing_period_start + 1`

3. **Calculate Daily Rate**
   - `gross_amount / invoice_days`

4. **Check Vacancy Overlap**
   - Get vacancy periods for unit_id
   - Calculate total overlap days

5. **Determine Status**
   - `total_overlap == 0` → 'Invalid'
   - `total_overlap == invoice_days` → 'Valid'
   - `total_overlap < invoice_days` → 'Needs Review'

6. **Generate Determination**
   - Based on status + daily_rate + payment_status
   - Examples: 'OK TO PAY', 'COT', 'DO NOT PAY', etc.

## Next Steps for Stress Testing

1. **Test Large Uploads**
   - Upload 1000+ invoices
   - Measure performance
   - Check memory usage

2. **Test Duplicate Detection**
   - Upload same file multiple times
   - Verify duplicates are caught
   - Measure detection speed

3. **Test Validation Performance**
   - Validate 1000+ invoices
   - Measure timeline generation time
   - Check query performance

4. **Test Database Queries**
   - Count queries
   - Filtered queries
   - Join queries
   - Group by queries

## Commands to Inspect Database

```bash
# View database overview
python scripts/inspect_database.py

# Detailed view
python scripts/inspect_database.py --detailed

# Run stress tests
python scripts/stress_test.py --invoices=1000
```




