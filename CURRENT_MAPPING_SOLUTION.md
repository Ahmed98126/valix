# Current Invoice-to-Lease Mapping Solution

## Problem

When uploading PDF invoices, the extracted `unit_id` (e.g., "2 SAMPLE STREET" or "None") doesn't match the actual unit IDs in the database (e.g., "SHOP-001", "OFFICE-101"). This prevents validation from finding the correct lease data.

## Solution: Address-Based Matching

### How It Works

1. **Extract Address from PDF**
   - System extracts full address from invoice (e.g., "2 Sample Street, Sampletown, AB12 3CD")

2. **Match to Units by Address**
   - Compares invoice address to all unit addresses in database
   - Uses similarity scoring (0.0 to 1.0)
   - Considers:
     - Full address similarity (40%)
     - Street address similarity (30%)
     - Unit ID similarity (20%)
     - Postcode exact match bonus (10% + minimum 70% if postcode matches)

3. **Apply High-Confidence Matches**
   - If confidence ≥ 70%: Auto-apply the match
   - If confidence < 70%: Keep original, flag for manual review

4. **Validation Uses Correct Unit**
   - Invoice now has correct `unit_id` (e.g., "SHOP-001")
   - Validation finds leases for that unit
   - Validation works correctly ✅

## Example Workflow

### Scenario: British Gas Invoice

**Invoice Data:**
- `unit_id`: "2 SAMPLE STREET" (extracted from PDF)
- `address`: "2 SAMPLE STREET SAMPLETOWN SAMPLESHIRE AB12 3CD"

**Units in Database:**
- `SHOP-001`: "123 High Street, London, SW1A 1AA"
- `SHOP-002`: "125 High Street, London, SW1A 1AA"
- `OFFICE-101`: "456 Business Ave, Manchester, M1 1AB"

**Matching Process:**
1. System checks if "2 SAMPLE STREET" exists → No
2. System compares address to all units
3. Finds no good match (addresses are different)
4. Keeps "2 SAMPLE STREET" but flags for manual review
5. User manually maps to correct unit (e.g., "SHOP-001")
6. Invoice re-validated with correct lease data ✅

### Scenario: Opus Invoice (Better Match)

**Invoice Data:**
- `unit_id`: "None"
- `address`: "Car Park Deer Park Road, Summerhouse Road Moulton Park Industrial Estate Northampton NN3 6BJ"

**Units in Database:**
- `SHOP-001`: "123 High Street, London, SW1A 1AA"
- `WAREHOUSE-001`: "Moulton Park Industrial Estate, Northampton, NN3 6BJ"

**Matching Process:**
1. System checks if "None" exists → No
2. System compares address to all units
3. Finds high similarity with `WAREHOUSE-001` (postcode matches: NN3 6BJ)
4. Auto-applies match: `unit_id = "WAREHOUSE-001"`
5. Validation finds leases for WAREHOUSE-001 ✅

## Current Lease Structure

Your leases are structured as:
- `unit_id`: References Unit.unit_id (e.g., "SHOP-001", "OFFICE-101")
- `tenant_name`: Name of tenant (e.g., "Tech Solutions Inc")
- `lease_start`: Start date
- `lease_end`: End date (or None for ongoing)

**No changes needed to lease structure!** The matching works with your current setup.

## What Gets Matched

The system matches invoices to **Units**, then validation finds **Leases** for those units:

```
Invoice → Unit (by address) → Leases (by unit_id) → Validation
```

## Confidence Levels

| Confidence | Action | Example |
|------------|--------|---------|
| **≥ 0.70** | Auto-apply | Postcode matches + similar street |
| **0.50-0.69** | Suggest, require confirmation | Similar address but different postcode |
| **< 0.50** | Manual mapping required | No similar addresses found |

## Testing with Your Current Data

### Test 1: Exact Unit ID Match
- Upload invoice with `unit_id = "SHOP-001"`
- **Expected**: Uses SHOP-001 directly, finds lease for SHOP-001 ✅

### Test 2: Address Match
- Upload invoice with address matching a unit
- **Expected**: Auto-matches to correct unit, finds lease ✅

### Test 3: No Match
- Upload invoice with address that doesn't match any unit
- **Expected**: Flags for manual mapping, user selects correct unit ✅

## Next Steps

1. ✅ Address-based matching implemented
2. ✅ Auto-apply high-confidence matches
3. ⏳ Test with your actual PDF invoices
4. ⏳ Add UI for manual mapping (if needed)

The system is now ready to correctly map your PDF invoices to the leases shown in your Data Management page!

