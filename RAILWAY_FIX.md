# 🔧 Railway Build Failure - Quick Fix Guide

## 🚨 **Common Railway Build Issues & Solutions**

### **Issue 1: Import Path Problems**
**Problem**: `ModuleNotFoundError: No module named 'simple_multi_route'`

**Solution**: Fixed the import path in `multi_route_api.py`
```python
# Before (problematic):
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# After (fixed):
from simple_multi_route import find_multi_routes
```

### **Issue 2: Missing Dependencies**
**Problem**: Package installation failures

**Solution**: Updated `requirements.txt` with exact versions:
```
Flask==3.0.0
Flask-CORS==4.0.0
python-dotenv==1.0.0
requests==2.31.0
polyline==2.0.0
gunicorn==21.2.0
```

### **Issue 3: Procfile Configuration**
**Problem**: Incorrect start command

**Solution**: Updated `Procfile`:
```
web: gunicorn multi_route_api:app --host 0.0.0.0 --port $PORT
```

---

## 🛠️ **Step-by-Step Fix**

### **Step 1: Update Your Code**
Make sure these files are correctly configured:

#### **backend/multi_route_api.py**
```python
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os

from simple_multi_route import find_multi_routes

load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "Kolkata AQI Multi-Route System - Version 2.0"

# ... rest of your code

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(debug=False, host='0.0.0.0', port=port)
```

#### **backend/requirements.txt**
```
Flask==3.0.0
Flask-CORS==4.0.0
python-dotenv==1.0.0
requests==2.31.0
polyline==2.0.0
gunicorn==21.2.0
```

#### **backend/Procfile**
```
web: gunicorn multi_route_api:app --host 0.0.0.0 --port $PORT
```

### **Step 2: Push Updates to GitHub**
```bash
git add .
git commit -m "Fix Railway deployment issues"
git push origin main
```

### **Step 3: Redeploy on Railway**
1. Go to your Railway project
2. Click **"Redeploy"** or **"New Deployment"**
3. Select the latest commit
4. Click **"Deploy"**

### **Step 4: Add Environment Variables**
In Railway dashboard:
1. Go to your service settings
2. Click **"Variables"**
3. Add:
   ```
   Maps_API_KEY=your_google_maps_api_key_here
   ```

---

## 🔍 **Debugging Railway Build Logs**

### **Common Error Messages & Fixes**

#### **Error**: `No such file or directory: 'requirements.txt'`
**Fix**: Make sure `requirements.txt` is in the root of your backend folder

#### **Error**: `ModuleNotFoundError: No module named 'flask'`
**Fix**: Check `requirements.txt` has correct Flask version

#### **Error**: `Application failed to start`
**Fix**: Check Procfile syntax and make sure `multi_route_api.py` has `app` variable

#### **Error**: `Port already in use`
**Fix**: Railway handles PORT automatically, just use `$PORT`

---

## 🚀 **Alternative: Use Docker**

If Railway continues to fail, try Docker:

### **Create Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE $PORT

CMD ["gunicorn", "multi_route_api:app", "--host", "0.0.0.0", "--port", "$PORT"]
```

### **Update railway.toml**
```toml
[build]
builder = "dockerfile"

[deploy]
startCommand = "gunicorn multi_route_api:app --host 0.0.0.0 --port $PORT"
```

---

## 📋 **Pre-Deployment Checklist**

### **Before Deploying**
- [ ] All Python files have no syntax errors
- [ ] `requirements.txt` has exact versions
- [ ] `Procfile` is correctly formatted
- [ ] Environment variables are set in Railway
- [ ] Code is pushed to GitHub

### **Test Local Build**
```bash
# Test locally first
cd backend
python -m pip install -r requirements.txt
python multi_route_api.py
```

---

## 🆘 **Getting Help**

### **Railway Support**
- Check build logs in Railway dashboard
- Railway Discord: https://discord.gg/railway
- Support: support@railway.app

### **Common Fixes**
1. **Clear cache**: Delete and recreate service
2. **Check Python version**: Railway uses Python 3.11 by default
3. **Verify file paths**: All files should be in correct directories
4. **Test locally**: Make sure it works locally before deploying

---

## 🎯 **Quick Fix Commands**

```bash
# 1. Fix any syntax errors
python -m py_compile backend/multi_route_api.py
python -m py_compile backend/simple_multi_route.py

# 2. Test requirements
pip install -r backend/requirements.txt

# 3. Test local server
cd backend
python multi_route_api.py

# 4. If local works, push and redeploy
git add .
git commit -m "Fix Railway deployment"
git push origin main
```

---

## ✅ **Success Indicators**

### **Build Success**
- ✅ All dependencies install successfully
- ✅ No import errors
- ✅ Gunicorn starts correctly
- ✅ Service responds to HTTP requests

### **Test Your Deployment**
```bash
# Test health endpoint
curl https://your-app.up.railway.app/

# Test API endpoint
curl "https://your-app.up.railway.app/routes/multi?start_lat=22.5&start_lon=88.3&end_lat=22.6&end_lon=88.4"
```

---

**If you follow these steps, your Railway deployment should work!** 🎉

The most common issues are:
1. Import path problems (fixed)
2. Missing dependencies (fixed)
3. Incorrect Procfile (fixed)
4. Missing environment variables (add Maps_API_KEY)

Try redeploying with these fixes and it should work!
