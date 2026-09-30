# 📧 SendGrid Domain Setup - Step-by-Step

## 🎯 **Important: Use Root Domain (Not www)**

For email authentication, use **`valixs.com`** (without www), not `www.valixs.com`.

**Why?**
- Email addresses use: `noreply@valixs.com` (not `noreply@www.valixs.com`)
- Root domain authentication covers both `valixs.com` and `www.valixs.com`
- This is the standard practice

---

## 📋 **Step-by-Step Configuration**

### **Step 1: Domain Field**

1. **Change the domain in the input field:**
   - Remove `www.` from the field
   - Enter: **`valixs.com`** (just the root domain)
   - Should show: `https://valixs.com`

**Why?** Email authentication works at the root domain level.

---

### **Step 2: Link Branding**

**Question:** "Would you like to brand the link for this domain?"

**Recommendation: Select "Yes"** ✅

**Why?**
- ✅ Links in emails will use `valixs.com` instead of `sendgrid.net`
- ✅ More professional appearance
- ✅ Better trust from recipients
- ✅ All tracking links use your domain

**What it does:**
- Password reset links: `https://valixs.com/reset-password?token=...`
- Instead of: `https://sendgrid.net/...`

**Select:** **"Yes"** (check the "Yes" radio button)

---

### **Step 3: Advanced Settings**

**Keep these settings:**

1. **"Use automated security"** ✅ **KEEP CHECKED**
   - ✅ Automatically rotates DKIM keys
   - ✅ Better security
   - ✅ Recommended by SendGrid

2. **"Use custom return path"** ❌ **LEAVE UNCHECKED**
   - Only needed for advanced setups
   - Not required for basic email sending

3. **"Use a custom DKIM selector"** ❌ **LEAVE UNCHECKED**
   - Only needed if you have conflicts
   - Not needed for your setup

**Action:** Keep "Use automated security" checked, leave others unchecked.

---

### **Step 4: Continue/Next**

1. Click **"Next"** or **"Continue"** button
2. SendGrid will show you DNS records to add

---

## 🔧 **What Happens Next**

After you click "Next", SendGrid will:

1. **Generate DNS Records:**
   - 3-4 CNAME records (for DKIM, SPF, etc.)
   - 1 TXT record (for domain verification)
   - These will be specific to your SendGrid account

2. **Show You the Records:**
   - Copy these records
   - You'll add them to Namecheap DNS

3. **Add to Namecheap:**
   - Go to Namecheap → Domain List → valixs.com → Advanced DNS
   - Add each CNAME and TXT record
   - Save changes

4. **Verify:**
   - Go back to SendGrid
   - Click "Verify"
   - Wait 5-10 minutes for DNS propagation
   - Status should show "Verified" ✅

---

## 📝 **Quick Checklist**

- [ ] Domain field shows: `valixs.com` (not www.valixs.com)
- [ ] Link branding: **"Yes"** selected
- [ ] Advanced settings: "Use automated security" checked
- [ ] Click "Next" to continue
- [ ] Copy DNS records from SendGrid
- [ ] Add DNS records to Namecheap
- [ ] Verify domain in SendGrid

---

## 💡 **About Your 2 Domains**

You mentioned you have 2 domains:
- `valixs.com` (root domain)
- `www.valixs.com` (www subdomain)

**For Email Authentication:**
- ✅ Use **`valixs.com`** (root domain)
- ✅ This covers both domains automatically
- ✅ Email addresses use root domain: `noreply@valixs.com`

**For Website:**
- ✅ Both `valixs.com` and `www.valixs.com` work (already configured)
- ✅ Email authentication is separate from website DNS

**You only need to authenticate ONE domain (the root domain) for email!**

---

## 🚀 **Next Steps**

1. **Update the domain field** to `valixs.com` (remove www)
2. **Select "Yes"** for link branding
3. **Click "Next"** to continue
4. **Copy the DNS records** SendGrid provides
5. **Add them to Namecheap**
6. **Verify in SendGrid**

**Let me know when you've clicked "Next" and I'll help you with the DNS records!** 🎯

