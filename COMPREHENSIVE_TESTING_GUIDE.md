# Comprehensive Testing Guide - Multi-Tenant Workflow

## Overview

This guide walks you through testing the complete system as a client would use it, from login to invoice validation, and explains how tenant isolation works.

---

## Part 1: Understanding Tenant Isolation

### How the System Differentiates Between Tenants

1. **Every Record Has `tenant_id`**: All data (units, leases, invoices, validations) includes a `tenant_id` foreign key.

2. **All Queries Filter by `tenant_id`**: When a user logs in, their `tenant_id` is stored in the session. All database queries automatically filter by this `tenant_id`.

3. **Same IDs Can Exist in Different Tenants**: 
   - Tenant A can have unit "SHOP-001"
   - Tenant B can also have unit "SHOP-001"
   - They are completely separate because of `tenant_id`

4. **Validation Logic is Tenant-Scoped**: When validating an invoice, the system only looks at:
   - Units belonging to the invoice's tenant
   - Leases belonging to the invoice's tenant
   - Timeline periods belonging to the invoice's tenant

### Database Schema

See `TENANT_ISOLATION_EXPLANATION.md` for detailed schema documentation.

**Key Points:**
- `tenants` table stores organization information
- All other tables have `tenant_id` foreign key
- Unique constraints include `tenant_id` (e.g., `UNIQUE(tenant_id, unit_id)`)
- Foreign keys include `tenant_id` for referential integrity

---

## Part 2: Step-by-Step Testing Workflow

### Test Scenario: Multiple Clients Using the System

We'll test with 3 different tenants to verify isolation.

---

### Step 1: Start the Server

```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open: http://localhost:8000

---

### Step 2: Create Test Data (Run Once)

```bash
python scripts/test_multi_tenant_workflow.py
```

This creates:
- 3 tenants (Acme, Global, City)
- Users for each tenant
- Units, leases, and invoices for each tenant

---

### Step 3: Test as Client 1 - Acme Property Management

#### 3.1 Login
1. Go to http://localhost:8000/login
2. Email: `acme@example.com`
3. Password: `test123`
4. Click "Sign In"

**Expected**: You should see the dashboard for Acme Property Management.

#### 3.2 View Data Management
1. Click "Data Management" in sidebar
2. Check "Units" tab - you should see 5 units (SHOP-001, SHOP-002, OFFICE-101, OFFICE-102, WAREHOUSE-001)
3. Check "Leases" tab - you should see 6 leases

**Expected**: Only Acme's data is visible.

#### 3.3 View Invoices
1. Click "Invoices" in sidebar
2. You should see 10 invoices for Acme

**Expected**: Only Acme's invoices are visible.

#### 3.4 Test Validation
1. Click on an invoice to view details
2. Check the validation result

**Expected**: Validation is based on Acme's leases and timeline data only.

---

### Step 4: Test as Client 2 - Global Real Estate Group

#### 4.1 Logout
1. Click "Sign Out" in sidebar

#### 4.2 Login as Different Client
1. Go to http://localhost:8000/login
2. Email: `global@example.com`
3. Password: `test123`
4. Click "Sign In"

**Expected**: You should see the dashboard for Global Real Estate Group.

#### 4.3 Verify Isolation
1. Check "Data Management" - you should see Global's units (same IDs like "SHOP-001" but different data)
2. Check "Invoices" - you should see Global's invoices (different from Acme's)

**Expected**: 
- You cannot see Acme's data
- Same unit IDs exist but with different data
- Validations are based on Global's leases only

---

### Step 5: Test as Client 3 - City Properties Ltd

Repeat Step 4 with:
- Email: `city@example.com`
- Password: `test123`

**Expected**: Complete isolation from Acme and Global.

---

## Part 3: Manual Testing - Full Workflow

### Test Scenario: New Client Onboarding

Let's simulate a completely new client from scratch.

### Step 1: Sign Up New Client

1. Go to http://localhost:8000/signup
2. Fill in:
   - Email: `newclient@example.com`
   - Password: `test123`
   - Full Name: `New Client User`
   - Organization Name: `New Client Properties`
   - Organization Slug: `new-client-properties`
3. Click "Sign Up"

**Expected**: Account created, automatically logged in.

### Step 2: Import Units

1. Click "Import Units" in sidebar
2. Create a test Excel file with columns:
   ```
   unit_id,building_name,address_line_1,city,postcode
   SHOP-001,Main Street Mall,100 Main St,London,SW1A 1AA
   SHOP-002,Main Street Mall,100 Main St,London,SW1A 1AA
   OFFICE-101,Business Tower,200 Business Ave,Manchester,M1 1AA
   ```
3. Upload the file
4. Click "Import Units"

**Expected**: Units imported successfully, visible in Data Management.

### Step 3: Import Leases

1. Click "Import Leases" in sidebar
2. Create a test Excel file with columns:
   ```
   unit_id,tenant_name,lease_start,lease_end
   SHOP-001,Coffee Shop Ltd,2024-01-01,
   SHOP-002,Bakery Corp,2023-06-01,2025-06-01
   OFFICE-101,Law Firm A,2022-01-01,2025-03-31
   ```
3. Upload the file
4. Click "Import Leases"

**Expected**: 
- Leases imported successfully
- Unit timelines automatically generated
- Visible in Data Management

### Step 4: Upload Invoices

1. Click "Upload Invoices" in sidebar
2. Create a test Excel file with 10 invoices:
   ```
   invoice_number,supplier_name,unit_id,billing_period_start,billing_period_end,gross_amount,utility_type
   INV-001,British Gas,SHOP-001,2024-01-01,2024-01-31,150.00,Electricity
   INV-002,Thames Water,SHOP-002,2024-02-01,2024-02-28,200.00,Water
   INV-003,EDF Energy,OFFICE-101,2024-03-01,2024-03-31,300.00,Gas
   ... (7 more invoices)
   ```
3. Upload the file
4. Watch progress bar
5. Wait for validation to complete

**Expected**: 
- 10 invoices uploaded
- All validated
- Results visible in Invoices page

### Step 5: Verify Validation Results

1. Go to "Invoices" page
2. Check each invoice's validation status
3. Click "View" on an invoice to see details

**Expected**: 
- Validations are correct based on your leases
- Vacant units show "Landlord Supply - OK TO PAY"
- Occupied units show appropriate determinations

---

## Part 4: Stress Testing

### Test 1: Large Dataset

1. Create Excel file with 100 invoices
2. Upload and validate
3. Check pagination works (should show 50 per page)
4. Test search functionality
5. Test filters

**Expected**: System handles large datasets efficiently.

### Test 2: Multiple Tenants Simultaneously

1. Open browser in incognito mode
2. Login as Tenant A
3. Open another incognito window
4. Login as Tenant B
5. Verify each sees only their data

**Expected**: Complete isolation, no data leakage.

### Test 3: Validation Logic Accuracy

1. Create specific test cases:
   - Invoice for vacant unit → Should be "Valid - Landlord Supply - OK TO PAY"
   - Invoice for occupied unit → Should be "Invalid - COT" or "DO NOT PAY"
   - Duplicate invoice → Should be flagged as duplicate
   - Invoice with no unit → Should show error

**Expected**: Validation logic works correctly per tenant.

---

## Part 5: Understanding Validation Logic Per Tenant

### How Validation Works

1. **Invoice Received** (with `tenant_id`)
   ```
   Invoice {
     tenant_id: 2,
     invoice_number: "INV-001",
     unit_id: "SHOP-001",
     ...
   }
   ```

2. **System Looks Up Unit** (tenant-scoped)
   ```python
   unit = session.query(Unit).filter(
       Unit.tenant_id == 2,  # Only this tenant's units
       Unit.unit_id == "SHOP-001"
   ).first()
   ```

3. **System Looks Up Leases** (tenant-scoped)
   ```python
   leases = session.query(Lease).filter(
       Lease.tenant_id == 2,  # Only this tenant's leases
       Lease.unit_id == "SHOP-001"
   ).all()
   ```

4. **System Generates Timeline** (tenant-scoped)
   ```python
   timeline = session.query(UnitTimeline).filter(
       UnitTimeline.tenant_id == 2,  # Only this tenant's timelines
       UnitTimeline.unit_id == "SHOP-001"
   ).all()
   ```

5. **System Calculates Vacancy Overlap** (using tenant's timeline)
   ```python
   # Only considers vacancy periods for this tenant
   vacancy_days = calculate_vacancy_overlap(
       invoice, 
       timeline_periods  # Only this tenant's periods
   )
   ```

6. **System Generates Validation** (with tenant_id)
   ```python
   validation = InvoiceValidation(
       tenant_id=2,  # Scoped to this tenant
       invoice_id=invoice.id,
       validation_status="Valid" or "Invalid",
       determination="OK TO PAY" or "DO NOT PAY",
       ...
   )
   ```

### Key Point

**Validation logic only uses data belonging to the invoice's tenant.** Even if another tenant has the same unit_id, it's completely ignored.

---

## Part 6: Database Inspection

### View Database Structure

```bash
# Using SQLite command line
sqlite3 app.db

# List all tables
.tables

# View tenants
SELECT * FROM tenants;

# View units for a specific tenant
SELECT * FROM units WHERE tenant_id = 1;

# View invoices for a specific tenant
SELECT * FROM invoices WHERE tenant_id = 1;

# View validations for a specific tenant
SELECT * FROM invoice_validations WHERE tenant_id = 1;
```

### Verify Tenant Isolation

```sql
-- Count units per tenant
SELECT t.name, COUNT(u.id) as unit_count
FROM tenants t
LEFT JOIN units u ON u.tenant_id = t.id
GROUP BY t.id, t.name;

-- Count invoices per tenant
SELECT t.name, COUNT(i.id) as invoice_count
FROM tenants t
LEFT JOIN invoices i ON i.tenant_id = t.id
GROUP BY t.id, t.name;

-- Verify no cross-tenant references
-- This should return 0 rows (no units from tenant 1 referencing tenant 2's leases)
SELECT u.id, u.tenant_id, u.unit_id, l.tenant_id as lease_tenant_id
FROM units u
JOIN leases l ON l.unit_id = u.unit_id
WHERE u.tenant_id != l.tenant_id;
```

---

## Part 7: Testing Checklist

### Tenant Isolation
- [ ] Login as Tenant A - see only Tenant A's data
- [ ] Login as Tenant B - see only Tenant B's data
- [ ] Same unit_id exists in both tenants but different data
- [ ] No cross-tenant data visible

### Data Import
- [ ] Import units successfully
- [ ] Import leases successfully
- [ ] Unit timelines generated automatically
- [ ] Data visible in Data Management

### Invoice Validation
- [ ] Upload invoices successfully
- [ ] Validation uses correct tenant's data
- [ ] Vacant units validated correctly
- [ ] Occupied units validated correctly
- [ ] Duplicates detected correctly

### UI/UX
- [ ] Pagination works correctly
- [ ] Search works correctly
- [ ] Filters work correctly
- [ ] Loading states display correctly
- [ ] Error messages are clear

### Performance
- [ ] Large file uploads work (100+ invoices)
- [ ] Pagination handles large datasets
- [ ] Search is responsive
- [ ] No performance degradation with multiple tenants

---

## Part 8: Troubleshooting

### Issue: Can't see data after login
**Solution**: Check that user has `tenant_id` set. Verify in database:
```sql
SELECT id, email, tenant_id FROM users WHERE email = 'your-email@example.com';
```

### Issue: Validation seems wrong
**Solution**: Check that leases and timelines exist for the tenant:
```sql
-- Check leases for tenant
SELECT * FROM leases WHERE tenant_id = YOUR_TENANT_ID;

-- Check timelines for tenant
SELECT * FROM unit_timeline WHERE tenant_id = YOUR_TENANT_ID;
```

### Issue: Duplicate unit_id error
**Solution**: This is expected if the unit already exists for that tenant. The constraint is `UNIQUE(tenant_id, unit_id)`, so same unit_id can exist in different tenants, but not twice in the same tenant.

---

## Summary

The system ensures complete tenant isolation through:
1. **`tenant_id` on every record** - Links data to specific tenant
2. **All queries filter by `tenant_id`** - Users only see their tenant's data
3. **Validation uses tenant-specific data** - Only looks at units, leases, timelines for the invoice's tenant
4. **Unique constraints include `tenant_id`** - Same IDs can exist in different tenants
5. **Foreign keys include `tenant_id`** - Ensures referential integrity within tenants

This architecture allows multiple clients to use the same system while maintaining complete data isolation and correct validation logic per tenant.


