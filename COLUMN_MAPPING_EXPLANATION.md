# Column Mapping Configuration - Explained

## What Problem Does This Solve?

### The Problem:
Different clients use **different column names** in their Excel files.

**Example Scenario:**
- **Client A** uses: `Invoice #`, `Supplier`, `Property ID`, `Start Date`
- **Client B** uses: `invoice_number`, `supplier_name`, `unit_id`, `billing_period_start`
- **Client C** uses: `INV-NO`, `Vendor`, `Unit Code`, `From`

**Without Column Mapping:**
- System only recognizes one set of column names
- Other clients' files fail to import
- You'd have to manually edit code for each client

**With Column Mapping:**
- Each client can configure their own column names
- System automatically recognizes their format
- No code changes needed

---

## How It Works

### Step 1: Client Uploads Excel File

**Client A's Excel:**
```
Invoice # | Supplier | Property ID | Start Date | End Date | Amount
INV-001   | British Gas | SHOP-001 | 2024-01-01 | 2024-01-31 | £150.00
```

**Client B's Excel:**
```
invoice_number | supplier_name | unit_id | billing_period_start | billing_period_end | gross_amount
INV-001        | British Gas   | SHOP-001 | 2024-01-01 | 2024-01-31 | 150.00
```

### Step 2: System Checks Column Mapping

**For Client A:**
- System looks up Client A's column mapping config
- Finds: `invoice_number` maps to `["Invoice #", "invoice_number", "invoice no"]`
- Finds: `supplier_name` maps to `["Supplier", "supplier_name", "supplier"]`
- Finds: `unit_id` maps to `["Property ID", "unit_id", "property_id"]`
- **Result:** System recognizes Client A's column names ✅

**For Client B:**
- System looks up Client B's column mapping config
- Finds: `invoice_number` maps to `["invoice_number", "invoice #"]`
- Finds: `supplier_name` maps to `["supplier_name", "supplier"]`
- Finds: `unit_id` maps to `["unit_id", "unit id"]`
- **Result:** System recognizes Client B's column names ✅

### Step 3: Data Processing

Both files are processed correctly, even though they use different column names!

---

## Real-World Example

### Before Column Mapping (Hardcoded):
```python
# System only recognizes these exact names:
column_mapping = {
    'invoice_number': ['invoice_number', 'invoice #'],
    'supplier_name': ['supplier_name', 'supplier'],
    # ...
}
```

**Problem:** If client uses `Invoice #` instead of `invoice_number`, import fails ❌

### After Column Mapping (Configurable):
```python
# System checks tenant's config first:
tenant_mapping = get_column_mapping(session, tenant_id, "invoice")
# Returns: {'invoice_number': ['Invoice #', 'invoice_number', ...], ...}
```

**Solution:** Client can configure their column names in Settings page ✅

---

## How Clients Use It

### During Onboarding:

1. **Client uploads their first Excel file**
   - System tries to auto-detect columns
   - If some columns aren't recognized, shows error

2. **Client goes to Settings page** (`/settings`)
   - Sees "Column Mappings" section
   - Edits the mappings to match their Excel column names
   - Clicks "Save Column Mappings"

3. **Client uploads Excel again**
   - System now recognizes their column names
   - Import succeeds! ✅

### Example Configuration:

**Client's Excel has:**
- Column: `Invoice Number` (with space)
- Column: `Vendor Name` (not "Supplier")
- Column: `Property Code` (not "Unit ID")

**Client configures in Settings:**
```
Invoice Number → invoice_number: "Invoice Number, Invoice #, invoice_number"
Vendor Name → supplier_name: "Vendor Name, Supplier, supplier_name"
Property Code → unit_id: "Property Code, Unit ID, unit_id"
```

**Result:** System now recognizes their format!

---

## Benefits

1. **Flexibility:** Each client can use their own Excel format
2. **No Code Changes:** Configure via UI, no developer needed
3. **Self-Service:** Clients can fix their own mapping issues
4. **Multi-Tenant:** Each tenant has their own mappings

---

## Technical Details

### Storage:
- Stored in `Tenant.column_mapping_config` (JSON field)
- Format: `{"invoice": {...}, "unit": {...}, "lease": {...}}`

### Default Mappings:
- If client doesn't configure, system uses defaults
- Defaults cover common variations: `invoice_number`, `invoice #`, `invoice no`, etc.

### Processing:
- When file is uploaded, system:
  1. Gets tenant's column mapping config
  2. Maps Excel columns to system fields
  3. Processes data using mapped columns


