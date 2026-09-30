# Horizon Integration - How It Works

## What is Horizon?

**Horizon** is a Property Management System (PMS) that your clients use to manage:
- Property units
- Lease agreements
- Tenant information
- Lease dates

**The Problem:**
- Clients manually export data from Horizon to Excel
- Then upload Excel to your system
- This is time-consuming and error-prone

**The Solution:**
- Connect directly to Horizon API
- Automatically sync units and leases
- No manual Excel uploads needed!

---

## How It Works - Step by Step

### Phase 1: Setup (One-Time)

#### Step 1: Client Provides Horizon API Access
- Client gives you:
  - Horizon API endpoint URL
  - API key/token for authentication
  - (Optional) API documentation

#### Step 2: Configure in Settings
- Client (or admin) goes to `/settings`
- Scrolls to "Data Source Configuration"
- Selects "Horizon API" from dropdown
- Enters:
  - **API Endpoint:** `https://api.horizon.com/v1`
  - **API Key:** `abc123xyz...`
  - **Sync Schedule:** Daily (or Hourly/Weekly/Manual)
- Clicks "Save Data Source Configuration"

#### Step 3: Test Connection
- Clicks "Test Connection" button
- System verifies API credentials work
- Shows success/error message

---

### Phase 2: Data Sync

#### Option A: Manual Sync (On-Demand)
1. Client clicks "Sync Now" button in Settings
2. System connects to Horizon API
3. Fetches all units from Horizon
4. Fetches all leases from Horizon
5. Updates database:
   - Adds new units/leases
   - Updates existing ones
   - Regenerates unit timelines
6. Shows results: "50 units and 120 leases imported"

#### Option B: Automatic Sync (Scheduled)
1. Background job runs on schedule (daily/hourly)
2. Same process as manual sync
3. Client doesn't need to do anything
4. Data stays up-to-date automatically

---

## Real-World Workflow

### Scenario: Client Onboarding with Horizon

**Day 1: Initial Setup**
```
1. Client signs up → Creates tenant account
2. Admin configures Horizon API in Settings
3. Clicks "Sync Now" → Imports all units and leases
4. System generates unit timelines automatically
5. Client can now upload invoices!
```

**Day 2+: Ongoing**
```
1. New lease signed in Horizon
2. (Automatic) Daily sync runs at 2 AM
3. New lease appears in system automatically
4. Next invoice upload uses updated lease data
```

### Scenario: Manual Excel Upload (Alternative)

**If client doesn't have Horizon API:**
```
1. Client exports units from Horizon → Excel
2. Client exports leases from Horizon → Excel
3. Client uploads via /import-units page
4. Client uploads via /import-leases page
5. System processes and validates
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    HORIZON INTEGRATION                    │
└─────────────────────────────────────────────────────────┘

┌──────────────┐
│  Horizon PMS │  (Client's property management system)
│              │
│  - Units     │
│  - Leases    │
│  - Tenants   │
└──────┬───────┘
       │
       │ API Call (REST/GraphQL)
       │
       ▼
┌─────────────────────────────────────┐
│   Our System - Horizon Connector     │
│                                      │
│  1. Authenticate (API Key)          │
│  2. Fetch Units                      │
│  3. Fetch Leases                     │
│  4. Map Fields                       │
└──────┬───────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│      Our Database (Per Tenant)       │
│                                      │
│  Units Table                         │
│  ├─ unit_id: SHOP-001               │
│  ├─ building_name: High Street      │
│  └─ ...                             │
│                                      │
│  Leases Table                        │
│  ├─ unit_id: SHOP-001               │
│  ├─ tenant_name: Coffee Shop Ltd    │
│  ├─ lease_start: 2024-01-01         │
│  └─ lease_end: 2025-12-31           │
└──────┬───────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│   Auto-Generate Unit Timeline       │
│                                      │
│  UnitTimeline Table                  │
│  ├─ SHOP-001: Vacant 2020-01-01     │
│  │            to 2023-12-31         │
│  ├─ SHOP-001: Occupied 2024-01-01   │
│  │            to 2025-12-31         │
│  └─ SHOP-001: Vacant 2026-01-01     │
│            to ongoing                │
└──────┬───────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│   Invoice Validation                │
│                                      │
│  Invoice uploaded → Check timeline  │
│  → Determine if valid/invalid       │
└─────────────────────────────────────┘
```

---

## Benefits of Horizon Integration

### For Clients:
1. **No Manual Work:** No Excel exports/uploads needed
2. **Always Up-to-Date:** Data syncs automatically
3. **Less Errors:** No copy-paste mistakes
4. **Time Savings:** Minutes instead of hours

### For You:
1. **Better Data Quality:** Direct from source
2. **Scalability:** Can handle many clients
3. **Automation:** Set it and forget it
4. **Competitive Advantage:** Real-time data sync

---

## Comparison: Manual vs Horizon

### Manual Excel Upload:
```
Client Workflow:
1. Export units from Horizon → Excel
2. Export leases from Horizon → Excel
3. Open /import-units page
4. Upload units Excel
5. Open /import-leases page
6. Upload leases Excel
7. Wait for processing
8. Repeat monthly/quarterly

Time: ~30 minutes per sync
Errors: High (manual steps)
```

### Horizon API Integration:
```
Client Workflow:
1. Configure Horizon API once (5 minutes)
2. Click "Sync Now" (or automatic)
3. Done!

Time: ~2 minutes per sync (or automatic)
Errors: Low (automated)
```

---

## Implementation Status

### ✅ Completed:
- Horizon connector framework (`app/horizon_connector.py`)
- Settings page UI for configuration
- API endpoints for sync
- Data import/update logic

### ⏳ Needs Horizon API Access:
- Actual Horizon API endpoints (need documentation)
- Field mapping adjustments (based on Horizon's response format)
- Authentication method (OAuth vs API Key)

### 🔄 Next Steps:
1. Get Horizon API documentation from client
2. Update `HorizonConnector` with actual endpoints
3. Test connection
4. Configure sync schedule
5. Enable automatic syncing

---

## Example: Client Onboarding with Horizon

**Step 1: Client Setup**
```
Client: "We use Horizon for property management"
You: "Great! We can connect directly to Horizon."
```

**Step 2: Get API Credentials**
```
Client provides:
- API Endpoint: https://api.horizon-property.com/v1
- API Key: hz_live_abc123xyz789
```

**Step 3: Configure**
```
1. Go to /settings
2. Select "Horizon API" as data source
3. Enter endpoint and API key
4. Set sync schedule: Daily
5. Click "Test Connection" → Success!
6. Click "Save"
```

**Step 4: Initial Sync**
```
1. Click "Sync Now"
2. System fetches:
   - 50 units
   - 120 leases
3. Updates database
4. Generates timelines
5. Shows: "50 units and 120 leases imported successfully"
```

**Step 5: Ongoing**
```
- Daily sync runs automatically at 2 AM
- New leases appear automatically
- Client just uploads invoices
- System validates against latest data
```

---

## Technical Details

### Horizon Connector Class:
```python
connector = HorizonConnector(
    api_endpoint="https://api.horizon.com/v1",
    api_key="abc123..."
)

# Test connection
result = connector.test_connection()

# Fetch data
units = connector.fetch_units()
leases = connector.fetch_leases()

# Sync to database
sync_from_horizon(session, tenant_id, endpoint, api_key)
```

### Storage:
- Horizon config stored in `Tenant.data_source_config` (JSON)
- Format: `{"type": "horizon", "api_endpoint": "...", "api_key": "...", "sync_schedule": "daily"}`

### Security:
- API keys encrypted in database
- Per-tenant isolation
- Secure API communication (HTTPS)

---

## Questions & Answers

**Q: What if client doesn't have Horizon API access?**
A: They can still use manual Excel upload via `/import-units` and `/import-leases` pages.

**Q: Can we support other PMS systems?**
A: Yes! The connector framework can be extended for Yardi, MRI, AppFolio, etc.

**Q: How often should we sync?**
A: Depends on client needs:
- **Hourly:** For high-volume, time-sensitive operations
- **Daily:** Most common (overnight sync)
- **Weekly:** For smaller portfolios
- **Manual:** Client triggers when needed

**Q: What happens if sync fails?**
A: System logs error, shows notification, client can retry or use manual upload.


