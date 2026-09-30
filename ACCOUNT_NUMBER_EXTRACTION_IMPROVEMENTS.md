# 🔧 Account Number Extraction Improvements

## **Issues Fixed**

### **Problem 1: Account Number Not Extracted Correctly**
- **Issue:** Account number was showing as invoice number (ABC123ABC instead of 0123 4567 89)
- **Fix:** Improved extraction to look in multiple places:
  - Azure fields (CustomerAccountNumber, AccountNumber, etc.)
  - PDF content text (searches for "Your account number: 0123 4567 89")
  - Table cells (searches tables for account number patterns)

### **Problem 2: Fallback to Invoice Number**
- **Issue:** If account number not found, it defaulted to invoice number
- **Fix:** Removed fallback - now fails validation if account number is missing
- **Reason:** Account number is mandatory and unique - should never use invoice number as fallback

---

## **✅ Changes Made**

### **1. PDF Normalizer** (`app/pdf_normalizer.py`)
- ✅ Improved account number extraction patterns
- ✅ Searches content for "Your account number: 0123 4567 89" format
- ✅ Searches tables for account number patterns
- ✅ Removed fallback to invoice number
- ✅ Returns None if not found (validation will catch it)

### **2. Validation** (`main.py`)
- ✅ Stricter validation - fails if account number is missing
- ✅ Checks that account number is not "UNKNOWN"
- ✅ Checks that account number is not same as invoice number
- ✅ Clear error messages

### **3. Debug Script** (`scripts/debug_pdf_extraction.py`)
- ✅ Added account number to output for debugging

---

## **🔍 How Account Number Extraction Works Now**

### **Step 1: Try Azure Fields**
Looks for:
- `CustomerAccountNumber`
- `AccountNumber`
- `Account`
- `CustomerNumber`
- `CustomerAccount`
- `AccountNo`
- `Account Number`

### **Step 2: Search PDF Content**
Searches for patterns like:
- "Your account number: 0123 4567 89"
- "Account number: 0123 4567 89"
- "Account: 0123456789"
- "Customer account: 0123 4567 89"

### **Step 3: Search Tables**
If not found in content, searches table cells for account number patterns.

### **Step 4: Validation**
- If still not found → Returns None
- Validation catches it → Shows clear error
- **No fallback to invoice number** ✅

---

## **🧪 Testing Your E.ON PDF**

Run the debug script to see what's extracted:

```bash
python scripts/debug_pdf_extraction.py EonElectricityBill.pdf
```

**Expected Result:**
- Account Number: `0123 4567 89` (from "Your account number: 0123 4567 89")
- Invoice Number: `ABC123ABC` (different from account number)

---

## **⚠️ Important**

1. **No Fallbacks:** Account number must be extracted - no defaults
2. **Validation:** Upload will fail if account number is missing
3. **Unique:** Account number should be different from invoice number
4. **Required:** Both PDF and Excel/CSV must include account number

---

## **📋 Next Steps**

1. **Test extraction:**
   ```bash
   python scripts/debug_pdf_extraction.py EonElectricityBill.pdf
   ```

2. **Check what Azure extracted:**
   - Look at the fields output
   - See if account number is in the content

3. **If still not extracting:**
   - We may need to add E.ON-specific extraction logic
   - Or improve the content search patterns

---

## **✅ Status**

- ✅ Improved extraction patterns
- ✅ Removed fallback logic
- ✅ Stricter validation
- ✅ Better error messages

**Ready to test!** 🚀

