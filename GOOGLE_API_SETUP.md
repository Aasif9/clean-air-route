# Google API Integration Setup Guide

## 🚀 Overview

This guide shows how to set up and run the Kolkata AQI Clean Route system with Google Live APIs instead of dummy data.

## 📋 Prerequisites

### Required Google APIs
1. **Routes API** - For getting alternative routes
2. **Air Quality API** - For getting real-time AQI data

### Getting Your API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable these APIs:
   - Routes API
   - Air Quality API
4. Create an API key:
   - Go to "Credentials" → "Create Credentials" → "API Key"
   - **Important**: Restrict the key to your APIs for security
5. Copy the API key

## 📁 Project Structure

```
clean-air/
├── backend/
│   ├── aqi_cache.py           # TTL cache for AQI responses
│   ├── google_aqi_service.py  # Core Google API integration
│   └── api.py                 # Flask API server
├── frontend/
│   ├── index.html             # Updated frontend
│   └── js/
│       └── app.js             # Updated with percentage display
├── .env                       # API key configuration
└── requirements.txt           # Updated dependencies
```

## ⚙️ Setup Instructions

### 1. Install Dependencies
```bash
cd /Users/asifali/Desktop/web-projects/clean-air
pip install -r requirements.txt
```

### 2. Configure API Key
Edit the `.env` file:
```bash
# Replace YOUR_ACTUAL_KEY_HERE with your real Google Maps API key
Maps_API_KEY=YOUR_ACTUAL_KEY_HERE
```

### 3. Start the Backend Server
```bash
cd backend
python api.py
```

**Expected Output:**
```
✅ Google Maps API key loaded
Starting Google Live API server on http://localhost:5002
Test endpoints:
  http://localhost:5002/
  http://localhost:5002/routes/clean?start_lat=22.5750&start_lon=88.3500&end_lat=22.5800&end_lon=88.3800
 * Running on http://127.0.0.1:5002
```

### 4. Start the Frontend
```bash
cd frontend
python -m http.server 8000
```

### 5. Access the Application
- **Frontend**: http://localhost:8000
- **Backend API**: http://localhost:5002

## 🧪 Testing the Integration

### 1. Test Backend API
```bash
curl http://localhost:5002/
# Expected: "Kolkata AQI Routing - Google Live API Version"

curl http://localhost:5002/routes/clean?start_lat=22.5750&start_lon=88.3500&end_lat=22.5800&end_lon=88.3800
# Expected: JSON response with fast_route, clean_route, and comparison
```

### 2. Test Frontend
1. Open http://localhost:8000 in browser
2. Click on map to set start/end points in Kolkata
3. Click "Calculate Routes"
4. Should see:
   - "Data Source: Google Live API" in status
   - Real route polylines on map
   - AQI improvement percentage

## 🔍 Key Features

### What Changed vs. Dummy System
1. **Real Routes**: Uses Google Routes API instead of OSM network
2. **Live AQI**: Real-time air quality data vs. dummy stations
3. **Better Scoring**: Exponential exposure scoring (exp(aqi/75))
4. **Cache System**: 5-minute TTL cache to reduce API costs
5. **Percentage Display**: Shows "% cleaner air" improvement

### API Response Format
```json
{
  "fast_route": {
    "coordinates": [[lat, lon], ...],
    "analysis": {
      "total_distance_km": 8.5,
      "total_travel_time_min": 18.2,
      "average_aqi": 95.3,
      "exposure_score": 1234.5
    }
  },
  "clean_route": {...},
  "comparison": {
    "distance_increase_percent": 18.1,
    "aqi_improvement": 30.4,
    "aqi_improvement_pct": 31.9
  },
  "data_source": "google_live"
}
```

## 💰 Cost Optimization

### Cache System
- **Grid Size**: ~111m (lat/lon rounded to 3 decimals)
- **TTL**: 5 minutes
- **Savings**: Repeated queries in same area use cached data

### API Usage per Route
- **Routes API**: 1 call (returns multiple alternatives)
- **AQI API**: 6 calls (6 sample points per route)
- **With Cache**: Significantly reduced AQI calls for repeated areas

## 🚨 Troubleshooting

### Common Issues

1. **"Maps_API_KEY not set"**
   - Check `.env` file exists in project root
   - Verify API key is correctly set

2. **"No routes returned from Google Routes API"**
   - Check if Routes API is enabled in Google Cloud Console
   - Verify API key has Routes API permissions
   - Try coordinates within a supported region

3. **"AQI API fallback" errors**
   - Check if Air Quality API is enabled
   - Verify API key has Air Quality API permissions
   - Some regions may not have AQI coverage

4. **CORS errors**
   - Ensure backend is running on port 5002
   - Check Flask-CORS is properly configured

### Debug Mode
The backend runs in debug mode by default. Check console for detailed error messages.

## 🔄 Switching Back to Dummy System

To use the original dummy system:
```bash
python dummy_api.py  # Instead of backend/api.py
```

The frontend will automatically work with either backend.

## 📊 Performance Expectations

- **Response Time**: 3-8 seconds (API calls + processing)
- **Accuracy**: Real routes and live AQI data
- **Coverage**: Same as Google Maps/Air Quality APIs
- **Cost**: Depends on your Google Cloud pricing tier

## 🎯 Next Steps

1. **Monitor Usage**: Check Google Cloud Console for API usage
2. **Set Budgets**: Configure billing alerts to control costs
3. **Optimize Cache**: Adjust TTL based on your usage patterns
4. **Add Error Handling**: Implement fallbacks for API failures

---

**🎉 Congratulations!** Your Kolkata AQI system now uses real Google APIs for live routing and air quality data!
