# 🔧 Fix: ModuleNotFoundError: No module named 'uvicorn'

## 🚨 **The Problem**

Azure can't find `uvicorn` module. The deployment didn't install dependencies correctly, or we need to use uvicorn directly.

---

## ✅ **Solution: Use Uvicorn Directly**

Instead of Gunicorn with Uvicorn workers, let's use **Uvicorn directly**. This is simpler and works better with Azure.

---

## 🔧 **Fix: Update Startup Command**

### **In Azure Portal:**

1. **Go to App Service "Valix"**
2. **Click "Configuration"** (left menu)
3. **Click "General settings"** tab
4. **Find "Startup Command"**
5. **Replace with:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
6. **Click "Save"** at the top
7. **Click "Continue"** to confirm
8. **Restart the app** (Overview → Restart)

---

## ✅ **What Changed**

**Before (Gunicorn with Uvicorn workers - missing uvicorn):**
```bash
gunicorn main:app --bind 0.0.0.0:8000 --workers 2 --worker-class uvicorn.workers.UvicornWorker --timeout 120
```

**After (Uvicorn directly - simpler!):**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 🎯 **Why This Works**

- **Uvicorn** is already in `requirements.txt` as `uvicorn[standard]>=0.24.0`
- **Direct approach** - no need for Gunicorn wrapper
- **Simpler** - fewer moving parts
- **Works with Azure** - Azure will install uvicorn from requirements.txt

---

## 📋 **Alternative: If Uvicorn Still Not Found**

If you still get "uvicorn not found", we need to ensure dependencies are installed. But first, try the direct uvicorn command above.

---

**Update the startup command to use uvicorn directly!** 🚀

