# 🔍 Check Azure Logs for Error Details

## 🚨 **We Need the Actual Error Message**

The "Internal Server Error" is generic. We need to see the **actual error** in the logs.

---

## 📋 **Step 1: Get the Error Logs**

### **In Azure Portal:**

1. **Go to App Service "Valix"**
2. **Click "Log stream"** (left menu)
3. **Keep it open**
4. **Visit the URL again:** `https://valix-guepgdc6f4fwgtcu.westeurope-01.azurewebsites.net`
5. **Watch the logs** - you should see an error appear
6. **Copy the FULL error message** (including the traceback)

---

## 🎯 **What to Look For**

The error will likely be one of these:

### **1. Database Connection Error**
```
psycopg2.OperationalError: could not connect to server
```
or
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError)
```

**Fix:** Check `DATABASE_URL` in Configuration → Application settings

---

### **2. Missing Environment Variable**
```
KeyError: 'SECRET_KEY'
```
or
```
os.getenv returned None
```

**Fix:** Add missing environment variables

---

### **3. Import Error**
```
ModuleNotFoundError: No module named 'app'
```
or
```
ImportError: cannot import name 'X'
```

**Fix:** Dependencies not installed correctly

---

### **4. Table Not Found**
```
relation "users" does not exist
```
or
```
no such table: users
```

**Fix:** Database tables not created - need to run `init_db()`

---

## 🚀 **Quick Action**

**Please:**
1. Open Azure Portal → Log stream
2. Visit the URL
3. Copy the error message you see
4. Share it here

**This will tell us exactly what's wrong!** 🔍

