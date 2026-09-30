# How to Get the Correct Supabase Session Pooler Connection String

## Steps:

1. **Go to your Supabase Dashboard**
   - Navigate to: https://supabase.com/dashboard/project/xkbmbqejeoxfatcliftv

2. **Go to Settings → Database**
   - Click on "Settings" in the left sidebar
   - Click on "Database" in the settings menu

3. **Open Connection String Modal**
   - Click on "Connection string" button
   - A modal will open

4. **Configure the Connection String**
   - **Tab**: Make sure "Connection String" tab is selected (not "App Frameworks")
   - **Type**: Select "URI" from the dropdown
   - **Source**: Select "Primary Database"
   - **Method**: **IMPORTANT** - Change from "Direct connection" to **"Session Pooler"**

5. **Copy the Connection String**
   - The connection string will update automatically
   - It should look something like:
     ```
     postgresql://postgres.xkbmbqejeoxfatcliftv:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
     ```
   - Copy the entire string

6. **Replace [YOUR-PASSWORD]**
   - Replace `[YOUR-PASSWORD]` with your actual password: `[YOUR-SUPABASE-PASSWORD]`
   - The final string should be:
     ```
     postgresql://postgres.xkbmbqejeoxfatcliftv:[YOUR-SUPABASE-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
     ```

7. **Note the Region**
   - The region in the hostname (e.g., `us-east-1`, `eu-west-1`, etc.) - make sure it matches your project's region

## What to Send Me:

Please copy and paste the **exact** connection string from the Supabase dashboard (with Session Pooler selected), and I'll update your `.env` file with it.

