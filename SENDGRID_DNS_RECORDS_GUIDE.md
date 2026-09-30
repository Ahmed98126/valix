# 📧 SendGrid DNS Records Setup Guide

## 🎯 **Current Step: Install DNS Records**

You're on the "Install DNS Records" page. Here's what to do:

---

## ✅ **Step 1: Select "Setup now"**

1. **Click on "Setup now"** (the first option with the key icon)
2. This will show you the DNS records to add
3. Click **"Next"** or **"Continue"**

---

## 📋 **Step 2: Copy DNS Records**

After selecting "Setup now", SendGrid will show you DNS records like this:

### **Example Records (yours will be different):**

**CNAME Records (3-4 records):**
```
Type: CNAME
Host: em1234
Value: u1234567.wl123.sendgrid.net
TTL: Automatic (or 3600)
```

**TXT Record (1 record):**
```
Type: TXT
Host: @ (or valixs.com)
Value: v=spf1 include:sendgrid.net ~all
TTL: Automatic (or 3600)
```

**Important:** Your actual records will be different - copy the exact values SendGrid shows you!

---

## 🔧 **Step 3: Add Records to Namecheap**

### **Instructions:**

1. **Open Namecheap in a new tab:**
   - Go to: https://ap.www.namecheap.com/domains/list/
   - Login if needed

2. **Navigate to DNS Settings:**
   - Find **`valixs.com`** in your domain list
   - Click on it
   - Click **"Advanced DNS"** tab

3. **Add Each Record:**
   For each CNAME and TXT record from SendGrid:

   **For CNAME Records:**
   - Click **"+ Add New Record"**
   - Select **"CNAME Record"**
   - **Host:** Enter the host value from SendGrid (e.g., `em1234`)
   - **Value:** Enter the value from SendGrid (e.g., `u1234567.wl123.sendgrid.net`)
   - **TTL:** Select "Automatic" (or enter `3600`)
   - Click **"Save"** (green checkmark)

   **For TXT Record:**
   - Click **"+ Add New Record"**
   - Select **"TXT Record"**
   - **Host:** Enter `@` (or leave blank for root domain)
   - **Value:** Enter the full TXT value from SendGrid
   - **TTL:** Select "Automatic" (or enter `3600`)
   - Click **"Save"** (green checkmark)

4. **Add All Records:**
   - Add all 3-4 CNAME records
   - Add the 1 TXT record
   - Make sure all are saved

5. **Verify in Namecheap:**
   - You should see all the new records listed
   - Double-check the values match SendGrid exactly

---

## ⏱️ **Step 4: Wait for DNS Propagation**

1. **Go back to SendGrid**
2. **Click "Verify"** or **"I've Added These Records"**
3. **Wait 5-10 minutes** for DNS propagation
   - DNS changes can take a few minutes to propagate
   - SendGrid will check automatically

4. **Check Status:**
   - Status should change from "Pending" to **"Verified"** ✅
   - If it says "Not Verified", wait a few more minutes and click "Verify" again

---

## 🔍 **Troubleshooting**

### **DNS Not Verifying?**

1. **Double-check records:**
   - Values must match SendGrid exactly
   - No extra spaces or typos
   - Host values are correct

2. **Wait longer:**
   - DNS can take up to 24 hours (usually 5-10 minutes)
   - Try clicking "Verify" again after 10 minutes

3. **Check Namecheap:**
   - Make sure all records are saved
   - Records should appear in the DNS list

4. **Common mistakes:**
   - Wrong host value (should match SendGrid exactly)
   - Missing `@` or wrong host for TXT record
   - Typos in values

---

## 📝 **Quick Checklist**

- [ ] Selected "Setup now" in SendGrid
- [ ] Copied all DNS records from SendGrid
- [ ] Opened Namecheap Advanced DNS
- [ ] Added all CNAME records (3-4 records)
- [ ] Added TXT record (1 record)
- [ ] Verified all records are saved
- [ ] Clicked "Verify" in SendGrid
- [ ] Waited 5-10 minutes
- [ ] Status shows "Verified" ✅

---

## 🎯 **What to Do Right Now**

1. **Click "Setup now"** (first option)
2. **Click "Next"** or **"Continue"**
3. **Copy all the DNS records** SendGrid shows you
4. **Tell me when you have the records** and I'll help you add them to Namecheap!

---

**Once DNS records are added and verified, your emails will be sent from `noreply@valixs.com`!** 🎉

