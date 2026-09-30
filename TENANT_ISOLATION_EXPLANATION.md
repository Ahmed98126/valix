# Tenant Isolation & Database Schema Explanation

## Overview

This document explains how the system differentiates between tenants, how data is stored in the database, and how validation logic works per tenant.

---

## 1. Tenant Isolation Mechanism

### How Tenants Are Identified

Each tenant has:
- **Unique ID**: Primary key in the `tenants` table
- **Unique Slug**: URL-friendly identifier (e.g., "acme-properties")
- **Unique Name**: Display name (e.g., "Acme Property Management")

### Data Isolation Strategy

**Every data record includes a `tenant_id` foreign key** that links it to a specific tenant. This ensures complete data isolation.

---

## 2. Database Schema

### Core Tables

#### `tenants` Table
```sql
CREATE TABLE tenants (
    id INTEGER PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL,
    slug VARCHAR UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME,
    updated_at DATETIME,
    column_mapping_config TEXT  -- JSON for column mappings
);
```

**Purpose**: Stores tenant/organization information.

#### `users` Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    full_name VARCHAR,
    tenant_id INTEGER REFERENCES tenants(id),  -- Links user to tenant
    is_super_admin BOOLEAN DEFAULT FALSE,
    created_at DATETIME
);
```

**Purpose**: User accounts. Each user belongs to one tenant (except super admins).

**Isolation**: Users can only access data from their `tenant_id`.

#### `units` Table
```sql
CREATE TABLE units (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id),  -- Tenant isolation
    unit_id VARCHAR NOT NULL,
    building_name VARCHAR,
    address_line_1 VARCHAR,
    address_line_2 VARCHAR,
    city VARCHAR,
    postcode VARCHAR,
    created_at DATETIME,
    UNIQUE(tenant_id, unit_id)  -- Same unit_id can exist in different tenants
);
```

**Purpose**: Property units (shops, offices, etc.).

**Isolation**: `tenant_id` ensures each tenant only sees their units. The unique constraint `(tenant_id, unit_id)` allows the same `unit_id` (e.g., "SHOP-001") to exist in multiple tenants without conflict.

#### `leases` Table
```sql
CREATE TABLE leases (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id),  -- Tenant isolation
    unit_id VARCHAR NOT NULL,
    tenant_name VARCHAR,  -- Name of the lease tenant (not system tenant)
    lease_start DATE,
    lease_end DATE,
    created_at DATETIME,
    FOREIGN KEY (tenant_id, unit_id) REFERENCES units(tenant_id, unit_id)
);
```

**Purpose**: Lease agreements for units.

**Isolation**: `tenant_id` ensures leases are tenant-scoped. The foreign key `(tenant_id, unit_id)` ensures leases reference units within the same tenant.

#### `invoices` Table
```sql
CREATE TABLE invoices (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id),  -- Tenant isolation
    invoice_number VARCHAR NOT NULL,
    supplier_name VARCHAR,
    unit_id VARCHAR NOT NULL,
    billing_period_start DATE,
    billing_period_end DATE,
    gross_amount DECIMAL,
    net_amount DECIMAL,
    vat_amount DECIMAL,
    utility_type VARCHAR,
    source_batch VARCHAR,
    created_at DATETIME,
    UNIQUE(tenant_id, invoice_number, gross_amount)  -- Duplicate detection per tenant
);
```

**Purpose**: Invoices to validate.

**Isolation**: `tenant_id` ensures invoices are tenant-scoped. Duplicate detection only checks within the same tenant.

#### `invoice_validations` Table
```sql
CREATE TABLE invoice_validations (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id),  -- Tenant isolation
    invoice_id INTEGER REFERENCES invoices(id),
    validation_status VARCHAR,  -- 'Valid', 'Invalid', 'Needs Review'
    determination VARCHAR,  -- 'OK TO PAY', 'DO NOT PAY', 'COT', etc.
    vacancy_overlap_days INTEGER,
    daily_rate DECIMAL,
    validation_notes TEXT,
    created_at DATETIME
);
```

**Purpose**: Validation results for invoices.

**Isolation**: `tenant_id` ensures validations are tenant-scoped.

#### `unit_timelines` Table
```sql
CREATE TABLE unit_timelines (
    id INTEGER PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id),  -- Tenant isolation
    unit_id VARCHAR NOT NULL,
    period_start DATE,
    period_end DATE,
    is_vacant BOOLEAN,
    lease_id INTEGER REFERENCES leases(id),
    created_at DATETIME
);
```

**Purpose**: Explicit occupied/vacant periods for units (derived from leases).

**Isolation**: `tenant_id` ensures timelines are tenant-scoped.

---

## 3. How Validation Logic Works Per Tenant

### Step-by-Step Validation Process

When validating an invoice, the system:

1. **Receives Invoice** (with `tenant_id`)
   ```python
   invoice = Invoice(
       tenant_id=current_tenant.id,
       invoice_number="INV-001",
       unit_id="SHOP-001",
       ...
   )
   ```

2. **Checks for Duplicates** (tenant-scoped)
   ```python
   # Only checks duplicates within the same tenant
   existing = session.query(Invoice).filter(
       Invoice.tenant_id == invoice.tenant_id,  # Tenant isolation
       Invoice.invoice_number == invoice.invoice_number,
       Invoice.gross_amount == invoice.gross_amount
   ).first()
   ```

3. **Looks Up Unit** (tenant-scoped)
   ```python
   # Only finds units belonging to the same tenant
   unit = session.query(Unit).filter(
       Unit.tenant_id == invoice.tenant_id,  # Tenant isolation
       Unit.unit_id == invoice.unit_id
   ).first()
   ```

4. **Looks Up Leases** (tenant-scoped)
   ```python
   # Only finds leases for this unit within the same tenant
   leases = session.query(Lease).filter(
       Lease.tenant_id == invoice.tenant_id,  # Tenant isolation
       Lease.unit_id == invoice.unit_id
   ).all()
   ```

5. **Looks Up Timeline** (tenant-scoped)
   ```python
   # Only checks timeline periods for this unit within the same tenant
   timeline_periods = session.query(UnitTimeline).filter(
       UnitTimeline.tenant_id == invoice.tenant_id,  # Tenant isolation
       UnitTimeline.unit_id == invoice.unit_id,
       UnitTimeline.period_start <= invoice.billing_period_end,
       UnitTimeline.period_end >= invoice.billing_period_start
   ).all()
   ```

6. **Calculates Vacancy Overlap** (using tenant-specific timeline)
   ```python
   # Only considers vacancy periods for this tenant's unit
   vacancy_days = sum(
       period.vacancy_days 
       for period in timeline_periods 
       if period.is_vacant and period.tenant_id == invoice.tenant_id
   )
   ```

7. **Generates Validation Result** (with tenant_id)
   ```python
   validation = InvoiceValidation(
       tenant_id=invoice.tenant_id,  # Tenant isolation
       invoice_id=invoice.id,
       validation_status="Valid" or "Invalid",
       determination="OK TO PAY" or "DO NOT PAY",
       ...
   )
   ```

### Key Points

1. **Every Query Filters by `tenant_id`**: All database queries include `tenant_id` filtering to ensure data isolation.

2. **Foreign Keys Include `tenant_id`**: Composite foreign keys like `(tenant_id, unit_id)` ensure referential integrity within tenants.

3. **Unique Constraints Include `tenant_id`**: Same IDs can exist in different tenants (e.g., "SHOP-001" can exist in multiple tenants).

4. **Validation Uses Tenant-Specific Data**: Validation logic only looks at data belonging to the invoice's tenant.

---

## 4. Code Examples

### Query Filtering (from `app/tenant_helpers.py`)

```python
def filter_by_tenant(query, model, user, request):
    """Filter query by tenant_id."""
    tenant_id = get_tenant_id(user, request)
    
    if tenant_id:
        # Regular user: only see their tenant's data
        return query.filter(model.tenant_id == tenant_id)
    elif user.is_super_admin:
        # Super admin: can see all data (no filter)
        return query
    else:
        # No tenant: return empty result
        return query.filter(False)
```

### Validation Function (from `app/validation.py`)

```python
def validate_invoice(session, invoice):
    """Validate an invoice (tenant-scoped)."""
    tenant_id = invoice.tenant_id  # Get tenant from invoice
    
    # Check duplicates (tenant-scoped)
    duplicate = check_duplicate_invoice(session, invoice, tenant_id)
    
    # Get unit (tenant-scoped)
    unit = session.query(Unit).filter(
        Unit.tenant_id == tenant_id,
        Unit.unit_id == invoice.unit_id
    ).first()
    
    # Get timeline (tenant-scoped)
    timeline_periods = session.query(UnitTimeline).filter(
        UnitTimeline.tenant_id == tenant_id,
        UnitTimeline.unit_id == invoice.unit_id,
        ...
    ).all()
    
    # Calculate vacancy overlap (tenant-specific)
    vacancy_overlap = check_invoice_vacancy_overlap(
        session, invoice, tenant_id
    )
    
    # Generate validation (with tenant_id)
    validation = InvoiceValidation(
        tenant_id=tenant_id,  # Tenant isolation
        invoice_id=invoice.id,
        ...
    )
    
    return validation
```

---

## 5. Testing Tenant Isolation

### Test Scenario

1. **Tenant A** has:
   - Unit: "SHOP-001"
   - Lease: Coffee Shop Ltd (2024-01-01 to ongoing)
   - Invoice: INV-001 for SHOP-001

2. **Tenant B** has:
   - Unit: "SHOP-001" (same ID, different tenant!)
   - Lease: Bakery Corp (2023-06-01 to 2025-06-01)
   - Invoice: INV-001 for SHOP-001 (same invoice number!)

### Expected Behavior

- **Tenant A** can only see:
  - Their own "SHOP-001" unit
  - Their own Coffee Shop lease
  - Their own INV-001 invoice
  - Validation based on their own lease data

- **Tenant B** can only see:
  - Their own "SHOP-001" unit (different from Tenant A's)
  - Their own Bakery Corp lease
  - Their own INV-001 invoice (different from Tenant A's)
  - Validation based on their own lease data

- **No Cross-Tenant Access**: Tenant A cannot see Tenant B's data and vice versa.

---

## 6. Summary

### How It Works

1. **Every record has `tenant_id`**: Links data to a specific tenant.
2. **All queries filter by `tenant_id`**: Ensures users only see their tenant's data.
3. **Validation uses tenant-specific data**: Only looks at units, leases, and timelines for the invoice's tenant.
4. **Unique constraints include `tenant_id`**: Allows same IDs in different tenants.
5. **Foreign keys include `tenant_id`**: Ensures referential integrity within tenants.

### Benefits

- ✅ Complete data isolation between tenants
- ✅ Same IDs can exist in different tenants
- ✅ Validation logic correctly scoped per tenant
- ✅ Scalable for multiple clients
- ✅ Secure (users can't access other tenants' data)

---

## 7. Database Schema Diagram

```
tenants (id, name, slug, ...)
    │
    ├── users (id, email, tenant_id, ...)
    │
    ├── units (id, tenant_id, unit_id, ...)
    │       │
    │       ├── leases (id, tenant_id, unit_id, ...)
    │       │       │
    │       │       └── unit_timelines (id, tenant_id, unit_id, lease_id, ...)
    │       │
    │       └── invoices (id, tenant_id, unit_id, ...)
    │               │
    │               └── invoice_validations (id, tenant_id, invoice_id, ...)
```

**Key**: All relationships include `tenant_id` for isolation.

---

This architecture ensures complete tenant isolation while maintaining data integrity and correct validation logic per tenant.


