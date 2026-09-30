# 🌐 Custom Domain Setup Guide (valixs.com)

## 📋 **Prerequisites**

- ✅ Domain purchased: `valixs.com`
- ✅ Azure App Service running
- ✅ App is working on Azure URL

---

## 🔧 **Step 1: Add Domain in Azure** (5 minutes)

### **In Azure Portal:**

1. **Go to App Service "Valix"**
2. **Click "Custom domains"** (left menu, under "Settings")
3. **Click "+ Add custom domain"** (top button)
4. **Enter domain name:** `valixs.com`
5. **Click "Validate"**
6. **Azure will show you DNS records to add**

---

## 📝 **Step 2: Get DNS Records from Azure**

After clicking "Validate", Azure will show you:

### **Option A: A Record + TXT Record**
```
Type: A
Name: @
Value: [IP Address from Azure]

Type: TXT
Name: @
Value: [Verification string from Azure]
```

### **Option B: CNAME Record**
```
Type: CNAME
Name: @
Value: valix-guepgdc6f4fwgtcu.westeurope-01.azurewebsites.net
```

**Azure will tell you exactly which records to add!**

---

## 🔧 **Step 3: Update DNS in Namecheap** (10 minutes)

### **In Namecheap:**

1. **Log in to Namecheap**
   - Go to: https://www.namecheap.com
   - Sign in

2. **Go to Domain List**
   - Click "Domain List" (top menu)
   - Find `valixs.com`
   - Click "Manage"

3. **Go to Advanced DNS**
   - Click "Advanced DNS" tab
   - Scroll to "Host Records" section

4. **Add DNS Records**
   - Click "Add New Record"
   - Add each record Azure provided:
     - **A Record** (if Azure provided one)
     - **CNAME Record** (if Azure provided one)
     - **TXT Record** (for verification)
   - Click "Save All Changes"

---

## ⏳ **Step 4: Wait for DNS Propagation** (5-60 minutes)

1. **DNS changes take time to propagate**
2. **Check status in Azure:**
   - Go to Custom domains
   - Status should change from "Pending" to "Verified"

3. **Azure will automatically:**
   - Provision SSL certificate
   - Enable HTTPS for your domain

---

## ✅ **Step 5: Verify SSL Certificate** (Automatic)

1. **Azure automatically provisions SSL**
2. **Check in Azure Portal:**
   - Custom domains → SSL certificate status
   - Should show "Active" after DNS is verified

3. **Test HTTPS:**
   - Visit: `https://valixs.com`
   - Should see your app with SSL lock icon

---

## 🎯 **Quick Summary**

1. Azure Portal → Custom domains → Add `valixs.com`
2. Copy DNS records from Azure
3. Namecheap → Advanced DNS → Add records
4. Wait for DNS propagation
5. Azure automatically sets up SSL

---

**Let's start with testing first, then configure the domain!** 🚀

