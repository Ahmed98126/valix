# Frontend-Backend Connection Explained

## 🔗 How Frontend Connects to Supabase Backend

### **The Connection Flow**

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Browser   │  HTTP   │   FastAPI    │  SQL    │   Supabase  │
│  (Frontend) │ ──────> │   (Backend)  │ ──────> │ (PostgreSQL)│
└─────────────┘         └──────────────┘         └─────────────┘
```

---

## 📋 Step-by-Step Connection

### **1. User Action (Frontend)**

User clicks "Upload File" in the browser:
```javascript
// templates/upload.html
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const xhr = new XMLHttpRequest();
xhr.open('POST', '/api/upload');  // ← Sends to FastAPI backend
xhr.send(formData);
```

---

### **2. FastAPI Receives Request (Backend)**

FastAPI endpoint receives the file:
```python
# main.py
@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session)  # ← Gets Supabase connection
):
    # Process file...
    # Store in Supabase via session
```

---

### **3. Database Connection (Backend → Supabase)**

`get_session()` creates a connection to Supabase:
```python
# app/db.py
from app.config import DATABASE_URL  # ← From .env file

engine = create_engine(
    DATABASE_URL,  # ← postgresql://postgres.xkbmbqejeoxfatcliftv:...@aws-1-eu-west-1.pooler.supabase.com:5432/postgres
    pool_pre_ping=True
)

def get_session():
    return SessionLocal()  # ← Returns SQLAlchemy session connected to Supabase
```

---

### **4. Data Storage (Backend → Supabase)**

Data is stored using SQLAlchemy ORM:
```python
# Create invoice record
invoice = Invoice(
    tenant_id=user.tenant_id,  # ← Multi-tenant isolation
    invoice_number="INV-001",
    gross_amount=500.00,
    ...
)
session.add(invoice)
session.commit()  # ← Saves to Supabase PostgreSQL database
```

---

### **5. Response to Frontend (Backend → Frontend)**

FastAPI returns JSON response:
```python
return JSONResponse({
    "status": "success",
    "message": "File uploaded successfully",
    "batch_id": batch_id
})
```

---

### **6. Frontend Updates UI**

JavaScript receives response and updates UI:
```javascript
xhr.addEventListener('load', () => {
    if (xhr.status === 200) {
        const response = JSON.parse(xhr.responseText);
        showMessage(response.message, 'success');
        // Redirect to invoices page
        window.location.href = '/invoices';
    }
});
```

---

## 🔄 Complete Data Flow Example

### **Scenario: User Uploads Units File**

1. **Frontend**: User selects `test_data_units.xlsx` and clicks "Upload"
2. **Frontend → Backend**: JavaScript sends POST request to `/api/import/units`
3. **Backend**: FastAPI receives file, reads Excel using pandas
4. **Backend → Supabase**: Creates `Unit` records with `tenant_id` and saves to database
5. **Backend → Frontend**: Returns success message with count of units imported
6. **Frontend**: Shows success message, updates UI

**Result**: Data is now in Supabase, visible in:
- ✅ Application UI (via `/data-management`)
- ✅ Supabase Dashboard (Table Editor)

---

## 🔐 Multi-Tenant Isolation

### **How It Works**

Every request includes the logged-in user's `tenant_id`:

```python
# User logs in
request.session["tenant_id"] = user.tenant_id  # ← Stored in session

# When querying data
user: User = Depends(get_current_user)  # ← Gets user from session
tenant_id = user.tenant_id  # ← Gets tenant_id

# All queries filter by tenant_id
units = session.query(Unit).filter(
    Unit.tenant_id == tenant_id  # ← Only returns this tenant's data
).all()
```

**Result**: 
- ✅ User A (tenant_id=1) only sees tenant 1's data
- ✅ User B (tenant_id=2) only sees tenant 2's data
- ✅ Complete data isolation at database level

---

## 📊 API Endpoints (Frontend → Backend)

### **Authentication**
- `POST /login` - User login
- `POST /signup` - User registration
- `GET /logout` - User logout

### **Data Import**
- `POST /api/import/units` - Upload units Excel/CSV
- `POST /api/import/leases` - Upload leases Excel/CSV
- `POST /api/upload` - Upload invoices Excel/CSV

### **Data Management**
- `GET /api/units` - Get all units (filtered by tenant)
- `GET /api/leases` - Get all leases (filtered by tenant)
- `GET /api/invoices` - Get all invoices (filtered by tenant)
- `PUT /api/units/{id}` - Update unit
- `DELETE /api/units/{id}` - Delete unit

### **Validation**
- `GET /api/invoices/{id}` - Get invoice with validation
- `POST /api/validate/{id}` - Re-validate invoice

---

## ✅ Verification: Is Frontend Connected to Backend?

### **Test 1: Check Server is Running**

```bash
uvicorn main:app --reload
```

Should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### **Test 2: Check Database Connection**

```bash
python scripts/test_supabase_connection.py
```

Should see:
```
✅ Database connection successful!
✅ Session works!
```

### **Test 3: Upload File via UI**

1. Go to http://localhost:8000/login
2. Login with test credentials
3. Upload `test_data_units.xlsx`
4. Check Supabase dashboard - data should appear

### **Test 4: Check Browser Console**

1. Open browser DevTools (F12)
2. Go to "Network" tab
3. Upload a file
4. Should see POST request to `/api/import/units` with status 200

---

## 🐛 Troubleshooting

### **Issue: "Cannot connect to server"**

**Check**:
1. Is server running? (`uvicorn main:app --reload`)
2. Is port 8000 available?
3. Check server logs for errors

### **Issue: "Database error"**

**Check**:
1. Is `.env` file present with `DATABASE_URL`?
2. Is Supabase connection working? (`python scripts/test_supabase_connection.py`)
3. Check server logs for SQL errors

### **Issue: "File upload fails"**

**Check**:
1. Browser console for JavaScript errors
2. Server logs for backend errors
3. File format (must be .xlsx, .xls, or .csv)
4. File size (max 50MB)

### **Issue: "Data not showing"**

**Check**:
1. Supabase dashboard - is data there?
2. Are you logged in as correct tenant?
3. Check browser console for API errors
4. Check server logs for processing errors

---

## 📝 Summary

**Frontend-Backend Connection**:
- ✅ Frontend uses JavaScript `XMLHttpRequest` to call API endpoints
- ✅ Backend (FastAPI) receives requests and processes them
- ✅ Backend uses SQLAlchemy to connect to Supabase PostgreSQL
- ✅ All data is stored in Supabase with `tenant_id` for isolation
- ✅ Frontend receives responses and updates UI

**The connection is automatic** - as long as:
1. Server is running
2. `.env` has correct `DATABASE_URL`
3. Supabase is accessible

**No additional configuration needed!** 🎉

