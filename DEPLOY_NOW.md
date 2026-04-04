# 🚀 Deploy Your AQI Navigation System - Step by Step

## 📋 **Prerequisites**
- GitHub account with your code pushed
- Google Maps API Key
- Railway account (free tier available)
- Vercel account (free tier available)

---

## 🛤️ **Step 1: Backend Deployment (Railway)**

### **1.1 Prepare Your Code**
```bash
# Make sure your code is on GitHub
git add .
git commit -m "Ready for production deployment"
git push origin main
```

### **1.2 Deploy to Railway**
1. Go to [railway.app](https://railway.app)
2. Click **"Start a New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose your repository
5. Select **Backend** folder (or configure root path)

### **1.3 Configure Environment Variables**
In Railway dashboard, add these environment variables:
```
Maps_API_KEY=your_google_maps_api_key_here
PORT=5002
```

### **1.4 Deploy**
- Click **"Deploy"**
- Wait for deployment to complete
- Copy your Railway URL (e.g., `https://your-app-name.up.railway.app`)

### **1.5 Test Backend**
```bash
# Test your deployed backend
curl https://your-app-name.up.railway.app/
```

---

## 🌐 **Step 2: Frontend Deployment (Vercel)**

### **2.1 Update API URL**
Edit `frontend/config.js`:
```javascript
production: {
    apiBaseUrl: 'https://your-app-name.up.railway.app', // Replace with your Railway URL
    environment: 'Production'
}
```

### **2.2 Deploy to Vercel**
1. Go to [vercel.com](https://vercel.com)
2. Click **"New Project"**
3. Connect your GitHub repository
4. Select **Frontend** folder as root directory
5. Configure build settings (if needed)

### **2.3 Deploy**
- Click **"Deploy"**
- Wait for deployment to complete
- Your app will be available at `https://your-app-name.vercel.app`

---

## 🔧 **Step 3: Update Frontend for Production**

### **3.1 Add Config Script to HTML**
Add this to both `index.html` and `multi_route.html` before other scripts:
```html
<script src="config.js"></script>
```

### **3.2 Update API Classes**
In your JavaScript files, replace hardcoded URLs:
```javascript
// Before
this.baseURL = 'http://localhost:5002';

// After  
this.baseURL = window.APP_CONFIG.apiBaseUrl;
```

### **3.3 Commit and Deploy**
```bash
git add .
git commit -m "Update API configuration for production"
git push origin main
```

---

## ✅ **Step 4: Test Your Deployed App**

### **4.1 Test Backend**
```bash
curl https://your-app-name.up.railway.app/routes/multi?start_lat=22.5878&start_lon=88.3747&end_lat=22.5174&end_lon=88.3668
```

### **4.2 Test Frontend**
1. Open `https://your-app-name.vercel.app`
2. Try clicking on the map
3. Test route calculation
4. Check both Classic and Multi-Route views

---

## 🎯 **Quick Deployment Commands**

### **Backend (Railway)**
```bash
# 1. Push to GitHub
git add backend/Procfile backend/requirements.txt
git commit -m "Add production backend files"
git push

# 2. Deploy on Railway
# - Go to railway.app
# - Connect repo
# - Add Maps_API_KEY environment variable
# - Deploy
```

### **Frontend (Vercel)**
```bash
# 1. Update config
# Edit frontend/config.js with your Railway URL

# 2. Push to GitHub
git add frontend/config.js
git commit -m "Update production config"
git push

# 3. Deploy on Vercel
# - Go to vercel.com
# - Connect repo
# - Deploy
```

---

## 🔍 **Troubleshooting**

### **Common Issues**

#### **Backend Issues**
- **Error**: "Maps_API_KEY not set"
  - **Fix**: Add environment variable in Railway dashboard
- **Error**: "Port already in use"
  - **Fix**: Railway automatically sets PORT, just use it
- **Error**: "Module not found"
  - **Fix**: Check requirements.txt has all dependencies

#### **Frontend Issues**
- **Error**: "CORS policy"
  - **Fix**: Ensure backend URL is correct in config.js
- **Error**: "API request failed"
  - **Fix**: Check backend is deployed and accessible
- **Error**: "404 Not Found"
  - **Fix**: Verify API endpoints are correct

### **Debug Commands**
```bash
# Test backend health
curl https://your-backend.railway.app/

# Test API endpoint
curl "https://your-backend.railway.app/routes/multi?start_lat=22.5&start_lon=88.3&end_lat=22.6&end_lon=88.4"

# Check frontend config
# Open browser console and type:
console.log(window.APP_CONFIG)
```

---

## 💰 **Cost Breakdown**

### **Monthly Costs**
- **Railway**: $5-20 (after free trial)
- **Vercel**: $0 (static hosting)
- **Google APIs**: $20-50 (depending on usage)
- **Total**: $25-70/month

### **Free Tier Limits**
- **Railway**: $5 credit/month, then $5/month
- **Vercel**: 100GB bandwidth/month
- **Google Maps**: $200 credit/month, then usage-based

---

## 🎊 **Success Checklist**

### **Before Going Live**
- [ ] Backend deployed on Railway
- [ ] Frontend deployed on Vercel
- [ ] API key configured in Railway
- [ ] Frontend config updated with Railway URL
- [ ] All routes tested in production
- [ ] Error handling tested
- [ ] Mobile responsiveness checked

### **After Deployment**
- [ ] Monitor Railway logs for errors
- [ ] Check Vercel analytics
- [ ] Monitor Google API usage
- [ ] Set up alerts for downtime
- [ ] Test user feedback flow

---

## 🚀 **Alternative: Render.com (All-in-One)**

If you prefer a single platform:

### **Render Setup**
1. Go to [render.com](https://render.com)
2. Connect GitHub repository
3. Create **Web Service** for backend
4. Create **Static Site** for frontend
5. Configure environment variables

### **Benefits**
- Single dashboard
- Built-in CI/CD
- Good free tier
- Easy SSL certificates

---

## 📞 **Need Help?**

### **Documentation**
- Railway docs: docs.railway.app
- Vercel docs: vercel.com/docs
- Google Maps API: developers.google.com/maps

### **Support**
- Railway: support@railway.app
- Vercel: support@vercel.com
- Google Maps: google.com/maps/support

---

**Your AQI Navigation System is now ready for production deployment! 🎉**

Follow these steps and you'll have a fully functional web app deployed and accessible to users worldwide.
