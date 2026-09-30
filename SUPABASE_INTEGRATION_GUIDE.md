# Supabase Integration Guide

## ✅ Supabase Compatibility - YES, It's Doable!

Your current setup is **100% compatible** with Supabase. Here's why and how:

---

## 🎯 Why Supabase Works Perfectly

### 1. **PostgreSQL-Based**
- ✅ Supabase uses **PostgreSQL** (same as your production target)
- ✅ Your app already supports PostgreSQL via SQLAlchemy
- ✅ No code changes needed - just connection string!

### 2. **SQLAlchemy Compatibility**
- ✅ SQLAlchemy works seamlessly with PostgreSQL
- ✅ Your models are already PostgreSQL-ready
- ✅ All queries will work as-is

### 3. **Multi-Tenant Ready**
- ✅ Supabase supports row-level security (perfect for multi-tenant)
- ✅ Your `tenant_id` architecture works perfectly
- ✅ Can add RLS policies for extra security

---

## 🔧 How to Integrate Supabase

### Step 1: Get Supabase Connection String

1. **Create Supabase Project**
   - Go to https://supabase.com
   - Create new project
   - Wait for database to provision (~2 minutes)

2. **Get Connection String**
   - Go to Project Settings → Database
   - Find "Connection string" → "URI"
   - Copy the connection string
   - Format: `postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres`

### Step 2: Update Your Configuration

**Option A: Environment Variable (Recommended)**
```bash
# .env file
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

**Option B: Direct in config.py (for testing)**
```python
# app/config.py
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"
)
```

### Step 3: Install PostgreSQL Driver

```bash
pip install psycopg2-binary
# or
pip install asyncpg  # if using async
```

Add to `requirements.txt`:
```
psycopg2-binary>=2.9.0
```

### Step 4: Update Database Connection

**File: `app/db.py`**
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Supabase uses PostgreSQL, so remove SQLite-specific args
engine = create_engine(
    DATABASE_URL,
    # Remove: connect_args={"check_same_thread": False}  # SQLite only
    echo=False,
    pool_pre_ping=True,  # Reconnect if connection lost
    pool_size=5,  # Connection pool size
    max_overflow=10,
)
```

### Step 5: Run Migration

```bash
# Initialize database tables
python -m app.db

# Or use Alembic for migrations (recommended for production)
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

---

## 🚀 Supabase Features You Can Use

### 1. **SQL Editor** (What You Want!)
- ✅ Direct SQL queries in Supabase dashboard
- ✅ Query your tables: `SELECT * FROM invoices WHERE tenant_id = 1;`
- ✅ Run complex analytics queries
- ✅ Export results to CSV

### 2. **Database Management**
- ✅ Visual table editor
- ✅ View/edit data directly
- ✅ Index management
- ✅ Query performance insights

### 3. **Row-Level Security (RLS)** (Optional)
```sql
-- Example: Ensure users only see their tenant's data
CREATE POLICY tenant_isolation ON invoices
  FOR ALL
  USING (tenant_id = current_setting('app.tenant_id')::int);
```

### 4. **Real-time Subscriptions** (Future Enhancement)
- Real-time invoice updates
- Live validation status
- WebSocket support

### 5. **Storage** (For Invoice Files)
- Store uploaded Excel/CSV files
- PDF storage for future AI scanning
- Automatic backups

---

## 📊 Migration Strategy

### Option 1: Fresh Start (Recommended for New Projects)
1. Create Supabase project
2. Run `python -m app.db` to create tables
3. Import data via scripts

### Option 2: Migrate Existing Data
1. Export from SQLite:
   ```python
   # scripts/export_sqlite_data.py
   # Export all tables to JSON/CSV
   ```
2. Import to Supabase:
   ```python
   # scripts/import_to_supabase.py
   # Import data maintaining relationships
   ```

---

## 🔒 Security Best Practices

### 1. **Connection String Security**
- ✅ Never commit connection strings to Git
- ✅ Use environment variables
- ✅ Use Supabase's connection pooling

### 2. **Database Credentials**
- ✅ Use Supabase's built-in user management
- ✅ Create separate database users per tenant (optional)
- ✅ Enable SSL connections

### 3. **Row-Level Security**
- ✅ Add RLS policies for extra security
- ✅ Ensure tenant isolation at database level
- ✅ Audit logs for sensitive operations

---

## 🧪 Testing Supabase Connection

**Test Script: `scripts/test_supabase_connection.py`**
```python
"""Test Supabase database connection."""
from app.db import engine, get_session
from app.models import Tenant

# Test connection
with get_session() as session:
    tenants = session.query(Tenant).all()
    print(f"✅ Connected! Found {len(tenants)} tenants")
```

---

## 📝 Environment Variables

**`.env` file:**
```env
# Supabase Database
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres

# Security
SECRET_KEY=your-secret-key-min-32-chars
SESSION_SECRET=your-session-secret

# Optional: Supabase API (for future features)
SUPABASE_URL=https://[PROJECT-REF].supabase.co
SUPABASE_KEY=your-anon-key
```

---

## ✅ What Works Out of the Box

- ✅ All your SQLAlchemy models
- ✅ All database queries
- ✅ Multi-tenant architecture
- ✅ Foreign key relationships
- ✅ Unique constraints
- ✅ All validation logic

---

## 🎯 Next Steps

1. **Create Supabase Account** → https://supabase.com
2. **Create Project** → Get connection string
3. **Update `.env`** → Add `DATABASE_URL`
4. **Install Driver** → `pip install psycopg2-binary`
5. **Test Connection** → Run test script
6. **Migrate Data** → Use migration script
7. **Start Using SQL Editor** → Query your data!

---

## 💡 Benefits of Supabase

1. **SQL Editor** - Direct SQL queries (what you want!)
2. **Free Tier** - 500MB database, 2GB bandwidth
3. **Automatic Backups** - Daily backups included
4. **Scalable** - Easy to upgrade as you grow
5. **PostgreSQL** - Full PostgreSQL features
6. **Dashboard** - Visual database management
7. **API** - REST and GraphQL APIs (future use)

---

## ⚠️ Important Notes

1. **Connection Pooling**: Supabase handles this automatically
2. **SSL Required**: Supabase requires SSL connections (SQLAlchemy handles this)
3. **Rate Limits**: Free tier has limits (check Supabase docs)
4. **Backups**: Daily backups included, can restore to any point
5. **Migrations**: Use Alembic for production migrations

---

**Status**: ✅ **100% Compatible - Ready to Use!**

Your current architecture is perfect for Supabase. Just update the connection string and you're good to go!


