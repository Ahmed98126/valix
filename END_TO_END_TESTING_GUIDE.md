# End-to-End Testing Guide

## 🎯 Purpose

This guide walks you through testing the complete workflow as if you're a new client onboarding to the invoice validator system. It verifies that:
- ✅ Frontend connects to Supabase backend
- ✅ User authentication works
- ✅ File uploads work
- ✅ Data is stored in Supabase
- ✅ Validation engine runs correctly
- ✅ Multi-tenant isolation works

---

## 📋 Prerequisites

1. **Supabase connection is working** (already verified ✅)
2. **Test data files created** (already created ✅)
3. **Database cleaned** (already done ✅)
4. **Test client created** (already done ✅)

---

## 🚀 Step-by-Step Testing

### **Step 1: Start the Server**

```bash
uvicorn main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

### **Step 2: Open the Application**

1. Open your browser
2. Go to: **http://localhost:8000**
3. You should see the **landing page**

---

### **Step 3: Login as Test Client**

1. Click **"Login"** or go to: **http://localhost:8000/login**
2. Enter credentials:
   - **Email**: `test@testproperties.com`
   - **Password**: `test123`
3. Click **"Sign In"**

**Expected Result**: 
- ✅ You're redirected to the dashboard
- ✅ You see "Test Property Management" as your tenant
- ✅ Dashboard shows 0 units, 0 leases, 0 invoices (empty state)

---

### **Step 4: Import Units Data**

1. In the sidebar, click **"Import Units"** (or go to `/import-units`)
2. Click **"Choose File"** or drag and drop
3. Select: **`test_data_units.xlsx`**
4. Click **"Upload and Import"**

**Expected Result**:
- ✅ File uploads successfully
- ✅ Success message appears
- ✅ You see 5 units imported:
   - SHOP-001 (High Street Mall, London)
   - SHOP-002 (High Street Mall, London)
   - OFFICE-101 (Business Tower, Manchester)
   - SHOP-003 (Shopping Centre, Birmingham)
   - WAREHOUSE-01 (Industrial Park, Leeds)

**Verify in Supabase**:
1. Go to: https://supabase.com/dashboard/project/xkbmbqejeoxfatcliftv/editor
2. Click on `units` table
3. You should see 5 records with `tenant_id = 1`

---

### **Step 5: Import Leases Data**

1. In the sidebar, click **"Import Leases"** (or go to `/import-leases`)
2. Click **"Choose File"** or drag and drop
3. Select: **`test_data_leases.xlsx`**
4. Click **"Upload and Import"**

**Expected Result**:
- ✅ File uploads successfully
- ✅ Success message appears
- ✅ You see 5 leases imported:
   - SHOP-001: Coffee Shop Ltd (2024-01-01 to 2026-12-31)
   - SHOP-002: Bakery Corp (2023-06-01, ongoing)
   - OFFICE-101: Tech Solutions Inc (2024-03-01 to 2027-03-01)
   - SHOP-003: Fashion Store (2024-01-15 to 2025-01-14)
   - WAREHOUSE-01: Logistics Co (2023-01-01 to 2028-12-31)

**Verify in Supabase**:
1. Go to `leases` table in Supabase
2. You should see 5 records with `tenant_id = 1`

**Automatic Timeline Generation**:
- ✅ System automatically generates `unit_timeline` records
- ✅ Check `unit_timeline` table in Supabase
- ✅ Should see occupied periods for each unit with a lease

---

### **Step 6: View Data Management**

1. In the sidebar, click **"Data Management"** (or go to `/data-management`)
2. Click on **"Units"** tab

**Expected Result**:
- ✅ You see all 5 units listed
- ✅ You can view details, edit, or delete units

3. Click on **"Leases"** tab

**Expected Result**:
- ✅ You see all 5 leases listed
- ✅ You can view details, edit, or delete leases

---

### **Step 7: Upload Invoices**

1. In the sidebar, click **"Upload Invoices"** (or go to `/upload`)
2. Click **"Choose File"** or drag and drop
3. Select: **`test_data_invoices.xlsx`**
4. Click **"Upload and Validate"**

**Expected Result**:
- ✅ File uploads successfully
- ✅ Progress bar shows upload progress
- ✅ Success message: "File uploaded successfully. Processing in background..."
- ✅ System processes invoices in background

**Wait 10-30 seconds** for processing to complete.

---

### **Step 8: View Invoice Validation Results**

1. In the sidebar, click **"Invoices"** (or go to `/invoices`)
2. You should see 10 invoices listed

**Expected Result**:
- ✅ All 10 invoices are displayed
- ✅ Each invoice shows:
   - Invoice Number
   - Supplier Name
   - Unit ID
   - Gross Amount
   - Validation Status (Valid/Invalid/Needs Review)
   - Determination (OK TO PAY / DO NOT PAY / etc.)

**Verify Validation Logic**:
- ✅ Invoices for units with leases during billing period → "OK TO PAY"
- ✅ Invoices for vacant periods → "DO NOT PAY"
- ✅ Duplicate invoices → "COT" (Check Other Tenant)

---

### **Step 9: Verify in Supabase Dashboard**

1. Go to: https://supabase.com/dashboard/project/xkbmbqejeoxfatcliftv/editor

2. **Check `invoices` table**:
   - Should see 10 records
   - All have `tenant_id = 1`
   - All have invoice numbers, amounts, dates

3. **Check `invoice_validation` table**:
   - Should see 10 validation records
   - Each linked to an invoice (`invoice_id`)
   - Each has `tenant_id = 1`
   - Each has `validation_status` and `determination`

4. **Check `unit_timeline` table**:
   - Should see timeline periods for each unit
   - Shows occupied/vacant periods
   - All have `tenant_id = 1`

---

### **Step 10: Test Multi-Tenant Isolation**

1. **Create a second test client**:
   ```bash
   python scripts/create_test_client.py
   ```
   (This will create a second tenant)

2. **Or manually create via UI**:
   - Logout
   - Go to `/signup`
   - Create a new account (this creates a new tenant)

3. **Login as second client**

4. **Verify isolation**:
   - ✅ Dashboard shows 0 units, 0 leases, 0 invoices
   - ✅ Cannot see first client's data
   - ✅ Upload data for second client
   - ✅ Data is stored with different `tenant_id`

---

## 🔍 Troubleshooting

### **Issue: "Connection failed" or "Database error"**

**Solution**:
1. Check `.env` file has correct `DATABASE_URL`
2. Verify Supabase connection:
   ```bash
   python scripts/test_supabase_connection.py
   ```

### **Issue: "File upload failed"**

**Solution**:
1. Check file format (must be .xlsx, .xls, or .csv)
2. Check file size (max 50MB)
3. Check server logs for errors

### **Issue: "No data showing after upload"**

**Solution**:
1. Check Supabase dashboard - is data there?
2. Check browser console for JavaScript errors
3. Check server logs for processing errors
4. Verify you're logged in as the correct tenant

### **Issue: "Validation not working"**

**Solution**:
1. Ensure units are imported first
2. Ensure leases are imported (for timeline generation)
3. Check `unit_timeline` table has data
4. Verify invoice billing periods match date format

---

## ✅ Success Criteria

The test is successful if:

1. ✅ **Login works** - Can login with test credentials
2. ✅ **Units import works** - 5 units imported and visible
3. ✅ **Leases import works** - 5 leases imported and visible
4. ✅ **Timeline generated** - `unit_timeline` table has data
5. ✅ **Invoices upload works** - 10 invoices uploaded
6. ✅ **Validation runs** - All invoices have validation results
7. ✅ **Data in Supabase** - All data visible in Supabase dashboard
8. ✅ **Multi-tenant isolation** - Second client can't see first client's data

---

## 📊 Test Data Files

### **test_data_units.xlsx**
- 5 property units
- Columns: Unit ID, Building Name, Address Line 1, City, Postcode

### **test_data_leases.xlsx**
- 5 lease agreements
- Columns: Unit ID, Tenant Name, Lease Start, Lease End
- One lease is ongoing (no end date)

### **test_data_invoices.xlsx**
- 10 invoices
- Columns: Invoice Number, Supplier Name, Unit ID, Billing Period Start/End, Invoice Date, Gross/Net/VAT Amount, Utility Type, Currency
- Spread across different units and dates

---

## 🎉 Next Steps After Testing

Once testing is complete:

1. **Clean database** (if needed):
   ```bash
   python scripts/clean_database.py
   ```

2. **Create production client**:
   - Use signup page or create via script
   - Set proper credentials
   - Configure column mappings if needed

3. **Deploy to production**:
   - Set up production Supabase project
   - Update `.env` with production `DATABASE_URL`
   - Deploy application

---

## 📝 Notes

- **Frontend-Backend Connection**: The frontend uses JavaScript `XMLHttpRequest` to POST to API endpoints (`/api/upload`, `/api/import/units`, etc.). These endpoints use `get_session()` which connects to Supabase via the `DATABASE_URL` in `.env`.

- **Data Flow**:
  1. User uploads file via frontend
  2. Frontend sends file to API endpoint
  3. API endpoint saves file and processes it
  4. Data is stored in Supabase via SQLAlchemy
  5. Frontend polls for results or refreshes page

- **Multi-Tenant Isolation**: Every database query automatically filters by `tenant_id` from the logged-in user's session. This ensures complete data isolation.

---

**Happy Testing! 🚀**

