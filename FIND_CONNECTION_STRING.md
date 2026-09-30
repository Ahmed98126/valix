# How to Find Your Database Connection String

## 🎯 What You're Looking For

You need a string that looks like this:
```
postgresql://postgres.xkbmbqejeoxfatcliftv:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
```

**NOT** a URL like `https://xkbmbqejeoxfatcliftv.supabase.co`

---

## 📍 Step-by-Step Instructions

### Step 1: Go to Your Project
1. Visit: https://supabase.com/dashboard/project/xkbmbqejeoxfatcliftv
2. You should see your project dashboard

### Step 2: Open Settings
1. Look at the **left sidebar**
2. Find and click **"Settings"** (it has a gear icon ⚙️)
3. A submenu will appear

### Step 3: Go to Database Settings
1. In the Settings submenu, click **"Database"**
2. You'll see database configuration options

### Step 4: Find Connection String Section
1. Scroll down the Database settings page
2. Look for a section titled **"Connection string"** or **"Connection pooling"**
3. You should see a button that says **"Connection string"** or **"Connect"** or **"Show connection string"**
4. **Click that button**

### Step 5: Configure the Modal
A modal/popup window will open. In that modal:

1. **Tab**: Make sure you're on the **"Connection String"** tab (not "App Frameworks")
2. **Type**: Select **"URI"** from the dropdown menu
3. **Source**: Select **"Primary Database"**
4. **Method**: **IMPORTANT** - Change this to **"Session Pooler"** (not "Direct connection")

### Step 6: Copy the String
1. You'll see a text box with a connection string
2. It will look like:
   ```
   postgres://postgres.xkbmbqejeoxfatcliftv:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
   ```
3. **Copy the entire string** (you can click a copy button or select all and copy)

### Step 7: Replace Password
1. The string has `[YOUR-PASSWORD]` in it
2. Replace `[YOUR-PASSWORD]` with: `[YOUR-SUPABASE-PASSWORD]`
3. The final string should be:
   ```
   postgres://postgres.xkbmbqejeoxfatcliftv:[YOUR-SUPABASE-PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
   ```

---

## 🔍 What If You Can't Find It?

If you don't see a "Connection string" button:

1. Look for **"Connection pooling"** section
2. Or look for **"Database URL"** 
3. Or try clicking **"Connect"** button at the top of the Database settings page
4. The connection string might be in a different location - look for any text that starts with `postgres://` or `postgresql://`

---

## ✅ Once You Have It

**Paste the complete connection string here** (with password already replaced), and I'll:
1. Update your `.env` file
2. Test the connection
3. Initialize your database tables

---

## 📸 Visual Guide

The connection string modal should look something like this:

```
┌─────────────────────────────────────────┐
│  Connect to your project          [X]   │
├─────────────────────────────────────────┤
│  [Connection String] [App Frameworks]   │
│                                         │
│  Type: [URI ▼]                          │
│  Source: [Primary Database ▼]           │
│  Method: [Session Pooler ▼]            │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │ postgres://postgres.xkbmbqe...    │ │
│  │ [Copy]                             │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

