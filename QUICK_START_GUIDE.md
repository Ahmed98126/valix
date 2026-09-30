# Quick Start Guide: Excel vs PDF Workflows

## 🎯 The Key Difference

| Excel/CSV | PDF |
|-----------|-----|
| **Client provides unit_id** | **System finds unit_id automatically** |
| Fast bulk import | Automated extraction |
| Requires data preparation | No data entry needed |

---

## 📊 Excel/CSV Workflow (5 Steps)

```
1. Prepare Excel File
   ├─ Required columns: invoice_number, supplier_account_number, 
   │  supplier_name, unit_id, billing_period_start, billing_period_end,
   │  gross_amount, utility_type
   └─ unit_id must match your Units table

2. Upload at /upload
   └─ Select Excel/CSV file

3. System Processes
   ├─ Maps columns (uses your tenant config)
   ├─ Validates required fields
   ├─ Creates Invoice records
   └─ Runs validation

4. Review Results at /invoices
   └─ Check validation status

5. Export for Payment
   └─ Filter by status and export
```

**Time:** ~30 seconds for 100 invoices  
**Best For:** Bulk imports, clients with unit IDs

---

## 📄 PDF Workflow (6 Steps)

```
1. Download PDF from Supplier
   └─ British Gas, E.ON, Opus Energy, etc.

2. Upload at /upload
   └─ Select PDF file

3. System Extracts (10-15 seconds)
   ├─ Azure Document Intelligence extracts data
   ├─ PDF Normalizer converts to Invoice schema
   └─ InvoiceUnitMapper finds matching unit

4. Review Results at /invoices
   ├─ Check if unit_id was matched correctly
   ├─ Review validation status
   └─ Flag any "UNKNOWN" unit_ids

5. Manual Mapping (if needed)
   ├─ Click invoice with unit_id = "UNKNOWN"
   ├─ View suggested matches
   └─ Select correct unit

6. Export for Payment
   └─ Filter by status and export
```

**Time:** ~15 seconds per PDF  
**Best For:** PDF invoices, automation, clients without unit IDs

---

## 🔄 Both Workflows Converge Here

```
┌─────────────────────────────────────┐
│   Invoice Record Created            │
│   (Same database table)             │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Validation Engine Runs             │
│   (Same validation logic)            │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Results Displayed                  │
│   (Same UI)                          │
└─────────────────────────────────────┘
```

**Key Point:** After extraction/mapping, both workflows are identical!

---

## ✅ What to Test Now

### Immediate Testing (This Week)

1. **Test Excel Upload**
   - [ ] Create sample Excel with 5-10 invoices
   - [ ] Upload and verify all import correctly
   - [ ] Check validation status is correct

2. **Test PDF Upload (All 3 Suppliers)**
   - [ ] British Gas PDF → Verify unit matching works
   - [ ] E.ON PDF → Verify extraction works
   - [ ] Opus PDF → Verify extraction works

3. **Test Validation Logic**
   - [ ] Invoice with no lease → Should be VALID
   - [ ] Invoice with active lease → Should be INVALID
   - [ ] Invoice with partial lease → Should be NEEDS REVIEW

4. **Test Edge Cases**
   - [ ] PDF with unmapped address → Should show "UNKNOWN"
   - [ ] Excel with missing unit_id → Should show error
   - [ ] Duplicate invoice → Should detect duplicate

---

## 👥 Client Onboarding Steps

### Phase 1: Setup (One-Time, 15 minutes)

1. **Sign Up** → Create account at `/signup`
2. **Import Units** → Upload Excel with unit data at `/import-units`
3. **Import Leases** → Upload Excel with lease data at `/import-leases`
4. **Configure Mappings** (Optional) → Set column mappings at `/settings`

### Phase 2: Monthly Processing (5-10 minutes)

**Option A: Excel Users**
1. Export invoices from accounting system
2. Upload at `/upload`
3. Review at `/invoices`
4. Export results

**Option B: PDF Users**
1. Download PDFs from supplier portals
2. Upload at `/upload`
3. Review and map any unmapped invoices
4. Export results

### Phase 3: Review (5 minutes)

1. Check validation status
2. Review any "Needs Review" invoices
3. Verify unit assignments
4. Export for payment

---

## 🚀 Next Steps

### This Week
1. ✅ Test all 3 PDF invoices
2. ✅ Test Excel import
3. ✅ Verify validation logic
4. ✅ Document any issues

### Next 2 Weeks
1. Build manual mapping UI
2. Add account number mapping UI
3. Improve error messages
4. Add export functionality

### Next Month
1. Performance optimization
2. Additional suppliers
3. Reporting dashboard
4. Client training materials

---

## 📚 Full Documentation

- **Excel vs PDF Workflow:** `EXCEL_VS_PDF_WORKFLOW.md`
- **Testing & Onboarding:** `TESTING_AND_CLIENT_ONBOARDING.md`
- **Mapping Strategy:** `INVOICE_UNIT_MAPPING_STRATEGY.md`
- **Address Extraction:** `ADDRESS_EXTRACTION_EXPLANATION.md`

---

## 💡 Key Takeaways

1. **Excel = Fast bulk import** (client provides unit_id)
2. **PDF = Automated extraction** (system finds unit_id)
3. **Both use same validation engine**
4. **Both display in same UI**
5. **System is ready for testing!**

