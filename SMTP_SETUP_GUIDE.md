# 📧 SMTP Setup Guide - Password Reset Emails

## 🎯 **Goal**
Configure SMTP so password reset emails can be sent.

## ⚠️ **IMPORTANT: For Production SaaS**

**For a production SaaS where clients sign up with organization emails, I recommend SendGrid (Option 2) instead of Gmail.**

**Why?**
- ✅ Professional emails from your domain (noreply@valixs.com)
- ✅ Better deliverability (emails reach inboxes)
- ✅ Free tier: 100 emails/day (perfect for MVP)
- ✅ Scalable as you grow
- ✅ Analytics to track delivery

**Gmail is fine for testing, but SendGrid is better for production.**

---

## 📋 **Step-by-Step Instructions**

### **Option 1: Gmail (Quick Testing Only)** ⚠️

#### **Step 1: Enable 2-Factor Authentication**
1. Go to: https://myaccount.google.com/security
2. Under "Signing in to Google", click **"2-Step Verification"**
3. Follow the prompts to enable it (if not already enabled)

#### **Step 2: Generate App Password**
1. Go to: https://myaccount.google.com/apppasswords
   - Or: Google Account → Security → 2-Step Verification → App passwords
2. Select **"Mail"** from the dropdown
3. Select **"Other (Custom name)"** from device dropdown
4. Enter name: **"Valix"**
5. Click **"Generate"**
6. **Copy the 16-character password** (you'll need this!)

#### **Step 3: Add to Azure App Service**
1. Go to **Azure Portal**: https://portal.azure.com
2. Navigate to your **App Service** (Valix)
3. Click **"Configuration"** in the left menu
4. Click **"Application settings"** tab
5. Click **"+ New application setting"** for each variable:

   **Setting 1:**
   - Name: `SMTP_HOST`
   - Value: `smtp.gmail.com`
   - Click **"OK"**

   **Setting 2:**
   - Name: `SMTP_PORT`
   - Value: `587`
   - Click **"OK"**

   **Setting 3:**
   - Name: `SMTP_USER`
   - Value: `your-email@gmail.com` (your Gmail address)
   - Click **"OK"**

   **Setting 4:**
   - Name: `SMTP_PASSWORD`
   - Value: `xxxx xxxx xxxx xxxx` (the 16-character app password from Step 2)
   - Click **"OK"**

   **Setting 5:**
   - Name: `SMTP_FROM_EMAIL`
   - Value: `noreply@valixs.com` (or your Gmail address)
   - Click **"OK"**

6. Click **"Save"** at the top
7. Click **"Continue"** when prompted
8. Wait for the app to restart (takes ~30 seconds)

#### **Step 4: Test**
1. Go to: `https://valixs.com/forgot-password`
2. Enter your email
3. Check your inbox for the password reset email
4. Click the reset link
5. Set a new password

---

### **Option 2: SendGrid (RECOMMENDED FOR PRODUCTION)** ⭐ **BEST CHOICE**

#### **Step 1: Create SendGrid Account** (2 minutes)
1. Go to: https://signup.sendgrid.com
2. Create a free account (100 emails/day free - perfect for MVP!)
3. Verify your email

#### **Step 2: Verify Your Domain** (5 minutes) ⭐ **IMPORTANT**
**Why?** This allows emails from `noreply@valixs.com` instead of SendGrid's domain.

1. Go to SendGrid Dashboard
2. Settings → Sender Authentication
3. Click **"Authenticate Your Domain"**
4. Select your DNS provider: **Namecheap**
5. Enter domain: **valixs.com**
6. SendGrid will provide DNS records to add:
   - 3-4 CNAME records
   - 1 TXT record (SPF)
7. **Add these records to Namecheap:**
   - Go to Namecheap → Domain List → valixs.com → Advanced DNS
   - Add the CNAME and TXT records provided by SendGrid
8. Click **"Verify"** in SendGrid
9. Wait 5-10 minutes for DNS propagation

**Note:** You can skip this step for now and use SendGrid's domain, but verifying your domain is recommended for professional emails.

#### **Step 3: Create API Key** (1 minute)
1. Go to SendGrid Dashboard
2. Settings → API Keys
3. Click **"Create API Key"**
4. Name: **"Valix Production"**
5. Permissions: **"Full Access"** (or just "Mail Send")
6. Click **"Create & View"**
7. **Copy the API key** (you'll only see it once! Save it securely)

#### **Step 4: Add to Azure** (2 minutes)
1. Go to Azure Portal → Your App Service → Configuration → Application settings
2. Add these 5 settings:

   **Setting 1:**
   - Name: `SMTP_HOST`
   - Value: `smtp.sendgrid.net`
   
   **Setting 2:**
   - Name: `SMTP_PORT`
   - Value: `587`
   
   **Setting 3:**
   - Name: `SMTP_USER`
   - Value: `apikey` (literally the word "apikey" - not your username!)
   
   **Setting 4:**
   - Name: `SMTP_PASSWORD`
   - Value: `SG.xxxxxxxxxxxxxxxxxxxxx` (your API key from Step 3)
   
   **Setting 5:**
   - Name: `SMTP_FROM_EMAIL`
   - Value: `noreply@valixs.com` (or use SendGrid's domain if you skipped Step 2)

3. Click **"Save"** and wait for app restart (~30 seconds)

#### **Step 5: Test** (1 minute)
1. Go to: `https://valixs.com/forgot-password`
2. Enter your email
3. Check inbox - should receive email from `noreply@valixs.com`
4. Complete password reset flow

---

### **Option 3: Mailgun (Alternative)**

1. Create account at: https://www.mailgun.com
2. Verify domain or use sandbox domain
3. Get SMTP credentials from dashboard
4. Use these settings:
   - `SMTP_HOST`: `smtp.mailgun.org`
   - `SMTP_PORT`: `587`
   - `SMTP_USER`: `your-mailgun-username`
   - `SMTP_PASSWORD`: `your-mailgun-password`
   - `SMTP_FROM_EMAIL`: `noreply@valixs.com`

---

## ✅ **Verification**

After configuring SMTP:

1. **Check Azure Logs:**
   - Azure Portal → App Service → Log stream
   - Look for: `INFO: Email sent successfully to...`
   - Should NOT see: `WARNING: SMTP not configured`

2. **Test Password Reset:**
   - Go to forgot password page
   - Enter email
   - Check inbox
   - Should receive email within 1-2 minutes

---

## 🔧 **Troubleshooting**

### **Email Not Sending?**
1. **Check Azure Logs:**
   - Look for error messages
   - Common errors:
     - "Authentication failed" → Wrong password/API key
     - "Connection refused" → Wrong SMTP_HOST or SMTP_PORT
     - "SMTP not configured" → Variables not saved/restarted

2. **Verify Settings:**
   - All 5 variables are set
   - No typos in values
   - App was restarted after saving

3. **Gmail Specific:**
   - Make sure you're using **App Password**, not regular password
   - 2FA must be enabled
   - Check spam folder

---

## 📝 **Quick Checklist**

- [ ] 2FA enabled (Gmail) or account created (SendGrid/Mailgun)
- [ ] App password/API key generated
- [ ] All 5 SMTP variables added to Azure
- [ ] App restarted
- [ ] Tested password reset
- [ ] Email received

---

**Once SMTP is configured, password reset will be fully functional!** 🎉

