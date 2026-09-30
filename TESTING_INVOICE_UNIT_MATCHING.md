# Testing Invoice-to-Unit Matching

## Test Setup

### Prerequisites
1. Database has units imported (e.g., SHOP-001, SHOP-002, OFFICE-101)
2. Database has leases for those units
3. PDF invoices ready to upload

### Test Data Setup

**Units in Database:**
```
SHOP-001: "123 High Street, London, SW1A 1AA"
SHOP-002: "125 High Street, London, SW1A 1AA"
OFFICE-101: "456 Business Ave, Manchester, M1 1AB"
```

**Leases in Database:**
```
SHOP-001: 2024-01-01 to 2026-12-31 (Active)
SHOP-002: 2023-06-01 to Ongoing (Active)
OFFICE-101: 2024-03-01 to 2027-03-01 (Active)
```

---

## Test Case 1: Auto-Matching Success ✅

### Scenario
Invoice has address that closely matches a unit in database.

### Steps
1. Upload PDF invoice with:
   - `unit_id`: "UNKNOWN" (extracted from PDF)
   - `address`: "123 High Street, London, SW1A 1AA"

2. **Expected Result:**
   - System auto-matches to `SHOP-001` (high similarity ≥85%)
   - Invoice `unit_id` updated to `SHOP-001`
   - Validation runs successfully
   - Status: "Invalid" (tenant liable - active lease)
   - Determination: "COT" (outgoing COT)

### Verification
- Check invoice in database: `unit_id = "SHOP-001"`
- Check validation: Status should be "Invalid" (not "Needs Review")
- Check validation_notes: Should be empty (no errors)

---

## Test Case 2: Manual Mapping Required 🔧

### Scenario
Invoice has address that partially matches units, but similarity is below auto-match threshold.

### Steps
1. Upload PDF invoice with:
   - `unit_id`: "2 SAMPLE STREET" (extracted from PDF)
   - `address`: "2 Sample Street, Sampletown, AB12 3CD"

2. **Expected Result:**
   - Auto-match fails (similarity < 85%)
   - Invoice `unit_id` remains "2 SAMPLE STREET"
   - Validation shows "Needs Review"
   - Validation notes: "Unit '2 SAMPLE STREET' not found in database"

3. **Manual Mapping:**
   - Go to Invoices page
   - Find invoice with "Needs Review" status
   - Click "Map Unit" button
   - Modal shows suggested matches:
     - SHOP-001: 45% similarity
     - SHOP-002: 42% similarity
   - User selects `SHOP-001`
   - Invoice updated and re-validated

4. **After Mapping:**
   - Invoice `unit_id` = "SHOP-001"
   - Validation status: "Invalid" (tenant liable)
   - Determination: "COT"

### Verification
- Check invoice: `unit_id` updated to `SHOP-001`
- Check validation: Status changed from "Needs Review" to "Invalid"
- Check validation_notes: Should be empty

---

## Test Case 3: No Match Found ⚠️

### Scenario
Invoice address doesn't match any units in database.

### Steps
1. Upload PDF invoice with:
   - `unit_id`: "UNKNOWN"
   - `address`: "999 Unknown Road, Nowhere, XX99 9XX"

2. **Expected Result:**
   - Auto-match fails (no similar units)
   - Invoice `unit_id` remains "UNKNOWN"
   - Validation shows "Needs Review"
   - Validation notes: "Unit 'UNKNOWN' not found in database"

3. **Manual Action Required:**
   - User must manually create unit or map to existing unit
   - Or update invoice unit_id directly

### Verification
- Check invoice: `unit_id = "UNKNOWN"`
- Check validation: Status = "Needs Review"
- Check validation_notes: Contains error message

---

## Test Case 4: Exact Unit ID Match ✅

### Scenario
Invoice has exact unit_id that exists in database.

### Steps
1. Upload PDF invoice with:
   - `unit_id`: "SHOP-001" (exact match)
   - `address`: "123 High Street, London, SW1A 1AA"

2. **Expected Result:**
   - No matching needed (unit exists)
   - Validation runs immediately
   - Status: "Invalid" (tenant liable - active lease)
   - Determination: "COT"

### Verification
- Check invoice: `unit_id = "SHOP-001"` (unchanged)
- Check validation: Status = "Invalid"
- No matching process needed

---

## Test Case 5: Unit with No Leases 🏢

### Scenario
Invoice matches to unit that has no leases (company liable).

### Steps
1. Create unit in database:
   - `unit_id`: "WAREHOUSE-001"
   - No leases for this unit

2. Upload PDF invoice with:
   - `unit_id`: "UNKNOWN"
   - `address`: "Warehouse 1, Industrial Estate, Manchester"

3. **Expected Result:**
   - Auto-matches to `WAREHOUSE-001`
   - Validation runs
   - Status: "Valid" (company liable - no leases)
   - Determination: "OK TO PAY" (company should pay)
   - Validation notes: "Unit has no leases - company liable"

### Verification
- Check invoice: `unit_id = "WAREHOUSE-001"`
- Check validation: Status = "Valid"
- Check validation_notes: "Unit has no leases - company liable"

---

## Test Case 6: Partial Lease Overlap 🔄

### Scenario
Invoice period partially overlaps with lease period.

### Steps
1. Upload invoice with:
   - `unit_id`: "SHOP-001"
   - `billing_period`: 2024-12-15 to 2025-01-15
   - Lease: 2024-01-01 to 2024-12-31 (ends Dec 31)

2. **Expected Result:**
   - Unit found: `SHOP-001`
   - Partial overlap: 17 days in lease, 15 days in vacancy
   - Status: "Needs Review" (partial liability)
   - Determination: "COT" (needs investigation)

### Verification
- Check validation: Status = "Needs Review"
- Check total_vacancy_overlap_days: Should be 15 (partial)
- Check determination: "COT"

---

## API Testing

### Test Get Unit Matches
```bash
GET /api/invoices/{invoice_id}/unit-matches
```

**Expected Response:**
```json
{
  "matches": [
    {
      "unit_id": "SHOP-001",
      "building_name": "High Street Mall",
      "address": "123 High Street, London, SW1A 1AA",
      "similarity_score": 0.92,
      "address_similarity": 0.95,
      "unit_id_similarity": 0.85
    }
  ]
}
```

### Test Update Invoice Unit
```bash
PATCH /api/invoices/{invoice_id}/unit
Body: { "unit_id": "SHOP-001" }
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Invoice unit_id updated to SHOP-001",
  "validation_status": "Invalid",
  "determination": "COT"
}
```

---

## Checklist

- [ ] Test Case 1: Auto-matching success
- [ ] Test Case 2: Manual mapping required
- [ ] Test Case 3: No match found
- [ ] Test Case 4: Exact unit ID match
- [ ] Test Case 5: Unit with no leases
- [ ] Test Case 6: Partial lease overlap
- [ ] API: Get unit matches endpoint
- [ ] API: Update invoice unit endpoint
- [ ] UI: "Map Unit" button appears for unmapped invoices
- [ ] UI: Unit mapping modal shows suggested matches
- [ ] UI: Manual mapping updates invoice and re-validates

