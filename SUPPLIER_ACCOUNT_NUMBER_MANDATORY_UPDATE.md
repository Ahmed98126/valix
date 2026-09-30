# ✅ Supplier Account Number - Now Mandatory

## **What Changed**

`supplier_account_number` is now a **required field** across the entire system.

---

## **✅ Updates Made**

### **1. Database Model** (`app/models.py`)
- ✅ Changed from `nullable=True` to `nullable=False`
- ✅ Field is now **required** in database

### **2. Invoice Table** (`templates/invoices.html`)
- ✅ Added "Account #" column **next to Invoice #**
- ✅ Displays account number in monospace font
- ✅ Shows "N/A" if missing (shouldn't happen now)

### **3. Invoice Detail Page** (`templates/invoice_detail.html`)
- ✅ Added "Account Number" field
- ✅ Displays next to Invoice Number

### **4. Upload Page** (`templates/upload.html`)
- ✅ Moved `supplier_account_number` to **Required Columns** list
- ✅ Removed from Optional list

### **5. Column Mapping** (`app/column_mapping.py`)
- ✅ Already includes `supplier_account_number` mappings

### **6. Excel/CSV Processing** (`main.py`)
- ✅ Added to required fields validation
- ✅ Validates account number exists before creating invoice
- ✅ Shows error if missing

### **7. PDF Processing** (`main.py` + `app/pdf_normalizer.py`)
- ✅ Validates account number is extracted
- ✅ Falls back to invoice number if not found (ensures it's never None)
- ✅ Shows error if missing

### **8. Schemas** (`app/schemas.py`)
- ✅ Changed from `Optional[str]` to `str` (required)

---

## **📋 Database Migration**

Since you already ran the migration in Supabase, you may need to update the column to be NOT NULL:

```sql
-- Make the column NOT NULL (if it's currently nullable)
ALTER TABLE invoices 
ALTER COLUMN supplier_account_number SET NOT NULL;

-- If you have existing NULL values, update them first:
UPDATE invoices 
SET supplier_account_number = invoice_number 
WHERE supplier_account_number IS NULL;
```

---

## **🎯 How It Works Now**

### **Excel/CSV Upload:**
- **Required:** Must have `supplier_account_number` column (or mapped equivalent)
- **Error if missing:** Upload will fail with clear error message

### **PDF Upload:**
- **Extracts:** Account number from PDF
- **Fallback:** Uses invoice number if not found (ensures it's never empty)
- **Error if missing:** Processing will fail

### **Invoice Table:**
- **Shows:** Account # column next to Invoice #
- **Format:** Monospace font for readability

---

## **✅ Status**

- ✅ Model updated (NOT NULL)
- ✅ UI updated (table + detail page)
- ✅ Upload page updated (required)
- ✅ Validation updated (required check)
- ✅ PDF normalizer updated (always extracts)
- ✅ Excel/CSV processing updated (required)

**Ready to test!** 🚀

---

## **⚠️ Important Notes**

1. **Existing invoices:** If you have invoices with NULL account numbers, update them first:
   ```sql
   UPDATE invoices 
   SET supplier_account_number = invoice_number 
   WHERE supplier_account_number IS NULL;
   ```

2. **PDF fallback:** If account number can't be extracted from PDF, it uses invoice number as fallback (ensures it's never None)

3. **Excel/CSV:** Must include account number column or upload will fail

---

## **🧪 Testing**

1. **Test Excel/CSV upload** with `supplier_account_number` column
2. **Test PDF upload** - should extract account number
3. **Check invoice table** - should show Account # column
4. **Check invoice detail** - should show Account Number field

**Everything is ready!** ✅

