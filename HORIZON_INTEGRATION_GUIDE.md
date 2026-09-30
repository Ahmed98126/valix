# Horizon Integration & Data Management Guide

## Overview

This document explains:
1. **Horizon Integration** - How to connect to Horizon API for real-time unit/lease updates
2. **Data Management Page** - What it does and how it works
3. **Validation Process** - How invoices are validated against unit/lease data

---

## 1. Horizon Integration (API Connector)

### What is Horizon?
Horizon is a property management software that tracks:
- Property units
- Lease agreements
- Tenant information
- Lease start/end dates
- Vacancy periods

### Integration Architecture

```
┌─────────────────┐
│   Horizon API   │
│  (Client's PMS) │
└────────┬────────┘
         │
         │ API Calls (OAuth/API Key)
         │
         ▼
┌─────────────────────────────────┐
│   Our System - API Connector    │
│                                 │
│  ┌───────────────────────────┐  │
│  │ Tenant 1: Horizon Config  │  │
│  │ - API Endpoint            │  │
│  │ - API Key/Token           │  │
│  │ - Sync Schedule            │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ Tenant 2: Manual Upload   │  │
│  │ - Excel/CSV Import         │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ Tenant 3: Horizon Config  │  │
│  │ - Different Horizon Instance│ │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│   Our Database  │
│  (Per Tenant)   │
└─────────────────┘
```

### How It Would Work

#### **Option A: Scheduled Sync (Recommended)**
1. **Configuration per Tenant:**
   - Each tenant can configure their Horizon connection
   - Store API credentials securely (encrypted)
   - Set sync schedule (hourly, daily, weekly)

2. **Sync Process:**
   - Background job runs on schedule
   - Fetches units from Horizon API
   - Fetches leases from Horizon API
   - Updates our database (adds new, updates existing)
   - Regenerates unit timelines
   - Logs sync status

3. **Manual Trigger:**
   - "Sync Now" button in UI
   - Immediate sync on demand

#### **Option B: Webhook Integration (Advanced)**
- Horizon sends webhooks when data changes
- Our system receives webhook and updates immediately
- More real-time but requires Horizon webhook support

### Implementation Plan

**Phase 1: Manual Import (Current - DONE)**
- ✅ Excel/CSV upload for units
- ✅ Excel/CSV upload for leases

**Phase 2: Horizon API Connector (Next)**
- Add `data_source_config` field to `Tenant` model (JSON)
- Store Horizon API credentials per tenant
- Create sync service/background job
- Add "Sync from Horizon" button in UI
- Handle API authentication (OAuth/API Key)

**Phase 3: Multi-Source Support (Future)**
- Support multiple PMS systems (Horizon, Yardi, MRI, etc.)
- Generic connector framework
- Per-tenant data source selection

---

## 2. Data Management Page

### Purpose
The Data Management page allows clients to:
- **View** all their units and leases
- **Edit** unit/lease information
- **Delete** units/leases (with validation)
- **See** unit timeline (vacancy/occupied periods)
- **Monitor** data quality

### Features

#### **Units Tab**
- Table showing all units
- Columns: Unit ID, Building, Address, City, Postcode
- Actions: Edit, Delete, View Details
- Search/Filter functionality
- Export to CSV

#### **Leases Tab**
- Table showing all leases
- Columns: Unit ID, Tenant Name, Start Date, End Date, Status
- Actions: Edit, Delete, View Details
- Filter by: Active, Expired, Upcoming
- Search functionality

#### **Unit Timeline View**
- Visual timeline for each unit
- Shows occupied (green) and vacant (red) periods
- Derived from leases data
- Used for invoice validation

#### **Data Quality Indicators**
- Units without leases
- Leases with invalid unit_id references
- Overlapping leases (data quality issue)
- Missing required fields

### Implementation

**Page Route:** `/data-management`

**Features:**
1. **Units List:**
   - Paginated table
   - Edit modal/form
   - Delete with confirmation
   - Bulk operations (future)

2. **Leases List:**
   - Paginated table
   - Edit modal/form
   - Delete with confirmation
   - Date range filters

3. **Unit Timeline Visualization:**
   - Gantt chart or timeline view
   - Shows vacancy/occupied periods
   - Click to see details

4. **Sync Status (if Horizon connected):**
   - Last sync time
   - Sync status (success/error)
   - "Sync Now" button
   - Sync logs

---

## 3. Validation Process (How It Works)

### The Magic: Step-by-Step

#### **Step 1: Data Setup (One-Time)**
```
Client imports:
├── Units (e.g., 50 units)
└── Leases (e.g., 120 lease periods)
    │
    ▼
System generates:
└── Unit Timeline (vacancy/occupied periods)
    ├── Unit A: Vacant 2020-01-01 to 2021-06-30
    ├── Unit A: Occupied 2021-07-01 to 2024-12-31
    ├── Unit A: Vacant 2025-01-01 to ongoing
    └── ... (for all units)
```

#### **Step 2: Invoice Upload**
```
Client uploads Excel with invoices:
├── Invoice #12345
│   ├── Unit ID: SHOP-001
│   ├── Period: 2024-10-01 to 2024-10-31
│   └── Amount: £150.00
└── Invoice #12346
    ├── Unit ID: SHOP-002
    ├── Period: 2024-10-01 to 2024-10-31
    └── Amount: £200.00
```

#### **Step 3: Validation Logic (The Magic)**

For each invoice, the system:

**A. Check Duplicates**
```
Is this invoice_number + amount already in database?
├── YES → Mark as duplicate, skip validation
└── NO → Continue
```

**B. Find Unit Timeline**
```
Look up unit_id in UnitTimeline table:
├── Found → Get all vacancy/occupied periods
└── Not Found → Mark as "Unit not found"
```

**C. Calculate Vacancy Overlap**
```
For invoice period (2024-10-01 to 2024-10-31):
├── Check all timeline periods for this unit
├── Calculate days overlapping with VACANT periods
└── Calculate days overlapping with OCCUPIED periods

Example:
├── Invoice: 2024-10-01 to 2024-10-31 (31 days)
├── Timeline: Vacant 2024-10-01 to 2024-10-15 (15 days)
│             Occupied 2024-10-16 to 2024-10-31 (16 days)
└── Result: 15 days vacant, 16 days occupied
```

**D. Determine Validation Status**
```
If total_overlap_days == invoice_days:
├── All days were VACANT → Status: "Valid" (landlord liable)
└── All days were OCCUPIED → Status: "Invalid" (tenant liable)

If total_overlap_days < invoice_days:
└── Partial overlap → Status: "Needs Review"

If total_overlap_days == 0:
└── No overlap found → Status: "Invalid" (no data)
```

**E. Generate Determination**
```
Based on validation status + unit type:

Valid (all vacant):
├── Unit ends in '00' → "Landlord Supply - OK TO PAY"
└── Otherwise → "OK TO PAY, SUBMIT METER READING"

Invalid (all occupied):
├── Unit ends in '00' → "Landlord Supply - OK TO PAY"
└── Otherwise → "DO NOT PAY" or "COT"

Needs Review:
└── "COT" (Check Other Things)
```

#### **Step 4: Results**
```
Invoice #12345:
├── Status: Invalid
├── Determination: DO NOT PAY
├── Reason: Unit was occupied during invoice period
└── Details: 31 days occupied, 0 days vacant

Invoice #12346:
├── Status: Valid
├── Determination: OK TO PAY, SUBMIT METER READING
├── Reason: Unit was vacant during invoice period
└── Details: 0 days occupied, 31 days vacant
```

### The Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    VALIDATION WORKFLOW                        │
└─────────────────────────────────────────────────────────────┘

1. DATA SETUP (One-Time)
   │
   ├─ Import Units (via UI or Horizon sync)
   │  └─> Units table
   │
   ├─ Import Leases (via UI or Horizon sync)
   │  └─> Leases table
   │
   └─> Generate Unit Timeline (automatic)
       └─> UnitTimeline table (vacancy/occupied periods)
   
2. INVOICE UPLOAD
   │
   └─> Client uploads Excel/CSV
       └─> Invoices table (pending validation)

3. VALIDATION (Per Invoice)
   │
   ├─> Check Duplicates
   │   └─> Skip if duplicate
   │
   ├─> Find Unit in UnitTimeline
   │   └─> Get all periods for this unit
   │
   ├─> Calculate Overlap
   │   ├─> Days overlapping with VACANT periods
   │   └─> Days overlapping with OCCUPIED periods
   │
   ├─> Determine Status
   │   ├─> Valid (all vacant)
   │   ├─> Invalid (all occupied)
   │   └─> Needs Review (partial/mixed)
   │
   └─> Generate Determination
       ├─> OK TO PAY
       ├─> DO NOT PAY
       ├─> COT
       └─> Landlord Supply - OK TO PAY

4. RESULTS
   │
   └─> InvoiceValidation table
       └─> Displayed in Dashboard/Invoices page
```

---

## Implementation Roadmap

### **Phase 1: Current (DONE)**
- ✅ Manual Excel/CSV import for Units
- ✅ Manual Excel/CSV import for Leases
- ✅ Validation engine
- ✅ Invoice upload & validation

### **Phase 2: Data Management Page (NEXT)**
- ⏳ View Units/Leases
- ⏳ Edit Units/Leases
- ⏳ Delete Units/Leases
- ⏳ Unit Timeline visualization
- ⏳ Data quality indicators

### **Phase 3: Horizon Integration**
- ⏳ Horizon API connector
- ⏳ Per-tenant API configuration
- ⏳ Scheduled sync jobs
- ⏳ Manual sync trigger
- ⏳ Sync status/logs

### **Phase 4: Advanced Features**
- ⏳ Multi-PMS support (Yardi, MRI, etc.)
- ⏳ Webhook integration
- ⏳ Real-time updates
- ⏳ Data conflict resolution

---

## Horizon API Integration Details

### What We Need from Client

1. **API Credentials:**
   - API endpoint URL
   - API key or OAuth credentials
   - Authentication method

2. **API Documentation:**
   - Endpoints for fetching units
   - Endpoints for fetching leases
   - Data format/response structure
   - Rate limits

3. **Data Mapping:**
   - How Horizon fields map to our fields
   - Custom field mappings per tenant

### Database Schema Addition

```python
# Add to Tenant model
data_source_config = Column(JSON, nullable=True)
# Example:
{
    "type": "horizon",
    "api_endpoint": "https://api.horizon.com/v1",
    "api_key": "encrypted_key",
    "sync_schedule": "daily",
    "last_sync": "2024-12-25T10:00:00Z",
    "field_mappings": {
        "unit_id": "property_code",
        "building_name": "building_name",
        ...
    }
}
```

### Sync Service

```python
# Background job that runs on schedule
def sync_from_horizon(tenant_id: int):
    tenant = get_tenant(tenant_id)
    config = tenant.data_source_config
    
    if config["type"] == "horizon":
        # Fetch units from Horizon API
        units = horizon_api.get_units(config)
        
        # Fetch leases from Horizon API
        leases = horizon_api.get_leases(config)
        
        # Update database
        update_units(tenant_id, units)
        update_leases(tenant_id, leases)
        
        # Regenerate timelines
        generate_unit_timeline(tenant_id)
```

---

## Questions to Answer

1. **Horizon API Access:**
   - Does your client have Horizon API access?
   - What authentication method does Horizon use?
   - Do you have API documentation?

2. **Sync Frequency:**
   - How often should data sync? (hourly, daily, weekly)
   - Do clients need real-time updates?

3. **Data Ownership:**
   - Can clients edit data synced from Horizon?
   - What happens if data conflicts?

4. **Multi-Client:**
   - Will different clients use different Horizon instances?
   - Do we need separate API credentials per client?

---

## Next Steps

1. **Build Data Management Page** (Priority 1)
2. **Research Horizon API** (if client has access)
3. **Design API Connector Framework** (Priority 2)
4. **Implement Horizon Sync** (Priority 3)

Would you like me to:
1. Build the Data Management page first?
2. Research/create Horizon API connector structure?
3. Both?


