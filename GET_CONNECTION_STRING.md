# Get Your Supabase Connection String

## Steps:

1. **Go to your Supabase Dashboard**
   - Visit: https://supabase.com/dashboard/project/xkbmbqejeoxfatcliftv

2. **Navigate to Database Settings**
   - Click **"Settings"** in the left sidebar
   - Click **"Database"** in the settings menu

3. **Open Connection String**
   - Scroll down to find **"Connection string"** section
   - Click the **"Connection string"** button/link

4. **Configure for Session Pooler**
   - In the modal that opens:
     - **Tab**: Make sure "Connection String" tab is selected
     - **Type**: Select **"URI"** from dropdown
     - **Source**: Select **"Primary Database"**
     - **Method**: Select **"Session Pooler"** (NOT "Direct connection")

5. **Copy the Connection String**
   - The connection string will be displayed in a text box
   - It should look like:
     ```
     postgres://postgres.xkbmbqejeoxfatcliftv:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
     ```
   - **Copy the entire string**

6. **Replace the Password**
   - The string will have `[YOUR-PASSWORD]` placeholder
   - Replace it with your actual password: `[YOUR-SUPABASE-PASSWORD]`
   - Final string should be:
     ```
     postgres://postgres.xkbmbqejeoxfatcliftv:[YOUR-SUPABASE-PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
     ```

## What to Send Me:

**Paste the complete connection string here** (with your password already replaced), and I'll update your `.env` file and test the connection.

---

## Alternative: If Session Pooler Doesn't Work

If you're on an IPv4-only network and Session Pooler doesn't work, you can also try:

1. **Transaction Pooler** (port 6543):
   - Method: Select **"Transaction Pooler"**
   - Format: `postgres://postgres:[PASSWORD]@db.xkbmbqejeoxfatcliftv.supabase.co:6543/postgres`

2. **Direct Connection with IPv4 Add-on**:
   - You may need to purchase the IPv4 add-on from Supabase
   - Or use a VPN/network that supports IPv6

