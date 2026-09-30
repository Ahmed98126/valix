# 🔧 Fix: Startup Command Not Saving

## 🚨 **The Problem**

The startup command change didn't save. Azure is still using the old command.

---

## ✅ **Solution: Force Save and Redeploy**

### **Step 1: Verify Startup Command is Saved**

1. **Go to Azure Portal**
2. **App Service "Valix"** → **"Configuration"** → **"General settings"**
3. **Check "Startup Command"** - does it show `uvicorn main:app --host 0.0.0.0 --port 8000`?
   - If NO → Update it again and click "Apply"
   - If YES → Continue to Step 2

---

### **Step 2: Redeploy Code** ⭐ **IMPORTANT**

The issue is that dependencies (uvicorn) aren't installed. We need to redeploy:

1. **In VS Code:**
   - Right-click project folder
   - Select **"Deploy to Web App..."**
   - Choose **"Valix"**
   - Wait for deployment (5-10 minutes)

2. **This will:**
   - Install all dependencies from `requirements.txt` (including uvicorn)
   - Deploy all files
   - Use the new startup command

---

### **Step 3: Verify After Deployment**

1. **Check Logs:**
   - Should see: `Site's appCommandLine: uvicorn main:app --host 0.0.0.0 --port 8000`
   - Should see: `Uvicorn running on http://0.0.0.0:8000`

2. **Test URL:**
   - Visit: `https://valix-guepgdc6f4fwgtcu.westeurope-01.azurewebsites.net`

---

## 🎯 **Why This Happens**

- Azure caches the startup command
- Dependencies need to be installed during deployment
- The deployment process installs packages from `requirements.txt`

---

**Redeploy now - that's the key!** 🚀

