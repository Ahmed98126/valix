# PDF Testing Results & Analysis

## 📋 **Testing Process**

We're systematically testing all PDF invoices to verify Azure Document Intelligence extraction accuracy.

---

## 🧪 **Test Script**

Run the test script to analyze all PDFs:
```bash
python scripts/test_all_pdfs.py
```

This will:
1. Extract data from each PDF using Azure Document Intelligence
2. Show raw Azure fields
3. Normalize to our Invoice schema
4. Check for missing required fields
5. Report any issues

---

## 📊 **Results**

### **PDF 1: EonElectricityBill.pdf**
- Status: [To be tested]
- Issues: [To be filled]
- Notes: [To be filled]

### **PDF 2: british gas energy bill.pdf**
- Status: [To be tested]
- Issues: [To be filled]
- Notes: [To be filled]

### **PDF 3: Opus-Invoice.pdf**
- Status: [To be tested]
- Issues: [To be filled]
- Notes: [To be filled]

---

## 🔍 **What We're Checking**

### **Required Fields:**
- ✅ `invoice_number` - Must be present
- ✅ `supplier_account_number` - Must be present and different from invoice_number
- ✅ `supplier_name` - Should be present
- ✅ `billing_period_start` - Should be present
- ✅ `billing_period_end` - Should be present
- ✅ `gross_amount` - Should be present

### **Optional but Important:**
- `unit_id` - May need manual mapping
- `utility_type` - Should be detected
- `invoice_date` - Should be present

---

## 🐛 **Common Issues to Watch For**

1. **Account Number Extraction**
   - Not found in Azure fields
   - Found but same as invoice number
   - Found but incorrect format

2. **Date Parsing**
   - Dates in unexpected formats
   - Missing dates
   - Incorrect date ranges

3. **Amount Extraction**
   - Missing amounts
   - Incorrect currency
   - Wrong decimal places

4. **Supplier Detection**
   - Supplier name not recognized
   - Utility type not detected

---

## ✅ **Next Steps After Testing**

1. **If extraction is good:**
   - Proceed to production deployment
   - Test with more invoices
   - Monitor in production

2. **If issues found:**
   - Fix extraction patterns
   - Improve normalization logic
   - Add supplier-specific rules
   - Test again

---

**Run the test script to see results!**

