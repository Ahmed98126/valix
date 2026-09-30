# 📄 PDF Invoice Testing Guide

## ✅ **You Have Real PDFs - Perfect for Testing!**

Having 3 real UK energy bill PDFs (like your E.ON bill) is actually **ideal** for initial testing. Here's how to use them effectively.

---

## 🎯 **What You Have**

Based on your E.ON bill, I can see it contains:
- ✅ Invoice number: `ABC123ABC`
- ✅ Date: `18 February 2014`
- ✅ Account number: `0123 4567 89`
- ✅ Amount: `£48.59`
- ✅ Billing period: `08 Jan 14 to 18 Feb 14`
- ✅ Address: Street, City, County, Post Code
- ✅ Meter readings and charges

**This is perfect for testing!** 🎉

---

## 📋 **Step-by-Step Testing Process**

### **Step 1: Organize Your PDFs** (2 minutes)

1. **Create a test folder:**
   ```bash
   mkdir test_pdfs
   ```

2. **Copy your PDFs there:**
   - `test_pdfs/EonElectricityBill.pdf`
   - `test_pdfs/BritishGas_xxx.pdf` (if you have one)
   - `test_pdfs/Octopus_xxx.pdf` (if you have one)

### **Step 2: Set Up Azure Document Intelligence** (15 minutes)

If you haven't already:

1. **Create Azure Resource:**
   - Go to [Azure Portal](https://portal.azure.com)
   - Create "Document Intelligence" resource
   - Get Endpoint and API Key

2. **Add to `.env`:**
   ```env
   AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
   AZURE_DOCUMENT_INTELLIGENCE_API_KEY=your-api-key-here
   ```

3. **Install package:**
   ```bash
   pip install azure-ai-documentintelligence
   ```

### **Step 3: Test PDF Extraction** (5 minutes)

I'll create a test script for you to verify extraction works:

```bash
python scripts/test_pdf_extraction.py test_pdfs/EonElectricityBill.pdf
```

This will show you:
- What Azure extracted
- What the normalizer converted it to
- Any issues or missing fields

### **Step 4: Upload via UI** (5 minutes)

1. **Start your app:**
   ```bash
   uvicorn main:app --reload
   ```

2. **Go to upload page:**
   - Navigate to `http://localhost:8000/upload`
   - Login if needed

3. **Upload PDF:**
   - Drag and drop or select your E.ON PDF
   - Click "Upload"
   - Wait for processing (check console logs)

4. **Check results:**
   - Go to `/invoices` page
   - Find your invoice
   - Click to view details
   - Verify extracted data matches the PDF

### **Step 5: Verify Extraction Accuracy** (10 minutes)

**Check these fields match your PDF:**

| Field | Expected (from your E.ON bill) | Check |
|-------|----------------------------------|-------|
| Invoice Number | `ABC123ABC` | ✅ |
| Supplier Name | `E.ON` or `E.ON Energy Solutions` | ✅ |
| Invoice Date | `2014-02-18` | ✅ |
| Billing Period Start | `2014-01-08` | ✅ |
| Billing Period End | `2014-02-18` | ✅ |
| Gross Amount | `48.59` | ✅ |
| Unit ID | (from address or account number) | ⚠️ |
| Utility Type | `Electricity` | ✅ |

**Common Issues to Watch For:**

1. **Unit ID Missing:**
   - May extract from address or account number
   - Check if it's in the "unit_id" field
   - If missing, we may need to adjust the normalizer

2. **Dates Wrong Format:**
   - E.ON uses `08 Jan 14` format
   - Should parse to `2014-01-08`
   - Check if dates are correct

3. **Amount Parsing:**
   - Should extract `£48.59` as `48.59`
   - Check VAT and net amounts too

---

## 🔍 **What to Look For**

### **✅ Success Indicators:**

- Invoice number extracted correctly
- Dates parsed correctly (billing period)
- Amount extracted correctly
- Supplier name recognized
- Invoice appears in database
- Validation runs successfully

### **⚠️ Issues to Note:**

- Missing fields (especially unit_id)
- Wrong date formats
- Amount parsing errors
- Supplier name variations
- Multi-page invoices (page 2 data)

---

## 📊 **Testing Checklist**

Use this checklist for each PDF:

- [ ] PDF uploads successfully
- [ ] No errors in console logs
- [ ] Invoice appears in `/invoices` page
- [ ] Invoice number matches PDF
- [ ] Supplier name matches PDF
- [ ] Dates match PDF (invoice date, billing period)
- [ ] Amount matches PDF (gross, net, VAT)
- [ ] Unit ID extracted (or noted if missing)
- [ ] Utility type correct (Electricity/Gas/Water)
- [ ] Validation runs (status: Valid/Invalid/Needs Review)
- [ ] Invoice detail page shows all data

---

## 🛠️ **If Something Doesn't Work**

### **Issue: Extraction fails**

**Check:**
- Azure credentials are correct
- PDF is not password-protected
- PDF is not corrupted
- Check logs in `uploads/upload_BATCH_xxx.log`

**Fix:**
- Verify Azure endpoint and API key
- Try a different PDF
- Check Azure portal for quota/errors

### **Issue: Missing fields**

**Check:**
- What Azure extracted (use test script)
- If field exists in Azure output but not normalized
- Check normalizer logic

**Fix:**
- Adjust `app/pdf_normalizer.py` for E.ON-specific fields
- Add supplier-specific logic if needed

### **Issue: Wrong dates/amounts**

**Check:**
- Date format in PDF
- Amount format in PDF
- Normalizer parsing logic

**Fix:**
- Update date parsing in normalizer
- Update amount parsing if needed

---

## 🎯 **Next Steps After Testing**

### **1. Document Findings**

Create a file `PDF_TEST_RESULTS.md`:

```markdown
# PDF Test Results

## E.ON Bill (EonElectricityBill.pdf)

**Date Tested:** [Today's date]

**Extraction Results:**
- Invoice Number: ✅ Extracted correctly
- Dates: ✅ Parsed correctly
- Amount: ✅ Extracted correctly
- Unit ID: ⚠️ Missing (needs address extraction)

**Issues Found:**
- [List any issues]

**Actions Needed:**
- [List fixes needed]
```

### **2. Improve Normalizer**

Based on test results, update `app/pdf_normalizer.py`:
- Add E.ON-specific field mappings
- Improve date parsing for E.ON format
- Enhance unit ID extraction

### **3. Test Other PDFs**

Repeat the process for:
- British Gas PDF (if you have one)
- Octopus PDF (if you have one)
- Any other energy bills

### **4. Create Supplier-Specific Normalizers** (Optional)

Once you have patterns, create:
- `app/pdf_normalizers/eon.py`
- `app/pdf_normalizers/british_gas.py`
- `app/pdf_normalizers/octopus.py`

---

## 💡 **Pro Tips**

1. **Test One PDF at a Time:**
   - Upload one PDF
   - Verify it works
   - Then test the next

2. **Check Logs:**
   - Console logs show extraction progress
   - `uploads/upload_BATCH_xxx.log` has detailed logs

3. **Compare with PDF:**
   - Open PDF side-by-side with invoice detail page
   - Verify each field matches

4. **Note Patterns:**
   - How does E.ON format dates?
   - Where is the unit ID in the PDF?
   - What fields are always present/missing?

5. **Iterate:**
   - Test → Find issues → Fix normalizer → Test again
   - Each iteration improves accuracy

---

## 🚀 **Quick Start Command**

Once Azure is set up:

```bash
# 1. Test extraction (see what Azure extracts)
python scripts/test_pdf_extraction.py test_pdfs/EonElectricityBill.pdf

# 2. Upload via UI
# Go to http://localhost:8000/upload and upload the PDF

# 3. Check results
# Go to http://localhost:8000/invoices
```

---

## ✅ **You're Ready!**

With 3 real PDFs, you can:
- ✅ Test the complete workflow
- ✅ Verify extraction accuracy
- ✅ Identify improvement areas
- ✅ Build confidence before production

**Start with your E.ON PDF and go from there!** 🎯

