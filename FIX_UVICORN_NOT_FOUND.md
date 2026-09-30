# 🔧 Fix: uvicorn: not found

## 🚨 **The Problem**

Uvicorn command is not found because dependencies weren't installed during deployment.

---

## ✅ **Solution: Use Python Module Syntax**

Instead of `uvicorn`, use `python -m uvicorn` which will use the Python interpreter.

---

## 🔧 **Fix: Update Startup Command**

### **In Azure Portal:**

1. **Go to App Service "Valix"**
2. **Click "Configuration"** → **"General settings"** tab
3. **Find "Startup Command"**
4. **Replace with:**
   ```bash
   python -m uvicorn main:app --host 0.0.0.0 --port 8000
   ```
5. **Click "Apply"** → **"Continue"**
6. **Restart the app** (Overview → Restart)

---

## ✅ **What Changed**

**Before (uvicorn not found):**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

**After (uses Python module):**
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 🎯 **Why This Works**

- `python -m uvicorn` uses Python's module system
- It will find uvicorn if it's installed in the Python environment
- Works even if uvicorn isn't in PATH

---

**Update the startup command now!** 🚀

