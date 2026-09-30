# Client Deployment & Configuration Guide

## Current Status & Limitations

### 1. Excel File Structure Flexibility

**Current State:**
- ✅ The system has flexible column mapping that tries to match common column name variations
- ✅ Supports multiple date formats (YYYY-MM-DD, DD/MM/YYYY, with/without time)
- ⚠️ **Limitation**: Still requires specific column names to be present (invoice_number, supplier_name, unit_id, etc.)

**What Works:**
- Automatically detects header rows (tries row 0, 5, or 6)
- Maps common variations like:
  - "Invoice Number" → invoice_number
  - "Property or Unit reference" → unit_id
  - "Gross Inv Amt" → gross_amount
  - "Period From Date" → billing_period_start

**What Needs Improvement:**
- Each client may have completely different column names
- Need a way to configure column mappings per client
- Need better error messages when columns are missing

### 2. Current Validation Logic

The validation engine performs these checks:

#### ✅ **Duplicate Detection**
- Checks if invoice_number + gross_amount already exists in database
- **Uses historical invoices** - yes, it checks against all previously processed invoices
- Stores duplicate batch numbers for reference

#### ✅ **Vacancy Overlap Check**
- Calculates occupied/vacant periods from Units + Leases
- Checks if invoice billing period overlaps with vacancy periods
- Calculates total overlap days

#### ✅ **Validation Status**
- **Valid**: Invoice overlaps fully with vacancy OR is a credit note
- **Invalid**: No overlap with vacancy (0 days)
- **Needs Review**: Partial overlap or missing data

#### ✅ **Final Determination**
Based on validation status + daily rate + payment status:
- **OK TO PAY**: Valid, unpaid, daily rate < £4
- **OK TO PAY, SUBMIT METER READING**: Valid, unpaid, daily rate £4-£10
- **DO NOT PAY, SUBMIT METER READING**: Valid, unpaid, daily rate >= £10
- **COT** (Check on This): Needs Review or Invalid
- **CREDIT OWED**: Invalid invoice that was already paid
- **Landlord Supply - OK TO PAY**: Unit ending in '00'

### 3. Historical Invoice Database

**Current Implementation:**
- ✅ **YES** - All processed invoices are stored in the database
- ✅ Duplicate detection checks against ALL historical invoices
- ✅ Each invoice has a `source_batch` field to track which upload it came from
- ✅ Validation results are stored permanently

**Database Tables:**
- `invoices`: All historical invoices
- `invoice_validation`: Validation results for each invoice
- `upload_status`: Track of all file uploads

**What This Means:**
- If you upload the same invoice twice, it will be flagged as duplicate
- Historical data is preserved for reporting and analysis
- Can track which batch an invoice came from

## Deployment Requirements

### Option 1: Single-Client Deployment (Current Setup)

**What's Needed:**
1. **Server/Cloud Instance**
   - Python 3.11+
   - SQLite database (or PostgreSQL for production)
   - ~2GB RAM minimum
   - FastAPI/uvicorn server

2. **Client Setup:**
   - Load their Units and Leases data (one-time setup)
   - Configure column mappings if needed (manual or via config file)
   - Create user accounts for client team

3. **Data Requirements:**
   - Units table: All property units
   - Leases table: All lease periods (past and current)
   - These are loaded once, then invoices are validated against them

### Option 2: Multi-Tenant Deployment (Future)

**What Would Be Needed:**
1. **Tenant/Client Model**
   - Each client has their own:
     - Units and Leases
     - Invoice history
     - User accounts
     - Column mapping configuration

2. **Database Changes:**
   - Add `tenant_id` to all tables
   - Filter all queries by tenant
   - Separate data per client

3. **Configuration System:**
   - Per-client column mapping configs
   - Per-client validation rules (if needed)
   - Per-client branding/UI customization

## Recommended Improvements

### Priority 1: Column Mapping Configuration

**Problem:** Each client may have different Excel column names

**Solution:** Create a configuration system:

```python
# config/client_mappings.json
{
  "client_1": {
    "invoice_number": ["Invoice Number", "Invoice #", "Inv No"],
    "unit_id": ["Unit ID", "Property Reference", "Unit Reference"],
    "supplier_name": ["Supplier", "Vendor", "Supplier Name"],
    ...
  },
  "client_2": {
    "invoice_number": ["INV_NUM", "InvoiceNum"],
    ...
  }
}
```

### Priority 2: Better Error Handling

**Current:** Generic "missing column" errors

**Improvement:** 
- Show which columns were found
- Suggest closest matches
- Allow manual column mapping via UI

### Priority 3: Data Validation Dashboard

**Add:**
- Summary of validation results
- Charts showing validation trends
- Export capabilities
- Historical view of past validations

### Priority 4: Multi-Tenant Support

**If deploying for multiple clients:**
- Tenant isolation
- Per-tenant configuration
- Separate databases or schema separation

## Deployment Steps

### For Single Client:

1. **Setup Server**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Initialize database
   python -m app.db
   ```

2. **Load Client Data**
   ```bash
   # Load units and leases
   python scripts/load_sample_data.py  # Or load from client's data
   ```

3. **Create User Accounts**
   ```bash
   python scripts/create_test_user.py  # Or create via UI
   ```

4. **Configure Column Mappings** (if needed)
   - Edit column mapping in `main.py` or create config file

5. **Start Server**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

6. **Access Application**
   - Web UI: http://your-server:8000
   - Login with created credentials
   - Upload invoices

### For Production:

1. **Use PostgreSQL instead of SQLite**
   - Better for concurrent access
   - Better performance with large datasets

2. **Add Environment Variables**
   - Database connection strings
   - Secret keys
   - Email configuration

3. **Add Reverse Proxy** (nginx)
   - SSL/TLS termination
   - Static file serving

4. **Add Monitoring**
   - Error logging
   - Performance monitoring
   - Backup strategy

## Testing the Validation

To verify validation is working:

1. **Check Duplicate Detection:**
   - Upload same invoice twice
   - Should show "Duplicate" in validation results

2. **Check Vacancy Overlap:**
   - Upload invoice for unit with known vacancy period
   - Check if overlap days are calculated correctly

3. **Check Determinations:**
   - Upload invoices with different daily rates
   - Verify correct determinations are generated

## Next Steps

1. **Create column mapping configuration system**
2. **Add UI for column mapping** (for non-technical users)
3. **Add validation testing dashboard**
4. **Document client-specific requirements**
5. **Create deployment scripts**




