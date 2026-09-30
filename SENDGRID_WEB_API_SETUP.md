# 🚀 SendGrid Web API Setup Guide

## ✅ **Code Updated!**

I've updated your code to use SendGrid Web API. Here's what changed:

### **Changes Made:**
1. ✅ Added `sendgrid>=6.10.0` to `requirements.txt`
2. ✅ Updated `app/email_service.py` to use SendGrid API
3. ✅ Updated `app/config.py` to use `SENDGRID_API_KEY` instead of SMTP settings

---

## 📋 **Next Steps**

### **Step 1: Install SendGrid Library**

**On your local machine:**
```bash
pip install sendgrid>=6.10.0
```

**Or update requirements:**
```bash
pip install -r requirements.txt
```

---

### **Step 2: Create SendGrid API Key**

1. **In SendGrid:**
   - Go to: **Settings** → **API Keys**
   - Click: **"Create API Key"** (top right)

2. **Configure API Key:**
   - **Name:** `Valix Production`
   - **Permissions:** Select **"Full Access"** (or "Restricted Access" with Mail Send permissions)
   - Click **"Create & View"**

3. **Copy the API Key:**
   - ⚠️ **IMPORTANT:** Copy the key NOW - you won't be able to see it again!
   - It will look like: `SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - Save it somewhere safe!

---

### **Step 3: Add to Azure Configuration**

1. **Go to Azure Portal:**
   - Navigate to: **App Services** → Your app → **Configuration**

2. **Add Environment Variables:**

   **Setting 1:**
   - **Name:** `SENDGRID_API_KEY`
   - **Value:** `SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` (your API key)
   - Click **"OK"**

   **Setting 2:**
   - **Name:** `SENDGRID_FROM_EMAIL`
   - **Value:** `noreply@valixs.com`
   - Click **"OK"**

   **Setting 3:**
   - **Name:** `SENDGRID_FROM_NAME`
   - **Value:** `Valix`
   - Click **"OK"**

3. **Remove Old SMTP Settings (if they exist):**
   - Delete: `SMTP_HOST`
   - Delete: `SMTP_PORT`
   - Delete: `SMTP_USER`
   - Delete: `SMTP_PASSWORD`
   - Delete: `SMTP_FROM_EMAIL`

4. **Save Configuration:**
   - Click **"Save"** at the top
   - Wait for confirmation
   - Azure will restart your app automatically

---

### **Step 4: Update Local .env File (for development)**

**Add to your `.env` file:**
```env
SENDGRID_API_KEY=SG.your_api_key_here
SENDGRID_FROM_EMAIL=noreply@valixs.com
SENDGRID_FROM_NAME=Valix
```

**Remove old SMTP settings:**
```env
# Remove these:
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SMTP_USER=
# SMTP_PASSWORD=
# SMTP_FROM_EMAIL=
```

---

### **Step 5: Test Password Reset**

1. **Restart your local server** (if running):
   ```bash
   # Stop current server (Ctrl+C)
   # Then restart:
   uvicorn main:app --reload
   ```

2. **Go to your site:** `https://valixs.com` (or `http://localhost:8000` locally)

3. **Test password reset:**
   - Click "Login" → "Forgot password?"
   - Enter your email address
   - Click "Send Reset Link"

4. **Check your email:**
   - Check inbox (and spam folder)
   - You should receive a password reset email
   - Click the reset link
   - Set a new password

---

## ✅ **What You Get with Web API**

### **Benefits:**
- ✅ **Better Analytics:** Track opens, clicks, bounces in SendGrid dashboard
- ✅ **Better Error Handling:** Detailed error responses
- ✅ **Professional Setup:** Industry standard for SaaS
- ✅ **Scalability:** Handles high volume better
- ✅ **Webhooks:** Real-time event notifications (optional)
- ✅ **Templates:** Dynamic email templates (optional, for future)

---

## 🔍 **Verify It's Working**

### **In SendGrid Dashboard:**
1. Go to: **Activity** → **Email Activity**
2. You should see sent emails listed
3. Click on an email to see:
   - Delivery status
   - Opens (if recipient opens)
   - Clicks (if recipient clicks links)
   - Bounces/Spam reports

### **In Application Logs:**
- Check Azure logs or local terminal
- Should see: `Email sent successfully to {email} (status: 202)`

---

## 🐛 **Troubleshooting**

### **If emails don't send:**

1. **Check API Key:**
   - Is it correct in Azure?
   - Does it have Mail Send permissions?

2. **Check Logs:**
   - Look for error messages
   - Check SendGrid Activity dashboard

3. **Check Domain:**
   - Is domain verified in SendGrid?
   - Check Sender Authentication page

4. **Test API Key:**
   - Try sending a test email from SendGrid dashboard
   - Settings → API Keys → Test API Key

---

## 📋 **Quick Checklist**

- [ ] Installed `sendgrid` library locally
- [ ] Created SendGrid API key
- [ ] Added `SENDGRID_API_KEY` to Azure
- [ ] Added `SENDGRID_FROM_EMAIL` to Azure
- [ ] Added `SENDGRID_FROM_NAME` to Azure
- [ ] Removed old SMTP settings from Azure
- [ ] Updated local `.env` file
- [ ] Restarted local server (if testing locally)
- [ ] Tested password reset email
- [ ] Verified email received
- [ ] Checked SendGrid Activity dashboard

---

## 🚀 **You're All Set!**

**Your app now uses SendGrid Web API for production-grade email sending!**

**Next:** Test the password reset and verify emails are being sent! 🎉

