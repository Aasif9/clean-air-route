# Kolkata AQI Routing System - Technical Report

## 🎯 **Current Implementation Overview**

### **System Architecture**
- **Backend**: Python Flask API with Google Routes & Air Quality APIs
- **Frontend**: JavaScript with Leaflet.js for interactive mapping
- **Data Flow**: Google APIs → Backend Processing → Frontend Display

---

## 📁 **Core Files & Responsibilities**

### **Backend Files**

#### 1. `backend/enhanced_aqi_service.py`
**Primary Logic Engine**
- Fetches routes from Google Routes API
- Performs dynamic AQI sampling along routes
- Calculates exposure scores using exponential formula
- Manages multi-level caching (TTL + LRU)
- Handles coordinate rounding for cache optimization

**Key Functions:**
- `_fetch_routes()` - Gets up to 3 alternative routes from Google
- `_dynamic_sampling()` - Distance-based AQI sampling
- `_sample_route_aqi()` - Collects AQI data along routes
- `find_best_routes()` - Main orchestrator function

#### 2. `backend/aqi_cache.py`
**Caching Layer**
- TTL-based cache (10 minutes)
- Thread-safe operations
- Reduces API calls by 60-80%

#### 3. `backend/api.py`
**Flask API Server**
- RESTful endpoints
- CORS handling
- Error management
- API key validation

**Endpoints:**
- `GET /` - System status
- `GET /routes/clean` - Main route calculation
- `GET /stations` - Station compatibility

### **Frontend Files**

#### 4. `frontend/js/map.js`
**Interactive Mapping**
- Leaflet.js map management
- Route drawing and styling
- Hover effects and tooltips
- Multiple route support
- User interaction handling

**Key Methods:**
- `drawRoute()` - Draws main routes (clean/fast)
- `drawAlternativeRoutes()` - Draws additional options
- `handleMapClick()` - User input processing

#### 5. `frontend/js/app.js`
**Application Controller**
- API communication
- Route data processing
- UI updates
- User flow management

#### 6. `frontend/js/api.js`
**API Client**
- HTTP request handling
- Error management
- Timeout handling

#### 7. `frontend/index.html`
**User Interface**
- Responsive layout
- Route comparison cards
- Control panels
- Legend and status displays

#### 8. `frontend/css/enhancements.css`
**Styling & UX**
- Interactive route effects
- Hover animations
- Responsive design
- Visual feedback

---

## 🧠 **Current Logic Implementation**

### **Route Generation Logic**
```
1. User selects start/end points
2. Backend calls Google Routes API with:
   - computeAlternativeRoutes: true
   - routingPreference: TRAFFIC_AWARE
   - Returns up to 3 route alternatives
3. Each route gets AQI sampling:
   - Distance-based dynamic sampling
   - Coordinate rounding for caching
   - LRU cache for repeated points
4. Exposure scoring: duration × 1.05^AQI
5. Routes categorized:
   - Fastest = Lowest duration
   - Cleanest = Lowest exposure score
   - Others = Alternatives
```

### **Sampling Algorithm**
```
if distance < 3km: Sample every 500m (4-6 points)
if distance 3-15km: Sample every 1km (3-12 points)
if distance > 15km: Sample every 1.5km (max 15 points)
```

### **Caching Strategy**
```
1. Coordinate rounding to 4 decimals (~11m precision)
2. TTL cache: 10 minutes expiration
3. LRU cache: 1000 entries in memory
4. Cache hit recognition for same locations
```

---

## 🚨 **Current Problems & Issues**

### **1. API Request Error**
**Problem**: `[ERROR] API Request Error: {}` in console
**Root Cause**: Network or API key issues
**Impact**: Routes not displaying properly

### **2. Single Route Display**
**Problem**: Only one route showing despite multiple alternatives
**Root Cause**: Frontend not processing additional_routes correctly
**Impact**: Users don't see route options

### **3. Route Comparison UI**
**Problem**: Current UI shows comparison instead of individual route cards
**Root Cause**: Design doesn't match multi-route requirements
**Impact**: Hard to compare individual routes

### **4. Route Visualization**
**Problem**: Routes don't branch visually like Finland example
**Root Cause**: All routes share same start/end points
**Impact**: Doesn't show clear route differentiation

---

## 🔧 **Technical Stack Details**

### **Backend Dependencies**
- `flask` - Web framework
- `requests` - HTTP client for Google APIs
- `polyline` - Google polyline decoding
- `python-dotenv` - Environment variables
- `functools.lru_cache` - In-memory caching

### **Frontend Dependencies**
- `Leaflet.js` - Interactive mapping
- `Font Awesome` - Icons
- Vanilla JavaScript - No framework dependencies

### **External APIs**
- **Google Routes API**: Route calculation
- **Google Air Quality API**: AQI data
- **OpenStreetMap**: Base map tiles

---

## 📊 **Performance Metrics**

### **API Response Time**
- Target: 3-8 seconds
- Current: 30-40 seconds (too slow)
- Bottleneck: Multiple AQI API calls

### **Cache Efficiency**
- Hit Rate: 60-80%
- Reduction in API calls: Significant
- Cache Size: Dynamic based on usage

### **Route Processing**
- Max Routes: 3 alternatives
- Sampling Points: 3-15 per route
- Scoring Algorithm: Exponential exposure

---

## 🎨 **UI/UX Current State**

### **Strengths**
- Interactive map with hover effects
- Real-time route calculation
- Responsive design
- Color-coded routes

### **Weaknesses**
- Comparison-focused instead of route-focused
- No clear route branching visualization
- Error handling not user-friendly
- Loading states need improvement

---

## 🔄 **Data Flow Diagram**

```
User Input (Start/End Points)
    ↓
Frontend (app.js)
    ↓
Backend API (api.py)
    ↓
Enhanced Service (enhanced_aqi_service.py)
    ↓
Google Routes API → 3 Alternative Routes
    ↓
Dynamic AQI Sampling → Air Quality API
    ↓
Exposure Scoring & Analysis
    ↓
Route Classification (Fast/Clean/Alternative)
    ↓
Frontend Display (map.js + app.js)
    ↓
User Interaction & Selection
```

---

## 🚀 **Recommendations for Improvement**

### **Immediate Fixes**
1. **Debug API Error**: Check network connectivity and API key
2. **Fix Multi-Route Display**: Ensure all routes render correctly
3. **Update UI Design**: Change from comparison to individual route cards
4. **Add Error Handling**: Better user feedback for failures

### **Enhanced Features**
1. **Route Branching Visualization**: Show routes diverging from start point
2. **Real-time Updates**: Live AQI updates during travel
3. **Route Preferences**: User-weighted routing (time vs. air quality)
4. **Historical Data**: Route quality trends over time

### **Performance Optimizations**
1. **Parallel API Calls**: Concurrent AQI sampling
2. **Predictive Caching**: Cache likely routes in advance
3. **Compression**: Reduce response payload sizes
4. **CDN Integration**: Faster static asset delivery

---

## 📈 **Success Metrics**

### **Technical Metrics**
- API Response Time < 5 seconds
- Cache Hit Rate > 80%
- Zero API errors in production
- All routes displaying correctly

### **User Experience Metrics**
- Route selection time < 10 seconds
- User satisfaction with route options
- Mobile responsiveness score
- Error recovery success rate

---

## 🎯 **Next Implementation Phase**

The system needs immediate fixes for:
1. API error resolution
2. Multi-route display correction
3. UI redesign for route cards
4. Enhanced error handling

These fixes will transform the system from a proof-of-concept to a production-ready application.
