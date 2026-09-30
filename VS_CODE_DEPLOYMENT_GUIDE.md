# 🚀 VS Code Deployment Guide - Quick & Easy

## 📋 **Step-by-Step: Deploy from VS Code**

### **Step 1: Install Azure App Service Extension** (2 minutes)

1. **Open VS Code**
2. **Go to Extensions**
   - Click Extensions icon in left sidebar (or press `Ctrl+Shift+X`)
3. **Search for "Azure App Service"**
   - Type: `Azure App Service`
   - Look for extension by **Microsoft**
4. **Install**
   - Click "Install" button
   - Wait for installation to complete

---

### **Step 2: Sign In to Azure** (1 minute)

1. **Click Azure Icon**
   - Look for Azure icon in left sidebar (blue cloud icon)
   - If you don't see it, the extension might not be installed yet

2. **Sign In**
   - Click "Sign in to Azure..."
   - Browser will open
   - Sign in with your Azure account (ahmed98126@gmail.com)
   - Authorize VS Code
   - Browser will say "You have signed in"

3. **Verify**
   - You should see your Azure subscription in VS Code sidebar

---

### **Step 3: Deploy Your Code** (5-10 minutes)

1. **Open Your Project**
   - Make sure you're in the `invoice-validator` folder in VS Code

2. **Right-Click Project**
   - Right-click on the project folder in VS Code Explorer
   - Or right-click in the file explorer sidebar

3. **Select "Deploy to Web App..."**
   - Look for this option in the context menu
   - If you don't see it, make sure you're signed in to Azure

4. **Choose Subscription**
   - Select your Azure subscription
   - Click "Select"

5. **Choose App Service**
   - Select **"Valix"** (your App Service)
   - Click "Select"

6. **Wait for Deployment**
   - VS Code will show progress in the bottom status bar
   - This takes 5-10 minutes
   - You'll see "Deployment successful" when done

---

### **Step 4: Verify Deployment** (1 minute)

1. **Go to Azure Portal**
2. **Open your App Service "Valix"**
3. **Click "Overview"**
4. **Click the "Default domain" URL** (e.g., `valix.azurewebsites.net`)
5. **You should see your Valix landing page!** 🎉

---

## 🆘 **Troubleshooting**

### **Issue: Can't see "Deploy to Web App" option**
- Make sure you're signed in to Azure (Azure icon in sidebar)
- Make sure you're right-clicking the project folder, not a file
- Try refreshing VS Code

### **Issue: Deployment fails**
- Check that environment variables are saved in Azure
- Check that startup command is set
- Check VS Code output panel for error messages

### **Issue: App doesn't start**
- Check Azure Portal → Log stream for errors
- Verify environment variables are correct
- Verify startup command is set

---

## ✅ **After Deployment**

Once deployed:
1. Test the app at `https://valix.azurewebsites.net`
2. Configure custom domain (valixs.com)
3. Test all features

---

**Ready? Start with Step 1: Install the extension!** 🚀

