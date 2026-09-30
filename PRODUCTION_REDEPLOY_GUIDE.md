# 🚨 Production Redeployment Guide - Fix Connection Pool Issues

## **Problem**
Production is showing:
- ❌ Database connection pool exhaustion errors
- ❌ Signup button not working
- ❌ Slow performance
- ❌ "QueuePool limit of size 5 overflow 10 reached" errors

## **Root Cause**
Production environment is running **old code** that doesn't have the connection pool fixes.

## **Solution: Redeploy Latest Code**

---

## 🚀 **Quick Redeploy Steps** (15-20 minutes)

### **Option 1: VS Code Extension (Easiest)** ⭐ **RECOMMENDED**

1. **Open VS Code**
   - Make sure you have the "Azure App Service" extension installed
   - Sign in to Azure if needed

2. **Deploy**
   - Right-click on your project folder (`invoice-validator`)
   - Select **"Deploy to Web App"**
   - Choose your Azure App Service (should be `valix` or similar)
   - Wait for deployment to complete (5-10 minutes)

3. **Restart App Service**
   - Go to Azure Portal → Your App Service
   - Click **"Restart"** button (top toolbar)
   - Wait 1-2 minutes for restart

4. **Test**
   - Visit `https://valixs.com/signup`
   - Try creating an account
   - Should work without connection errors

---

### **Option 2: Azure CLI** (If VS Code doesn't work)

1. **Install Azure CLI** (if not installed)
   ```bash
   # Download from: https://aka.ms/installazurecliwindows
   ```

2. **Login to Azure**
   ```bash
   az login
   ```

3. **Navigate to Project**
   ```bash
   cd C:\Users\ahmed\invoice-validator
   ```

4. **Deploy**
   ```bash
   az webapp up --name YOUR_APP_NAME --resource-group YOUR_RESOURCE_GROUP --runtime "PYTHON:3.11"
   ```
   Replace:
   - `YOUR_APP_NAME` with your Azure App Service name (e.g., `valix-guepgdc6f4fwgtcu`)
   - `YOUR_RESOURCE_GROUP` with your resource group name

5. **Restart App Service**
   ```bash
   az webapp restart --name YOUR_APP_NAME --resource-group YOUR_RESOURCE_GROUP
   ```

---

### **Option 3: Git Deployment** (If you have Git set up)

1. **Commit Changes**
   ```bash
   cd C:\Users\ahmed\invoice-validator
   git add .
   git commit -m "Fix: Database connection pool exhaustion"
   git push
   ```

2. **Azure will auto-deploy** if you have Git deployment configured

3. **Restart App Service** in Azure Portal

---

## ⚙️ **Verify Environment Variables** (Important!)

After redeploying, check that these are set in Azure:

1. **Go to Azure Portal**
   - Your App Service → **Configuration** → **Application settings**

2. **Verify These Settings Exist:**
   ```
   DATABASE_URL = postgresql://postgres.xkbmbqejeoxfatcliftv:YOUR_PASSWORD@aws-1-eu-west-1.pooler.supabase.com:5432/postgres
   SECRET_KEY = [your secret key]
   SENDGRID_API_KEY = [your SendGrid key]
   SENDGRID_FROM_EMAIL = noreply@valixs.com
   SENDGRID_FROM_NAME = Valix
   SESSION_EXPIRY_SECONDS = 86400
   ```

3. **If Missing, Add Them:**
   - Click **"+ New application setting"**
   - Add each setting
   - Click **"Save"** at the top
   - Click **"Continue"** to confirm

---

## 🔧 **Verify Startup Command**

1. **Go to Configuration** → **General settings**

2. **Check Startup Command:**
   ```
   python -m uvicorn main:app --host 0.0.0.0 --port 8000
   ```
   
   OR (if using Gunicorn):
   ```
   gunicorn main:app --bind 0.0.0.0:8000 --workers 2 --timeout 120 --worker-class uvicorn.workers.UvicornWorker
   ```

3. **If Wrong, Update It:**
   - Change to the command above
   - Click **"Save"**

---

## ✅ **What Was Fixed in Latest Code**

1. **Database Connection Pool** ✅
   - `pool_size=3` (was 5, causing exhaustion)
   - `max_overflow=7` (was 10, too high)
   - `pool_recycle=1800` (30 minutes, faster cleanup)
   - `pool_timeout=30` (wait time for connection)

2. **Session Management** ✅
   - Fixed `get_session()` to properly close sessions
   - Fixed background task session handling
   - All sessions now properly closed

3. **Error Handling** ✅
   - Added validation error handler
   - Better error messages for users
   - No more JSON errors on HTML pages

4. **Forgot Password** ✅
   - Restored forgot password link
   - Full password reset flow working

---

## 🧪 **Testing After Redeploy**

1. **Test Signup**
   - Go to `https://valixs.com/signup`
   - Create a new account
   - Should work without errors

2. **Test Login**
   - Go to `https://valixs.com/login`
   - Sign in with existing account
   - Should work without errors

3. **Test Forgot Password**
   - Click "Forgot password?" on login page
   - Enter email
   - Should receive reset email

4. **Check Performance**
   - Pages should load faster
   - No connection timeout errors
   - Smooth user experience

---

## 📊 **Monitor After Deployment**

1. **Check Azure Logs**
   - Go to App Service → **Log stream**
   - Watch for any connection errors
   - Should see "Database initialized successfully"

2. **Check Application Insights** (if enabled)
   - Monitor response times
   - Check for errors

3. **Test with Real Users**
   - Have a few users try signup/login
   - Monitor for any issues

---

## 🚨 **If Issues Persist**

### **Still Getting Connection Errors?**

1. **Check Database Connection String**
   - Make sure `DATABASE_URL` uses the **pooler** connection:
   - Should be: `aws-1-eu-west-1.pooler.supabase.com`
   - NOT: `db.xkbmbqejeoxfatcliftv.supabase.co`

2. **Restart App Service**
   - Sometimes a restart is needed after config changes

3. **Check Supabase Limits**
   - Free tier has connection limits
   - Check Supabase dashboard for connection count

4. **Scale Up App Service** (if needed)
   - Basic B1 plan has more resources
   - Free F1 is very limited

---

## 📝 **Summary**

**What to do:**
1. ✅ Redeploy latest code (VS Code extension easiest)
2. ✅ Verify environment variables
3. ✅ Restart App Service
4. ✅ Test signup/login
5. ✅ Monitor for errors

**Expected Result:**
- ✅ No connection pool errors
- ✅ Signup button works
- ✅ Fast page loads
- ✅ Smooth user experience

---

## 🎯 **Quick Checklist**

- [ ] Code deployed to Azure
- [ ] App Service restarted
- [ ] Environment variables verified
- [ ] Startup command correct
- [ ] Signup tested and working
- [ ] Login tested and working
- [ ] No connection errors in logs
- [ ] Performance is good

**After completing these steps, production should work perfectly!** 🎉

