# 🚨 URGENT: Production Redeploy - Fix Connection Pool

## **Current Problem**
Production is running **OLD CODE** with connection pool settings:
- ❌ `pool_size=5` (should be 3)
- ❌ `max_overflow=10` (should be 7)
- ❌ Sessions not being closed properly

**Result:** All 15 connections are exhausted, website is down.

---

## ⚡ **IMMEDIATE FIX (5-10 minutes)**

### **Step 1: Deploy Latest Code**

**Option A: VS Code Extension (Easiest)** ⭐

1. Open VS Code
2. Make sure "Azure App Service" extension is installed
3. Right-click on project folder (`invoice-validator`)
4. Select **"Deploy to Web App"**
5. Choose your Azure App Service
6. Wait for deployment (5-10 minutes)

**Option B: Azure Portal (If VS Code doesn't work)**

1. Go to Azure Portal → Your App Service
2. Go to **"Deployment Center"**
3. If you have Git configured:
   - Push your code: `git push`
   - Azure will auto-deploy
4. If not, use **"Local Git"** or **"FTP"** deployment

---

### **Step 2: RESTART App Service** (CRITICAL!)

**This is REQUIRED** - new connection pool settings only apply after restart:

1. Go to Azure Portal → Your App Service
2. Click **"Restart"** button (top toolbar)
3. Wait 1-2 minutes for restart
4. App will reload with new code

---

### **Step 3: Verify Fix**

1. Check logs (should see no more connection errors):
   - Azure Portal → App Service → **"Log stream"**
   - Should see: "Database initialized successfully"
   - No more "QueuePool limit" errors

2. Test signup:
   - Visit `https://valixs.com/signup`
   - Should load without errors
   - Should be able to create account

---

## 🔍 **How to Verify Code is Updated**

After deployment, check logs for:
- ✅ `pool_size=3` (not 5)
- ✅ `max_overflow=7` (not 10)
- ✅ No connection timeout errors

Or check the actual code in Azure:
- Go to **"SSH"** or **"Console"** in Azure Portal
- Check `/home/site/wwwroot/app/db.py`
- Should show `pool_size=3, max_overflow=7`

---

## 📋 **What Changed in Latest Code**

### **`app/db.py`** - Connection Pool Settings:
```python
pool_size=3,        # Was: 5
max_overflow=7,     # Was: 10
pool_recycle=1800,  # 30 minutes
pool_timeout=30     # Wait time
```

### **`main.py`** - Session Management:
- ✅ `get_session()` properly closes sessions
- ✅ Background tasks use `SessionLocal()` with `finally: session.close()`
- ✅ All sessions are properly cleaned up

---

## ⚠️ **If Deployment Fails**

1. **Check Azure Logs:**
   - Deployment Center → Logs
   - Look for errors

2. **Manual File Upload:**
   - Use Azure Portal → **"Advanced Tools"** → **"Go"** (Kudu)
   - Navigate to `/home/site/wwwroot`
   - Upload files manually

3. **Check Environment Variables:**
   - Configuration → Application settings
   - Verify `DATABASE_URL` is correct

---

## ✅ **After Successful Deployment**

You should see:
- ✅ No connection pool errors
- ✅ Signup page loads
- ✅ Login works
- ✅ Fast page loads
- ✅ Smooth user experience

---

## 🎯 **Quick Checklist**

- [ ] Code deployed to Azure
- [ ] App Service restarted
- [ ] Logs show no connection errors
- [ ] Signup page works
- [ ] Login works
- [ ] Performance is good

**Once these are checked, production will be fixed!** 🎉

