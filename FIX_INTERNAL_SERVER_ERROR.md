# 🔧 Fix: Internal Server Error

## 🚨 **The Problem**

The app is running (workers booted), but requests are failing with "Internal Server Error".

This usually means:
- Database connection issue
- Missing environment variables
- Code error when handling requests
- Missing dependencies

---

## 🔍 **Step 1: Check Detailed Error Logs**

### **In Azure Portal:**

1. **Go to App Service "Valix"**
2. **Click "Log stream"** (left menu)
3. **Scroll to the bottom** - look for error messages
4. **Try accessing the URL again** while watching logs
5. **Copy the error message** you see

### **Or Check Application Logs:**

1. **App Service "Valix"** → **"Log stream"**
2. **Look for lines with "ERROR" or "Exception"**
3. **Copy the full error traceback**

---

## 🎯 **Common Causes & Fixes**

### **1. Database Connection Error** ⭐ **MOST LIKELY**

**Symptom:** Error about database connection or PostgreSQL

**Fix:**
1. Go to **Configuration** → **Application settings**
2. Verify `DATABASE_URL` is set correctly:
   ```
   postgresql://postgres:YOUR_PASSWORD@db.xkbmbqejeoxfatcliftv.supabase.co:5432/postgres
   ```
3. Make sure password is correct
4. **Save** and **Restart** the app

---

### **2. Missing Environment Variables**

**Symptom:** Error about `SECRET_KEY` or `SESSION_SECRET`

**Fix:**
1. Go to **Configuration** → **Application settings**
2. Verify all 6 variables are set:
   - `DATABASE_URL`
   - `SECRET_KEY`
   - `SESSION_SECRET`
   - `ENVIRONMENT=production`
   - `DEBUG=False`
   - `MAX_UPLOAD_SIZE=52428800`
3. **Save** and **Restart**

---

### **3. Import Error**

**Symptom:** `ModuleNotFoundError` or `ImportError`

**Fix:**
- Check if all dependencies are installed
- Verify `requirements.txt` is deployed

---

### **4. Code Error**

**Symptom:** Python traceback with file names and line numbers

**Fix:**
- Share the error message
- We'll fix the code

---

## 🚀 **Quick Action**

**First, check the logs and share the error message!**

The logs will tell us exactly what's wrong.

