# Invoice-to-Unit Mapping Strategy

## Overview

This document explains the flexible, multi-strategy approach for mapping invoices to units. The system supports organization-specific configurations and multiple matching methods with priority ordering.

## Mapping Priority (Highest to Lowest)

### 1. **Exact Unit ID Match** (Highest Priority)
- **When**: Invoice has a `unit_id` that exists in the database
- **Confidence**: 100%
- **Use Case**: Organizations that consistently use unit IDs in their invoices
- **Example**: Invoice has `unit_id="SHOP-001"` and `Unit.unit_id="SHOP-001"` exists

### 2. **Account Number Mapping** (Custom Mappings)
- **When**: Organization has created custom mappings (`supplier_account_number` → `unit_id`)
- **Confidence**: 100%
- **Use Case**: 
  - Consistent account numbers that map to specific units
  - Organizations with their own internal unit identifiers
  - When address matching is unreliable
- **Example**: 
  - Account number `"1234 1234 1234"` → Unit `"UNIT-A"`
  - Managed via UI or API: `/api/invoices/{invoice_id}/unit-mappings`

### 3. **Address Similarity Matching** (Fuzzy Matching)
- **When**: Invoice has an address and no exact match found
- **Confidence**: 0-100% (based on similarity score)
- **Auto-apply Threshold**: 70% (configurable per tenant)
- **Use Case**: 
  - PDF invoices with addresses but no unit IDs
  - UK utility bills (British Gas, E.ON, Opus Energy)
- **Matching Factors**:
  - Full address similarity (40% weight)
  - Street address similarity (30% weight)
  - Unit ID similarity (20% weight)
  - Postcode exact match bonus (10% boost)
- **Example**: 
  - Invoice address: `"86 EDLESTONE ROAD, CREWE, CW8 1AB"`
  - Unit address: `"86 Edlestone Road, Crewe, CW8 1AB"`
  - Match score: 95% → Auto-assigned

### 4. **Manual Mapping** (Fallback)
- **When**: All automatic strategies fail or confidence is too low
- **Confidence**: 0%
- **Use Case**: 
  - Invoices with incomplete/incorrect addresses
  - New units not yet in database
  - Complex scenarios requiring human judgment
- **UI**: Manual mapping interface shows suggestions and allows user selection

## Implementation

### Code Structure

```
app/
├── invoice_unit_mapper.py    # Main mapping service (InvoiceUnitMapper)
├── unit_matcher.py           # Address similarity matching logic
└── models.py                 # InvoiceUnitMapping model for custom mappings
```

### Usage Example

```python
from app.invoice_unit_mapper import InvoiceUnitMapper

# Initialize mapper
mapper = InvoiceUnitMapper(session, tenant_id)

# Map an invoice
matched_unit_id, method, details = mapper.map_invoice_to_unit(
    invoice,
    extracted_unit_id="SHOP-001",
    auto_apply_threshold=0.7
)

# Result:
# - matched_unit_id: "SHOP-001" or None
# - method: "exact_match" | "account_mapping" | "address_match" | "manual_required"
# - details: Dict with confidence scores, suggestions, etc.
```

## Organization-Specific Configuration

### Custom Account Number Mappings

Organizations can create custom mappings via:

1. **API Endpoint**: `POST /api/invoices/{invoice_id}/unit-mappings`
2. **UI**: Manual mapping interface (coming soon)
3. **Bulk Import**: CSV/Excel import of mappings

**Example Mapping**:
```json
{
  "supplier_account_number": "1234 1234 1234",
  "unit_id": "UNIT-A",
  "supplier_name": "British Gas",
  "notes": "Main office electricity account"
}
```

### Tenant-Level Configuration

Future enhancements:
- Per-tenant auto-apply thresholds
- Per-tenant mapping strategy preferences
- Supplier-specific mapping rules

## Best Practices

### For Organizations

1. **Use Consistent Unit IDs**: If your invoices include unit IDs, ensure they match your database exactly
2. **Create Account Mappings**: For recurring invoices, create account number mappings to avoid repeated matching
3. **Complete Address Data**: Ensure `Units` table has complete address information (street, city, postcode)
4. **Review Low-Confidence Matches**: System flags matches below threshold for manual review

### For Developers

1. **Always Use InvoiceUnitMapper**: Don't bypass the mapper service
2. **Log Mapping Decisions**: All mapping decisions are logged with method and confidence
3. **Handle Manual Mapping**: Provide UI for users to map unmapped invoices
4. **Monitor Mapping Success**: Track mapping method distribution to identify issues

## Workflow

```
Invoice Upload
    ↓
Extract Data (PDF/Excel)
    ↓
Try Mapping (Priority Order):
    1. Exact Unit ID Match?
       ├─ Yes → Use it (100% confidence)
       └─ No → Continue
    2. Account Number Mapping?
       ├─ Yes → Use it (100% confidence)
       └─ No → Continue
    3. Address Similarity Match?
       ├─ High Confidence (≥70%) → Auto-assign
       ├─ Low Confidence (<70%) → Flag for review
       └─ No Match → Flag for manual mapping
    4. Manual Mapping Required
       └─ User selects from suggestions or creates new mapping
    ↓
Invoice Created with unit_id
    ↓
Validation Engine Runs
```

## API Endpoints

### Get Mapping Suggestions
```
GET /api/invoices/{invoice_id}/unit-matches
```
Returns potential unit matches with confidence scores.

### Create Custom Mapping
```
POST /api/invoices/{invoice_id}/unit-mappings
Body: {
  "supplier_account_number": "1234 1234 1234",
  "unit_id": "UNIT-A"
}
```

### Update Invoice Unit
```
PATCH /api/invoices/{invoice_id}/unit
Body: {
  "unit_id": "UNIT-A"
}
```

## Database Schema

### InvoiceUnitMapping Table
```sql
CREATE TABLE invoice_unit_mappings (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL,
    supplier_account_number VARCHAR NOT NULL,
    unit_id VARCHAR NOT NULL,
    supplier_name VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by_user_id INTEGER,
    notes TEXT
);
```

## Future Enhancements

1. **Machine Learning**: Learn from manual mappings to improve auto-matching
2. **Supplier-Specific Rules**: Custom extraction rules per supplier
3. **Batch Mapping**: Map multiple invoices at once
4. **Mapping History**: Track mapping changes and audit trail
5. **Confidence Thresholds**: Per-tenant configuration of auto-apply thresholds

