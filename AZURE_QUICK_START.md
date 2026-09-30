# ⚡ Azure Quick Start - 5 Steps to Deploy

## 🚀 **Fastest Way to Deploy**

### **Step 1: Create App Service** (5 min)
1. Go to https://portal.azure.com
2. Create → App Service
3. Name: `valix` (or `valix-app`)
4. Runtime: Python 3.11
5. Plan: Basic B1 (~$13/month) or Free F1 (testing)
6. Create

### **Step 2: Add Environment Variables** (5 min)
In App Service → Configuration → Application settings:

```
DATABASE_URL = postgresql://postgres:YOUR_PASSWORD@db.xkbmbqejeoxfatcliftv.supabase.co:5432/postgres
SECRET_KEY = [generate 32+ char random string]
SESSION_SECRET = [generate 32+ char random string]
ENVIRONMENT = production
DEBUG = False
```

### **Step 3: Set Startup Command** (2 min)
Configuration → General settings:
```
gunicorn main:app --bind 0.0.0.0:8000 --workers 2 --timeout 120
```

### **Step 4: Deploy with VS Code** (10 min)
1. Install "Azure App Service" extension
2. Right-click project → "Deploy to Web App"
3. Select your App Service
4. Wait for deployment

### **Step 5: Configure Domain** (10 min)
1. App Service → Custom domains → Add `valixs.com`
2. Update DNS in Namecheap (A record + CNAME)
3. Wait for SSL (automatic)

**Total Time: ~30 minutes!** 🎉

---

## 🔑 **Generate Secrets**

Run this to generate secure secrets:
```bash
python -c "import secrets; print('SECRET_KEY:', secrets.token_urlsafe(32)); print('SESSION_SECRET:', secrets.token_urlsafe(32))"
```

---

**See `AZURE_DEPLOYMENT_GUIDE.md` for detailed instructions!**

