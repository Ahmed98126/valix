# 🔧 Azure Deployment Structure Fix

## 🚨 **Current Issue**

Azure is extracting files to a temp directory (`/tmp/8de46398f8ba2d2`), but gunicorn might be looking in the wrong place.

---

## ✅ **Solution: Update Startup Command**

The startup command needs to change directory to where the app is extracted.

### **Option 1: Use Absolute Path** ⭐ **RECOMMENDED**

1. **Go to Azure Portal:**
   - App Service "Valix" → **"Configuration"**
   - **"General settings"** tab
   - Find **"Startup Command"**

2. **Update to:**
   ```bash
   cd /home/site/wwwroot && gunicorn main:app --bind 0.0.0.0:8000 --workers 2 --timeout 120
   ```

3. **Save** and restart the app

---

### **Option 2: Use Python Module Path**

If Option 1 doesn't work, try:

```bash
cd /home/site/wwwroot && python -m gunicorn main:app --bind 0.0.0.0:8000 --workers 2 --timeout 120
```

---

### **Option 3: Check Actual File Location**

1. **In Azure Portal:**
   - App Service "Valix" → **"Advanced Tools"** → **"Go"**
   - **"Debug console"** → **"CMD"**
   - Navigate to: `site\wwwroot`
   - Check if `main.py` is there

2. **If files are in a subdirectory:**
   - Note the exact path
   - Update startup command to include that path

---

## 🎯 **Quick Test**

After updating the startup command:

1. **Restart the App:**
   - Azure Portal → App Service "Valix" → **"Restart"**

2. **Check Logs:**
   - Should see: `Starting gunicorn` without errors
   - Workers should boot successfully

3. **Test URL:**
   - Visit: `https://valix-guepgdc6f4fwgtcu.westeurope-01.azurewebsites.net`
   - Should see landing page

---

**Let's update the startup command first!** 🔧

