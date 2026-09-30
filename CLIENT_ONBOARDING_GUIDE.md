# Client Onboarding Guide

## Overview

This document outlines the **step-by-step process** for onboarding a new client, importing their data, and setting up invoice validation.

---

## Current State vs. What's Needed

### ✅ **What We Have Now**

1. **Multi-tenant infrastructure** - Each client gets their own tenant/organization
2. **User authentication** - Clients can login with their own accounts
3. **Invoice upload & validation** - Can upload Excel/CSV files and validate
4. **Command-line data import** - Scripts to import Units/Leases (but no UI)

### ❌ **What's Missing (Needed for MVP)**

1. **UI for Units/Leases import** - Currently only command-line scripts
2. **Per-tenant column mapping** - Currently hardcoded, needs per-client config
3. **Client onboarding workflow** - No guided setup process
4. **Data source connections** - No API/sync capabilities (future)

---

## Step-by-Step Client Onboarding Process

### **Phase 1: Initial Setup (Admin/Super Admin)**

#### Step 1: Create Client Organization
**Current Method:** Manual via script or signup
```bash
# Option A: Via signup (creates tenant automatically)
# Client goes to /signup and creates account

# Option B: Admin creates tenant manually
python scripts/create_dummy_tenants.py  # (modify for real client)
```

**What We Need:**
- ✅ Admin UI to create tenants (partially done via signup)
- ⚠️ Better admin dashboard for tenant management

#### Step 2: Create Client User Account
**Current Method:** Via signup or script
```bash
# Client signs up at /signup
# Or admin creates via script
```

**What We Need:**
- ✅ Signup works
- ⚠️ Admin UI to create/manage users per tenant

---

### **Phase 2: Data Import (CRITICAL - Currently Missing UI)**

#### Step 3: Import Units Data
**Current Method:** Command-line script only
```bash
# Client provides Excel/CSV with units
# Admin runs script to import
python scripts/import_units.py --tenant-id 1 --file client_units.xlsx
```

**What Client Provides:**
- Excel/CSV file with columns:
  - `unit_id` (e.g., "SHOP-001")
  - `building_name`
  - `address_line_1`, `address_line_2`
  - `city`, `postcode`

**What We Need:**
- ❌ **UI for Units Import** (`/admin/import-units` or `/tenant/import-units`)
  - Upload Excel/CSV
  - Preview data
  - Map columns (if different names)
  - Import with tenant_id automatically set

#### Step 4: Import Leases Data
**Current Method:** Command-line script only
```bash
# Client provides Excel/CSV with leases
python scripts/import_leases.py --tenant-id 1 --file client_leases.xlsx
```

**What Client Provides:**
- Excel/CSV file with columns:
  - `unit_id` (must match imported units)
  - `tenant_name` (lease tenant name)
  - `lease_start` (date)
  - `lease_end` (date, or NULL for ongoing)

**What We Need:**
- ❌ **UI for Leases Import** (`/admin/import-leases` or `/tenant/import-leases`)
  - Upload Excel/CSV
  - Preview data
  - Map columns
  - Validate unit_id references
  - Import with tenant_id automatically set

#### Step 5: Generate Unit Timeline
**Current Method:** Automatic when leases imported
```python
# Runs automatically via generate_unit_timeline()
# Creates vacancy/occupied periods for validation
```

**Status:** ✅ Works automatically

---

### **Phase 3: Configuration**

#### Step 6: Configure Column Mappings (If Needed)
**Current Method:** Hardcoded in `main.py`
```python
# Currently in main.py line ~443
column_mapping = {
    "invoice_number": ["invoice_number", "invoice #", "invoice_no", ...],
    "unit_id": ["unit_id", "unit", "property_id", ...],
    # ... etc
}
```

**What We Need:**
- ❌ **Per-Tenant Column Mapping Config**
  - Store in `Tenant.column_mapping_config` (JSON field exists, not used)
  - UI to configure mappings per tenant
  - Or config file per tenant
  - Fallback to default if not configured

**When Needed:**
- If client's Excel has different column names
- Example: Client uses "Invoice #" instead of "invoice_number"

---

### **Phase 4: Invoice Processing (Ready Now)**

#### Step 7: Upload Invoices
**Current Method:** ✅ **Works via UI**
- Client goes to `/upload`
- Uploads Excel/CSV file
- System validates against their units/leases
- Results shown in dashboard

**Status:** ✅ **Fully functional**

---

## What Needs to Be Added to MVP

### **Priority 1: Data Import UI** 🔴 **CRITICAL**

**Why:** Clients can't import their own Units/Leases data without technical help.

**What to Build:**

1. **Units Import Page** (`/import-units`)
   - Upload Excel/CSV
   - Column mapping (if needed)
   - Preview before import
   - Import with tenant_id auto-set
   - Show existing units count

2. **Leases Import Page** (`/import-leases`)
   - Upload Excel/CSV
   - Column mapping
   - Validate unit_id references
   - Preview before import
   - Import with tenant_id auto-set
   - Show existing leases count

3. **Data Management Page** (`/data-management`)
   - View all units
   - View all leases
   - Edit/delete units/leases
   - Re-import/update data

**Implementation:**
- Similar to invoice upload page
- Use same file parsing logic
- Add to tenant-scoped routes
- Background processing for large files

---

### **Priority 2: Column Mapping Configuration** 🟡 **HIGH**

**Why:** Different clients may have different Excel column names.

**What to Build:**

1. **Column Mapping Config System**
   - Store per-tenant in `Tenant.column_mapping_config` (JSON)
   - Default mappings for common variations
   - Override per tenant if needed

2. **Column Mapping UI** (Optional for MVP)
   - Admin can configure mappings per tenant
   - Or use config files (simpler for MVP)

**Implementation:**
- Use existing `Tenant.column_mapping_config` field
- Load from tenant config in `main.py` upload handler
- Fallback to default if not set

---

### **Priority 3: Client Onboarding Workflow** 🟢 **NICE TO HAVE**

**Why:** Makes onboarding smoother and more professional.

**What to Build:**

1. **Onboarding Wizard**
   - Step 1: Create account / organization
   - Step 2: Import Units
   - Step 3: Import Leases
   - Step 4: Configure column mappings (if needed)
   - Step 5: Test with sample invoice

2. **Admin Dashboard**
   - View all tenants
   - Create/manage tenants
   - View tenant data (units, leases, invoices)
   - Configure tenant settings

---

## Recommended MVP Scope

### **Must Have (Before First Client):**
1. ✅ Multi-tenant infrastructure (DONE)
2. ✅ Invoice upload & validation (DONE)
3. ❌ **Units/Leases import UI** (CRITICAL)
4. ❌ **Per-tenant column mapping** (HIGH)

### **Nice to Have (Can Add Later):**
1. Onboarding wizard
2. Admin dashboard enhancements
3. Data source API connections
4. Email notifications
5. Advanced reporting

---

## Current Workaround (For Testing)

**Until UI is built, you can:**

1. **Create tenant:** Via signup or script
2. **Import Units:** Use command-line script (modify to accept tenant_id)
3. **Import Leases:** Use command-line script (modify to accept tenant_id)
4. **Upload Invoices:** Use existing UI ✅

**Scripts to modify:**
- `scripts/load_sample_data.py` - Add `--tenant-id` parameter
- Create `scripts/import_units_from_excel.py` - New script
- Create `scripts/import_leases_from_excel.py` - New script

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENT ONBOARDING                      │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────┐
        │  1. Create Tenant/Organization   │
        │     (via signup or admin)         │
        └─────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────┐
        │  2. Create User Account          │
        │     (via signup)                 │
        └─────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────┐
        │  3. Import Units Data           │
        │     ❌ NEEDS UI                  │
        │     (Excel/CSV → Units table)    │
        └─────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────┐
        │  4. Import Leases Data           │
        │     ❌ NEEDS UI                  │
        │     (Excel/CSV → Leases table)   │
        └─────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────┐
        │  5. Generate Unit Timeline      │
        │     ✅ Automatic                │
        │     (Leases → UnitTimeline)     │
        └─────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────┐
        │  6. Configure Column Mappings   │
        │     ❌ NEEDS CONFIG SYSTEM       │
        │     (if Excel format differs)    │
        └─────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────┐
        │  7. Upload & Validate Invoices  │
        │     ✅ READY NOW                 │
        │     (Excel → Validation)        │
        └─────────────────────────────────┘
```

---

## Next Steps

1. **Build Units/Leases Import UI** (Priority 1)
2. **Build Column Mapping Config** (Priority 2)
3. **Test full onboarding workflow**
4. **Document client data requirements**
5. **Create client-facing onboarding guide**

---

## Questions to Answer

1. **Data Format:** Will all clients use the same Excel format, or will formats vary?
2. **Data Updates:** How often will clients update Units/Leases? (Monthly? Quarterly?)
3. **Data Source:** Will clients provide Excel files, or do we need API connections?
4. **Validation:** Do we need to validate Units/Leases data before import? (duplicates, date ranges, etc.)


