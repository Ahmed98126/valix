# Supabase Session Pooler Connection

## ✅ Solution: Use Session Pooler

The "Not IPv4 compatible" warning means you need to use the **Session Pooler** connection instead of the direct connection.

### Connection String Format

**Direct Connection** (IPv6 only - not working):
```
postgresql://postgres:[PASSWORD]@db.xkbmbqejeoxfatcliftv.supabase.co:5432/postgres
```

**Session Pooler** (IPv4 compatible - use this):
```
postgresql://postgres.xkbmbqejeoxfatcliftv:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

### How to Get the Correct Pooler Connection String

1. In Supabase Dashboard → **Settings** → **Database**
2. Under "Connection string" → **URI** tab
3. Change **Method** from "Direct connection" to **"Session Pooler"**
4. Copy the connection string shown
5. It should have:
   - Port: `6543` (not 5432)
   - Host: `aws-0-[REGION].pooler.supabase.com` (not `db.[PROJECT].supabase.co`)
   - User: `postgres.[PROJECT-REF]` (not just `postgres`)

### Update Your .env File

Replace the DATABASE_URL with the Session Pooler connection string.

---

## 🔧 Alternative: Get Pooler String from Dashboard

1. Go to Supabase → Settings → Database
2. Click "Connection string" → "URI" tab
3. Change **Method** dropdown to **"Session Pooler"**
4. Copy the connection string
5. Update `.env` file

---

## ✅ Benefits of Session Pooler

- ✅ IPv4 compatible
- ✅ Better connection management
- ✅ Recommended for production
- ✅ Handles connection pooling automatically


