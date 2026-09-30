# Invoice-to-Lease Mapping Flow (Current Setup)

## Current Data Structure

### Units Table (HAS Addresses) ✅
- `unit_id`: "SHOP-001", "OFFICE-101", etc.
- `address_line_1`: "123 High Street"
- `address_line_2`: (optional)
- `city`: "London"
- `postcode`: "SW1A 1AA"

### Leases Table (NO Addresses) ✅
- `unit_id`: References Unit.unit_id (e.g., "SHOP-001")
- `tenant_name`: "Coffee Shop Ltd"
- `lease_start`: 2024-01-01
- `lease_end`: 2026-12-31

### Invoices (from PDF) ✅
- `unit_id`: Usually "None" or address-like text (UK utilities don't have unit IDs)
- `address`: Full address from invoice (e.g., "123 High Street, London, SW1A 1AA")

## The Mapping Flow

```
PDF Invoice Uploaded
   ↓
Extract: unit_id = "None", address = "123 High Street, London, SW1A 1AA"
   ↓
Match Invoice Address → Unit Addresses
   ├─ Compare: "123 High Street, London, SW1A 1AA" 
   └─ To: All units in database
   ↓
Find Best Match: SHOP-001 (95% confidence)
   ├─ Unit: SHOP-001
   ├─ Address: "123 High Street, London, SW1A 1AA"
   └─ Confidence: 95% (postcode matches!)
   ↓
Auto-Apply: invoice.unit_id = "SHOP-001"
   ↓
Validation Finds Leases for "SHOP-001"
   ├─ Lease: Coffee Shop Ltd, 2024-01-01 to 2026-12-31
   └─ Validates against this lease ✅
```

## Why This Works

1. **Units have addresses** (required when importing)
   - System can match invoice addresses to unit addresses
   
2. **Leases reference units by unit_id**
   - Once we find the correct unit, we can find its leases
   
3. **No need to add addresses to leases**
   - Leases already link to units via `unit_id`
   - Units have the addresses we need for matching

## What You Need to Ensure

### 1. Units Must Have Complete Addresses

When importing units, make sure each unit has:
- ✅ `address_line_1` (required)
- ✅ `city` (required)
- ✅ `postcode` (required - very important for matching!)

**Example Unit Import:**
```
unit_id      | address_line_1      | city      | postcode
SHOP-001     | 123 High Street     | London    | SW1A 1AA
OFFICE-101   | 456 Business Ave    | Manchester| M1 1AB
```

### 2. Leases Reference Units Correctly

When importing leases, make sure:
- ✅ `unit_id` matches an existing unit
- ✅ `lease_start` and `lease_end` are correct

**Example Lease Import:**
```
unit_id      | tenant_name         | lease_start  | lease_end
SHOP-001     | Coffee Shop Ltd     | 2024-01-01   | 2026-12-31
OFFICE-101   | Tech Solutions Inc  | 2024-03-01   | 2027-03-01
```

## How Matching Works

### Step 1: Invoice Address Extraction
PDF invoice → Extracts full address:
```
"123 High Street, London, SW1A 1AA"
```

### Step 2: Compare to Unit Addresses
System compares to all units:
```
SHOP-001: "123 High Street, London, SW1A 1AA" → 100% match ✅
SHOP-002: "125 High Street, London, SW1A 1AA" → 85% match
OFFICE-101: "456 Business Ave, Manchester, M1 1AB" → 10% match
```

### Step 3: Auto-Apply High Confidence Match
If confidence ≥ 70%:
- Auto-update: `invoice.unit_id = "SHOP-001"`

### Step 4: Validation Uses Correct Lease
Validation finds leases for "SHOP-001":
- Finds: Coffee Shop Ltd, 2024-01-01 to 2026-12-31
- Validates invoice against this lease ✅

## Current Status

✅ **Units table has addresses** (required fields)
✅ **Leases table references units** (by unit_id)
✅ **Matching logic implemented** (address-based)
✅ **No changes needed to lease structure**

## What Happens When You Upload a PDF

1. **System extracts address from PDF**
   - Example: "2 SAMPLE STREET SAMPLETOWN SAMPLESHIRE AB12 3CD"

2. **System tries to match to units**
   - Compares to all unit addresses
   - Calculates similarity score

3. **If high confidence (≥70%)**
   - Auto-applies match
   - Invoice gets correct `unit_id`
   - Validation works ✅

4. **If low confidence (<70%)**
   - Keeps original `unit_id`
   - Shows "Needs Review"
   - You can manually map via API

## Testing

To verify it works:

1. **Check your units have addresses:**
   - Go to Data Management → Units
   - Verify all units have: address_line_1, city, postcode

2. **Upload a PDF invoice:**
   - System will extract address
   - Try to match to units
   - Check if `unit_id` was updated

3. **Check validation:**
   - Invoice should use correct lease data
   - Status should be correct (not "Needs Review" due to unit not found)

## Summary

**You DON'T need to add addresses to leases!** ✅

The system works like this:
- **Invoices** (have addresses) → Match to **Units** (have addresses)
- **Units** (have unit_id) → Find **Leases** (reference unit_id)
- **Validation** uses the correct lease data ✅

Just make sure your **Units have complete addresses** when importing, and the matching will work!

