# 📧 SendGrid Setup - Step-by-Step Guide

## ✅ **Step 1: Account Created** (DONE!)

Great! You've signed up for SendGrid. Now let's configure it.

---

## 📋 **Step 2: Verify Your Domain** (5 minutes) ⭐ **RECOMMENDED**

**Why?** This allows emails from `noreply@valixs.com` instead of SendGrid's domain.

### **Instructions:**

1. **Go to SendGrid Dashboard**
   - Log in at: https://app.sendgrid.com

2. **Navigate to Domain Authentication:**
   - Click **"Settings"** (gear icon, top right)
   - Click **"Sender Authentication"**
   - Click **"Authenticate Your Domain"**

3. **Select DNS Provider:**
   - Choose: **"Namecheap"** (or "Other" if not listed)
   - Click **"Next"**

4. **Enter Domain:**
   - Enter: **`valixs.com`** (without www)
   - Click **"Next"**

5. **Get DNS Records:**
   - SendGrid will show you DNS records to add
   - You'll see:
     - **3-4 CNAME records** (for DKIM, SPF, etc.)
     - **1 TXT record** (for domain verification)
   - **Copy these records** (or keep the page open)

6. **Add Records to Namecheap:**
   - Go to: https://ap.www.namecheap.com/domains/list/
   - Click on **`valixs.com`**
   - Click **"Advanced DNS"** tab
   - Click **"+ Add New Record"** for each record:
     - **Type:** CNAME (or TXT)
     - **Host:** (from SendGrid - usually something like `em1234`)
     - **Value:** (from SendGrid - usually a long string)
     - **TTL:** Automatic (or 3600)
   - **Add all 3-4 CNAME records and 1 TXT record**
   - Click **"Save All Changes"**

7. **Verify in SendGrid:**
   - Go back to SendGrid
   - Click **"Verify"** or **"I've Added These Records"**
   - Wait 5-10 minutes for DNS propagation
   - Status should change to **"Verified"** ✅

**Note:** You can skip this step for now and use SendGrid's domain, but verifying your domain is recommended for professional emails.

---

## 🔑 **Step 3: Create API Key** (2 minutes)

1. **Go to API Keys:**
   - SendGrid Dashboard
   - Click **"Settings"** (gear icon)
   - Click **"API Keys"**

2. **Create New Key:**
   - Click **"Create API Key"** (top right)
   - **Name:** `Valix Production`
   - **API Key Permissions:** Select **"Full Access"** (or just "Mail Send" if you prefer)
   - Click **"Create & View"**

3. **Copy the API Key:**
   - **IMPORTANT:** Copy the API key NOW
   - It starts with `SG.` followed by a long string
   - Example: `SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - **You'll only see it once!** Save it somewhere safe.

4. **Save the Key:**
   - Paste it in a secure place (password manager, notes, etc.)
   - You'll need it for Azure configuration

---

## ☁️ **Step 4: Add to Azure App Service** (3 minutes)

1. **Go to Azure Portal:**
   - https://portal.azure.com
   - Navigate to your **App Service** (Valix)

2. **Open Configuration:**
   - Click **"Configuration"** in the left menu
   - Click **"Application settings"** tab

3. **Add SMTP Settings:**
   Click **"+ New application setting"** for each:

   **Setting 1:**
   - **Name:** `SMTP_HOST`
   - **Value:** `smtp.sendgrid.net`
   - Click **"OK"**

   **Setting 2:**
   - **Name:** `SMTP_PORT`
   - **Value:** `587`
   - Click **"OK"**

   **Setting 3:**
   - **Name:** `SMTP_USER`
   - **Value:** `apikey` (literally the word "apikey" - not your username!)
   - Click **"OK"**

   **Setting 4:**
   - **Name:** `SMTP_PASSWORD`
   - **Value:** `SG.xxxxxxxxxxxxxxxxxxxxx` (your API key from Step 3)
   - Click **"OK"**

   **Setting 5:**
   - **Name:** `SMTP_FROM_EMAIL`
   - **Value:** `noreply@valixs.com` (or use SendGrid's domain if you skipped Step 2)
   - Click **"OK"**

4. **Save and Restart:**
   - Click **"Save"** at the top
   - Click **"Continue"** when prompted
   - Wait ~30 seconds for the app to restart

---

## ✅ **Step 5: Test Password Reset** (2 minutes)

1. **Go to Your App:**
   - Visit: `https://valixs.com/forgot-password`
   - Or: `http://localhost:8000/forgot-password` (if testing locally)

2. **Request Password Reset:**
   - Enter your email address
   - Click **"Send Reset Link"**

3. **Check Your Email:**
   - Check your inbox (and spam folder)
   - You should receive an email from `noreply@valixs.com`
   - Email should arrive within 1-2 minutes

4. **Complete Reset:**
   - Click the reset link in the email
   - Set a new password
   - Login with new password

5. **Verify in SendGrid:**
   - Go to SendGrid Dashboard
   - Click **"Activity"** in left menu
   - You should see your email in the activity feed
   - Status should be **"Delivered"** ✅

---

## 🔧 **Troubleshooting**

### **Email Not Received?**

1. **Check SendGrid Activity:**
   - Dashboard → Activity
   - Look for your email
   - Check status:
     - **"Delivered"** = Email sent successfully
     - **"Bounced"** = Email address invalid
     - **"Blocked"** = Email blocked by recipient
     - **"Dropped"** = Email filtered out

2. **Check Azure Logs:**
   - Azure Portal → App Service → Log stream
   - Look for: `INFO: Email sent successfully to...`
   - Should NOT see: `WARNING: SMTP not configured`

3. **Verify Settings:**
   - All 5 variables are set in Azure
   - `SMTP_USER` is exactly `"apikey"` (not your username)
   - `SMTP_PASSWORD` is your full API key (starts with `SG.`)
   - App was restarted after saving

4. **Check Spam Folder:**
   - Password reset emails sometimes go to spam
   - Check spam/junk folder

### **Common Issues:**

**"Authentication failed":**
- Wrong API key
- `SMTP_USER` is not exactly `"apikey"`

**"Connection refused":**
- Wrong `SMTP_HOST` or `SMTP_PORT`
- Check firewall settings

**"SMTP not configured":**
- Variables not saved
- App not restarted
- Check Azure Configuration

---

## 📝 **Quick Checklist**

- [ ] SendGrid account created ✅
- [ ] Domain verified (optional but recommended)
- [ ] API key created and saved
- [ ] All 5 SMTP variables added to Azure
- [ ] App restarted
- [ ] Password reset tested
- [ ] Email received
- [ ] Password reset completed successfully

---

## 🎉 **You're Done!**

Once you complete these steps, password reset emails will work perfectly!

**Next:** Test the full password reset flow and verify emails are being delivered.

---

**Let me know which step you're on and I'll help you through it!** 🚀

