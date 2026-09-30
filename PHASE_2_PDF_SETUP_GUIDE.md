# 🚀 Phase 2: PDF Invoice Integration - Setup Guide

## ✅ **What's Been Implemented**

### **1. PDF Processor Module** (`app/pdf_processor.py`)
- ✅ Azure Document Intelligence integration
- ✅ PDF extraction using prebuilt Invoice model
- ✅ Structured JSON output conversion
- ✅ Error handling and logging

### **2. PDF Normalizer Module** (`app/pdf_normalizer.py`)
- ✅ Converts Azure JSON to Invoice schema
- ✅ Handles UK energy suppliers (British Gas, E.ON, Octopus)
- ✅ Date parsing (multiple formats)
- ✅ Amount parsing (currency handling)
- ✅ Unit ID extraction from addresses
- ✅ Utility type detection

### **3. Upload Integration** (`main.py`)
- ✅ Updated `/api/upload` endpoint to accept PDF files
- ✅ Created `process_pdf_invoice()` function
- ✅ Background processing for PDFs
- ✅ Automatic validation after extraction

### **4. UI Updates** (`templates/upload.html`)
- ✅ File input accepts `.pdf` files
- ✅ Updated help text to mention PDF support

---

## 📦 **Required Dependencies**

### **Install Azure Document Intelligence SDK**

```bash
pip install azure-ai-documentintelligence
```

Or add to `requirements.txt`:

```
azure-ai-documentintelligence>=1.0.0
```

---

## 🔧 **Configuration**

### **1. Azure Document Intelligence Setup**

You need to set up an Azure Document Intelligence resource:

1. **Create Azure Resource:**
   - Go to [Azure Portal](https://portal.azure.com)
   - Create a "Document Intelligence" resource (or "Form Recognizer" in older regions)
   - Choose a pricing tier (Free tier available for testing)

2. **Get Credentials:**
   - Copy the **Endpoint** URL
   - Copy the **API Key**

3. **Set Environment Variables:**

Add to your `.env` file:

```env
# Azure Document Intelligence
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_DOCUMENT_INTELLIGENCE_API_KEY=your-api-key-here
```

Or set in Azure App Service:
- Go to Configuration → Application Settings
- Add:
  - `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT`
  - `AZURE_DOCUMENT_INTELLIGENCE_API_KEY`

---

## 🧪 **Testing**

### **1. Test PDF Upload**

1. **Start the application:**
   ```bash
   uvicorn main:app --reload
   ```

2. **Upload a PDF invoice:**
   - Go to `/upload`
   - Select a PDF file (British Gas, E.ON, or Octopus invoice)
   - Click "Upload"

3. **Check processing:**
   - Monitor console logs for extraction progress
   - Check `/invoices` page for processed invoice
   - View invoice details to verify extracted data

### **2. Test with Sample PDFs**

You can test with:
- British Gas invoice PDF
- E.ON invoice PDF
- Octopus Energy invoice PDF

---

## 📋 **How It Works**

### **PDF Processing Flow:**

```
1. User uploads PDF
   ↓
2. File saved to uploads/ directory
   ↓
3. Background task: process_pdf_invoice()
   ↓
4. PDF Processor: Extract data using Azure Document Intelligence
   ↓
5. PDF Normalizer: Convert Azure JSON to Invoice schema
   ↓
6. Save to database (Invoice table)
   ↓
7. Auto-validate using existing validation engine
   ↓
8. Display results in UI
```

### **Key Features:**

- **Multi-page support:** Azure Document Intelligence handles multi-page invoices
- **Table extraction:** Line items and tables are extracted
- **Supplier-specific:** Normalizer can be extended for supplier-specific logic
- **Error handling:** Comprehensive error logging and user feedback
- **Duplicate detection:** Same as Excel/CSV flow

---

## 🔍 **Troubleshooting**

### **Error: "Azure Document Intelligence credentials not found"**

**Solution:**
- Check that `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT` and `AZURE_DOCUMENT_INTELLIGENCE_API_KEY` are set
- Verify `.env` file is loaded
- Check Azure App Service configuration

### **Error: "Failed to extract PDF invoice"**

**Possible causes:**
- Invalid PDF file
- PDF is password-protected
- PDF is corrupted
- Azure API quota exceeded

**Solution:**
- Verify PDF is valid and not password-protected
- Check Azure portal for API usage/quota
- Review logs in `uploads/upload_BATCH_xxx.log`

### **Error: "No valid invoice data extracted"**

**Possible causes:**
- PDF doesn't contain invoice data
- Invoice format not recognized
- Missing required fields (invoice number, dates, amounts)

**Solution:**
- Check extracted data in logs
- Verify PDF contains standard invoice fields
- May need supplier-specific normalizer adjustments

---

## 🚀 **Next Steps**

### **1. Supplier-Specific Normalizers** (Optional)

Create custom normalizers for each supplier:

```python
# app/pdf_normalizers/british_gas.py
class BritishGasNormalizer(PDFNormalizer):
    def _extract_unit_id(self, address, fields):
        # British Gas-specific logic
        pass
```

### **2. Manual Correction UI** (Future)

Allow users to correct low-confidence extractions:
- Show extracted data with confidence scores
- Provide edit interface
- Save corrections for training

### **3. Batch PDF Processing** (Future)

Process multiple PDFs in one upload:
- Extract each PDF separately
- Combine into single batch
- Show progress per PDF

---

## 📊 **Cost Estimation**

### **Azure Document Intelligence Pricing:**

- **Free Tier:** 500 pages/month
- **S0 Tier:** $1.50 per 1,000 pages
- **S1 Tier:** Custom pricing

**For 3,000 invoices/month:**
- Average 2 pages per invoice = 6,000 pages/month
- Cost: ~$9/month (S0 tier)

---

## ✅ **Checklist**

- [ ] Install `azure-ai-documentintelligence` package
- [ ] Set up Azure Document Intelligence resource
- [ ] Add environment variables to `.env`
- [ ] Test PDF upload with sample invoice
- [ ] Verify extraction accuracy
- [ ] Check validation results
- [ ] Monitor Azure usage/quota

---

## 🎯 **Status**

**Phase 2 PDF Integration: COMPLETE** ✅

- ✅ PDF processor module
- ✅ PDF normalizer module
- ✅ Upload endpoint integration
- ✅ UI updates
- ✅ Background processing
- ✅ Error handling

**Ready for testing!** 🚀



