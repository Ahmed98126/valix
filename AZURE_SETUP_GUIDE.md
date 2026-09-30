# 🔧 Azure Document Intelligence Setup Guide

## ✅ **Package Installed!**

The `azure-ai-documentintelligence` package has been installed. Now you need to set up your Azure resource.

---

## 🚀 **Quick Setup (15 minutes)**

### **Step 1: Create Azure Resource** (10 minutes)

1. **Go to Azure Portal:**
   - Visit: https://portal.azure.com
   - Sign in with your Azure account (or create a free account)

2. **Create Document Intelligence Resource:**
   - Click "Create a resource"
   - Search for "Document Intelligence" (or "Form Recognizer" in older regions)
   - Click "Create"

3. **Fill in Details:**
   - **Subscription:** Choose your subscription
   - **Resource Group:** Create new or use existing
   - **Region:** Choose closest to you (e.g., "UK South" or "West Europe")
   - **Name:** e.g., `valix-document-intelligence`
   - **Pricing Tier:** 
     - **Free (F0):** 500 pages/month - Perfect for testing! ✅
     - **S0:** $1.50 per 1,000 pages - For production

4. **Click "Review + create"** then **"Create"**

5. **Wait for deployment** (1-2 minutes)

### **Step 2: Get Your Credentials** (2 minutes)

1. **Go to your resource:**
   - Click "Go to resource" after deployment
   - Or search for your resource name in Azure Portal

2. **Get Endpoint:**
   - Go to "Keys and Endpoint" in left menu
   - Copy the **Endpoint** URL
   - Looks like: `https://your-resource.cognitiveservices.azure.com/`

3. **Get API Key:**
   - In same "Keys and Endpoint" page
   - Copy **Key 1** (or Key 2, both work)

### **Step 3: Add to Your Project** (2 minutes)

1. **Open your `.env` file** (in project root)

2. **Add these lines:**
   ```env
   # Azure Document Intelligence
   AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
   AZURE_DOCUMENT_INTELLIGENCE_API_KEY=your-key-here
   ```

3. **Replace with your actual values:**
   - Replace `https://your-resource...` with your Endpoint
   - Replace `your-key-here` with your Key 1

4. **Save the file**

### **Step 4: Test It!** (1 minute)

1. **Restart your app:**
   ```bash
   uvicorn main:app --reload
   ```

2. **Test PDF extraction:**
   ```bash
   python scripts/test_pdf_extraction.py EonElectricityBill.pdf
   ```

---

## ✅ **Verification**

After setup, you should see:

1. **App starts without errors:**
   - No "ModuleNotFoundError"
   - No "credentials not found" errors

2. **Test script works:**
   - Extracts data from PDF
   - Shows normalized invoice data

3. **UI upload works:**
   - Can upload PDF files
   - Processing starts in background

---

## 💰 **Pricing**

### **Free Tier (F0):**
- ✅ 500 pages/month
- ✅ Perfect for testing
- ✅ No credit card required

### **S0 Tier (Production):**
- 💰 $1.50 per 1,000 pages
- 📊 For 3,000 invoices/month (avg 2 pages each = 6,000 pages)
- 💵 Cost: ~$9/month

**Recommendation:** Start with Free tier for testing, upgrade when ready for production.

---

## 🔍 **Troubleshooting**

### **Error: "Azure Document Intelligence credentials not found"**

**Solution:**
- Check `.env` file exists in project root
- Verify variable names are exact:
  - `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT`
  - `AZURE_DOCUMENT_INTELLIGENCE_API_KEY`
- Make sure no extra spaces or quotes
- Restart your app after adding to `.env`

### **Error: "Failed to extract PDF invoice"**

**Possible causes:**
- Invalid endpoint URL (must end with `/`)
- Wrong API key
- PDF is password-protected
- Azure quota exceeded (check Azure portal)

**Solution:**
- Verify endpoint and key in Azure portal
- Check PDF is not password-protected
- Check Azure portal → Usage for quota

### **Error: "ModuleNotFoundError: No module named 'azure'"**

**Solution:**
```bash
python -m pip install azure-ai-documentintelligence
```

---

## 📋 **Quick Checklist**

- [ ] Created Azure Document Intelligence resource
- [ ] Copied Endpoint URL
- [ ] Copied API Key
- [ ] Added to `.env` file
- [ ] Restarted app
- [ ] Tested with `test_pdf_extraction.py`
- [ ] Uploaded PDF via UI

---

## 🎯 **Next Steps**

Once Azure is set up:

1. **Test your E.ON PDF:**
   ```bash
   python scripts/test_pdf_extraction.py EonElectricityBill.pdf
   ```

2. **Upload via UI:**
   - Go to `/upload`
   - Upload your PDF
   - Check results at `/invoices`

3. **Test your other 2 PDFs**

4. **Verify extraction accuracy**

---

## ✅ **You're Ready!**

Once you've:
- ✅ Created Azure resource
- ✅ Added credentials to `.env`
- ✅ Restarted app

You can start testing PDF uploads! 🚀

