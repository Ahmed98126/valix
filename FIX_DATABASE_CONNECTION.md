# 🔧 Fix: Database Connection Issue

## 🚨 **The Problem**

The app is running, but database connection is failing:
```
connection to server at "db.xkbmbqejeoxfatcliftv.supabase.co" failed: Cannot assign requested address
```

This is an **IPv6 vs IPv4** issue. Azure App Service might not support IPv6 connections.

---

## ✅ **Solution: Use Supabase Connection Pooler (IPv4)**

Supabase provides a **connection pooler** that uses IPv4, which works better with Azure.

---

## 🔧 **Step 1: Get Connection Pooler URL**

1. **Go to Supabase Dashboard**
   - Visit: https://supabase.com/dashboard
   - Select your project
   - Go to **"Settings"** → **"Database"**
   - Scroll to **"Connection string"** section

2. **Find "Connection Pooling"**
   - Look for **"Session mode"** or **"Transaction mode"**
   - Copy the connection string (it will look like):
     ```
     postgres://postgres.apbkobhfnmcqqzqeeqss:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
     ```
   - Or use **"Transaction mode"** (port 6543):
     ```
     postgres://postgres:[YOUR-PASSWORD]@db.xkbmbqejeoxfatcliftv.supabase.co:6543/postgres
     ```

---

## 🔧 **Step 2: Update DATABASE_URL in Azure**

1. **Go to Azure Portal** → App Service "Valix"
2. **Click "Configuration"** → **"Application settings"** tab
3. **Find "DATABASE_URL"**
4. **Update the value** with the connection pooler URL
5. **Click "Save"** → **"Continue"**
6. **Restart the app** (Overview → Restart)

---

## 🎯 **Alternative: Force IPv4 in Connection String**

If connection pooler doesn't work, we can modify the connection to force IPv4, but the pooler is recommended.

---

## 📋 **After Fixing**

1. **Check Logs:**
   - Should see: `✅ Database initialized successfully`
   - No more connection errors

2. **Test App:**
   - Try signing up
   - Try logging in
   - Should work with database!

---

**Let's fix the database connection next!** 🔧

