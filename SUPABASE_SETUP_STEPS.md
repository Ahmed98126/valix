# Supabase Setup - Step by Step

## ✅ You Have Your Connection String!

Your connection string:
```
postgresql://postgres:[YOUR-PASSWORD]@db.xkbmbqejeoxfatcliftv.supabase.co:5432/postgres
```

---

## 📝 Step-by-Step Setup

### Step 1: Get Your Database Password

1. Go to your Supabase project dashboard
2. Click **Settings** (gear icon) → **Database**
3. Scroll down to **Database password**
4. If you don't see it, click **"Reset database password"**
5. **Copy the password** (you'll need it!)

### Step 2: Create `.env` File

1. In your project root, create a file named `.env`
2. Copy the content from `.env.example`
3. Replace `[YOUR-PASSWORD]` with your actual password

**Example `.env` file:**
```env
DATABASE_URL=postgresql://postgres:your-actual-password-here@db.xkbmbqejeoxfatcliftv.supabase.co:5432/postgres

SECRET_KEY=your-secret-key-min-32-chars
SESSION_SECRET=your-session-secret-min-32-chars
```

### Step 3: Install PostgreSQL Driver

```bash
pip install psycopg2-binary
```

Or if using requirements.txt:
```bash
pip install -r requirements.txt
```

### Step 4: Test Connection

```bash
python scripts/test_supabase_connection.py
```

**Expected output:**
```
🔌 Testing Supabase connection...
✅ Database connection successful!
✅ Session works! Found 0 tenant(s)
✅ Found 0 user(s)
✅ PostgreSQL version: PostgreSQL 15.x...
🎉 All tests passed! Supabase connection is working!
```

### Step 5: Initialize Database Tables

```bash
python -m app.db
```

This will create all your tables in Supabase!

### Step 6: Verify in Supabase Dashboard

1. Go to Supabase → **Table Editor**
2. You should see all your tables:
   - `tenants`
   - `users`
   - `units`
   - `leases`
   - `invoices`
   - `invoice_validations`
   - `unit_timeline`
   - `upload_status`

---

## 🧪 Test SQL Queries

Now you can use the **SQL Editor** in Supabase!

1. Go to **SQL Editor** in Supabase dashboard
2. Try this query:
```sql
SELECT * FROM tenants;
```

3. Or check your tables:
```sql
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';
```

---

## ✅ Success Checklist

- [ ] Got database password from Supabase
- [ ] Created `.env` file with correct connection string
- [ ] Installed `psycopg2-binary`
- [ ] Test connection script passes
- [ ] Database tables created
- [ ] Can see tables in Supabase dashboard
- [ ] Can run SQL queries in SQL Editor

---

## 🚨 Troubleshooting

### Error: "password authentication failed"
- **Fix:** Check your password is correct in `.env`
- Make sure you replaced `[YOUR-PASSWORD]` with actual password

### Error: "could not connect to server"
- **Fix:** Check your connection string is correct
- Verify Supabase project is active
- Check network/firewall settings

### Error: "No module named 'psycopg2'"
- **Fix:** Run `pip install psycopg2-binary`

### Error: "relation does not exist"
- **Fix:** Run `python -m app.db` to create tables

---

## 🎉 Next Steps

Once connection works:
1. ✅ Test all features
2. ✅ Import test data
3. ✅ Run comprehensive tests
4. ✅ Deploy to production

**You're ready to go!** 🚀


