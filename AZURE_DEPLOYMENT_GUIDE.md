# 🚀 Azure Deployment Guide for Valix

## 📋 **Prerequisites**

- ✅ Azure account (free tier available)
- ✅ Domain: valixs.com (already purchased)
- ✅ Supabase database (already set up)
- ✅ Code ready (✅ done)

---

## 🎯 **Step-by-Step Deployment**

### **Step 1: Create Azure App Service** (15-20 minutes)

1. **Go to Azure Portal**
   - Visit: https://portal.azure.com
   - Sign in with your Azure account

2. **Create App Service**
   - Click "Create a resource" (top left)
   - Search for "App Service"
   - Click "Create"

3. **Configure App Service**
   - **Subscription**: Choose your subscription
   - **Resource Group**: Create new or use existing
     - Name: `valix-resources`
   - **Name**: `valix` or `valix-app` (must be globally unique)
   - **Publish**: Code
   - **Runtime stack**: Python 3.11
   - **Operating System**: Linux (recommended) or Windows
   - **Region**: Choose closest to your users
   - **App Service Plan**: 
     - **Free F1** (for testing) - Limited resources
     - **Basic B1** (~$13/month) - Recommended for production
   - Click "Review + create"
   - Click "Create"

4. **Wait for Deployment** (2-3 minutes)
   - You'll see "Deployment in progress"
   - Wait for "Your deployment is complete"

---

### **Step 2: Configure Environment Variables** (10 minutes)

1. **Go to Your App Service**
   - Click "Go to resource" after deployment
   - Or search for your app name in Azure Portal

2. **Add Configuration**
   - In left menu, click "Configuration"
   - Click "Application settings" tab
   - Click "+ New application setting"

3. **Add These Settings** (one by one):

   ```
   Name: DATABASE_URL
   Value: postgresql://postgres:YOUR_PASSWORD@db.xkbmbqejeoxfatcliftv.supabase.co:5432/postgres
   ```

   ```
   Name: SECRET_KEY
   Value: [Generate a random 32+ character string]
   ```

   ```
   Name: SESSION_SECRET
   Value: [Generate a random 32+ character string]
   ```

   ```
   Name: ENVIRONMENT
   Value: production
   ```

   ```
   Name: DEBUG
   Value: False
   ```

   ```
   Name: MAX_UPLOAD_SIZE
   Value: 52428800
   ```

4. **Save Configuration**
   - Click "Save" at the top
   - Click "Continue" to confirm
   - Wait for save to complete

---

### **Step 3: Configure Startup Command** (5 minutes)

1. **Go to Configuration**
   - In App Service, click "Configuration"
   - Click "General settings" tab

2. **Set Startup Command**
   - **Startup Command**: 
   ```
   gunicorn main:app --bind 0.0.0.0:8000 --workers 2 --timeout 120
   ```

3. **Save**
   - Click "Save"

---

### **Step 4: Install Dependencies** (5 minutes)

1. **Go to Deployment Center**
   - In App Service, click "Deployment Center"
   - Choose deployment method:
     - **Option A**: Local Git (easiest for first time)
     - **Option B**: GitHub (if you have repo)
     - **Option C**: VS Code extension (recommended)

---

### **Step 5: Deploy Code** (15-30 minutes)

#### **Option A: VS Code Extension (Easiest)** ⭐ **RECOMMENDED**

1. **Install Extension**
   - Open VS Code
   - Install "Azure App Service" extension
   - Sign in to Azure

2. **Deploy**
   - Right-click your project folder
   - Select "Deploy to Web App"
   - Choose your App Service
   - Wait for deployment (5-10 minutes)

#### **Option B: Azure CLI**

1. **Install Azure CLI**
   ```bash
   # Download from: https://aka.ms/installazurecliwindows
   ```

2. **Login**
   ```bash
   az login
   ```

3. **Deploy**
   ```bash
   cd C:\Users\ahmed\invoice-validator
   az webapp up --name valix-app --resource-group valix-resources --runtime "PYTHON:3.11"
   ```

#### **Option C: Local Git**

1. **In Azure Portal**
   - Go to Deployment Center
   - Choose "Local Git"
   - Copy the Git URL

2. **In Terminal**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add azure [YOUR_GIT_URL]
   git push azure master
   ```

---

### **Step 6: Configure Domain** (15-20 minutes)

1. **In Azure App Service**
   - Click "Custom domains"
   - Click "+ Add custom domain"

2. **Add Domain**
   - Enter: `valixs.com`
   - Click "Validate"
   - Azure will show you DNS records needed

3. **Update DNS in Namecheap**
   - Go to Namecheap → Domain List → valixs.com → Advanced DNS
   - Add these records:
     - **Type**: A Record
       - **Host**: @
       - **Value**: [Azure IP from portal]
       - **TTL**: Automatic
     - **Type**: CNAME
       - **Host**: www
       - **Value**: `valix-app.azurewebsites.net`
       - **TTL**: Automatic
     - **Type**: TXT
       - **Host**: @
       - **Value**: [Verification string from Azure]
       - **TTL**: Automatic

4. **Wait for DNS Propagation** (5-30 minutes)
   - DNS changes can take time
   - Azure will automatically provision SSL certificate

5. **Verify Domain**
   - Go back to Azure → Custom domains
   - Click "Refresh"
   - Domain should show as "Secure" with SSL

---

### **Step 7: Test Deployment** (10 minutes)

1. **Test Azure URL**
   - Visit: `https://valix-app.azurewebsites.net`
   - Should see landing page

2. **Test Custom Domain**
   - Visit: `https://valixs.com`
   - Should see landing page with SSL

3. **Test Features**
   - Sign up new user
   - Login
   - Upload invoices
   - Verify everything works

---

## 🔧 **Troubleshooting**

### **Issue: App won't start**
- Check "Log stream" in Azure Portal
- Verify startup command is correct
- Check environment variables

### **Issue: Database connection fails**
- Verify `DATABASE_URL` is correct
- Check Supabase firewall settings
- Test connection from Azure

### **Issue: Static files not loading**
- Verify `StaticFiles` is mounted in `main.py`
- Check file paths are correct

### **Issue: Domain not working**
- Wait for DNS propagation (up to 48 hours)
- Verify DNS records in Namecheap
- Check domain status in Azure

---

## 📊 **Post-Deployment Checklist**

- [ ] App is accessible via Azure URL
- [ ] Custom domain is working
- [ ] SSL certificate is active
- [ ] Can sign up new users
- [ ] Can login
- [ ] Can upload invoices
- [ ] Validation is working
- [ ] Multi-tenant isolation works
- [ ] Database connection is stable

---

## 🎉 **You're Live!**

Once deployed, your app will be accessible at:
- **Azure URL**: `https://valix-app.azurewebsites.net`
- **Custom Domain**: `https://valixs.com`

---

## 📝 **Next Steps After Deployment**

1. Monitor application logs
2. Set up monitoring/alerts
3. Configure backups
4. Add password reset feature
5. Add email service

---

**Ready to start? Let's begin with Step 1!** 🚀

