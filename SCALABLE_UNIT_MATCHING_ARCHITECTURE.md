# Scalable Unit Matching Architecture

## Problem Statement

At scale, with multiple invoices and external data sources, we need:
1. **Bulk Processing**: Match hundreds/thousands of invoices efficiently
2. **External Data Integration**: Connect to client's leasing data (API, database, file)
3. **Reliable Mapping**: Ensure invoices map to correct units even when IDs don't match
4. **Review Workflow**: Handle cases where auto-matching fails
5. **Audit Trail**: Track all mappings for compliance

---

## Architecture Overview

### Multi-Layer Matching Strategy

```
Layer 1: Exact Match (Fastest)
├─ Invoice unit_id exists in database?
└─ YES → Use as-is ✅

Layer 2: Mapping Rules (Fast, Configurable)
├─ Check tenant's custom mapping rules
├─ Pattern matching (e.g., "2 SAMPLE STREET" → "SHOP-001")
└─ YES → Apply rule ✅

Layer 3: Auto-Matching (Smart, Address-Based)
├─ Compare invoice address to unit addresses
├─ Calculate similarity score
├─ High confidence (≥85%) → Auto-match ✅
└─ Low confidence → Queue for review ⚠️

Layer 4: Manual Review (Human-in-the-Loop)
├─ Show suggested matches
├─ User selects correct unit
└─ Save as new mapping rule for future ✅
```

---

## Components

### 1. Unit Mapping Rules (`app/unit_mapping_config.py`)

**Purpose**: Store tenant-specific mapping rules

**Storage**: `Tenant.column_mapping_config` (JSON)
```json
{
  "unit_mappings": [
    {
      "source": "2 SAMPLE STREET",
      "target": "SHOP-001",
      "confidence": 1.0,
      "created_at": "2025-01-01T00:00:00"
    }
  ]
}
```

**Benefits**:
- Learn from manual mappings
- Handle recurring patterns
- Tenant-specific rules

### 2. Batch Unit Matcher (`app/batch_unit_matcher.py`)

**Purpose**: Efficiently match multiple invoices

**Features**:
- Pre-loads all units (single query)
- Processes invoices in batch
- Returns statistics and review queue

**Performance**:
- O(n*m) where n=invoices, m=units
- Optimized with pre-loading
- Can process 1000+ invoices in seconds

### 3. External Data Source Integration

**Options**:

#### Option A: API Integration
```python
# app/external_data_sync.py
def sync_units_from_api(tenant_id: int, api_endpoint: str, api_key: str):
    """Sync units from external API."""
    response = requests.get(api_endpoint, headers={"Authorization": f"Bearer {api_key}"})
    units_data = response.json()
    
    for unit_data in units_data:
        # Create/update unit in database
        unit = Unit(
            tenant_id=tenant_id,
            unit_id=unit_data["unit_id"],
            address_line_1=unit_data["address"],
            # ...
        )
        session.merge(unit)
```

#### Option B: Database Connection
```python
# app/external_data_sync.py
def sync_units_from_external_db(tenant_id: int, connection_string: str):
    """Sync units from external database."""
    external_db = create_engine(connection_string)
    
    with external_db.connect() as conn:
        units = conn.execute("SELECT * FROM units WHERE tenant_id = ?", tenant_id)
        
        for unit_row in units:
            # Map external schema to internal schema
            unit = Unit(
                tenant_id=tenant_id,
                unit_id=unit_row["external_unit_id"],
                # ...
            )
            session.merge(unit)
```

#### Option C: File Import (CSV/Excel)
```python
# Already implemented in main.py
@app.post("/api/import/units")
async def import_units(...):
    # Handles CSV/Excel import
    # Can be scheduled for regular sync
```

---

## Workflow: Invoice Processing at Scale

### Step 1: Data Synchronization (Background Job)

```python
# Scheduled job (e.g., daily at 2 AM)
def sync_tenant_data(tenant_id: int):
    """Sync units and leases from external source."""
    tenant = get_tenant(tenant_id)
    
    if tenant.external_data_source_type == "api":
        sync_units_from_api(tenant_id, tenant.api_endpoint, tenant.api_key)
        sync_leases_from_api(tenant_id, tenant.api_endpoint, tenant.api_key)
    elif tenant.external_data_source_type == "database":
        sync_units_from_external_db(tenant_id, tenant.db_connection_string)
        sync_leases_from_external_db(tenant_id, tenant.db_connection_string)
    
    # Regenerate unit timeline after sync
    generate_unit_timeline(session, tenant_id=tenant_id)
```

### Step 2: Invoice Upload (Bulk Processing)

```python
# When client uploads 1000 invoices
def process_bulk_invoice_upload(batch_id: str, tenant_id: int):
    # 1. Load all invoices from batch
    invoices = session.query(Invoice).filter(
        Invoice.source_batch == batch_id,
        Invoice.tenant_id == tenant_id
    ).all()
    
    # 2. Batch match to units
    match_result = batch_match_invoices_to_units(
        session, invoices, tenant_id,
        auto_apply_threshold=0.85,
        rule_priority=True
    )
    
    # 3. Log results
    logger.info(f"Batch {batch_id}: {match_result.auto_matched} auto-matched, "
                f"{match_result.rule_matched} rule-matched, "
                f"{match_result.needs_review} need review")
    
    # 4. Validate matched invoices
    for match in match_result.matches:
        if match["method"] != "needs_review":
            invoice = session.query(Invoice).get(match["invoice_id"])
            validate_invoice(session, invoice)
    
    # 5. Return review queue
    return {
        "auto_matched": match_result.auto_matched,
        "needs_review": get_invoices_needing_review(session, tenant_id, limit=100)
    }
```

### Step 3: Review Queue (Manual Mapping)

```python
# UI shows invoices needing review
@app.get("/api/invoices/needing-review")
async def get_invoices_needing_review(...):
    """Get invoices that need unit mapping."""
    return get_invoices_needing_review(session, tenant_id, limit=100)

# User maps invoice to unit
@app.patch("/api/invoices/{invoice_id}/unit")
async def update_invoice_unit(...):
    # Update invoice
    # Save as mapping rule for future
    save_unit_mapping_rule(session, tenant_id, old_unit_id, new_unit_id)
    # Re-validate
    validate_invoice(session, invoice)
```

---

## Configuration: External Data Sources

### Tenant Configuration Schema

```json
{
  "external_data_source": {
    "type": "api|database|file|none",
    "api_endpoint": "https://client-api.example.com/units",
    "api_key": "***",
    "sync_schedule": "daily|weekly|manual",
    "last_sync": "2025-01-01T00:00:00"
  },
  "unit_mappings": [
    {
      "source": "2 SAMPLE STREET",
      "target": "SHOP-001",
      "confidence": 1.0
    }
  ]
}
```

### UI for Configuration

**Settings Page** → **Data Sources**:
- External API configuration
- Database connection (encrypted)
- Sync schedule
- Manual sync button
- View mapping rules
- Add/edit mapping rules

---

## Performance Optimization

### 1. Pre-loading Units
```python
# Instead of querying per invoice
units = session.query(Unit).filter(Unit.tenant_id == tenant_id).all()
unit_dict = {unit.unit_id: unit for unit in units}

# Use in-memory dict for matching
for invoice in invoices:
    if invoice.unit_id in unit_dict:
        # Fast lookup
```

### 2. Batch Database Operations
```python
# Instead of committing per invoice
for invoice in invoices:
    invoice.unit_id = matched_unit_id
    session.commit()  # ❌ Slow

# Batch commit
for invoice in invoices:
    invoice.unit_id = matched_unit_id
session.commit()  # ✅ Fast
```

### 3. Caching Mapping Rules
```python
# Cache rules in memory for batch processing
rules_cache = get_unit_mapping_rules(session, tenant_id)
# Use cached rules for all invoices in batch
```

---

## Testing at Scale

### Test Scenario: 1000 Invoices

```python
# Generate test data
invoices = generate_test_invoices(1000)

# Measure performance
import time
start = time.time()
result = batch_match_invoices_to_units(session, invoices, tenant_id)
duration = time.time() - start

# Expected: < 10 seconds for 1000 invoices
assert duration < 10.0
assert result.auto_matched + result.rule_matched > 800  # 80%+ success rate
```

---

## Monitoring & Analytics

### Metrics to Track

1. **Auto-Match Rate**: % of invoices auto-matched successfully
2. **Review Queue Size**: Number of invoices needing manual review
3. **Mapping Rule Usage**: How often rules are applied
4. **Sync Success Rate**: External data sync reliability
5. **Validation Accuracy**: % of correctly validated invoices

### Dashboard

```
Unit Matching Dashboard
├─ Today's Stats
│  ├─ Invoices Processed: 1,234
│  ├─ Auto-Matched: 987 (80%)
│  ├─ Rule-Matched: 123 (10%)
│  └─ Needs Review: 124 (10%)
├─ Review Queue: 45 invoices
└─ Mapping Rules: 234 active rules
```

---

## Next Steps

1. ✅ Create batch unit matcher
2. ✅ Create mapping rules system
3. ⏳ Add external data source sync
4. ⏳ Add review queue UI
5. ⏳ Add mapping rules UI
6. ⏳ Add monitoring dashboard
7. ⏳ Performance testing with large batches

