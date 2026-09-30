# Testing Checklist - Invoice Validator MVP

## 🧪 Comprehensive Testing Guide

Use this checklist to test all features before MVP launch.

---

## 1. Authentication & Multi-Tenant

### Login/Signup
- [ ] Create new account
- [ ] Login with existing account
- [ ] Select organization on login
- [ ] Auto-detect organization
- [ ] Logout works
- [ ] Session persists on page refresh
- [ ] Redirect to dashboard after login

### Multi-Tenant Isolation
- [ ] Create Tenant 1 with User 1
- [ ] Create Tenant 2 with User 2
- [ ] Login as User 1 → Only see Tenant 1 data
- [ ] Login as User 2 → Only see Tenant 2 data
- [ ] Verify no cross-tenant data access
- [ ] Test super admin (if exists) → Can see all tenants

---

## 2. Units & Leases Import

### Import Units
- [ ] Upload Excel file with units
- [ ] Upload CSV file with units
- [ ] Verify units created in database
- [ ] Test with missing columns (should handle gracefully)
- [ ] Test with invalid data (should show errors)
- [ ] Verify column mapping works
- [ ] Test updating existing units (same unit_id)

### Import Leases
- [ ] Upload Excel file with leases
- [ ] Upload CSV file with leases
- [ ] Verify leases created
- [ ] Test with invalid unit_id (should skip)
- [ ] Test with date formats (YYYY-MM-DD, DD/MM/YYYY)
- [ ] Verify unit timeline regenerated after import
- [ ] Test ongoing leases (empty lease_end)

---

## 3. Invoice Upload & Validation

### Upload
- [ ] Upload Excel invoice file
- [ ] Upload CSV invoice file
- [ ] Verify progress bar shows
- [ ] Test drag-and-drop
- [ ] Test file size limit (50MB)
- [ ] Test invalid file types (should reject)
- [ ] Verify background processing works

### Validation Logic
- [ ] Test duplicate detection (same invoice_number + gross_amount)
- [ ] Test vacancy overlap calculation
- [ ] Test occupied unit invoices
- [ ] Test vacant unit invoices
- [ ] Test landlord supply invoices
- [ ] Verify all determination types:
  - [ ] "OK TO PAY"
  - [ ] "DO NOT PAY"
  - [ ] "COT"
  - [ ] "Landlord Supply - OK TO PAY"
  - [ ] "OK TO PAY, SUBMIT METER READING"
  - [ ] "DO NOT PAY, SUBMIT METER READING"

### Validation Results
- [ ] View invoice details
- [ ] Verify validation status (Valid/Invalid/Needs Review)
- [ ] Check determination matches Databricks logic
- [ ] Verify error messages are clear

---

## 4. Data Management

### Units
- [ ] View all units
- [ ] Search units
- [ ] Edit unit details
- [ ] Delete unit (should cascade to leases)
- [ ] Pagination works
- [ ] Verify tenant isolation

### Leases
- [ ] View all leases
- [ ] Search leases
- [ ] Edit lease details
- [ ] Delete lease
- [ ] Verify timeline regenerated after edit
- [ ] Pagination works
- [ ] Verify tenant isolation

---

## 5. Invoices List

### Viewing
- [ ] View all invoices
- [ ] Search invoices (by invoice number, supplier, unit)
- [ ] Filter by status (Valid/Invalid/Needs Review)
- [ ] Filter by determination
- [ ] Pagination works
- [ ] Sort by date/amount
- [ ] View invoice details

### Export
- [ ] Export to CSV
- [ ] Verify CSV contains all data
- [ ] Test with filtered results
- [ ] Test with paginated results

---

## 6. Settings

### Column Mapping
- [ ] View current mappings
- [ ] Edit invoice column mappings
- [ ] Edit unit column mappings
- [ ] Edit lease column mappings
- [ ] Reset to defaults
- [ ] Save mappings
- [ ] Verify mappings applied to imports

### Data Source (Horizon)
- [ ] View Horizon configuration
- [ ] Test connection (if API available)
- [ ] Trigger sync (if available)

---

## 7. UI/UX

### Responsive Design
- [ ] Test on desktop (1920x1080)
- [ ] Test on laptop (1366x768)
- [ ] Test on tablet (768x1024)
- [ ] Test on mobile (375x667)
- [ ] Sidebar collapses on mobile
- [ ] Tables scroll horizontally on mobile
- [ ] Forms are usable on mobile

### Navigation
- [ ] All sidebar links work
- [ ] Active page highlighted
- [ ] Breadcrumbs (if any) work
- [ ] Back button works
- [ ] Logo links to dashboard

### Visual
- [ ] All colors match theme (black/white/gray)
- [ ] No blue colors remaining
- [ ] Hover effects work
- [ ] Animations smooth
- [ ] Loading states show
- [ ] Error messages clear

---

## 8. Edge Cases

### Data
- [ ] Empty database (no units/leases)
- [ ] No invoices uploaded
- [ ] Very large files (near 50MB limit)
- [ ] Special characters in data
- [ ] Unicode characters
- [ ] Very long text fields

### Validation
- [ ] Invoice with no matching unit
- [ ] Invoice with overlapping dates
- [ ] Invoice with zero amount
- [ ] Invoice with negative amount
- [ ] Invoice with future dates
- [ ] Invoice with very old dates

### Multi-Tenant
- [ ] User with no tenant
- [ ] Tenant with no users
- [ ] Tenant with no data
- [ ] Delete tenant (should handle gracefully)

---

## 9. Performance

### Load Testing
- [ ] Upload 100+ invoices
- [ ] Import 1000+ units
- [ ] Import 1000+ leases
- [ ] Search with large dataset
- [ ] Pagination with large dataset
- [ ] Export large dataset

### Response Times
- [ ] Page load < 2 seconds
- [ ] Search results < 1 second
- [ ] File upload progress updates
- [ ] Validation completes in reasonable time

---

## 10. Security

### Authentication
- [ ] Cannot access pages without login
- [ ] Session expires after inactivity
- [ ] Passwords hashed (not plain text)
- [ ] CSRF protection (if implemented)

### Data Access
- [ ] Users cannot access other tenants' data
- [ ] SQL injection protection
- [ ] File upload validation
- [ ] XSS protection

---

## 11. Error Handling

### User-Friendly Errors
- [ ] Invalid file format → Clear error
- [ ] Missing columns → Helpful message
- [ ] Network errors → Retry option
- [ ] Validation errors → Explain issue
- [ ] Database errors → Generic message (no stack trace)

### Logging
- [ ] Errors logged to file
- [ ] Important actions logged
- [ ] No sensitive data in logs

---

## 12. End-to-End Scenarios

### Scenario 1: New Client Onboarding
1. [ ] Create tenant
2. [ ] Create user for tenant
3. [ ] Login as new user
4. [ ] Import units
5. [ ] Import leases
6. [ ] Upload invoices
7. [ ] View validation results
8. [ ] Export CSV

### Scenario 2: Multiple Clients
1. [ ] Create 3 tenants
2. [ ] Create users for each
3. [ ] Import data for each
4. [ ] Upload invoices for each
5. [ ] Verify complete isolation
6. [ ] Test switching between tenants (if super admin)

### Scenario 3: Data Updates
1. [ ] Import initial units/leases
2. [ ] Upload invoices
3. [ ] Update lease dates
4. [ ] Verify timeline regenerated
5. [ ] Re-validate invoices
6. [ ] Verify results updated

---

## 📝 Test Results Template

**Date:** _______________
**Tester:** _______________
**Environment:** Development / Production

### Issues Found:
1. [Issue description]
   - Severity: Critical / High / Medium / Low
   - Steps to reproduce:
   - Expected:
   - Actual:

---

## ✅ Sign-Off

**Testing Complete:** [ ] Yes / [ ] No
**Ready for Production:** [ ] Yes / [ ] No
**Blockers:** _______________

**Notes:**
_______________
_______________


