# How Invoice-to-Lease Mapping Works (Current Setup)

## Your Current Lease Structure

From your Data Management page, your leases have:
- **UNIT ID**: e.g., "SHOP-001", "OFFICE-101", "SHOP-002", "SHOP-003"
- **TENANT NAME**: e.g., "Tech Solutions Inc", "Coffee Shop Ltd"
- **START DATE**: e.g., "2024-03-01"
- **END DATE**: e.g., "2027-03-01" or "Ongoing"

**No changes needed to your lease structure!** ✅

## The Problem

When you upload a PDF invoice:
- System extracts `unit_id` from PDF (e.g., "2 SAMPLE STREET" or "None")
- This doesn't match your actual unit IDs ("SHOP-001", etc.)
- Validation can't find the correct lease → Shows "Needs Review"

## The Solution: Address-Based Matching

### Step-by-Step Process

```
1. PDF Invoice Uploaded
   ↓
2. System Extracts:
   - unit_id: "2 SAMPLE STREET" (or "None")
   - address: "2 SAMPLE STREET SAMPLETOWN SAMPLESHIRE AB12 3CD"
   ↓
3. System Checks:
   - Does "2 SAMPLE STREET" exist in Units table? → NO
   ↓
4. System Tries Address Matching:
   - Compares invoice address to all unit addresses
   - Finds best match by similarity
   ↓
5. If High Confidence (≥70%):
   - Auto-applies match: unit_id = "SHOP-001" ✅
   ↓
6. Validation Runs:
   - Finds leases for "SHOP-001"
   - Validates against those leases ✅
```

## How Matching Works

### Matching Algorithm

The system compares:
1. **Full Address** (40% weight): "2 Sample Street, Sampletown, AB12 3CD" vs "123 High Street, London, SW1A 1AA"
2. **Street Address** (30% weight): "2 Sample Street" vs "123 High Street"
3. **Unit ID** (20% weight): "2 SAMPLE STREET" vs "SHOP-001"
4. **Postcode Match** (10% bonus): "AB12 3CD" vs "SW1A 1AA" (exact match = +20% boost)

### Confidence Levels

| Confidence | Action | What Happens |
|------------|--------|--------------|
| **≥ 0.70** | Auto-apply | Invoice unit_id updated automatically ✅ |
| **0.50-0.69** | Suggest | Kept for manual review, but shows suggestions |
| **< 0.50** | Manual | Requires manual mapping |

## Real Example with Your Data

### Scenario: Invoice for SHOP-001

**Invoice from PDF:**
- `unit_id`: "None" (not found in PDF)
- `address`: "123 High Street, London, SW1A 1AA"

**Your Units:**
- `SHOP-001`: "123 High Street, London, SW1A 1AA"

**Matching Process:**
1. System checks "None" → Doesn't exist
2. System compares addresses:
   - Full address: 100% match ✅
   - Postcode: Exact match ✅
   - Confidence: **95%** ✅
3. **Auto-applies**: `unit_id = "SHOP-001"`
4. Validation finds lease for SHOP-001:
   - Coffee Shop Ltd, 2024-01-01 to 2026-12-31
5. **Validation works correctly!** ✅

## What You Need to Do

### 1. Ensure Units Have Complete Addresses

Make sure your units in the database have:
- `address_line_1`: Street address
- `city`: City name
- `postcode`: Postcode (important for matching!)

**Example:**
```
SHOP-001:
  address_line_1: "123 High Street"
  city: "London"
  postcode: "SW1A 1AA"
```

### 2. Upload PDF Invoices

The system will:
- Extract address from PDF
- Match to your units automatically
- Use correct lease data for validation

### 3. Review Unmapped Invoices

If an invoice can't be auto-matched:
- It will show "Needs Review" status
- You can manually map it using the API:
  ```
  PATCH /api/invoices/{invoice_id}/unit
  Body: { "unit_id": "SHOP-001" }
  ```

## Testing

To test if mapping works:

1. **Check your units have addresses:**
   - Go to Data Management → Units
   - Verify all units have complete addresses

2. **Upload a PDF invoice:**
   - System will try to match automatically
   - Check the invoice in the Invoices page
   - If `unit_id` matches one of your units → Success! ✅

3. **Check validation:**
   - Invoice should show correct status
   - Should use the correct lease data

## Current Status

✅ **Address-based matching implemented**
✅ **Auto-apply high-confidence matches (≥70%)**
✅ **Works with your current lease structure**
✅ **No changes needed to lease data**

**Ready to test!** Upload your PDF invoices and the system will automatically match them to your units and leases.

