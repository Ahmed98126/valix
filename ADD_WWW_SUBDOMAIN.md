# 🌐 Add www.valixs.com Support

## 🚨 **Current Status**

- ✅ `valixs.com` - **Works!**
- ❌ `www.valixs.com` - **Doesn't work yet**

---

## ✅ **Solution: Add www Subdomain**

You have two options:

### **Option 1: Add www as Separate Domain** (Recommended)
- Both `valixs.com` and `www.valixs.com` will work
- Each needs its own SSL certificate
- Users can access either URL

### **Option 2: Redirect www to Non-www** (Alternative)
- `www.valixs.com` automatically redirects to `valixs.com`
- Only one SSL certificate needed
- Simpler setup

---

## 🔧 **Option 1: Add www Subdomain** (Recommended)

### **Step 1: Add www in Azure**

1. **Go to Azure Portal** → App Service "Valix"
2. **Click "Custom domains"** (left menu)
3. **Click "+ Add custom domain"**
4. **Enter:** `www.valixs.com`
5. **Click "Validate"**
6. **Azure will show DNS records** (CNAME record)

### **Step 2: Add CNAME Record in Namecheap**

Azure will show you a CNAME record like:
```
Type: CNAME
Name: www
Value: valix-guepgdc6f4fwgtcu.westeurope-01.azurewebsites.net
```

1. **Go to Namecheap** → Domain List → `valixs.com` → Manage
2. **Click "Advanced DNS"** tab
3. **Add New Record:**
   - Type: `CNAME Record`
   - Host: `www`
   - Value: `valix-guepgdc6f4fwgtcu.westeurope-01.azurewebsites.net`
   - TTL: `Automatic`
4. **Save All Changes**

### **Step 3: Add Domain in Azure**

1. **Wait 2-3 minutes** for DNS to propagate
2. **Go back to Azure** → Custom domains
3. **Click "Add"** next to `www.valixs.com`
4. **Add SSL certificate** (same process as before)

---

## 🔧 **Option 2: Redirect www to Non-www** (Simpler)

This requires code changes to add a redirect. We can do this if you prefer.

---

## 🎯 **Recommendation**

**I recommend Option 1** - Add www as a separate domain. This way:
- ✅ Both URLs work
- ✅ Users can type either
- ✅ More professional
- ✅ Better for SEO

---

## 📋 **After Adding www**

Both URLs will work:
- `https://valixs.com` ✅
- `https://www.valixs.com` ✅

---

**Would you like to add www support now?** 🚀

