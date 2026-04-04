# Kolkata AQI Routing System - Deployment Guide

## 🚀 **Task 1: Production Deployment Options**

### **Current Architecture Analysis**
```
Frontend: HTML/CSS/JavaScript (Static files)
Backend: Python Flask API (Google Maps & Air Quality APIs)
Database: In-memory caching (TTL + LRU)
External APIs: Google Routes API, Google Air Quality API
```

### **Deployment Options Comparison**

#### **Option 1: Vercel (Recommended for Frontend Only)**
**✅ Pros:**
- Free hosting for static sites
- Automatic HTTPS
- Global CDN
- Easy deployment with Git integration
- Zero maintenance

**❌ Limitations:**
- **Cannot host Python Flask backend**
- No server-side processing
- Cannot handle API keys securely
- No Google API integration

**What works on Vercel:**
- ✅ Static frontend files
- ✅ Map display
- ✅ UI interactions
- ❌ Route calculations
- ❌ AQI data fetching

#### **Option 2: Railway (Recommended Full-Stack)**
**✅ Pros:**
- Supports Python Flask
- Free tier available
- Built-in PostgreSQL (if needed)
- Environment variables support
- Automatic HTTPS
- Easy deployment

**💰 Cost:** $5-20/month for production

#### **Option 3: Render (Alternative Full-Stack)**
**✅ Pros:**
- Free tier for web services
- Python Flask support
- Environment variables
- Auto-deploys from Git
- Background workers support

**💰 Cost:** $0-7/month startup plan

#### **Option 4: AWS/Google Cloud (Enterprise)**
**✅ Pros:**
- Full control
- Scalable
- Professional
- Multiple services

**❌ Cons:**
- Complex setup
- Expensive ($50-200/month)
- Requires DevOps knowledge

---

## 🛠️ **Recommended Deployment Strategy**

### **Phase 1: Development (Current)**
```
Localhost:8001 (Frontend) → Localhost:5002 (Backend)
```

### **Phase 2: Staging (Free)**
```
Vercel (Frontend) → Railway/Render (Backend)
```

### **Phase 3: Production (Paid)**
```
Custom Domain → Railway/Render + CDN
```

---

## 📋 **Step-by-Step Railway Deployment**

### **Backend Deployment (Railway)**

#### **1. Prepare Backend for Production**
```bash
# Create production requirements
pip freeze > requirements.txt

# Add production server
pip install gunicorn
```

#### **2. Create Procfile**
```bash
# Create file: Procfile
web: gunicorn multi_route_api:app --host 0.0.0.0 --port $PORT
```

#### **3. Update API for Production**
```python
# In multi_route_api.py, add:
import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(host='0.0.0.0', port=port, debug=False)
```

#### **4. Railway Setup**
1. Go to [railway.app](https://railway.app)
2. Connect GitHub repository
3. Select backend folder
4. Add environment variables:
   ```
   Maps_API_KEY=your_google_api_key
   PORT=5002
   ```
5. Deploy

#### **5. Get Production URL**
```
Your backend URL: https://your-app-name.up.railway.app
```

### **Frontend Deployment (Vercel)**

#### **1. Update API URL for Production**
```javascript
// In multi_route.html, update:
class AQIAPI {
    constructor() {
        this.baseURL = 'https://your-app-name.up.railway.app'; // Production URL
        this.timeout = 60000;
    }
}
```

#### **2. Vercel Setup**
1. Go to [vercel.com](https://vercel.com)
2. Connect GitHub repository
3. Select frontend folder
4. Deploy

#### **3. Configure Custom Domain (Optional)**
```
Your domain: your-app.vercel.app
```

---

## 🔧 **Alternative: Single Service Deployment**

### **Render.com (All-in-One)**

#### **1. Structure for Render**
```
your-repo/
├── backend/
│   ├── multi_route_api.py
│   ├── requirements.txt
│   └── Procfile
├── frontend/
│   ├── multi_route.html
│   └── css/
└── render.yaml
```

#### **2. Create render.yaml**
```yaml
services:
  - type: web
    name: aqi-routing-api
    env: python
    buildCommand: cd backend && pip install -r requirements.txt
    startCommand: cd backend && gunicorn multi_route_api:app
    envVars:
      - key: Maps_API_KEY
        sync: false
      - key: PORT
        value: 5002

  - type: web
    name: aqi-routing-frontend
    env: static
    buildCommand: cd frontend && npm run build
    staticPublishPath: frontend
    envVars:
      - key: REACT_APP_API_URL
        value: https://aqi-routing-api.onrender.com
```

---

## 🔒 **Security Considerations**

### **API Key Management**
```python
# Never expose API keys in frontend
# Always keep them in backend environment variables

# Good: Backend handles API calls
Frontend → Backend → Google APIs

# Bad: Frontend calls Google APIs directly
Frontend → Google APIs (exposes API key)
```

### **Rate Limiting**
```python
# Add to backend for production
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(app, key_func=get_remote_address)

@app.route('/routes/multi')
@limiter.limit("10 per minute")
def get_multi_routes():
    # Your code here
```

---

## 💰 **Cost Analysis**

### **Free Tier Limitations**
- **Vercel**: 100GB bandwidth/month
- **Railway**: $5 credit/month (after free trial)
- **Render**: 750 hours/month free

### **Expected Usage**
```
API Calls per route calculation: 15-30 AQI calls
Users per day: 100
Routes per user: 3
Total API calls: 4,500/day → 135,000/month

Google API Cost: ~$20-50/month
Hosting Cost: $5-20/month
Total: $25-70/month
```

---

## 🚨 **Deployment Checklist**

### **Pre-Deployment**
- [ ] Test all features locally
- [ ] Add error handling for production
- [ ] Set up monitoring/logging
- [ ] Configure environment variables
- [ ] Test with production API keys

### **Post-Deployment**
- [ ] Test all API endpoints
- [ ] Verify frontend-backend connection
- [ ] Set up domain and SSL
- [ ] Monitor performance
- [ ] Set up alerts for errors

---

## 🌐 **Alternative: Firebase + Cloud Functions**

### **Architecture**
```
Frontend: Firebase Hosting
Backend: Google Cloud Functions
Database: Firestore (for caching)
APIs: Google Maps Platform
```

### **Benefits**
- Pay-per-use pricing
- Scales automatically
- Google ecosystem integration
- No server management

### **Cost Estimate**
```
Cloud Functions: $0.20/million requests
Firestore: $0.18/GB stored
Hosting: Free tier sufficient
Estimated: $10-30/month
```

---

## 📊 **Recommendation**

### **For Development/Hobby:**
- **Railway Backend + Vercel Frontend**
- Cost: $0-10/month
- Setup: 2-3 hours

### **For Production/Business:**
- **Render.com (all-in-one)** or **Firebase + Cloud Functions**
- Cost: $25-70/month
- Setup: 4-6 hours

### **For Enterprise:**
- **AWS/GCP with Kubernetes**
- Cost: $100-500/month
- Setup: 1-2 weeks

---

## 🔄 **Migration Steps**

### **From Local to Production**

1. **Backend Migration**
   ```bash
   # Test production setup locally
   export PORT=5002
   export Maps_API_KEY=your_key
   gunicorn multi_route_api:app
   ```

2. **Frontend Updates**
   ```javascript
   // Update API URL for production
   const API_URL = process.env.NODE_ENV === 'production' 
       ? 'https://your-backend.railway.app' 
       : 'http://localhost:5002';
   ```

3. **Testing**
   ```bash
   # Test production endpoints
   curl https://your-backend.railway.app/routes/multi?start_lat=22.5&start_lon=88.3&end_lat=22.6&end_lon=88.4
   ```

---

## 🎯 **Next Steps**

1. **Choose deployment platform** based on budget and requirements
2. **Set up backend** on Railway/Render with environment variables
3. **Deploy frontend** on Vercel with production API URL
4. **Test thoroughly** with real Google API calls
5. **Monitor usage** and optimize based on real traffic

This deployment strategy ensures your AQI routing system works reliably in production while keeping costs manageable.
