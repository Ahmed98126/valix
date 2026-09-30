# 🚀 Azure App Service - Next Steps

## ✅ **Step 1: App Service Created** ✅

Great! Your App Service "Valix" is now created.

---

## 📋 **Step 2: Configure Environment Variables** (5 minutes)

### **Where to Go:**
1. In Azure Portal, go to your App Service "Valix"
2. In the left menu, click **"Configuration"**
3. Click **"Application settings"** tab
4. Click **"+ New application setting"** for each variable

### **Add These Settings:**

#### **1. DATABASE_URL**
```
Name: DATABASE_URL
Value: postgresql://postgres:YOUR_PASSWORD@db.xkbmbqejeoxfatcliftv.supabase.co:5432/postgres
```
**⚠️ Replace `YOUR_PASSWORD` with your actual Supabase password!**

#### **2. SECRET_KEY**
```
Name: SECRET_KEY
Value: ixpUA9RpQet_v9ExhS-3rq7VjBT4FOIVzjA79TNR4B0
```

#### **3. SESSION_SECRET**
```
Name: SESSION_SECRET
Value: bigwjKyf4ghMGl30dSyqw-7L5bWsXfLtsu6I2up36Wo
```

#### **4. ENVIRONMENT**
```
Name: ENVIRONMENT
Value: production
```

#### **5. DEBUG**
```
Name: DEBUG
Value: False
```

#### **6. MAX_UPLOAD_SIZE**
```
Name: MAX_UPLOAD_SIZE
Value: 52428800
```

### **Save:**
- Click **"Save"** at the top
- Click **"Continue"** to confirm
- Wait for save to complete (~30 seconds)

---

## ⚙️ **Step 3: Set Startup Command** (2 minutes)

### **Where to Go:**
1. Still in **"Configuration"**
2. Click **"General settings"** tab
3. Scroll down to **"Startup Command"**

### **Set Startup Command:**
```
gunicorn main:app --bind 0.0.0.0:8000 --workers 2 --timeout 120
```

### **Save:**
- Click **"Save"** at the top
- Click **"Continue"** to confirm

---

## 📦 **Step 4: Deploy Your Code** (10-15 minutes)

### **Option A: VS Code Extension** ⭐ **EASIEST**

1. **Install Extension:**
   - Open VS Code
   - Go to Extensions (Ctrl+Shift+X)
   - Search for "Azure App Service"
   - Install by Microsoft

2. **Sign In:**
   - Click Azure icon in left sidebar
   - Click "Sign in to Azure"
   - Sign in with your Azure account

3. **Deploy:**
   - Right-click your project folder (`invoice-validator`)
   - Select **"Deploy to Web App..."**
   - Select your subscription
   - Select **"Valix"** (your App Service)
   - Wait for deployment (5-10 minutes)

### **Option B: Azure CLI** (Alternative)

1. **Install Azure CLI:**
   - Download from: https://aka.ms/installazurecliwindows

2. **Login:**
   ```bash
   az login
   ```

3. **Deploy:**
   ```bash
   cd C:\Users\ahmed\invoice-validator
   az webapp up --name Valix --resource-group Invoice_Validation_Project --runtime "PYTHON:3.11"
   ```

---

## 🌐 **Step 5: Test Deployment** (2 minutes)

1. **Go to your App Service**
2. Click **"Overview"** in left menu
3. Find **"Default domain"** (e.g., `valix.azurewebsites.net`)
4. Click the URL to open it
5. **You should see your landing page!** 🎉

---

## 🔧 **Step 6: Configure Domain** (15 minutes)

### **In Azure:**
1. Go to App Service → **"Custom domains"**
2. Click **"+ Add custom domain"**
3. Enter: `valixs.com`
4. Click **"Validate"**
5. Azure will show you DNS records needed

### **In Namecheap:**
1. Go to Namecheap → Domain List → valixs.com
2. Click **"Manage"** → **"Advanced DNS"**
3. Add these records:

   **A Record:**
   - Type: A Record
   - Host: @
   - Value: [IP address from Azure]
   - TTL: Automatic

   **CNAME Record:**
   - Type: CNAME Record
   - Host: www
   - Value: `valix.azurewebsites.net`
   - TTL: Automatic

   **TXT Record (for verification):**
   - Type: TXT Record
   - Host: @
   - Value: [Verification string from Azure]
   - TTL: Automatic

4. **Save** in Namecheap

### **Back in Azure:**
1. Wait 5-30 minutes for DNS propagation
2. Go back to Custom domains
3. Click **"Refresh"**
4. Domain should show as **"Secure"** with SSL ✅

---

## ✅ **Checklist**

- [ ] Environment variables added
- [ ] Startup command set
- [ ] Code deployed
- [ ] App accessible via Azure URL
- [ ] Domain configured
- [ ] SSL certificate active
- [ ] Test signup/login
- [ ] Test invoice upload

---

## 🎉 **You're Live!**

Once done, your app will be at:
- **Azure URL**: `https://valix.azurewebsites.net`
- **Custom Domain**: `https://valixs.com`

---

**Start with Step 2: Add environment variables!** 🚀

