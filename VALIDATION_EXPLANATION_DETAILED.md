# Detailed Validation Explanation - TEST-OCC-0001 & TEST-VAC-0010

## TEST-OCC-0001 Analysis

### Invoice Details:
- **Invoice Number**: TEST-OCC-0001
- **Unit ID**: SHOP-002
- **Billing Period**: 2024-05-14 to 2024-06-14 (32 days)
- **Gross Amount**: £280.96
- **Daily Rate**: £8.78/day

### Leasing Data for SHOP-002:

**Timeline Periods:**
1. 🔴 **VACANT**: 2000-01-01 to 2023-12-01 (before first lease)
2. 🟢 **OCCUPIED**: 2023-12-02 to 2025-09-02 (Bakery Corp lease)
3. 🔴 **VACANT**: 2025-09-03 to 2025-12-30 (gap between leases)
4. 🟢 **OCCUPIED**: 2025-12-31 to ONGOING (Tech Store Inc lease)

### Validation Process:

1. **Invoice Period**: 2024-05-14 to 2024-06-14
2. **Check Overlap**:
   - Period 1 (VACANT): No overlap (ends 2023-12-01, invoice starts 2024-05-14)
   - Period 2 (OCCUPIED): ✅ **OVERLAPS** - 2024-05-14 to 2024-06-14 (32 days) ← **OCCUPIED**
   - Period 3 (VACANT): No overlap (starts 2025-09-03, invoice ends 2024-06-14)
   - Period 4 (OCCUPIED): No overlap (starts 2025-12-31, invoice ends 2024-06-14)

3. **Vacancy Overlap Calculation**:
   - Total vacancy overlap: **0 days** (invoice is entirely during OCCUPIED period)

4. **Status Determination**:
   - `total_overlap = 0` → **Invalid** ✅
   - **Meaning**: Invoice is during OCCUPIED period → **Tenant is liable** (not landlord)

5. **Final Determination**:
   - Status: Invalid
   - Payment Status: Unpaid
   - **Result**: **COT** (Check on This) ✅

### ✅ Is This Correct?

**YES!** This is **100% CORRECT**:

- TEST-OCC invoices are **intentionally** placed during **occupied periods**
- The invoice period (2024-05-14 to 2024-06-14) falls entirely within the Bakery Corp lease (2023-12-02 to 2025-09-02)
- Since there's **0 days of vacancy overlap**, the status is **Invalid** (tenant liable)
- Invalid invoices get **COT** determination

---

## TEST-VAC-0010 Analysis

### Invoice Details:
- **Invoice Number**: TEST-VAC-0010
- **Unit ID**: SHOP-100 (ends in '00' = Landlord Supply)
- **Billing Period**: 2007-12-09 to 2008-01-09 (32 days)
- **Gross Amount**: £435.34
- **Daily Rate**: £13.60/day

### Leasing Data for SHOP-100:

**Timeline Periods:**
1. 🔴 **VACANT**: 2000-01-01 to ONGOING (unit never leased - always vacant)

### Validation Process:

1. **Invoice Period**: 2007-12-09 to 2008-01-09
2. **Check Overlap**:
   - Period 1 (VACANT): ✅ **OVERLAPS** - 2007-12-09 to 2008-01-09 (32 days) ← **VACANCY**

3. **Vacancy Overlap Calculation**:
   - Total vacancy overlap: **32 days** (full overlap - invoice is entirely during VACANT period)

4. **Status Determination**:
   - `total_overlap = 32 days` = `invoice_days = 32 days` → **Valid** ✅
   - **Meaning**: Invoice is during VACANT period → **Landlord is liable**

5. **Final Determination**:
   - Status: Valid
   - Unit ends in '00': **YES** (SHOP-100)
   - **Result**: **Landlord Supply - OK TO PAY** ✅
   - **Note**: The '00' rule overrides the daily rate (even though daily rate is £13.60/day, which would normally be "DO NOT PAY, SUBMIT METER READING")

### ✅ Is This Correct?

**YES!** This is **100% CORRECT**:

- TEST-VAC invoices are **intentionally** placed during **vacancy periods**
- The invoice period (2007-12-09 to 2008-01-09) falls entirely within the vacant period (unit never leased)
- Since there's **full vacancy overlap (32 days = 32 days)**, the status is **Valid** (landlord liable)
- **Special Rule**: Unit ends in '00' → Always "Landlord Supply - OK TO PAY" (overrides daily rate)

---

## Key Validation Logic Summary

### Status Logic (from Databricks SQL):

```
IF total_overlap = 0 THEN 'Invalid'        → Tenant liable
IF total_overlap = invoice_days THEN 'Valid' → Landlord liable
IF 0 < total_overlap < invoice_days THEN 'Needs Review' → Partial
```

### Determination Logic (Priority Order):

1. **Unit ends in '00'** → Always "Landlord Supply - OK TO PAY" (overrides everything)
2. **Valid + Daily Rate < £4** → "OK TO PAY"
3. **Valid + Daily Rate £4-£10** → "OK TO PAY, SUBMIT METER READING"
4. **Valid + Daily Rate >= £10** → "DO NOT PAY, SUBMIT METER READING"
5. **Invalid or Needs Review** → "COT" (Check on This)

---

## Why These Results Are Correct

### TEST-OCC-0001:
- ✅ Invoice during **occupied period** (Bakery Corp lease)
- ✅ **0 days** vacancy overlap
- ✅ Status: **Invalid** (tenant liable)
- ✅ Determination: **COT** (Check on This)

### TEST-VAC-0010:
- ✅ Invoice during **vacant period** (unit never leased)
- ✅ **32 days** vacancy overlap (full overlap)
- ✅ Status: **Valid** (landlord liable)
- ✅ Unit ends in '00' → **Landlord Supply - OK TO PAY** (overrides daily rate)

---

## Understanding the Logic

The validation logic matches your Databricks SQL exactly:

- **No vacancy overlap (0 days)** = Invoice during occupied period = **Invalid** = Tenant liable
- **Full vacancy overlap (all days)** = Invoice during vacant period = **Valid** = Landlord liable

This might seem counterintuitive at first, but it's correct:
- When unit is **occupied** → Tenant pays utilities → Invoice is **Invalid** (landlord shouldn't pay)
- When unit is **vacant** → Landlord pays utilities → Invoice is **Valid** (landlord should pay)

---

**Both results are CORRECT and match your Databricks SQL logic!** ✅


