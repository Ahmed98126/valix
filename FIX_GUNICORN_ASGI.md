# 🔧 Fix: TypeError - FastAPI.__call__() missing 1 required positional argument: 'send'

## 🚨 **The Problem**

FastAPI is an **ASGI** framework, but Gunicorn's default workers are **WSGI**. They're incompatible!

**Error:**
```
TypeError: FastAPI.__call__() missing 1 required positional argument: 'send'
```

---

## ✅ **Solution: Use Uvicorn Workers**

Gunicorn needs to use **Uvicorn workers** to run FastAPI.

---

## 🔧 **Fix: Update Startup Command**

### **In Azure Portal:**

1. **Go to App Service "Valix"**
2. **Click "Configuration"** (left menu)
3. **Click "General settings"** tab
4. **Find "Startup Command"**
5. **Update to:**
   ```bash
   gunicorn main:app --bind 0.0.0.0:8000 --workers 2 --worker-class uvicorn.workers.UvicornWorker --timeout 120
   ```
6. **Click "Save"** at the top
7. **Click "Continue"** to confirm
8. **Restart the app** (Configuration → Restart)

---

## ✅ **What Changed**

**Before (WSGI - doesn't work):**
```bash
gunicorn main:app --bind 0.0.0.0:8000 --workers 2 --timeout 120
```

**After (ASGI with Uvicorn workers - works!):**
```bash
gunicorn main:app --bind 0.0.0.0:8000 --workers 2 --worker-class uvicorn.workers.UvicornWorker --timeout 120
```

The key addition: `--worker-class uvicorn.workers.UvicornWorker`

---

## 🎯 **Why This Works**

- **Gunicorn**: Production-ready server manager
- **Uvicorn Workers**: ASGI-compatible workers for FastAPI
- **Together**: Best of both worlds! 🚀

---

## 📋 **Verify**

After updating and restarting:

1. **Check Logs:**
   - Should see: `Using worker: uvicorn.workers.UvicornWorker`
   - No more TypeError!

2. **Test URL:**
   - Visit: `https://valix-guepgdc6f4fwgtcu.westeurope-01.azurewebsites.net`
   - Should see landing page! 🎉

---

**Update the startup command now!** 🔧

