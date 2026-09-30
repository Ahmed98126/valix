# Verify Supabase Connection String

## 🔍 Please Check Your Supabase Dashboard

The hostname isn't resolving. Let's verify the connection string is correct.

### Steps:

1. **Go to Supabase Dashboard**
   - https://supabase.com/dashboard
   - Select your project

2. **Get Connection String**
   - Click **Settings** (gear icon) → **Database**
   - Scroll to **Connection string** section
   - Click on **URI** tab
   - Copy the **exact** connection string shown

3. **Verify Format**
   The connection string should look like:
   ```
   postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
   ```
   
   OR
   
   ```
   postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   ```

4. **Update .env File**
   - Replace the DATABASE_URL in your `.env` file with the exact string from Supabase
   - Make sure there are no extra spaces or characters

## 🔄 Alternative: Use Connection Pooling

Supabase offers connection pooling. Try this format:

```
postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
```

## ✅ Once You Have the Correct String

1. Update `.env` file with the correct connection string
2. Run: `python scripts/test_supabase_connection.py`
3. If successful, run: `python -m app.db`

---

**Note**: The connection string format might be slightly different. Please copy it directly from your Supabase dashboard to ensure accuracy.


