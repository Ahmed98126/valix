# Invoice-to-Unit Matching Guide

## Problem Statement

When invoices are uploaded (especially from PDFs), the extracted `unit_id` may not match the actual unit IDs in the database. For example:
- Invoice has: `unit_id = "2 SAMPLE STREET"` (extracted from address)
- Database has: `unit_id = "SHOP-001"` (actual unit identifier)

This causes validation to fail because the system can't find the unit or its leases.

## Solution: Multi-Layer Matching System

### Layer 1: Auto-Matching (Automatic)
- **When**: During PDF/Excel upload
- **How**: Compares invoice address to unit addresses using similarity scoring
- **Threshold**: 85% similarity = auto-match
- **Result**: Invoice unit_id automatically updated if high-confidence match found

### Layer 2: Manual Mapping (User Action Required)
- **When**: After upload, for invoices that couldn't be auto-matched
- **How**: User reviews suggested matches and selects correct unit
- **UI**: New "Unit Mapping" section in invoices page
- **Result**: User manually maps invoice to correct unit

### Layer 3: Validation Feedback
- **When**: During validation
- **How**: Validation notes show why invoice needs review
- **Result**: Clear indication that unit mapping is needed

## Implementation

### 1. Unit Matcher Module (`app/unit_matcher.py`)
- `find_matching_units()`: Finds potential unit matches by address similarity
- `auto_match_invoice_to_unit()`: Auto-matches if confidence is high (≥85%)
- `check_unit_exists()`: Verifies if unit exists in database

### 2. API Endpoints

#### Get Unit Matches for Invoice
```
GET /api/invoice/{invoice_id}/unit-matches
```
Returns list of potential unit matches with similarity scores.

#### Update Invoice Unit ID
```
PATCH /api/invoice/{invoice_id}/unit
Body: { "unit_id": "SHOP-001" }
```
Updates invoice unit_id and re-validates.

### 3. UI Components

#### Invoices Page Enhancement
- Show "Needs Mapping" badge for invoices with unmapped units
- "Map Unit" button opens modal with suggested matches
- User selects correct unit from list

#### Unit Mapping Modal
- Shows invoice details (address, unit_id)
- Lists suggested unit matches (sorted by similarity)
- Allows manual unit selection
- Updates invoice and re-validates

## Testing Approach

### Test Scenario 1: Auto-Matching Success
1. **Setup**: 
   - Unit in DB: `SHOP-001`, Address: "123 High Street, London"
   - Invoice: `unit_id = "UNKNOWN"`, Address: "123 High Street, London"

2. **Action**: Upload invoice

3. **Expected**: 
   - Auto-matched to `SHOP-001` (high similarity)
   - Invoice shows correct unit_id
   - Validation works correctly

### Test Scenario 2: Manual Mapping Required
1. **Setup**:
   - Unit in DB: `SHOP-001`, Address: "123 High Street, London"
   - Invoice: `unit_id = "2 SAMPLE STREET"`, Address: "2 Sample Street, Sampletown"

2. **Action**: Upload invoice, then manually map

3. **Expected**:
   - Auto-match fails (low similarity)
   - Invoice shows "Needs Mapping" badge
   - User clicks "Map Unit"
   - Modal shows suggested matches
   - User selects `SHOP-001`
   - Invoice updated and re-validated

### Test Scenario 3: No Match Found
1. **Setup**:
   - No units in database
   - Invoice: `unit_id = "UNKNOWN"`

2. **Action**: Upload invoice

3. **Expected**:
   - Auto-match fails (no units)
   - Invoice shows "Needs Mapping" badge
   - Validation shows "Needs Review" with note: "Unit not found"

## Workflow

```
1. User uploads invoice (PDF/Excel)
   ↓
2. System extracts unit_id and address
   ↓
3. System checks if unit_id exists in database
   ├─ YES → Use as-is
   └─ NO → Try auto-matching by address
       ├─ High confidence match (≥85%) → Auto-update unit_id
       └─ Low confidence or no match → Leave as-is, mark for manual mapping
   ↓
4. Validation runs
   ├─ Unit found → Normal validation
   └─ Unit not found → "Needs Review" with note
   ↓
5. User reviews invoices
   ├─ Auto-matched correctly → No action needed
   └─ Needs mapping → User manually maps to correct unit
       ↓
       Invoice re-validated with correct unit
```

## Next Steps

1. ✅ Create unit matcher module
2. ✅ Integrate auto-matching into PDF upload
3. ⏳ Add API endpoints for unit matching
4. ⏳ Add UI for manual unit mapping
5. ⏳ Add "Needs Mapping" badge to invoices table
6. ⏳ Test with real invoices

