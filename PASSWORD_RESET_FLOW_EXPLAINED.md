# 🔐 Password Reset Flow - Complete Explanation

## ✅ **Yes! It Will Send Email to ANY Email Address (Gmail, Yahoo, etc.)**

**When a user requests password reset:**
1. User enters their email address (Gmail, Yahoo, Outlook, etc.)
2. System sends email to **that exact email address**
3. Email comes from: `noreply@valixs.com` (your domain)
4. User clicks link in email → resets password

**It works with ANY email provider!** ✅

---

## 🔄 **Complete Password Reset Flow**

### **Step 1: User Requests Reset**

**User goes to:** `https://valixs.com/forgot-password`

**User enters:** Their email address (e.g., `user@gmail.com`)

**What happens:**
1. System checks if email exists in database
2. If found, creates a **secure reset token**
3. Saves token to database with expiration (24 hours)
4. Sends email to that address
5. Shows success message (even if email doesn't exist - security best practice)

---

### **Step 2: Email Sent**

**Email sent to:** The email address the user entered

**Email contains:**
- Reset link: `https://valixs.com/reset-password?token=ABC123...`
- Expiration notice: "Link expires in 24 hours"
- Security notice: "If you didn't request this, ignore this email"

**Email sender:** `Valix <noreply@valixs.com>`

---

### **Step 3: User Clicks Link**

**User clicks link in email** → Goes to: `https://valixs.com/reset-password?token=ABC123...`

**What happens:**
1. System checks if token exists in database
2. Checks if token is valid (not used, not expired)
3. If valid → Shows password reset form
4. If invalid → Shows error, asks to request new link

---

### **Step 4: User Sets New Password**

**User enters:**
- New password
- Confirm password

**What happens:**
1. System validates passwords match
2. Validates password length (minimum 8 characters)
3. Updates user's password in database
4. **Marks token as used** (can't be used again)
5. Redirects to login page

---

## 📊 **Password Reset Token Management (Per User)**

### **Database Table: `password_reset_tokens`**

**Each token record stores:**
- `id` - Unique token ID
- `user_id` - Which user this token belongs to
- `token` - Secure random token (32 characters)
- `expires_at` - When token expires (24 hours from creation)
- `used` - Whether token has been used (False = not used, True = used)
- `created_at` - When token was created

---

### **Token Lifecycle Per User**

#### **1. Token Creation**
```
User requests reset → Token created → Saved to database
- user_id: 123
- token: "ABC123xyz..."
- expires_at: 2025-12-29 22:37:42 (24 hours from now)
- used: False
- created_at: 2025-12-28 22:37:42
```

#### **2. Token Validation**
```
User clicks link → System checks:
- Does token exist? ✅
- Is token expired? ❌ (not expired)
- Is token used? ❌ (not used)
→ Token is VALID ✅
```

#### **3. Token Used**
```
User resets password → Token marked as used
- used: True (changed from False)
→ Token can NEVER be used again
```

#### **4. Token Expired**
```
After 24 hours → Token expires
- expires_at: 2025-12-29 22:37:42 (in the past)
→ Token is INVALID ❌
```

---

## 🔍 **Transaction History / Log Management**

### **What Gets Logged:**

#### **1. Token Creation (Database)**
- **When:** User requests password reset
- **Stored in:** `password_reset_tokens` table
- **Fields:** `user_id`, `token`, `expires_at`, `created_at`, `used`

#### **2. Email Sent (Application Logs)**
- **When:** Email is sent
- **Logged:** `INFO - Email sent successfully to {email} (status: 202)`
- **Location:** Application logs (Azure logs, local terminal)

#### **3. Token Used (Database)**
- **When:** User successfully resets password
- **Stored in:** `password_reset_tokens` table
- **Field updated:** `used = True`

#### **4. Password Changed (Database)**
- **When:** User sets new password
- **Stored in:** `users` table
- **Field updated:** `password_hash` (encrypted)

---

## 📋 **Per-User Token History**

### **Multiple Tokens Per User**

**A user can have multiple tokens:**
- Token 1: Created Dec 28, 22:00 - Used ✅
- Token 2: Created Dec 28, 22:30 - Expired ❌
- Token 3: Created Dec 29, 10:00 - Active ✅

**Only ONE token can be active at a time:**
- Old tokens expire after 24 hours
- Used tokens are marked as used
- New tokens can be created anytime

---

## 🔒 **Security Features**

### **1. Secure Token Generation**
- Uses `secrets.token_urlsafe(32)` - cryptographically secure
- 32 characters long
- Unique per request

### **2. Token Expiration**
- Tokens expire after 24 hours
- Expired tokens cannot be used

### **3. One-Time Use**
- Tokens marked as `used = True` after password reset
- Used tokens cannot be reused

### **4. Password Validation**
- Minimum 8 characters
- Must match confirmation
- Stored as encrypted hash (never plain text)

### **5. Security Best Practice**
- Doesn't reveal if email exists (always shows success message)
- Prevents email enumeration attacks

---

## 📊 **How to View Token History**

### **In Database (Supabase):**

**Query all tokens for a user:**
```sql
SELECT * FROM password_reset_tokens 
WHERE user_id = 123 
ORDER BY created_at DESC;
```

**Query active tokens:**
```sql
SELECT * FROM password_reset_tokens 
WHERE user_id = 123 
  AND used = false 
  AND expires_at > NOW();
```

**Query used tokens:**
```sql
SELECT * FROM password_reset_tokens 
WHERE user_id = 123 
  AND used = true 
ORDER BY created_at DESC;
```

---

## 🎯 **Summary**

### **Email Sending:**
- ✅ Sends to ANY email address (Gmail, Yahoo, etc.)
- ✅ Email comes from `noreply@valixs.com`
- ✅ Professional HTML email template

### **Token Management:**
- ✅ Each token stored in database
- ✅ Tracks: user_id, expiration, usage status
- ✅ One-time use tokens
- ✅ 24-hour expiration

### **Transaction History:**
- ✅ All tokens logged in database
- ✅ Email sends logged in application logs
- ✅ Password changes logged in database
- ✅ Can query token history per user

### **Security:**
- ✅ Secure token generation
- ✅ Token expiration
- ✅ One-time use
- ✅ Password encryption
- ✅ Doesn't reveal if email exists

---

## 🚀 **Ready to Test!**

**To test the full flow:**

1. **Go to:** `https://valixs.com/forgot-password`
2. **Enter:** Your email address (Gmail, etc.)
3. **Check inbox:** You'll receive password reset email
4. **Click link:** Sets new password
5. **Login:** With new password

**Everything is logged and tracked in the database!** ✅

