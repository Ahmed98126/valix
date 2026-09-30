# 🔧 Troubleshooting Azure Application Error

## 🚨 **Application Error - Let's Fix It!**

The error means the app isn't starting correctly. Let's diagnose and fix it.

---

## 📋 **Step 1: Check Logs** (Find the Error)

### **Option A: Azure Portal** ⭐ **EASIEST**

1. **Go to Azure Portal**
   - Open your App Service "Valix"
   - In left menu, click **"Log stream"**
   - You'll see real-time logs
   - Look for error messages (red text)

### **Option B: VS Code**

1. **In VS Code Azure sidebar**
   - Right-click "Valix"
   - Select **"Start Streaming Logs"**
   - Or select **"View Logs"**

### **Option C: Advanced Tools (Kudu)**

1. **In Azure Portal**
   - App Service "Valix" → **"Advanced Tools"**
   - Click **"Go"**
   - Click **"Debug console"** → **"CMD"**
   - Navigate to `LogFiles` folder
   - Check error logs

---

## 🔍 **Common Issues & Fixes**

### **Issue 1: Startup Command Not Set**

**Symptom:** App doesn't start, no logs

**Fix:**
1. Go to Configuration → General settings
2. Set Startup Command:
   ```
   gunicorn main:app --bind 0.0.0.0:8000 --workers 2 --timeout 120
   ```
3. Save

---

### **Issue 2: Missing Dependencies**

**Symptom:** Import errors in logs

**Fix:**
1. Check `requirements.txt` includes `gunicorn`
2. Redeploy (dependencies should install automatically)

---

### **Issue 3: Database Connection Error**

**Symptom:** Database connection failed

**Fix:**
1. Verify `DATABASE_URL` is correct in environment variables
2. Check Supabase password is correct
3. Test connection

---

### **Issue 4: Port Binding Issue**

**Symptom:** Port already in use

**Fix:**
- Azure uses port 8000 automatically
- Make sure startup command uses `0.0.0.0:8000`

---

### **Issue 5: Missing Environment Variables**

**Symptom:** Configuration errors

**Fix:**
- Verify all 6 environment variables are set
- Check they're saved (not just added)

---

## 🎯 **Quick Fix Steps**

1. **Check Logs First** (to see actual error)
2. **Verify Startup Command** is set
3. **Verify Environment Variables** are saved
4. **Check Requirements** include gunicorn
5. **Redeploy** if needed

---

**Let's start by checking the logs to see the actual error!** 🔍

