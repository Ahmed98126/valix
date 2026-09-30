# Scalable Invoice-to-Unit Mapping Architecture

## Problem Statement

At scale, with multiple invoices and external data sources, we need:
1. **Reliable mapping** of invoices to correct units
2. **Batch processing** for efficiency
3. **Confidence scoring** to prioritize manual review
4. **External data integration** (APIs, databases)
5. **Audit trail** of mapping decisions
6. **Manual review workflow** for low-confidence matches

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Invoice Upload                            │
│  (PDF/Excel - Single or Batch)                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Unit Mapping Pipeline                           │
│                                                              │
│  1. Extract unit_id and address from invoice                 │
│  2. Check if unit_id exists (exact match)                   │
│  3. If not, try auto-matching by address similarity         │
│  4. Score confidence (0.0 to 1.0)                           │
│  5. Apply high-confidence matches automatically              │
│  6. Flag low-confidence for manual review                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Data Source Layer                               │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Database   │  │  External    │  │   API        │     │
│  │   (Default)  │  │  Database    │  │   Endpoint   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  • Sync units/leases from external sources                  │
│  • Cache frequently accessed data                           │
│  • Handle connection failures gracefully                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Validation Engine                               │
│                                                              │
│  • Uses mapped unit_id to find leases                        │
│  • Calculates vacancy overlap                               │
│  • Determines validation status                             │
│  • Stores mapping decision in validation_notes               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Manual Review Queue                             │
│                                                              │
│  • Invoices with low-confidence matches                      │
│  • Invoices with no matches                                  │
│  • User reviews and confirms/corrects mapping                │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Data Source Integration (`app/data_source.py`)

**Purpose**: Abstract interface for different data sources

**Supported Sources**:
- **DatabaseDataSource**: Internal database (default)
- **APIDataSource**: External REST API
- **DatabaseExternalDataSource**: External database (future)

**Features**:
- Sync units/leases from external sources
- Handle connection failures
- Cache data for performance

### 2. Invoice Mapper (`app/invoice_mapper.py`)

**Purpose**: Core mapping logic with confidence scoring

**Key Functions**:
- `map_invoice_to_unit()`: Map single invoice with confidence score
- `batch_map_invoices()`: Process multiple invoices efficiently
- `apply_unit_mapping()`: Apply mapping and re-validate
- `get_unmapped_invoices()`: Get invoices needing manual review

**Confidence Levels**:
- **1.0 (Exact)**: Unit ID exists in database
- **0.85-0.99 (High)**: Auto-match applied
- **0.50-0.84 (Medium)**: Manual review recommended
- **0.30-0.49 (Low)**: Manual review required
- **0.0 (None)**: No matches found

### 3. Unit Matcher (`app/unit_matcher.py`)

**Purpose**: Address similarity matching

**Algorithm**:
- Compares invoice address to unit addresses
- Uses SequenceMatcher for similarity (0.0 to 1.0)
- Weighted scoring: 70% address, 30% unit_id
- Returns top matches sorted by confidence

## Workflow: Single Invoice

```
1. Invoice Uploaded
   ↓
2. Extract unit_id and address
   ↓
3. Check if unit_id exists
   ├─ YES → Confidence: 1.0, Method: "exact" ✅
   └─ NO → Continue
   ↓
4. Find similar units by address
   ↓
5. Calculate confidence scores
   ↓
6. Apply mapping based on confidence:
   ├─ ≥ 0.85 → Auto-apply, Method: "auto" ✅
   ├─ 0.50-0.84 → Suggest match, Method: "manual_review_required" ⚠️
   └─ < 0.50 → No match, Method: "none" ❌
   ↓
7. Validate invoice with mapped unit_id
   ↓
8. Store mapping decision in validation_notes
```

## Workflow: Batch Processing

```
1. Multiple Invoices Uploaded (Excel/CSV)
   ↓
2. Batch Map Invoices:
   ├─ Process in parallel (if possible)
   ├─ Exact matches: Apply immediately
   ├─ High confidence (≥0.85): Auto-apply
   └─ Low confidence: Queue for review
   ↓
3. Generate Mapping Report:
   ├─ Total processed
   ├─ Exact matches count
   ├─ Auto-matched count
   ├─ Manual review required count
   └─ No match count
   ↓
4. User Reviews Low-Confidence Matches
   ↓
5. Apply Manual Mappings
   ↓
6. Re-validate All Invoices
```

## External Data Source Integration

### Scenario: Leases in External System

**Setup**:
1. Configure API endpoint in tenant settings
2. Set up API authentication (API key, OAuth, etc.)
3. Define sync schedule (real-time, hourly, daily)

**Sync Process**:
```
1. Scheduled Sync Triggered
   ↓
2. Fetch units from external API
   ├─ GET /api/units?tenant_id={id}
   └─ Returns: [{unit_id, address, ...}, ...]
   ↓
3. Fetch leases from external API
   ├─ GET /api/leases?tenant_id={id}
   └─ Returns: [{unit_id, lease_start, lease_end, ...}, ...]
   ↓
4. Update/Create units in database
   ↓
5. Update/Create leases in database
   ↓
6. Regenerate unit timelines
   ↓
7. Re-validate pending invoices
```

### API Data Source Configuration

**Tenant Settings** (stored in `Tenant` model):
```json
{
  "data_source": {
    "type": "api",
    "api_url": "https://client-api.example.com",
    "api_key": "***",
    "sync_schedule": "hourly",
    "last_sync": "2025-01-01T12:00:00Z"
  }
}
```

## Confidence Scoring Details

### Scoring Algorithm

```python
# Address similarity (70% weight)
address_similarity = SequenceMatcher(
    invoice_address.lower(),
    unit_address.lower()
).ratio()

# Unit ID similarity (30% weight)
unit_id_similarity = SequenceMatcher(
    invoice_unit_id.lower(),
    unit_unit_id.lower()
).ratio()

# Combined score
confidence = (address_similarity * 0.7) + (unit_id_similarity * 0.3)
```

### Decision Thresholds

| Confidence | Action | Method |
|------------|--------|--------|
| 1.0 | Use as-is | `exact` |
| 0.85-0.99 | Auto-apply | `auto` |
| 0.50-0.84 | Suggest, require confirmation | `manual_review_required` |
| 0.30-0.49 | Show in review queue | `manual_review_required` |
| < 0.30 | No match found | `none` |

## Manual Review Workflow

### UI Components Needed

1. **Unmapped Invoices Queue**
   - List of invoices needing mapping
   - Shows confidence scores
   - Shows suggested matches

2. **Mapping Modal**
   - Invoice details
   - Suggested unit matches (sorted by confidence)
   - Manual unit selection dropdown
   - "Apply & Validate" button

3. **Batch Mapping**
   - Select multiple invoices
   - Bulk apply same unit_id
   - Or review individually

### API Endpoints

```
GET  /api/invoices/unmapped
     → Returns list of invoices needing mapping

GET  /api/invoices/{id}/unit-matches
     → Returns suggested unit matches with confidence scores

PATCH /api/invoices/{id}/unit
     → Apply unit mapping and re-validate

POST /api/invoices/batch-map
     → Batch process multiple invoices
```

## Performance Considerations

### Batch Processing

**For 1000 invoices**:
- Sequential: ~10-15 seconds
- Parallel (10 workers): ~2-3 seconds
- Cached unit data: ~1-2 seconds

**Optimizations**:
1. Cache unit addresses in memory
2. Batch database queries
3. Parallel processing for independent invoices
4. Index on `unit_id` and `address` fields

### Data Source Caching

**Strategy**:
- Cache unit data for 1 hour
- Invalidate on sync
- Use Redis/Memcached for distributed systems

## Audit Trail

### What to Log

1. **Mapping Decision**:
   - Original unit_id
   - Matched unit_id
   - Confidence score
   - Match method (exact/auto/manual)
   - Timestamp
   - User/System that made decision

2. **Storage**:
   - Store in `InvoiceValidation.validation_notes`
   - Or separate `InvoiceMappingAudit` table

### Example Audit Entry

```
Mapped from '2 SAMPLE STREET' to 'SHOP-001' by user@example.com 
(confidence: 87%, method: auto) at 2025-01-01T12:00:00Z
```

## Testing at Scale

### Test Scenarios

1. **100 invoices, 50 units**
   - Expected: ~80% exact matches, ~15% auto-matched, ~5% manual

2. **1000 invoices, 200 units**
   - Expected: ~70% exact, ~20% auto, ~10% manual

3. **External API integration**
   - Test sync process
   - Test connection failures
   - Test data consistency

4. **Batch processing**
   - Test parallel processing
   - Test memory usage
   - Test error handling

## Next Steps

1. ✅ Create data source abstraction
2. ✅ Create invoice mapper with confidence scoring
3. ✅ Integrate batch processing
4. ⏳ Add API endpoints for batch mapping
5. ⏳ Add UI for manual review queue
6. ⏳ Add external API integration
7. ⏳ Add audit logging
8. ⏳ Performance testing at scale

