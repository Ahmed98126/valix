# 📁 Invo Sync - Complete Project Structure Guide

## 🎯 **THE BIG PICTURE**

**Invo Sync** is a **multi-tenant SaaS application** that validates commercial property invoices. Think of it like this:

1. **Multiple clients** (tenants) can use the same system
2. Each client uploads their **units** (properties), **leases** (rental agreements), and **invoices**
3. The system **validates invoices** against lease data to check if they're valid
4. Results show which invoices are **Valid**, **Invalid**, or **Needs Review**

---

## 📂 **FOLDER STRUCTURE - What Each Section Does**

### **🔴 CORE APPLICATION (`app/` folder) - THE BRAIN**

This is where all the business logic lives. **This is the most important folder.**

#### **`app/models.py`** ⭐ **CRITICAL**
- **What it does**: Defines your database tables (like a blueprint)
- **Key Models**:
  - `Tenant` - Each client/company using the system
  - `User` - Login accounts (belong to tenants)
  - `Unit` - Properties (e.g., "Shop 1", "Office 5")
  - `Lease` - Rental agreements (who rents what, when)
  - `Invoice` - Bills from suppliers
  - `InvoiceValidation` - Results of validation (Valid/Invalid/Needs Review)
  - `UnitTimeline` - Calculated periods of vacancy/occupancy
- **Why it matters**: Every piece of data in your system is defined here

#### **`app/validation.py`** ⭐ **CRITICAL - THE HEART**
- **What it does**: The **core validation engine** - this is where the magic happens
- **Key Functions**:
  - `validate_invoice()` - Main function that validates an invoice
  - `check_duplicate_invoices()` - Finds duplicate invoices
  - `check_vacancy_overlap()` - Checks if invoice overlaps with vacancy periods
  - `generate_unit_timeline()` - Creates vacancy/occupancy timeline from leases
- **Why it matters**: This implements your Databricks SQL logic in Python. **This is the core business logic.**

#### **`app/db.py`**
- **What it does**: Database connection and setup
- **Key**: Creates database tables, manages connections (SQLite or PostgreSQL/Supabase)
- **Why it matters**: Without this, nothing works

#### **`app/auth.py`**
- **What it does**: User authentication (login, signup, password hashing)
- **Key Functions**: `get_current_user()`, `authenticate_user()`, `create_user()`
- **Why it matters**: Security - ensures users can only see their tenant's data

#### **`app/tenant_helpers.py`**
- **What it does**: Multi-tenant isolation helpers
- **Key**: Ensures Tenant A can't see Tenant B's data
- **Why it matters**: Critical for multi-tenant security

#### **`app/column_mapping.py`**
- **What it does**: Maps client's Excel column names to your system's expected names
- **Example**: Client uses "Invoice #" but system expects "invoice_number"
- **Why it matters**: Makes imports flexible - clients can use their own column names

#### **`app/config.py`**
- **What it does**: Configuration settings (database URL, upload limits, etc.)
- **Key**: Reads from `.env` file for sensitive data
- **Why it matters**: Keeps secrets out of code

#### **`app/schemas.py`**
- **What it does**: Data validation schemas (Pydantic models)
- **Why it matters**: Ensures data coming in/out is in the right format

#### **`app/error_handling.py`**
- **What it does**: User-friendly error messages
- **Why it matters**: Better UX when things go wrong

#### **`app/horizon_connector.py`**
- **What it does**: Framework for connecting to Horizon API (external system)
- **Status**: Prepared but not fully implemented (needs API access)
- **Why it matters**: Future feature for real-time data sync

---

### **🌐 FRONTEND (`templates/` folder) - THE FACE**

HTML pages that users see. These are **Jinja2 templates** (HTML with Python variables).

#### **Key Pages**:
- **`landing.html`** - Public homepage (marketing page)
- **`login.html`** - Login page
- **`signup.html`** - Signup page
- **`dashboard.html`** - Main dashboard (stats, KPIs)
- **`upload.html`** - Upload invoices page
- **`invoices.html`** - List all invoices
- **`invoice_detail.html`** - View single invoice details
- **`import_units.html`** - Import units (properties) from Excel
- **`import_leases.html`** - Import leases from Excel
- **`data_management.html`** - View/edit units and leases
- **`settings.html`** - Configure column mappings and data sources
- **`base.html`** - Base template (shared layout)

---

### **🎨 STYLING (`static/` folder) - THE LOOK**

#### **`static/css/`**:
- **`invo-sync.css`** - Main stylesheet (branding, animations, theme)
- **`styles.css`** - Additional styles

#### **`static/js/`**:
- **`scroll-animations.js`** - Landing page scroll animations
- **`ui-enhancements.js`** - Loading states, toast notifications

---

### **🚀 MAIN ENTRY POINT (`main.py`) - THE ORCHESTRATOR**

**This is the most important file to understand the flow.**

#### **What it does**:
1. **Defines all routes** (URLs) - `/login`, `/dashboard`, `/api/invoices`, etc.
2. **Connects frontend to backend** - Takes user requests, processes them, returns responses
3. **Orchestrates everything** - Calls validation, saves to database, renders templates

#### **Key Sections**:

```python
# 1. Authentication Routes
@app.get("/login")  # Show login page
@app.post("/login")  # Process login
@app.get("/signup")  # Show signup page
@app.post("/signup")  # Process signup

# 2. Dashboard & Pages
@app.get("/dashboard")  # Main dashboard
@app.get("/upload")  # Upload page
@app.get("/invoices")  # Invoice list

# 3. API Endpoints (for AJAX calls)
@app.post("/api/upload/invoices")  # Upload invoices
@app.get("/api/invoices")  # Get invoices (JSON)
@app.post("/api/import/units")  # Import units
@app.post("/api/import/leases")  # Import leases

# 4. Data Management
@app.get("/data-management")  # View units/leases
@app.get("/api/units")  # Get units (JSON)
@app.delete("/api/units/{id}")  # Delete unit
```

#### **Flow Example - Upload Invoice**:
1. User visits `/upload` → `main.py` renders `upload.html`
2. User uploads file → Frontend sends to `/api/upload/invoices`
3. `main.py` receives file → Calls `validate_invoice()` from `app/validation.py`
4. Saves to database → Returns status to frontend
5. Frontend shows results → User sees validated invoices

---

### **🧪 TESTING & SCRIPTS (`scripts/` folder)**

Helper scripts for testing and setup:

- **`create_test_client.py`** - Creates a test tenant and user
- **`load_sample_data.py`** - Loads sample data for testing
- **`test_multi_tenant_workflow.py`** - Tests multiple tenants
- **`clean_database.py`** - Clears all data
- **`test_supabase_connection.py`** - Tests database connection

---

### **📊 DATA FILES**

- **`app.db`** - SQLite database (local development)
- **`.env`** - Environment variables (database URL, secrets) - **NEVER commit this!**
- **`test_data_*.xlsx`** - Sample Excel files for testing
- **`uploads/`** - User-uploaded files

---

### **📚 DOCUMENTATION (`.md` files)**

Lots of markdown files explaining different aspects:
- **`README.md`** - Main project documentation
- **`SUPABASE_*.md`** - Supabase setup guides
- **`TESTING_*.md`** - Testing guides
- **`UI_*.md`** - UI update summaries

---

## 🧠 **THE MEAT - What You Need to Understand**

### **1. Multi-Tenant Architecture** 🏢

**Concept**: One system, multiple clients, isolated data

**How it works**:
- Every table has a `tenant_id` column
- Every query filters by `tenant_id`
- User belongs to a tenant → can only see their tenant's data

**Key Files**:
- `app/models.py` - All models have `tenant_id`
- `app/tenant_helpers.py` - Helper functions for filtering
- `app/auth.py` - Gets current user's tenant

**Example**:
```python
# Tenant A uploads invoice for "SHOP-001"
# Tenant B also has "SHOP-001"
# They're completely separate because of tenant_id
```

---

### **2. Validation Engine** ⚙️

**Concept**: Check if invoices are valid based on lease data

**The Process**:
1. **Upload Invoice** → Save to database
2. **Generate Timeline** → From leases, create vacancy/occupancy periods
3. **Check Duplicates** → Same invoice number, same period?
4. **Check Vacancy Overlap** → Does invoice period overlap with vacancy?
5. **Determine Status**:
   - **Valid** → No duplicates, no vacancy overlap
   - **Invalid** → Has duplicates OR overlaps with vacancy
   - **Needs Review** → Edge cases, missing data

**Key File**: `app/validation.py`

**The Logic** (simplified):
```python
def validate_invoice(invoice, session, tenant_id):
    # 1. Check for duplicates
    duplicates = check_duplicate_invoices(invoice, session, tenant_id)
    
    # 2. Get unit timeline (vacancy periods)
    timeline = get_unit_timeline(invoice.unit_id, session, tenant_id)
    
    # 3. Check if invoice overlaps with vacancy
    overlaps = check_vacancy_overlap(invoice, timeline)
    
    # 4. Determine status
    if duplicates or overlaps:
        status = "Invalid"
    else:
        status = "Valid"
    
    return status
```

---

### **3. Data Flow** 🔄

**Complete Flow - User Uploads Invoice**:

```
1. User → Visits /upload
   ↓
2. Frontend (upload.html) → User selects Excel file
   ↓
3. JavaScript → Sends file to /api/upload/invoices
   ↓
4. main.py → Receives file, reads Excel
   ↓
5. main.py → Maps columns (using column_mapping.py)
   ↓
6. main.py → For each invoice row:
   ↓
7. app/validation.py → validate_invoice()
   ↓
8. Database → Save Invoice + InvoiceValidation
   ↓
9. main.py → Returns status to frontend
   ↓
10. Frontend → Shows progress, redirects to /invoices
   ↓
11. User → Sees validated invoices with status
```

---

### **4. Database Schema** 🗄️

**Key Tables**:

```
tenants
├── id
├── name (e.g., "Acme Properties")
├── slug (e.g., "acme-properties")
└── column_mapping_config (JSON)

users
├── id
├── email
├── tenant_id (links to tenants)
└── hashed_password

units
├── id
├── tenant_id
├── unit_id (e.g., "SHOP-001")
├── building_name
└── address fields

leases
├── id
├── tenant_id
├── unit_id (links to units)
├── tenant_name
├── lease_start
└── lease_end

invoices
├── id
├── tenant_id
├── invoice_number
├── unit_id
├── billing_period_start
├── billing_period_end
└── gross_amount

invoice_validation
├── id
├── tenant_id
├── invoice_id (links to invoices)
├── validation_status ("Valid", "Invalid", "Needs Review")
└── determination (explanation text)

unit_timeline
├── id
├── tenant_id
├── unit_id
├── period_start
├── period_end
└── status ("vacant" or "occupied")
```

---

## 🎯 **QUICK REFERENCE - Where to Find Things**

| **I want to...** | **Look in...** |
|------------------|----------------|
| Understand database structure | `app/models.py` |
| Understand validation logic | `app/validation.py` |
| Add a new page | `templates/` + add route in `main.py` |
| Change styling | `static/css/invo-sync.css` |
| Add JavaScript functionality | `static/js/` |
| Change authentication | `app/auth.py` |
| Add a new API endpoint | `main.py` (add `@app.get()` or `@app.post()`) |
| Test the system | `scripts/` folder |
| Configure database | `.env` file + `app/config.py` |

---

## 🚦 **HOW TO READ THE CODE**

### **Start Here**:
1. **`main.py`** - See how routes work, how data flows
2. **`app/models.py`** - Understand data structure
3. **`app/validation.py`** - Understand business logic
4. **`templates/dashboard.html`** - See how frontend works

### **Then Explore**:
- Other templates to see UI patterns
- `app/auth.py` to understand security
- `app/column_mapping.py` to understand flexibility

---

## 💡 **KEY CONCEPTS TO REMEMBER**

1. **Multi-Tenant**: Every query filters by `tenant_id`
2. **Validation**: Checks duplicates + vacancy overlap
3. **Timeline**: Generated from leases, shows vacancy periods
4. **Column Mapping**: Makes imports flexible for different clients
5. **FastAPI**: Web framework - routes in `main.py`, logic in `app/`
6. **Jinja2**: Template engine - HTML with Python variables

---

## 🔥 **MOST IMPORTANT FILES (Priority Order)**

1. ⭐⭐⭐ **`main.py`** - Entry point, routes, orchestration
2. ⭐⭐⭐ **`app/validation.py`** - Core business logic
3. ⭐⭐⭐ **`app/models.py`** - Database structure
4. ⭐⭐ **`app/auth.py`** - Security
5. ⭐⭐ **`app/tenant_helpers.py`** - Multi-tenant isolation
6. ⭐ **`templates/dashboard.html`** - Main UI
7. ⭐ **`app/column_mapping.py`** - Import flexibility

---

**This is your roadmap! Start with `main.py` and `app/validation.py` to understand the core flow.** 🚀

