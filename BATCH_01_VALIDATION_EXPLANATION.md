# Test Batch 01 - Validation Results Explanation

## Understanding the Validation Logic

### Key Concepts:

1. **Status = "Invalid"**: Invoice period has NO overlap with vacancy (0 days) → Tenant is liable
2. **Status = "Valid"**: Invoice period FULLY overlaps with vacancy (all days) → Landlord is liable
3. **Status = "Needs Review"**: Invoice period PARTIALLY overlaps with vacancy → Needs manual review

### Determination Rules (Priority Order):

1. **Unit ends in '00'** → Always "Landlord Supply - OK TO PAY" (overrides everything)
2. **Valid + Daily Rate < £4** → "OK TO PAY"
3. **Valid + Daily Rate £4-£10** → "OK TO PAY, SUBMIT METER READING"
4. **Valid + Daily Rate >= £10** → "DO NOT PAY, SUBMIT METER READING"
5. **Invalid or Needs Review** → "COT" (Check on This)

---

## Detailed Invoice Analysis

### TEST-OCC-* Invoices (Occupied Period Invoices)

These invoices are **intentionally** placed during **occupied periods** (when tenant is present).

**Expected Result**: Status = "Invalid" (tenant liable, not landlord)

#### Examples:

**TEST-OCC-0001**: CITY-000, 2025-08-16 to 2025-09-15, £270.88
- **Status**: Invalid ✅ (during occupied period)
- **Determination**: "Landlord Supply - OK TO PAY" ✅
- **Why**: Unit CITY-000 ends in '00', so determination overrides to "Landlord Supply - OK TO PAY"
- **Logic**: Even though status is Invalid, the unit ending in '00' rule takes priority

**TEST-OCC-0003**: INDUSTRIAL-021, 2025-07-21 to 2025-08-21, £421.57
- **Status**: Invalid ✅ (during occupied period)
- **Determination**: "COT" ✅
- **Why**: Invalid status + Unpaid → "COT" (Check on This)
- **Daily Rate**: £421.57 / 31 days = ~£13.60/day (but status is Invalid, so doesn't matter)

**TEST-OCC-0009**: HIGH-003, 2025-06-26 to 2025-07-27, £328.56
- **Status**: Invalid ✅ (during occupied period)
- **Determination**: "COT" ✅
- **Why**: Invalid status → "COT"
- **Note**: HIGH-003 has an active lease (Coffee Shop Ltd from 2023-03-07 ongoing)

---

### TEST-VAC-* Invoices (Vacancy Period Invoices)

These invoices are **intentionally** placed during **vacancy periods** (when unit is empty).

**Expected Result**: Status = "Valid" (landlord liable)

#### Examples:

**TEST-VAC-0010**: HIGH-003, 2019-04-23 to 2019-05-22, £135.35
- **Status**: Valid ✅ (during vacancy period)
- **Determination**: "OK TO PAY, SUBMIT METER READING" ✅
- **Why**: 
  - Valid status (full vacancy overlap)
  - Daily Rate: £135.35 / 29 days = ~£4.67/day
  - £4.67 is between £4-£10 → "OK TO PAY, SUBMIT METER READING"
- **Timeline**: 2019 is before any lease for HIGH-003 (first lease started 2023-03-07)

**TEST-VAC-0013**: HIGH-002, 2022-07-31 to 2022-08-29, £328.86
- **Status**: Valid ✅ (during vacancy period)
- **Determination**: "DO NOT PAY, SUBMIT METER READING" ✅
- **Why**:
  - Valid status (full vacancy overlap)
  - Daily Rate: £328.86 / 29 days = ~£11.34/day
  - £11.34 >= £10 → "DO NOT PAY, SUBMIT METER READING"
- **Timeline**: Gap between leases (Bakery Corp ended 2022-06-15, Print Shop started 2022-10-05)

**TEST-VAC-0015**: RETAIL-012, 2004-07-18 to 2004-08-17, £132.04
- **Status**: Valid ✅ (during vacancy period)
- **Determination**: "OK TO PAY, SUBMIT METER READING" ✅
- **Why**:
  - Valid status (unit never had a lease, so always vacant)
  - Daily Rate: £132.04 / 30 days = ~£4.40/day
  - £4.40 is between £4-£10 → "OK TO PAY, SUBMIT METER READING"

**TEST-VAC-0021**: INDUSTRIAL-000, 2022-04-05 to 2022-05-06, £284.70
- **Status**: Valid ✅ (during vacancy period)
- **Determination**: "Landlord Supply - OK TO PAY" ✅
- **Why**: Unit INDUSTRIAL-000 ends in '00' → "Landlord Supply - OK TO PAY" (overrides daily rate)

---

### TEST-LS-* Invoices (Landlord Supply Units)

These invoices are for units ending in '00' (Landlord Supply units).

**Expected Result**: Always "Landlord Supply - OK TO PAY" (regardless of status)

#### Examples:

**TEST-LS-0026**: RETAIL-000, 2025-10-12 to 2025-11-12, £392.44
- **Status**: Valid ✅
- **Determination**: "Landlord Supply - OK TO PAY" ✅
- **Why**: Unit RETAIL-000 ends in '00' → Always "Landlord Supply - OK TO PAY"

**TEST-LS-0027**: CITY-000, 2025-10-10 to 2025-11-07, £701.27
- **Status**: Invalid ✅ (during occupied period)
- **Determination**: "Landlord Supply - OK TO PAY" ✅
- **Why**: Unit CITY-000 ends in '00' → "Landlord Supply - OK TO PAY" (overrides Invalid status)
- **Note**: Even though status is Invalid, the '00' rule takes priority

**TEST-LS-0029**: HIGH-000, 2025-10-07 to 2025-11-05, £390.17
- **Status**: Valid ✅ (during vacancy period)
- **Determination**: "Landlord Supply - OK TO PAY" ✅
- **Why**: Unit HIGH-000 ends in '00' → "Landlord Supply - OK TO PAY"

---

### TEST-RATE-* Invoices (Daily Rate Testing)

These invoices test different daily rate scenarios.

#### Low Daily Rate (< £4):

**TEST-RATE-0038**: RETAIL-011, 2025-09-30 to 2025-10-30, £60.00
- **Status**: Valid ✅
- **Determination**: "OK TO PAY" ✅
- **Why**: 
  - Daily Rate: £60.00 / 30 days = £2.00/day
  - £2.00 < £4 → "OK TO PAY"

**TEST-RATE-0045**: INDUSTRIAL-022, 2025-09-09 to 2025-10-09, £60.00
- **Status**: Valid ✅
- **Determination**: "OK TO PAY" ✅
- **Why**: Daily Rate: £60.00 / 30 days = £2.00/day < £4

**TEST-RATE-0047**: CITY-018, 2025-09-10 to 2025-10-11, £62.00
- **Status**: Valid ✅
- **Determination**: "OK TO PAY" ✅
- **Why**: Daily Rate: £62.00 / 31 days = ~£2.00/day < £4

**TEST-RATE-0050**: CITY-017, 2025-10-24 to 2025-11-23, £60.00
- **Status**: Valid ✅
- **Determination**: "OK TO PAY" ✅
- **Why**: Daily Rate: £60.00 / 30 days = £2.00/day < £4

#### Medium Daily Rate (£4-£10):

**TEST-RATE-0042**: INDUSTRIAL-022, 2025-10-20 to 2025-11-18, £145.00
- **Status**: Valid ✅
- **Determination**: "OK TO PAY, SUBMIT METER READING" ✅
- **Why**: 
  - Daily Rate: £145.00 / 29 days = ~£5.00/day
  - £5.00 is between £4-£10 → "OK TO PAY, SUBMIT METER READING"

**TEST-RATE-0044**: HIGH-004, 2025-10-22 to 2025-11-19, £140.00
- **Status**: Valid ✅
- **Determination**: "OK TO PAY, SUBMIT METER READING" ✅
- **Why**: Daily Rate: £140.00 / 28 days = ~£5.00/day (between £4-£10)

#### High Daily Rate (>= £10):

**TEST-RATE-0033**: RETAIL-012, 2025-10-10 to 2025-11-10, £372.00
- **Status**: Valid ✅
- **Determination**: "DO NOT PAY, SUBMIT METER READING" ✅
- **Why**: 
  - Daily Rate: £372.00 / 31 days = ~£12.00/day
  - £12.00 >= £10 → "DO NOT PAY, SUBMIT METER READING"

**TEST-RATE-0035**: RETAIL-011, 2025-10-26 to 2025-11-24, £348.00
- **Status**: Valid ✅
- **Determination**: "DO NOT PAY, SUBMIT METER READING" ✅
- **Why**: Daily Rate: £348.00 / 29 days = ~£12.00/day >= £10

**TEST-RATE-0036**: BUSINESS-008, 2025-10-14 to 2025-11-12, £348.00
- **Status**: Valid ✅
- **Determination**: "DO NOT PAY, SUBMIT METER READING" ✅
- **Why**: Daily Rate: £348.00 / 29 days = ~£12.00/day >= £10

#### Invalid Status (COT):

**TEST-RATE-0031**: INDUSTRIAL-019, 2025-10-01 to 2025-10-29, £140.00
- **Status**: Invalid ✅ (during occupied period)
- **Determination**: "COT" ✅
- **Why**: Invalid status → "COT" (regardless of daily rate)
- **Note**: INDUSTRIAL-019 has active lease (Beauty Salon from 2025-01-12 ongoing)

**TEST-RATE-0032**: CITY-014, 2025-10-16 to 2025-11-13, £56.00
- **Status**: Invalid ✅ (during occupied period)
- **Determination**: "COT" ✅
- **Why**: Invalid status → "COT"
- **Note**: CITY-014 has active lease (Bookstore Inc from 2023-09-14 ongoing)

**TEST-RATE-0037**: CITY-014, 2025-09-11 to 2025-10-11, £360.00
- **Status**: Invalid ✅ (during occupied period)
- **Determination**: "COT" ✅
- **Why**: Invalid status → "COT"

#### Landlord Supply Units:

**TEST-RATE-0034**: INDUSTRIAL-000, 2025-09-05 to 2025-10-05, £150.00
- **Status**: Valid ✅
- **Determination**: "Landlord Supply - OK TO PAY" ✅
- **Why**: Unit INDUSTRIAL-000 ends in '00' → "Landlord Supply - OK TO PAY"

**TEST-RATE-0043**: INDUSTRIAL-000, 2025-08-28 to 2025-09-25, £56.00
- **Status**: Valid ✅
- **Determination**: "Landlord Supply - OK TO PAY" ✅
- **Why**: Unit INDUSTRIAL-000 ends in '00' → "Landlord Supply - OK TO PAY"

**TEST-RATE-0046**: RETAIL-000, 2025-09-11 to 2025-10-11, £150.00
- **Status**: Valid ✅
- **Determination**: "Landlord Supply - OK TO PAY" ✅
- **Why**: Unit RETAIL-000 ends in '00' → "Landlord Supply - OK TO PAY"

**TEST-RATE-0049**: HIGH-000, 2025-10-15 to 2025-11-12, £336.00
- **Status**: Valid ✅
- **Determination**: "Landlord Supply - OK TO PAY" ✅
- **Why**: Unit HIGH-000 ends in '00' → "Landlord Supply - OK TO PAY"

---

## Summary by Category

### Status Distribution:
- **Invalid**: 20 invoices (TEST-OCC-* and some TEST-RATE-* during occupied periods)
- **Valid**: 30 invoices (TEST-VAC-* and TEST-RATE-* during vacancy periods)

### Determination Distribution:
- **Landlord Supply - OK TO PAY**: 11 invoices (all units ending in '00')
- **COT**: 9 invoices (Invalid or Needs Review status)
- **OK TO PAY**: 4 invoices (Valid, Daily Rate < £4)
- **OK TO PAY, SUBMIT METER READING**: 10 invoices (Valid, Daily Rate £4-£10)
- **DO NOT PAY, SUBMIT METER READING**: 6 invoices (Valid, Daily Rate >= £10)

### Key Takeaways:

1. ✅ **TEST-OCC-* invoices correctly marked as Invalid** (tenant liable)
2. ✅ **TEST-VAC-* invoices correctly marked as Valid** (landlord liable)
3. ✅ **Units ending in '00' always get "Landlord Supply - OK TO PAY"** (overrides status)
4. ✅ **Daily rate determinations work correctly** (< £4, £4-£10, >= £10)
5. ✅ **Invalid invoices get "COT"** (Check on This)

---

## How to Verify in Database

You can check the validation details for any invoice by:

1. **Via Web UI**: Click "View" on any invoice
2. **Via Database**: 
   ```bash
   python scripts/inspect_database.py --detailed
   ```

The validation record stores:
- `invoice_days`: Total days in billing period
- `total_vacancy_overlap_days`: Days overlapping with vacancy
- `validation_status`: Valid/Invalid/Needs Review
- `daily_rate`: Gross amount / invoice days
- `determination`: Final determination

---

## Validation Logic Flow

For each invoice:

1. **Calculate Invoice Days**: billing_period_end - billing_period_start
2. **Calculate Daily Rate**: gross_amount / invoice_days
3. **Check Vacancy Overlap**: Count days that overlap with vacancy periods
4. **Determine Status**:
   - `total_overlap = 0` → Invalid (no vacancy = tenant liable)
   - `total_overlap = invoice_days` → Valid (full vacancy = landlord liable)
   - `0 < total_overlap < invoice_days` → Needs Review (partial)
5. **Generate Determination**:
   - Check if unit ends in '00' → "Landlord Supply - OK TO PAY"
   - If Valid + Daily Rate < £4 → "OK TO PAY"
   - If Valid + Daily Rate £4-£10 → "OK TO PAY, SUBMIT METER READING"
   - If Valid + Daily Rate >= £10 → "DO NOT PAY, SUBMIT METER READING"
   - If Invalid/Needs Review → "COT"

---

**All results are CORRECT and match the validation logic!** ✅


