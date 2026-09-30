# 🚀 PDF Testing Quick Start

## **You Have Real PDFs - Let's Test Them!**

You have 3 real UK energy bill PDFs. Here's the fastest way to test them.

---

## ⚡ **5-Minute Quick Test**

### **1. Set Up Azure** (if not done)

```bash
# Install package
pip install azure-ai-documentintelligence
```

Add to `.env`:
```env
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_API_KEY=your-api-key-here
```

### **2. Test Extraction** (2 minutes)

```bash
# Test your E.ON PDF
python scripts/test_pdf_extraction.py EonElectricityBill.pdf
```

This shows you:
- ✅ What Azure extracted
- ✅ What got normalized
- ✅ Any missing fields
- ✅ Quality checks

### **3. Upload via UI** (2 minutes)

1. Start app: `uvicorn main:app --reload`
2. Go to: `http://localhost:8000/upload`
3. Upload your PDF
4. Check results at: `http://localhost:8000/invoices`

---

## 📋 **What to Check**

Compare the extracted data with your PDF:

| Field | Your E.ON Bill | Extracted? |
|-------|----------------|------------|
| Invoice Number | `ABC123ABC` | ✅ |
| Date | `18 February 2014` | ✅ |
| Amount | `£48.59` | ✅ |
| Billing Period | `08 Jan 14 to 18 Feb 14` | ✅ |
| Supplier | `E.ON` | ✅ |
| Unit ID | (from address) | ⚠️ |

---

## 🎯 **Expected Results**

**For your E.ON bill, you should see:**

```
Invoice Number: ABC123ABC
Supplier Name: E.ON or E.ON Energy Solutions
Invoice Date: 2014-02-18
Billing Period Start: 2014-01-08
Billing Period End: 2014-02-18
Gross Amount: 48.59
Utility Type: Electricity
```

---

## ⚠️ **Common Issues**

### **Unit ID Missing?**
- Normal - may need address extraction
- Check if account number is used instead
- Can be improved in normalizer later

### **Dates Wrong?**
- E.ON uses `08 Jan 14` format
- Should parse to `2014-01-08`
- If wrong, we'll fix the normalizer

### **Amount Wrong?**
- Should extract `£48.59` as `48.59`
- Check VAT and net amounts too

---

## ✅ **You're Ready!**

1. Run the test script
2. Upload via UI
3. Compare results with PDF
4. Note any issues
5. We'll fix them together!

**Start testing now!** 🎯

