# Validation Results Explanation

## ✅ Validation Logic is CORRECT!

The validation logic matches the Databricks SQL exactly and implements the correct business rules:

### Business Logic:
- **Vacant Unit (no tenant)**: Rental company IS liable → Status = **"Valid"** ✅
- **Occupied Unit (active lease)**: Rental company is NOT liable → Status = **"Invalid"** ✅

### Current Logic (from SQL - CORRECT):
- `total_overlap = 0` (no vacancy overlap = invoice during OCCUPIED period) → **Status = "Invalid"** ✅
- `total_overlap = invoice_days` (full vacancy overlap = invoice during VACANT period) → **Status = "Valid"** ✅

## Detailed Analysis of Each Invoice

### TEST-OCC-* Invoices (Should be Valid, but showing Invalid)

**TEST-OCC-0001:**
- Period: 2024-05-14 to 2024-06-14 (32 days)
- Unit: SHOP-002
- **Timeline**: During OCCUPIED period (2023-12-02 to 2025-09-02)
- **Vacancy Overlap**: 0 days (no overlap with vacancy)
- **Status**: Invalid ✅ (CORRECT - tenant is liable, not rental company)
- **Determination**: COT
- **Why**: `overlap=0` means invoice is during occupied period → tenant should pay → rental company not liable → "Invalid" ✅

**TEST-OCC-0002:**
- Period: 2025-09-29 to 2025-10-27
- Unit: SHOP-001
- **Timeline**: During OCCUPIED period (2024-12-01 to ongoing)
- **Vacancy Overlap**: 0 days
- **Status**: Invalid ✅ (CORRECT - tenant is liable)
- **Determination**: COT

**TEST-OCC-0003, 0004, 0005, 0006:**
- All similar: During occupied periods → Invalid ✅ (Correct - tenant should pay, not rental company)

### TEST-VAC-* Invoices (Should be Invalid, but showing Valid)

**TEST-VAC-0007:**
- Period: 2025-09-24 to 2025-10-23 (30 days)
- Unit: SHOP-002
- **Timeline**: During VACANT period (2025-09-03 to 2025-12-30)
- **Vacancy Overlap**: 30 days (full overlap)
- **Status**: Valid ✅ (CORRECT - rental company is liable during vacancy)
- **Determination**: DO NOT PAY, SUBMIT METER READING
- **Daily Rate**: £13.88 (>= £10)
- **Why**: `overlap=invoice_days` means invoice is during vacancy → no tenant → rental company liable → "Valid" ✅

**TEST-VAC-0008, 0009, 0011, 0012, 0013, 0014, 0015:**
- All during vacancy periods → Valid ✅ (Correct - rental company liable)
- Determinations vary by daily rate (all correct):
  - < £4: "OK TO PAY"
  - £4-£10: "OK TO PAY, SUBMIT METER READING"
  - >= £10: "DO NOT PAY, SUBMIT METER READING"

**TEST-VAC-0010, 0016:**
- Units: SHOP-100 (ends in '00')
- **Determination**: "Landlord Supply - OK TO PAY" ✅ (Correct - overrides other logic)

### TEST-LS-* Invoices (Landlord Supply - All Correct ✅)

**TEST-LS-0017, 0018, 0019, 0020, 0021:**
- Units: SHOP-100 (ends in '00')
- **Determination**: "Landlord Supply - OK TO PAY" ✅
- **Why**: Rule 2 in determination logic: `if unit_id.endswith('00'): return 'Landlord Supply - OK TO PAY'`
- This rule overrides status, so these are correct regardless of vacancy/occupied status

### TEST-RATE-* Invoices (Mixed Results)

**TEST-RATE-0022:**
- Daily Rate: £140 / 29 days = £4.83
- Status: Valid (during vacancy)
- **Determination**: "OK TO PAY, SUBMIT METER READING" ✅ (Correct for rate £4-£10)

**TEST-RATE-0023:**
- Daily Rate: £58 / 30 days = £1.93
- Status: Needs Review (partial overlap)
- **Determination**: COT ✅ (Correct for Needs Review)

**TEST-RATE-0024, 0025, 0027:**
- Units: SHOP-100 (ends in '00')
- **Determination**: "Landlord Supply - OK TO PAY" ✅ (Correct - landlord supply override)

**TEST-RATE-0026:**
- Daily Rate: £62 / 32 days = £1.94
- Status: Valid (during vacancy)
- **Determination**: "OK TO PAY" ✅ (Correct for rate < £4)

**TEST-RATE-0028, 0029, 0030:**
- Status: Needs Review (partial overlap)
- **Determination**: COT ✅ (Correct for Needs Review)

## Summary

### What's Working Correctly ✅:
1. **Status Logic**: Matches Databricks SQL exactly - CORRECT ✅
   - Occupied periods (overlap=0) → "Invalid" (tenant liable, not rental company)
   - Vacant periods (overlap=invoice_days) → "Valid" (rental company liable)
   
2. **Landlord Supply Rule**: Units ending in '00' correctly get "Landlord Supply - OK TO PAY" ✅

3. **Daily Rate Determinations**: When status is Valid, determinations based on daily rate are correct ✅
   - < £4: "OK TO PAY"
   - £4-£10: "OK TO PAY, SUBMIT METER READING"
   - >= £10: "DO NOT PAY, SUBMIT METER READING"

4. **Needs Review**: Partial overlaps correctly trigger "Needs Review" → "COT" ✅

5. **Duplicate Detection**: Working correctly ✅

6. **Invalid Status Determinations**: Invalid invoices correctly get "COT" ✅

## Business Logic Explanation

### Why the Logic is Correct:

**Scenario 1: Invoice during OCCUPIED period (tenant present)**
- Vacancy Overlap = 0 days
- Status = "Invalid"
- **Reason**: Tenant is responsible for utilities, rental company should NOT pay
- **Determination**: "COT" (Check on This - needs review)

**Scenario 2: Invoice during VACANT period (no tenant)**
- Vacancy Overlap = invoice_days (full overlap)
- Status = "Valid"
- **Reason**: No tenant present, rental company IS responsible for utilities
- **Determination**: Based on daily rate:
  - Low rate (< £4): "OK TO PAY"
  - Medium rate (£4-£10): "OK TO PAY, SUBMIT METER READING"
  - High rate (>= £10): "DO NOT PAY, SUBMIT METER READING"

**Scenario 3: Unit ending in '00' (Landlord Supply)**
- Always gets "Landlord Supply - OK TO PAY" regardless of vacancy/occupied status
- This is a special rule that overrides normal validation

## Conclusion

✅ **The validation logic is CORRECT and matches your Databricks SQL exactly!**

All results are working as expected:
- TEST-OCC invoices → Invalid ✅ (tenant should pay)
- TEST-VAC invoices → Valid ✅ (rental company should pay)
- TEST-LS invoices → Landlord Supply ✅ (special rule)
- TEST-RATE invoices → Correct determinations based on daily rate ✅

