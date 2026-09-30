# Multi-Tenant Testing Guide

## ✅ Migration Complete!

The database has been successfully migrated to support multi-tenancy.

## 🧪 Testing Steps

### 1. Start the Server

```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or if you have a background process running:
```bash
# Check if server is running, then access http://localhost:8000
```

### 2. Test User Accounts

**Regular User (Tenant-scoped):**
- Email: `admin@test.com`
- Password: `admin123`
- Tenant: Default Tenant
- Can only see data for their tenant

**Super Admin (All tenants):**
- Email: `superadmin@test.com`
- Password: `admin123`
- Can access all tenants
- Can switch between tenants using the tenant switcher

### 3. Test Login Flow

1. Go to `http://localhost:8000/login`
2. Login with `admin@test.com` / `admin123`
3. You should see:
   - Dashboard with tenant name displayed
   - Only invoices/data for "Default Tenant"
   - No tenant switcher (regular user)

### 4. Test Super Admin

1. Logout
2. Login with `superadmin@test.com` / `admin123`
3. You should see:
   - Dashboard with tenant switcher in sidebar
   - Can switch between tenants
   - Can see all tenant data when no tenant selected

### 5. Test Tenant Isolation

1. Create a new tenant via signup:
   - Go to `/signup`
   - Enter new tenant name (e.g., "Client ABC")
   - Create account
2. Login with new account
3. Verify:
   - Only sees data for their tenant
   - Cannot see other tenant's data
   - Dashboard shows correct tenant name

### 6. Test Invoice Upload

1. Upload an Excel file
2. Verify:
   - Invoice is associated with current tenant
   - Validation runs correctly
   - Invoice appears in dashboard
   - Other tenants cannot see this invoice

### 7. Test Tenant Switching (Super Admin)

1. Login as super admin
2. Use tenant switcher in sidebar
3. Select different tenant
4. Verify:
   - Dashboard updates to show selected tenant's data
   - Invoice list filters to selected tenant
   - Stats update for selected tenant

## 🔍 Verification Checklist

- [ ] Can login with regular user
- [ ] Can login with super admin
- [ ] Regular user sees only their tenant's data
- [ ] Super admin can see all tenants
- [ ] Tenant switcher works (super admin only)
- [ ] Invoice upload associates with correct tenant
- [ ] Data isolation works (users can't see other tenant data)
- [ ] Dashboard shows correct tenant name
- [ ] Stats are filtered by tenant

## 📊 Current Database State

- **Tenants:** 1 (Default Tenant)
- **Users:** 2 (admin@test.com, superadmin@test.com)
- **Units:** 23 (all in Default Tenant)
- **Leases:** 27 (all in Default Tenant)
- **Invoices:** 1,221 (all in Default Tenant)

## 🚀 Next Steps

1. **Test the system** - Follow testing steps above
2. **Create additional tenants** - Test multi-tenant isolation
3. **Import data for new tenants** - Test data import scripts
4. **Configure column mappings** - Per-tenant Excel column mappings
5. **Deploy to production** - PostgreSQL + cloud hosting

## 🐛 Troubleshooting

**Issue: "no such column: users.is_super_admin"**
- ✅ Fixed: Run `python scripts/add_missing_column.py`

**Issue: Can't see tenant switcher**
- Check if logged in as super admin
- Check browser console for errors

**Issue: Data not filtering by tenant**
- Verify tenant_id is set in session
- Check database queries are using `filter_by_tenant`

**Issue: Migration already run**
- Use `python scripts/migrate_to_multi_tenant.py --force` to re-run


