# Multi-Tenant Migration Guide

## ✅ What's Been Done

### 1. Database Schema Updates
- ✅ Added `Tenant` model
- ✅ Added `tenant_id` to all tables:
  - `users` (nullable - NULL for super admin)
  - `units`
  - `leases`
  - `invoices`
  - `invoice_validations`
  - `unit_timeline`
  - `upload_status` (needs update)

### 2. Model Changes
- ✅ All models now have `tenant_id` foreign key
- ✅ Unique constraints updated (tenant_id + unique field)
- ✅ User model: Added `is_super_admin` flag
- ✅ Tenant model: Added `column_mapping_config` for per-tenant Excel column mappings

---

## ⚠️ What Needs to Be Done

### 1. Database Migration
**Current State**: Existing database has no `tenant_id` columns
**Action Needed**: Create migration script to:
- Add `tenants` table
- Add `tenant_id` columns to all tables
- Create default tenant for existing data
- Migrate existing data to default tenant

### 2. Update All Queries
**Action Needed**: All database queries must filter by `tenant_id`:
- Update `app/validation.py` queries
- Update `main.py` API endpoints
- Update all scripts

### 3. Authentication Updates
**Action Needed**: 
- Add tenant context to user session
- Tenant selection on login
- Tenant creation UI
- Super admin access

### 4. Upload Status Model
**Action Needed**: Add `tenant_id` to `UploadStatus` model

---

## 🗄️ Database Strategy

### Development (Current)
- **SQLite**: Good for development, single-user
- **Location**: `app.db` file

### Production (Recommended)
- **PostgreSQL**: Required for multi-tenant cloud deployment
- **Why**: 
  - Multi-user concurrent access
  - Better scalability
  - Row-level security (perfect for multi-tenant)
  - Cloud-ready

### Migration Path
1. Keep SQLite for development
2. Add PostgreSQL support via environment variable
3. Use same models (SQLAlchemy handles differences)
4. Migration scripts for both

---

## 📋 Next Steps

### Immediate (This Week)
1. ✅ Models updated (DONE)
2. ⏳ Create database migration script
3. ⏳ Update all queries with tenant filtering
4. ⏳ Update authentication system
5. ⏳ Add tenant selection UI

### Next Week
1. Column mapping configuration system
2. PostgreSQL setup and testing
3. Cloud deployment preparation

---

## 🔧 Database Migration Script

**File**: `scripts/migrate_to_multi_tenant.py`

**What it does**:
1. Creates `tenants` table
2. Creates default tenant ("Default Tenant")
3. Adds `tenant_id` columns to all tables
4. Migrates existing data to default tenant
5. Sets all existing users to default tenant

**Run**: `python scripts/migrate_to_multi_tenant.py`

---

## 🚨 Important Notes

### Data Isolation
- **CRITICAL**: All queries MUST filter by `tenant_id`
- Users can ONLY see their tenant's data
- Super admins can see all tenants

### Unique Constraints
- Changed from global unique to tenant-scoped unique
- Example: `unit_id` is unique per tenant, not globally
- Same `unit_id` can exist in different tenants

### Backward Compatibility
- Existing data will be migrated to default tenant
- No data loss
- Can rollback if needed

---

## 📝 Testing Checklist

After migration:
- [ ] Default tenant created
- [ ] Existing data migrated
- [ ] Users can only see their tenant's data
- [ ] Super admin can see all tenants
- [ ] New tenant creation works
- [ ] Tenant isolation verified
- [ ] All queries filter by tenant_id

---

## 🎯 Ready to Continue?

Next steps:
1. Create migration script
2. Update all queries
3. Update authentication
4. Add tenant UI

Let me know when you're ready to proceed!


