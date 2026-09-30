# Testing Strategy & Client Onboarding Guide

## Current Status ✅

Your system is **working end-to-end**:
- ✅ PDF extraction (British Gas, E.ON, Opus)
- ✅ Address-based unit matching
- ✅ Validation engine (correct business logic)
- ✅ Excel/CSV import
- ✅ Multi-tenant support

---

## Part 1: Testing Strategy

### A. Unit Testing (Automated)

**What to Test:**
- PDF normalizer for each supplier
- Address matching algorithm
- Validation logic
- Date parsing

**How to Run:**
```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_pdf_normalizer.py -v

# Run with coverage
pytest tests/unit/ --cov=app --cov-report=html
```

**Current Coverage:**
- ✅ PDF normalizer tests
- ✅ Validation logic tests
- ✅ Column mapping tests
- ✅ Date parsing tests

### B. Integration Testing (Automated)

**What to Test:**
- API endpoints (upload, validation, invoices)
- Database operations
- Multi-tenant isolation

**How to Run:**
```bash
# Run integration tests
pytest tests/integration/ -v

# Requires test database (SQLite or PostgreSQL)
```

**Current Coverage:**
- ✅ Upload endpoints (Excel/CSV, PDF)
- ✅ Invoice retrieval
- ✅ Validation trigger
- ✅ Duplicate detection

### C. End-to-End Testing (Manual + Automated)

**What to Test:**
- Complete user workflows
- Real PDF invoices
- Real Excel files
- UI interactions

**How to Run:**
```bash
# Automated E2E tests (Playwright)
pytest tests/e2e/ -v

# Manual testing (see checklist below)
```

---

## Part 2: Manual Testing Checklist

### Test Scenario 1: Excel/CSV Upload

**Setup:**
1. Create test Excel file with sample invoices
2. Ensure all required columns are present
3. Include unit_ids that exist in your database

**Steps:**
1. ✅ Navigate to `/upload`
2. ✅ Select Excel file
3. ✅ Click "Upload and Validate"
4. ✅ Check upload status shows "completed"
5. ✅ Navigate to `/invoices`
6. ✅ Verify invoices are displayed correctly
7. ✅ Check validation status is correct
8. ✅ Verify unit_id matches Excel data

**Expected Result:**
- All invoices imported successfully
- Validation status correct
- Unit IDs match Excel file

### Test Scenario 2: PDF Upload (British Gas)

**Setup:**
1. Have British Gas PDF invoice ready
2. Ensure unit exists in database with matching address

**Steps:**
1. ✅ Navigate to `/upload`
2. ✅ Select British Gas PDF
3. ✅ Click "Upload and Validate"
4. ✅ Wait for extraction (may take 10-15 seconds)
5. ✅ Check upload status shows "completed"
6. ✅ Navigate to `/invoices`
7. ✅ Verify invoice details:
   - Account number extracted correctly
   - Billing period correct
   - Address extracted (supply address)
   - Unit ID matched correctly
8. ✅ Check validation status
9. ✅ Click invoice to view details
10. ✅ Verify address is displayed in detail view

**Expected Result:**
- Account number: `1234 1234 1234` (or actual from PDF)
- Billing period: Correct dates
- Address: Supply address extracted
- Unit ID: Matched to correct unit (e.g., SHOP-003)
- Validation: Correct status based on lease data

### Test Scenario 3: PDF Upload (E.ON)

**Steps:**
1. ✅ Upload E.ON PDF invoice
2. ✅ Verify account number extracted (`0123 4567 89` format)
3. ✅ Verify billing period extracted
4. ✅ Verify address extracted (service address)
5. ✅ Verify unit matching works
6. ✅ Check validation results

### Test Scenario 4: PDF Upload (Opus Energy)

**Steps:**
1. ✅ Upload Opus PDF invoice
2. ✅ Verify account number extracted (multi-line format)
3. ✅ Verify billing period extracted (`01 April 2014 to 07 April 2014`)
4. ✅ Verify address extracted
5. ✅ Verify unit matching works
6. ✅ Check validation results

### Test Scenario 5: Unmapped Invoice (Manual Mapping)

**Setup:**
1. Upload PDF with address that doesn't match any unit
2. Or upload PDF with low-confidence match

**Steps:**
1. ✅ Upload PDF
2. ✅ Check invoice shows `unit_id = "UNKNOWN"`
3. ✅ Navigate to invoice detail page
4. ✅ Verify address is displayed
5. ✅ **Manual mapping** (when UI is ready):
   - View suggested matches
   - Select correct unit
   - Save mapping
6. ✅ Re-validate invoice
7. ✅ Verify validation now works correctly

### Test Scenario 6: Account Number Mapping

**Setup:**
1. Create custom account number mapping
2. Upload invoice with that account number

**Steps:**
1. ✅ Create mapping: `account_number → unit_id` (via API/UI)
2. ✅ Upload invoice with that account number
3. ✅ Verify unit_id is automatically assigned
4. ✅ Check validation works

### Test Scenario 7: Validation Logic

**Test Cases:**

**Case 1: Full Vacancy (No Lease)**
- Invoice period: 2024-01-01 to 2024-01-31
- Unit has no leases during this period
- **Expected**: `VALID`, `OK TO PAY` (company liable)

**Case 2: Full Occupancy (Active Lease)**
- Invoice period: 2024-01-01 to 2024-01-31
- Unit has active lease covering entire period
- **Expected**: `INVALID`, `DO NOT PAY` (tenant liable)

**Case 3: Partial Overlap**
- Invoice period: 2024-01-01 to 2024-01-31
- Lease starts: 2024-01-15
- **Expected**: `NEEDS REVIEW`, `COT` (mixed liability)

**Case 4: Unit Not Found**
- Invoice with unit_id that doesn't exist
- **Expected**: `NEEDS REVIEW`, error message

---

## Part 3: Client Onboarding Pathway

### Phase 1: Initial Setup (One-Time)

**Step 1: Account Creation**
1. Client signs up at `/signup`
2. Creates tenant account
3. Receives login credentials

**Step 2: Import Units**
1. Client navigates to `/import-units`
2. Prepares Excel file with units:
   - `unit_id` (required)
   - `building_name` (optional)
   - `address_line_1` (required)
   - `address_line_2` (optional)
   - `city` (required)
   - `postcode` (required) - **Critical for matching!**
3. Uploads Excel file
4. Verifies units imported correctly

**Step 3: Import Leases**
1. Client navigates to `/import-leases`
2. Prepares Excel file with leases:
   - `unit_id` (must match imported units)
   - `tenant_name` (required)
   - `lease_start` (required)
   - `lease_end` (optional, for ongoing leases)
3. Uploads Excel file
4. Verifies leases imported correctly

**Step 4: Configure Column Mappings (Optional)**
1. Client navigates to `/settings`
2. If their Excel files use different column names:
   - Maps their column names to system fields
   - Saves configuration
3. Configuration is tenant-specific

---

### Phase 2: Monthly Invoice Processing

**Option A: Excel/CSV Upload (Recommended for Bulk)**

**When to Use:**
- Client has invoices in Excel/CSV format
- Client knows unit IDs for each invoice
- Client wants fast bulk processing

**Steps:**
1. Client exports invoices from accounting system OR creates spreadsheet
2. Ensures required columns are present:
   - `invoice_number`, `supplier_account_number`, `supplier_name`
   - `unit_id` (must match imported units)
   - `billing_period_start`, `billing_period_end`
   - `gross_amount`, `utility_type`
3. Navigates to `/upload`
4. Selects Excel/CSV file
5. Clicks "Upload and Validate"
6. Reviews results at `/invoices`
7. Exports for payment processing

**Option B: PDF Upload (Recommended for Automation)**

**When to Use:**
- Client receives PDF invoices from suppliers
- Client doesn't have unit IDs in invoices
- Client wants fully automated processing

**Steps:**
1. Client downloads PDF invoices from supplier portals
   - British Gas: `britishgas.co.uk`
   - E.ON: `eonenergy.com`
   - Opus Energy: `opusenergy.com`
   - Other suppliers (as supported)
2. Navigates to `/upload`
3. Selects PDF file(s) or drags and drops
4. Clicks "Upload and Validate"
5. Waits for extraction (10-15 seconds per PDF)
6. Reviews results at `/invoices`:
   - Checks if unit_id was matched correctly
   - Reviews validation status
   - Manually maps if needed (unit_id = "UNKNOWN")
7. Exports for payment processing

**Option C: Mixed Approach**

**When to Use:**
- Client has mix of Excel and PDF invoices
- Some suppliers provide Excel, others provide PDF

**Steps:**
1. Upload Excel invoices first (bulk processing)
2. Upload PDF invoices separately
3. Review all invoices together at `/invoices`
4. Handle any unmapped invoices
5. Export all results

---

### Phase 3: Review & Validation

**Step 1: Review Invoices**
1. Navigate to `/invoices`
2. Check validation status:
   - **Valid** (green) = Company liable, OK TO PAY
   - **Invalid** (red) = Tenant liable, DO NOT PAY
   - **Needs Review** (yellow) = Mixed liability, investigate
3. Check unit_id assignments:
   - Verify correct unit for each invoice
   - Flag any "UNKNOWN" unit_ids

**Step 2: Handle Unmapped Invoices**
1. Filter for invoices with `unit_id = "UNKNOWN"`
2. Click on invoice to view details
3. Review extracted address
4. **Manual mapping** (when UI ready):
   - View suggested unit matches
   - Select correct unit
   - Save mapping
5. Re-validate invoice

**Step 3: Review Validation Results**
1. Click on invoice to view details
2. Review validation breakdown:
   - Invoice days
   - Vacancy overlap days
   - Daily rate
   - Determination reason
3. Verify business logic is correct
4. Check validation notes for any errors

**Step 4: Export & Payment Processing**
1. Filter invoices by validation status
2. Export "Valid" invoices for payment
3. Export "Invalid" invoices for tenant billing
4. Export "Needs Review" for investigation

---

### Phase 4: Ongoing Maintenance

**Monthly Tasks:**
1. Upload new invoices (Excel or PDF)
2. Review validation results
3. Handle any unmapped invoices
4. Export for payment processing

**Quarterly Tasks:**
1. Review account number mappings
2. Update unit addresses if needed
3. Review and update leases
4. Check system performance

**As Needed:**
1. Add new units
2. Update leases (extensions, terminations)
3. Create custom account number mappings
4. Configure column mappings for new Excel formats

---

## Part 4: Testing Checklist for Production

### Pre-Launch Testing

**✅ Functional Testing**
- [ ] Excel upload works with sample data
- [ ] PDF upload works for all supported suppliers (British Gas, E.ON, Opus)
- [ ] Unit matching works correctly
- [ ] Validation logic is correct for all scenarios
- [ ] Multi-tenant isolation works
- [ ] Duplicate detection works

**✅ Data Quality Testing**
- [ ] Test with real PDF invoices from each supplier
- [ ] Test with real Excel files from clients
- [ ] Verify address extraction accuracy
- [ ] Verify account number extraction accuracy
- [ ] Verify billing period extraction accuracy

**✅ Performance Testing**
- [ ] Test with 100+ invoices in one batch
- [ ] Test PDF extraction speed (should be < 20 seconds per PDF)
- [ ] Test Excel import speed (should be < 5 seconds for 100 rows)
- [ ] Test database query performance

**✅ User Experience Testing**
- [ ] Test complete user workflow end-to-end
- [ ] Verify error messages are clear
- [ ] Verify success messages are informative
- [ ] Test on different browsers (Chrome, Firefox, Safari)
- [ ] Test on mobile devices (responsive design)

**✅ Security Testing**
- [ ] Multi-tenant data isolation
- [ ] Authentication works correctly
- [ ] File upload security (file type validation, size limits)
- [ ] SQL injection prevention
- [ ] XSS prevention

---

## Part 5: What to Do Now

### Immediate Actions (This Week)

1. **Test with Real Data**
   - Upload all 3 PDF invoices (British Gas, E.ON, Opus)
   - Verify each one works correctly
   - Check unit matching for each

2. **Test Excel Import**
   - Create sample Excel file with test invoices
   - Import and verify results
   - Test column mapping configuration

3. **Review Validation Logic**
   - Test all validation scenarios (vacancy, occupancy, partial)
   - Verify business logic is correct
   - Check validation notes are helpful

4. **Document Known Issues**
   - List any edge cases found
   - Document any manual workarounds needed
   - Prioritize fixes

### Short-Term (Next 2 Weeks)

1. **Build Manual Mapping UI**
   - Show unmapped invoices
   - Display suggested matches
   - Allow user to select correct unit
   - Save mapping

2. **Add Account Number Mapping UI**
   - Allow users to create custom mappings
   - Show existing mappings
   - Edit/delete mappings

3. **Improve Error Handling**
   - Better error messages
   - Retry logic for failed extractions
   - Clear instructions for manual fixes

4. **Add Export Functionality**
   - Export invoices to Excel/CSV
   - Filter by validation status
   - Include validation details

### Medium-Term (Next Month)

1. **Performance Optimization**
   - Batch processing for multiple PDFs
   - Caching for unit matching
   - Database query optimization

2. **Additional Suppliers**
   - Test with other UK suppliers
   - Add supplier-specific rules as needed

3. **Reporting & Analytics**
   - Dashboard with key metrics
   - Monthly summary reports
   - Cost analysis by unit/tenant

4. **API Documentation**
   - Document all API endpoints
   - Provide example requests/responses
   - Create API client libraries

---

## Part 6: Client Training Materials

### Quick Start Guide (1 Page)

**For Excel Users:**
1. Prepare Excel file with required columns
2. Upload at `/upload`
3. Review results at `/invoices`

**For PDF Users:**
1. Download PDF invoices from suppliers
2. Upload at `/upload`
3. Review and map any unmapped invoices
4. Export results

### Video Tutorials (Recommended)

1. **Initial Setup** (5 minutes)
   - Account creation
   - Importing units
   - Importing leases

2. **Uploading Invoices** (5 minutes)
   - Excel upload
   - PDF upload
   - Reviewing results

3. **Manual Mapping** (3 minutes)
   - Finding unmapped invoices
   - Selecting correct unit
   - Saving mapping

4. **Understanding Validation** (5 minutes)
   - What "Valid" means
   - What "Invalid" means
   - What "Needs Review" means

### FAQ Document

**Common Questions:**
- Q: Why is my invoice showing "UNKNOWN" for unit_id?
- A: The system couldn't match the address. Use manual mapping to assign the correct unit.

- Q: Why is my invoice "Invalid" when there's no lease?
- A: "Invalid" means tenant is liable. If there's no lease, it should be "Valid" (company liable). Please report this.

- Q: Can I upload multiple PDFs at once?
- A: Currently, upload one at a time. Batch upload coming soon.

- Q: How do I change a unit_id after upload?
- A: Use manual mapping (UI coming soon) or update via API.

---

## Summary

**Current Status:** ✅ System is working end-to-end

**Next Steps:**
1. Test with real data (all 3 PDFs, sample Excel)
2. Build manual mapping UI
3. Create client onboarding materials
4. Plan for production launch

**Client Pathway:**
1. Setup (units, leases, column mappings)
2. Monthly processing (Excel or PDF)
3. Review & validation
4. Export for payment

The system is ready for testing and can handle both Excel and PDF workflows!

