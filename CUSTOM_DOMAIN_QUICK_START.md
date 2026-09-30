# 🌐 Custom Domain Setup - Quick Start

## ✅ **App is Working!**

Great! Your app is fully functional. Now let's add your custom domain `valixs.com`.

---

## 🚀 **Step-by-Step: Add Custom Domain**

### **Step 1: Add Domain in Azure** (5 minutes)

1. **Go to Azure Portal**
   - Visit: https://portal.azure.com
   - Navigate to App Service "Valix"

2. **Open Custom Domains**
   - Left menu → **"Custom domains"** (under Settings)
   - Click **"+ Add custom domain"** (top button)

3. **Enter Domain**
   - Domain name: `valixs.com`
   - Click **"Validate"**

4. **Azure will show DNS records**
   - You'll see what DNS records to add
   - **Copy these records** (you'll need them for Namecheap)

---

### **Step 2: Update DNS in Namecheap** (10 minutes)

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
   - Azure will tell you which records to add
   - Usually one of these:
     - **A Record** + **TXT Record** (for verification)
     - **CNAME Record** (alternative)
   - Click "Add New Record" for each
   - Click "Save All Changes"

---

### **Step 3: Wait for DNS Propagation** (5-60 minutes)

1. **DNS changes take time**
   - Can take 5-60 minutes
   - Usually 15-30 minutes

2. **Check Status in Azure**
   - Go back to Azure → Custom domains
   - Status will change from "Pending" to "Verified"
   - Azure will automatically provision SSL certificate

3. **Test Your Domain**
   - Visit: `https://valixs.com`
   - Should see your app!

---

## ✅ **What Happens Automatically**

- ✅ Azure provisions SSL certificate (free)
- ✅ HTTPS is enabled automatically
- ✅ Your app is accessible at `https://valixs.com`

---

## 🎯 **Quick Checklist**

- [ ] Azure Portal → Custom domains → Add `valixs.com`
- [ ] Copy DNS records from Azure
- [ ] Namecheap → Advanced DNS → Add records
- [ ] Wait for DNS propagation (15-30 min)
- [ ] Test: `https://valixs.com`

---

**Let's set up the custom domain now!** 🚀

