# 🔧 Update SendGrid DNS Records - NEW Hostnames!

## 🚨 **Important: SendGrid Changed the Hostnames!**

SendGrid has generated **NEW hostnames** that are different from before:

**NEW Records (from SendGrid):**
1. `url7756.valixs.com` → `sendgrid.net` (was `url4560`)
2. `58428036.valixs.com` → `sendgrid.net` (same)
3. `em3100.valixs.com` → `u58428036.wl037.sendgrid.net` (was `em7911`)

**You need to update Namecheap with these NEW values!**

---

## ✅ **Step-by-Step: Update Records in Namecheap**

### **Step 1: Go to Namecheap DNS**

1. **Login to Namecheap**
2. **Go to:** Domain List → `valixs.com` → Manage → Advanced DNS

---

### **Step 2: Delete OLD Records (if they exist)**

**Delete these OLD records if they exist:**
- ❌ `url4560` (old, delete it)
- ❌ `em7911` (old, delete it)
- ✅ Keep: `58428036` (this one is the same)

**How to delete:**
- Click the **trash icon** 🗑️ next to each old record
- Confirm deletion

---

### **Step 3: Add/Update NEW Records**

**Add these 3 CNAME records:**

#### **Record 1: url7756**
1. Click **"+ Add New Record"**
2. Select **"CNAME Record"**
3. **Host:** Enter `url7756` (just the subdomain, NOT `url7756.valixs.com`)
4. **Value:** Enter `sendgrid.net` (or `sendgrid.net.` - both work)
5. **TTL:** Automatic
6. Click **"Save"** (green checkmark)

#### **Record 2: 58428036** (if not already there)
1. Click **"+ Add New Record"**
2. Select **"CNAME Record"**
3. **Host:** Enter `58428036`
4. **Value:** Enter `sendgrid.net` (or `sendgrid.net.`)
5. **TTL:** Automatic
6. Click **"Save"**

#### **Record 3: em3100**
1. Click **"+ Add New Record"**
2. Select **"CNAME Record"**
3. **Host:** Enter `em3100` (just the subdomain)
4. **Value:** Enter `u58428036.wl037.sendgrid.net` (or `u58428036.wl037.sendgrid.net.`)
5. **TTL:** Automatic
6. Click **"Save"**

---

### **Step 4: Add DKIM Records (if shown in SendGrid)**

**If SendGrid shows DKIM records, add them too:**

#### **Record 4: s1._domainkey**
1. Click **"+ Add New Record"**
2. Select **"CNAME Record"**
3. **Host:** Enter `s1._domainkey`
4. **Value:** Enter `s1.domainkey.u58428036.wl037.sendgrid.net`
5. **TTL:** Automatic
6. Click **"Save"**

#### **Record 5: s2._domainkey**
1. Click **"+ Add New Record"**
2. Select **"CNAME Record"**
3. **Host:** Enter `s2._domainkey`
4. **Value:** Enter `s2.domainkey.u58428036.wl037.sendgrid.net`
5. **TTL:** Automatic
6. Click **"Save"**

---

### **Step 5: Add DMARC Record (if shown)**

#### **Record 6: _dmarc**
1. Click **"+ Add New Record"**
2. Select **"TXT Record"**
3. **Host:** Enter `_dmarc`
4. **Value:** Enter `v=DMARC1; p=none;`
5. **TTL:** Automatic
6. Click **"Save"**

---

### **Step 6: SAVE ALL CHANGES** ⚠️ **CRITICAL!**

1. **Scroll to the bottom** of the DNS page
2. Click the big green button: **"SAVE ALL CHANGES"**
3. **Wait for confirmation** (green checkmark or success message)
4. **This is critical - records won't work until you save!**

---

## ⏱️ **Step 7: Wait for DNS Propagation**

**After saving:**
- ⏱️ Wait **10-15 minutes** for DNS to propagate
- ⏱️ DNS propagation can take up to 30 minutes

---

## 🔍 **Step 8: Verify in SendGrid**

**After 10-15 minutes:**

1. **Go back to SendGrid** → Sender Authentication
2. **Click "Verify"** button (or refresh the page)
3. **Check if errors are gone:**
   - ✅ Green checkmarks = Success!
   - ⏱️ Yellow warnings = Still propagating, wait more

---

## 📋 **Quick Checklist**

**Before saving, verify you have:**

- [ ] `url7756` → CNAME → `sendgrid.net`
- [ ] `58428036` → CNAME → `sendgrid.net`
- [ ] `em3100` → CNAME → `u58428036.wl037.sendgrid.net`
- [ ] `s1._domainkey` → CNAME → `s1.domainkey.u58428036.wl037.sendgrid.net` (if shown)
- [ ] `s2._domainkey` → CNAME → `s2.domainkey.u58428036.wl037.sendgrid.net` (if shown)
- [ ] `_dmarc` → TXT → `v=DMARC1; p=none;` (if shown)
- [ ] **Clicked "SAVE ALL CHANGES"** ✅

---

## 🎯 **Important Notes**

### **Host Field Format:**
- ✅ **Correct:** `url7756` (just the subdomain)
- ❌ **Wrong:** `url7756.valixs.com` (Namecheap adds `.valixs.com` automatically)

### **Value Field Format:**
- ✅ **Correct:** `sendgrid.net` or `sendgrid.net.` (both work)
- ❌ **Wrong:** `sendgrid.net.valixs.com` (shouldn't have your domain)

### **Saving:**
- ⚠️ **MUST click "SAVE ALL CHANGES"** or records won't work!

---

## 🚀 **After DNS Verifies**

**Once SendGrid shows green checkmarks:**

1. **Domain is verified!** ✅
2. **You can now:**
   - Create API key
   - Add to Azure
   - Test password reset emails

---

**Go to Namecheap now and update the records with the NEW hostnames!** 🔧

