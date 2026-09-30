# 📄 PDF Invoice Workflow - Complete End-to-End Guide

## 🎯 **How PDF Processing Works with Your Existing System**

**Key Point:** PDFs are **NOT converted to Excel**. They're extracted directly to your invoice schema and validated the same way as Excel/CSV invoices.

---

## 🔄 **Complete Workflow Comparison**

### **Current Flow (Excel/CSV):**
```
1. User uploads Excel/CSV file
   ↓
2. File saved to disk
   ↓
3. Pandas reads Excel/CSV → DataFrame
   ↓
4. Column mapping (per-tenant) → Normalized DataFrame
   ↓
5. For each row:
   - Create Invoice record
   - Run validation engine
   - Save Invoice + InvoiceValidation
   ↓
6. Results displayed in UI
```

### **New Flow (PDF) - SAME END RESULT:**
```
1. User uploads PDF file
   ↓
2. File saved to disk
   ↓
3. Azure Document Intelligence extracts data → JSON
   ↓
4. PDF Normalizer converts JSON → Invoice Schema (same as Excel!)
   ↓
5. For each invoice (PDFs usually have 1 invoice per file):
   - Create Invoice record (SAME model as Excel!)
   - Run validation engine (SAME validation as Excel!)
   - Save Invoice + InvoiceValidation (SAME tables!)
   ↓
6. Results displayed in UI (SAME UI!)
```

**The Magic:** Both flows converge at step 5. Your validation engine doesn't know or care if the invoice came from Excel or PDF!

---

## 🏗️ **Architecture Integration**

### **Your Current Tech Stack:**
```
Frontend: HTML/CSS/JavaScript (Tailwind)
    ↓
Backend: FastAPI (Python)
    ↓
Database: Supabase (PostgreSQL)
    ↓
Deployment: Azure App Service
```

### **With PDF Processing Added:**
```
Frontend: HTML/CSS/JavaScript (Tailwind) [NO CHANGES]
    ↓
Backend: FastAPI (Python)
    ├─ Excel/CSV Processor (existing)
    └─ PDF Processor (NEW) → Azure Document Intelligence API
    ↓
Database: Supabase (PostgreSQL) [NO CHANGES]
    ↓
Deployment: Azure App Service [NO CHANGES]
```

**New Service:**
- Azure Document Intelligence (separate Azure resource, called via API)

---

## 📱 **UI/UX Flow - Step by Step**

### **Step 1: User Uploads PDF**

**Current Upload Page (`templates/upload.html`):**
```html
<!-- Current: Only accepts Excel/CSV -->
<input type="file" accept=".xlsx,.xls,.csv">

<!-- Updated: Also accepts PDF -->
<input type="file" accept=".xlsx,.xls,.csv,.pdf">
```

**User Experience:**
1. User visits `/upload` page
2. Drags & drops PDF invoice (or clicks to select)
3. File shows: "invoice_british_gas_jan2024.pdf"
4. Clicks "Upload and Validate"
5. **NEW:** Shows message: "📄 PDF detected. Extracting with AI..."

**No UI changes needed** - same upload page, just accepts PDFs too!

---

### **Step 2: Background Processing**

**What Happens Behind the Scenes:**

```python
# User uploads PDF
POST /api/upload
    ↓
# Backend detects PDF
if file.filename.endswith('.pdf'):
    # Save PDF to disk
    file_path = "uploads/BATCH_20241230_123456_invoice.pdf"
    
    # Start background task
    background_tasks.add_task(
        process_pdf_invoice,
        file_path,
        batch_id,
        user_id
    )
    
    # Return immediately (don't block user)
    return {
        "status": "success",
        "message": "PDF invoice uploaded. Processing with AI extraction...",
        "batch_id": "BATCH_20241230_123456"
    }
```

**User sees:** Progress indicator (same as Excel uploads)

---

### **Step 3: PDF Extraction (Background)**

**What Happens in `process_pdf_invoice()`:**

```python
def process_pdf_invoice(file_path: str, batch_id: str, user_id: int):
    """Process PDF invoice - runs in background."""
    
    # 1. Extract data from PDF using Azure Document Intelligence
    processor = PDFInvoiceProcessor()
    extracted_data = processor.extract_invoice_data(file_path)
    
    # extracted_data looks like:
    # {
    #     "invoice_number": "INV-12345",
    #     "supplier_name": "British Gas",
    #     "invoice_date": "2024-01-15",
    #     "billing_period_start": "2024-01-01",
    #     "billing_period_end": "2024-01-31",
    #     "gross_amount": 350.00,
    #     "unit_id": "SHOP-001",  # Extracted from address
    #     "utility_type": "Gas",
    #     ...
    # }
    
    # 2. Normalize to your invoice schema
    normalizer = PDFInvoiceNormalizer()
    invoice_data = normalizer.normalize(extracted_data)
    
    # invoice_data now matches Excel format:
    # {
    #     "invoice_number": "INV-12345",
    #     "supplier_name": "British Gas",
    #     "unit_id": "SHOP-001",
    #     "billing_period_start": date(2024, 1, 1),
    #     "billing_period_end": date(2024, 1, 31),
    #     "gross_amount": 350.00,
    #     "utility_type": "Gas",
    #     "currency": "GBP"
    # }
    
    # 3. Create Invoice record (SAME as Excel!)
    invoice = Invoice(
        tenant_id=tenant_id,
        invoice_number=invoice_data["invoice_number"],
        supplier_name=invoice_data["supplier_name"],
        unit_id=invoice_data["unit_id"],
        billing_period_start=invoice_data["billing_period_start"],
        billing_period_end=invoice_data["billing_period_end"],
        gross_amount=invoice_data["gross_amount"],
        utility_type=invoice_data["utility_type"],
        source_batch=batch_id
    )
    session.add(invoice)
    session.flush()  # Get invoice.id
    
    # 4. Run validation engine (SAME as Excel!)
    validate_invoice(invoice, session, tenant_id)
    # This creates InvoiceValidation record with:
    # - validation_status (Valid/Invalid/Needs Review)
    # - determination (OK TO PAY, COT, etc.)
    # - vacancy_overlap_days
    # - daily_rate
    # - etc.
    
    session.commit()
```

**Key Point:** After normalization, it's **identical** to Excel processing!

---

### **Step 4: Validation Engine (No Changes!)**

**Your existing `validate_invoice()` function:**

```python
# app/validation.py
def validate_invoice(invoice: Invoice, session: Session, tenant_id: int):
    """Validate invoice - works for Excel AND PDF invoices!"""
    
    # 1. Check duplicates
    duplicates = check_duplicate_invoices(invoice, session, tenant_id)
    
    # 2. Get unit timeline (vacancy periods)
    timeline = get_unit_timeline(invoice.unit_id, session, tenant_id)
    
    # 3. Calculate vacancy overlap
    overlap_days = check_vacancy_overlap(invoice, timeline)
    
    # 4. Determine status
    if duplicates or overlap_days > 0:
        status = "Invalid"
    else:
        status = "Valid"
    
    # 5. Generate determination
    determination = generate_determination(invoice, status, overlap_days)
    
    # 6. Save validation result
    validation = InvoiceValidation(
        invoice_id=invoice.id,
        validation_status=status,
        determination=determination,
        vacancy_overlap_days=overlap_days,
        ...
    )
    session.add(validation)
```

**This function doesn't care if invoice came from Excel or PDF!** It just works with the `Invoice` model.

---

### **Step 5: Results Display (No Changes!)**

**User visits `/invoices` page:**

```html
<!-- Same invoice list - shows Excel AND PDF invoices together! -->
<table>
    <tr>
        <td>INV-12345</td>
        <td>British Gas</td>
        <td>SHOP-001</td>
        <td>01/01/2024 - 31/01/2024</td>
        <td>£350.00</td>
        <td>
            <span class="badge valid">Valid</span>
        </td>
        <td>
            <span class="badge">OK TO PAY</span>
        </td>
        <td>
            <span class="text-xs text-gray-500">PDF</span>  <!-- NEW: Source indicator -->
        </td>
    </tr>
</table>
```

**User Experience:**
- Sees all invoices (Excel + PDF) in same list
- Same filters work (Status, Determination, Batch)
- Same validation results
- Optional: Show source type (Excel/CSV/PDF) badge

---

## 🔍 **Detailed Technical Flow**

### **Complete Request Flow:**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER ACTION: Upload PDF Invoice                          │
│    POST /api/upload                                          │
│    File: invoice_british_gas.pdf                            │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. BACKEND: Detect File Type                                │
│    if file.endswith('.pdf'):                                │
│        → Route to PDF processor                              │
│    else:                                                     │
│        → Route to Excel/CSV processor (existing)            │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. SAVE FILE                                                 │
│    File saved to: uploads/BATCH_xxx_invoice.pdf             │
│    Return: { status: "success", batch_id: "..." }           │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. BACKGROUND TASK: process_pdf_invoice()                   │
│    ┌──────────────────────────────────────────────┐         │
│    │ 4a. Azure Document Intelligence               │         │
│    │     - Send PDF to Azure API                   │         │
│    │     - Azure extracts:                          │         │
│    │       • Invoice number                         │         │
│    │       • Supplier name                          │         │
│    │       • Dates (invoice, billing period)        │         │
│    │       • Amounts (gross, net, VAT)              │         │
│    │       • Line items (tables)                    │         │
│    │       • Addresses                              │         │
│    │     - Returns: Structured JSON                 │         │
│    └──────────────────────────────────────────────┘         │
│                       ↓                                      │
│    ┌──────────────────────────────────────────────┐         │
│    │ 4b. PDF Normalizer                            │         │
│    │     - Convert Azure JSON → Invoice Schema     │         │
│    │     - Extract unit_id from address            │         │
│    │     - Detect utility_type                     │         │
│    │     - Parse dates                             │         │
│    │     - Returns: invoice_data dict              │         │
│    └──────────────────────────────────────────────┘         │
│                       ↓                                      │
│    ┌──────────────────────────────────────────────┐         │
│    │ 4c. Create Invoice Record                      │         │
│    │     invoice = Invoice(                        │         │
│    │         invoice_number=...,                   │         │
│    │         supplier_name=...,                    │         │
│    │         unit_id=...,                          │         │
│    │         ...                                   │         │
│    │     )                                          │         │
│    │     session.add(invoice)                       │         │
│    └──────────────────────────────────────────────┘         │
│                       ↓                                      │
│    ┌──────────────────────────────────────────────┐         │
│    │ 4d. Run Validation Engine                      │         │
│    │     validate_invoice(invoice, session, ...)   │         │
│    │     - Check duplicates                        │         │
│    │     - Check vacancy overlap                   │         │
│    │     - Generate determination                  │         │
│    │     - Create InvoiceValidation record         │         │
│    └──────────────────────────────────────────────┘         │
│                       ↓                                      │
│    ┌──────────────────────────────────────────────┐         │
│    │ 4e. Save to Database                           │         │
│    │     session.commit()                           │         │
│    │     - Invoice saved                            │         │
│    │     - InvoiceValidation saved                  │         │
│    └──────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. USER SEES RESULTS                                         │
│    - Visits /invoices page                                   │
│    - Sees invoice in list (same as Excel invoices)          │
│    - Can view details, filter, export                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 💾 **Database Schema (No Changes!)**

**Your existing tables work perfectly:**

```sql
-- invoices table (no changes needed)
CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER,
    invoice_number VARCHAR,
    supplier_name VARCHAR,
    unit_id VARCHAR,
    billing_period_start DATE,
    billing_period_end DATE,
    gross_amount NUMERIC,
    utility_type VARCHAR,
    source_batch VARCHAR,  -- Shows batch ID
    -- NEW: Optional field to track source type
    source_type VARCHAR DEFAULT 'excel'  -- 'excel', 'csv', or 'pdf'
);

-- invoice_validation table (no changes needed)
CREATE TABLE invoice_validation (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER REFERENCES invoices(id),
    validation_status VARCHAR,  -- 'Valid', 'Invalid', 'Needs Review'
    determination VARCHAR,      -- 'OK TO PAY', 'COT', etc.
    vacancy_overlap_days INTEGER,
    daily_rate NUMERIC,
    ...
);
```

**Optional Enhancement:** Add `source_type` column to track if invoice came from Excel/CSV/PDF (for analytics).

---

## 🎨 **UI Changes (Minimal)**

### **1. Upload Page - Accept PDFs**

**File: `templates/upload.html`**

```html
<!-- Current -->
<input type="file" accept=".xlsx,.xls,.csv">

<!-- Updated -->
<input type="file" accept=".xlsx,.xls,.csv,.pdf">

<!-- Update help text -->
<p class="text-sm text-gray-600">
    Excel (.xlsx, .xls), CSV, or PDF files up to 50MB
</p>

<!-- Optional: Show PDF-specific info -->
<div id="pdf-detected" class="hidden mt-2 p-3 bg-blue-50 rounded-lg">
    <p class="text-sm text-blue-800">
        📄 PDF invoice detected. Will be processed with AI extraction.
    </p>
</div>

<script>
// Detect PDF on file selection
fileInput.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file && file.name.endsWith('.pdf')) {
        document.getElementById('pdf-detected').classList.remove('hidden');
    } else {
        document.getElementById('pdf-detected').classList.add('hidden');
    }
});
</script>
```

### **2. Invoice List - Show Source Type (Optional)**

**File: `templates/invoices.html`**

```html
<!-- Add source type column (optional) -->
<thead>
    <tr>
        <th>Invoice #</th>
        <th>Supplier</th>
        <th>Unit ID</th>
        <th>Period</th>
        <th>Amount</th>
        <th>Status</th>
        <th>Source</th>  <!-- NEW -->
        <th>Actions</th>
    </tr>
</thead>

<tbody>
    {% for item in invoices %}
    <tr>
        <td>{{ item.invoice.invoice_number }}</td>
        <td>{{ item.invoice.supplier_name }}</td>
        <td>{{ item.invoice.unit_id }}</td>
        <td>{{ item.invoice.billing_period_start|ddmmyyyy }} - {{ item.invoice.billing_period_end|ddmmyyyy }}</td>
        <td>£{{ "{:,.2f}".format(item.invoice.gross_amount) }}</td>
        <td>
            <span class="badge {{ item.validation.validation_status|lower }}">
                {{ item.validation.validation_status }}
            </span>
        </td>
        <td>
            <!-- NEW: Show source type -->
            {% if item.invoice.source_type == 'pdf' %}
                <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                    📄 PDF
                </span>
            {% elif item.invoice.source_type == 'csv' %}
                <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    📊 CSV
                </span>
            {% else %}
                <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    📑 Excel
                </span>
            {% endif %}
        </td>
        <td>
            <a href="/invoice/{{ item.invoice.id }}">View</a>
        </td>
    </tr>
    {% endfor %}
</tbody>
```

---

## 🔧 **Code Structure**

### **New Files to Create:**

```
app/
├── pdf_processor.py          # NEW: Azure Document Intelligence client
├── pdf_normalizer.py          # NEW: Converts Azure output to invoice schema
└── supplier_normalizers.py    # NEW: Supplier-specific rules (optional)

main.py                        # MODIFY: Add PDF upload handling
templates/
└── upload.html               # MODIFY: Accept PDFs, show PDF info
```

### **Files to Modify:**

1. **`main.py`** - Add PDF upload endpoint
2. **`templates/upload.html`** - Accept PDFs
3. **`app/models.py`** - Optional: Add `source_type` field
4. **`requirements.txt`** - Add `azure-ai-formrecognizer`

### **Files That DON'T Change:**

- ✅ `app/validation.py` - Works with invoices regardless of source!
- ✅ `templates/invoices.html` - Shows all invoices the same way
- ✅ `templates/invoice_detail.html` - Shows invoice details the same way
- ✅ `app/db.py` - Database connection unchanged
- ✅ All other templates - No changes needed!

---

## 📊 **Data Flow Example**

### **Example: British Gas PDF Invoice**

**1. User uploads:** `british_gas_invoice_jan2024.pdf`

**2. Azure Document Intelligence extracts:**
```json
{
  "invoice_number": "BG12345678",
  "vendor_name": "British Gas",
  "invoice_date": "2024-01-15",
  "customer_address": "123 High Street, Unit 5, London, SW1A 1AA",
  "billing_period": {
    "start": "2024-01-01",
    "end": "2024-01-31"
  },
  "total_amount": 350.00,
  "subtotal": 291.67,
  "tax": 58.33,
  "currency": "GBP",
  "line_items": [
    {
      "description": "Gas Supply - January 2024",
      "quantity": 1,
      "amount": 350.00
    }
  ]
}
```

**3. PDF Normalizer converts to:**
```python
{
    "invoice_number": "BG12345678",
    "supplier_name": "British Gas",
    "unit_id": "UNIT-5",  # Extracted from address "Unit 5"
    "billing_period_start": date(2024, 1, 1),
    "billing_period_end": date(2024, 1, 31),
    "invoice_date": date(2024, 1, 15),
    "gross_amount": 350.00,
    "net_amount": 291.67,
    "vat_amount": 58.33,
    "utility_type": "Gas",  # Detected from supplier + content
    "currency": "GBP",
    "source_type": "pdf"
}
```

**4. Create Invoice record:**
```python
invoice = Invoice(
    tenant_id=1,
    invoice_number="BG12345678",
    supplier_name="British Gas",
    unit_id="UNIT-5",
    billing_period_start=date(2024, 1, 1),
    billing_period_end=date(2024, 1, 31),
    gross_amount=350.00,
    utility_type="Gas",
    source_batch="BATCH_20241230_123456",
    source_type="pdf"  # NEW field
)
```

**5. Validation engine runs:**
```python
validate_invoice(invoice, session, tenant_id)
# Checks:
# - Is this a duplicate? (checks invoice_number + gross_amount)
# - Does unit "UNIT-5" have vacancy periods?
# - Does billing period (Jan 1-31) overlap with vacancy?
# - Calculate daily rate: £350 / 31 days = £11.29/day
# - Generate determination: "DO NOT PAY, SUBMIT METER READING" (daily rate > £10)
```

**6. Results saved:**
```python
InvoiceValidation(
    invoice_id=invoice.id,
    validation_status="Valid",  # No duplicates, no vacancy overlap
    determination="DO NOT PAY, SUBMIT METER READING",
    daily_rate=11.29,
    vacancy_overlap_days=0
)
```

**7. User sees in UI:**
- Invoice appears in `/invoices` list
- Status: "Valid"
- Determination: "DO NOT PAY, SUBMIT METER READING"
- Source badge: "📄 PDF"
- Can view details, filter, export - everything works the same!

---

## ✅ **Key Takeaways**

1. **No Excel conversion** - PDFs are extracted directly to your invoice schema
2. **Same validation** - PDF invoices use the exact same validation engine
3. **Same database** - PDF invoices go into the same `invoices` table
4. **Same UI** - PDF invoices appear alongside Excel/CSV invoices
5. **Minimal changes** - Only need to add PDF processor and normalizer
6. **Seamless integration** - Users won't notice the difference!

---

## 🚀 **Implementation Steps**

1. **Set up Azure Document Intelligence** (30 min)
2. **Create PDF processor module** (2-3 hours)
3. **Create normalization layer** (2-3 hours)
4. **Integrate with upload endpoint** (1 hour)
5. **Update UI to accept PDFs** (30 min)
6. **Test with sample invoices** (1-2 hours)

**Total: ~1 day for basic implementation, 2-3 days for polished version**

---

**Ready to implement? I can create the PDF processor module now!** 🚀

