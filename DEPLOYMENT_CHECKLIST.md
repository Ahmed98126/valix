# ✅ Azure Deployment Checklist

## 🔑 **Generated Secrets** (Save These!)

```
SECRET_KEY: ixpUA9RpQet_v9ExhS-3rq7VjBT4FOIVzjA79TNR4B0
SESSION_SECRET: bigwjKyf4ghMGl30dSyqw-7L5bWsXfLtsu6I2up36Wo
```

**⚠️ Keep these secure! Don't commit to Git!**

---

## 📋 **Pre-Deployment Checklist**

### **Before You Start:**
- [ ] Azure account created and logged in
- [ ] Domain valixs.com purchased (✅ done)
- [ ] Supabase database ready (✅ done)
- [ ] Code is ready (✅ done)
- [ ] Secrets generated (✅ done above)

---

## 🚀 **Deployment Steps**

### **Step 1: Create Azure App Service**
- [ ] Go to Azure Portal
- [ ] Create → App Service
- [ ] Name: `valix` or `valix-app`
- [ ] Runtime: Python 3.11
- [ ] Plan: Basic B1 or Free F1
- [ ] Create and wait for deployment

### **Step 2: Configure Environment Variables**
- [ ] Go to App Service → Configuration
- [ ] Add `DATABASE_URL` (Supabase connection string)
- [ ] Add `SECRET_KEY` (use generated value above)
- [ ] Add `SESSION_SECRET` (use generated value above)
- [ ] Add `ENVIRONMENT=production`
- [ ] Add `DEBUG=False`
- [ ] Save configuration

### **Step 3: Set Startup Command**
- [ ] Go to Configuration → General settings
- [ ] Set startup command:
  ```
  gunicorn main:app --bind 0.0.0.0:8000 --workers 2 --timeout 120
  ```
- [ ] Save

### **Step 4: Deploy Code**
- [ ] Choose deployment method:
  - [ ] VS Code extension (easiest)
  - [ ] Azure CLI
  - [ ] Local Git
- [ ] Deploy and wait for completion

### **Step 5: Configure Domain**
- [ ] Go to App Service → Custom domains
- [ ] Add `valixs.com`
- [ ] Get DNS records from Azure
- [ ] Update DNS in Namecheap:
  - [ ] Add A record
  - [ ] Add CNAME record
  - [ ] Add TXT record (for verification)
- [ ] Wait for DNS propagation
- [ ] Verify SSL certificate is active

### **Step 6: Test Deployment**
- [ ] Test Azure URL: `https://valix-app.azurewebsites.net`
- [ ] Test custom domain: `https://valixs.com`
- [ ] Test signup
- [ ] Test login
- [ ] Test invoice upload
- [ ] Test validation
- [ ] Test multi-tenant isolation

---

## 📝 **Environment Variables Reference**

Copy these into Azure App Service Configuration:

```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.xkbmbqejeoxfatcliftv.supabase.co:5432/postgres
SECRET_KEY=ixpUA9RpQet_v9ExhS-3rq7VjBT4FOIVzjA79TNR4B0
SESSION_SECRET=bigwjKyf4ghMGl30dSyqw-7L5bWsXfLtsu6I2up36Wo
ENVIRONMENT=production
DEBUG=False
MAX_UPLOAD_SIZE=52428800
```

**⚠️ Replace `YOUR_PASSWORD` with your actual Supabase password!**

---

## 🎯 **Quick Start Commands**

### **Generate New Secrets** (if needed):
```bash
python -c "import secrets; print('SECRET_KEY:', secrets.token_urlsafe(32)); print('SESSION_SECRET:', secrets.token_urlsafe(32))"
```

### **Test Locally Before Deploying**:
```bash
gunicorn main:app --bind 0.0.0.0:8000 --workers 2 --timeout 120
```

---

## 📚 **Documentation Files Created**

1. **`AZURE_DEPLOYMENT_GUIDE.md`** - Detailed step-by-step guide
2. **`AZURE_QUICK_START.md`** - Quick 5-step guide
3. **`DEPLOYMENT_CHECKLIST.md`** - This file
4. **`startup.sh`** - Startup script for Azure
5. **`requirements-azure.txt`** - Dependencies for Azure

---

## 🆘 **Need Help?**

- Check `AZURE_DEPLOYMENT_GUIDE.md` for detailed instructions
- Check Azure Portal → Log stream for errors
- Check Azure Portal → Application Insights for monitoring

---

**Ready to deploy? Start with Step 1!** 🚀

