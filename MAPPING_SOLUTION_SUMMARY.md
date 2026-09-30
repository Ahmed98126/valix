# Invoice-to-Unit Mapping Solution Summary

## Problem Statement

Different organizations have different ways to map invoices to units:
- Some use consistent unit IDs in invoices
- Some rely on account numbers
- Some need address-based matching (especially for PDF invoices)
- Some require manual mapping

**Question**: "Is there a standard way to align invoices to units? What would you suggest is best?"

## Solution: Flexible Multi-Strategy Mapping System

We've implemented a **priority-based mapping system** that supports multiple strategies and organization-specific configurations.

## Key Features

### 1. **Four Mapping Strategies** (Priority Order)

1. **Exact Unit ID Match** (Highest Priority)
   - If invoice has `unit_id` and it exists in database → Use it (100% confidence)

2. **Account Number Mapping** (Custom Mappings)
   - Organizations can create custom mappings: `supplier_account_number` → `unit_id`
   - Perfect for recurring invoices with consistent account numbers
   - Managed via API/UI

3. **Address Similarity Matching** (Fuzzy Matching)
   - Compares invoice address with unit addresses
   - Uses weighted scoring (address, street, postcode, unit_id similarity)
   - Auto-applies if confidence ≥ 70% (configurable)

4. **Manual Mapping** (Fallback)
   - When all automatic strategies fail
   - UI shows suggestions for user to select

### 2. **Organization-Specific Configuration**

- **Custom Account Mappings**: Each tenant can create their own mappings
- **Configurable Thresholds**: Auto-apply threshold per tenant (default: 70%)
- **Mapping History**: Track who created mappings and when

### 3. **Benefits**

✅ **Flexible**: Supports different organizational needs  
✅ **Scalable**: Handles thousands of invoices efficiently  
✅ **Accurate**: Multiple strategies ensure best match  
✅ **Auditable**: All mapping decisions logged  
✅ **User-Friendly**: Manual mapping UI with suggestions  

## Implementation

### New Files Created

1. **`app/invoice_unit_mapper.py`**
   - `InvoiceUnitMapper` class: Main mapping service
   - Implements all 4 strategies with priority ordering

2. **`app/models.py`** (Updated)
   - `InvoiceUnitMapping` model: Stores custom account number mappings

3. **`migrations/add_invoice_unit_mappings_table.sql`**
   - Database migration for custom mappings table

4. **`INVOICE_UNIT_MAPPING_STRATEGY.md`**
   - Complete documentation of the mapping system

### Code Changes

- **`main.py`**: Updated PDF processing to use `InvoiceUnitMapper`
- **`main.py`**: Fixed IndexError bug in mapping logic
- Excel/CSV processing: Can be updated similarly (currently uses provided unit_id)

## Usage Example

```python
from app.invoice_unit_mapper import InvoiceUnitMapper

# Initialize mapper
mapper = InvoiceUnitMapper(session, tenant_id)

# Map an invoice (tries all strategies in priority order)
matched_unit_id, method, details = mapper.map_invoice_to_unit(
    invoice,
    extracted_unit_id="SHOP-001",
    auto_apply_threshold=0.7
)

# Result:
# - matched_unit_id: "SHOP-001" or None
# - method: "exact_match" | "account_mapping" | "address_match" | "manual_required"
# - details: Dict with confidence, suggestions, etc.
```

## Recommended Approach for Organizations

### For Organizations with Consistent Unit IDs
1. Ensure invoices include unit IDs that match your database
2. System will use exact match (Strategy 1) - fastest and most reliable

### For Organizations with Account Numbers
1. Create account number mappings for recurring invoices
2. System will use account mapping (Strategy 2) - 100% accurate
3. Example: `"1234 1234 1234"` → `"UNIT-A"`

### For Organizations with PDF Invoices (UK Utilities)
1. Ensure `Units` table has complete address data
2. System will use address matching (Strategy 3) - handles variations
3. Review low-confidence matches (<70%) manually

### For Complex Scenarios
1. Use manual mapping UI (Strategy 4)
2. System provides suggestions based on address similarity
3. User selects correct unit or creates new mapping

## Next Steps

1. ✅ **Fixed**: IndexError bug in mapping logic
2. ✅ **Created**: InvoiceUnitMapper service
3. ✅ **Created**: InvoiceUnitMapping model and migration
4. ⏳ **Pending**: API endpoints for managing custom mappings
5. ⏳ **Pending**: UI for manual mapping and mapping management
6. ⏳ **Pending**: Update Excel/CSV processing to use mapper (optional)

## Testing

Test the mapping system with:
1. Invoice with exact unit_id match
2. Invoice with account number mapping
3. Invoice with address (no unit_id)
4. Invoice with no match (manual required)

## Documentation

See `INVOICE_UNIT_MAPPING_STRATEGY.md` for complete technical documentation.

