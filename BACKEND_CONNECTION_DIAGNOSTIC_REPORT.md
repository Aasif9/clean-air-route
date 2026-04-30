# Backend Connection Diagnostic Report
**Generated:** April 28, 2026  
**Issue:** `/health` endpoint returning 404 Not Found on Render  
**URL:** https://kolkata-clean-air-route.onrender.com/health

---

## Executive Summary

The backend is returning 404 errors because the **Procfile configuration is incorrect**. The root-level Procfile attempts to run `gunicorn api:app`, but the Flask application (`api.py`) is located in the `backend/` subdirectory, not at the root level.

---

## Root Cause Analysis

### 1. **Procfile Mismatch (CRITICAL)**

**Root Procfile (`/Procfile`):**
```procfile
web: gunicorn api:app --host 0.0.0.0 --port $PORT
```

**Problem:** This command tries to import `api` from the root directory, but `api.py` only exists in `backend/`.

**Backend Procfile (`/backend/Procfile`):**
```procfile
web: gunicorn api:app --host 0.0.0.0 --port $PORT
```

**Status:** This is correct for the backend directory, but Render may be using the root Procfile.

---

### 2. **Health Endpoint Implementation**

**File:** `backend/api.py` (Lines 25-45)

```python
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint to test PostgreSQL connection"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({
            "success": True,
            "status": "healthy",
            "database": "connected"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }), 500
```

**Status:** ✅ Endpoint exists and is correctly implemented

---

### 3. **Database Connection Code**

**File:** `backend/db.py` (Full file)

```python
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Get a database connection with SSL for Render PostgreSQL"""
    try:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL not set in environment variables")
        
        print(f"Connecting to database: {database_url[:20]}...")  # Print first 20 chars for debugging
        
        conn = psycopg2.connect(database_url, sslmode='require')
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise

def test_connection():
    """Test database connection"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.fetchone()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False
```

**Status:** ✅ Connection code is correct with SSL enabled

---

### 4. **Environment Variable Configuration**

**File:** `backend/.env`

```env
# Google Maps API Key
Maps_API_KEY=AIzaSyCzMoywDG3r8V_tPln24w-vRv6Y6_i85Hw

# PostgreSQL Database URL (Render)
DATABASE_URL=postgresql://clean_air_route_db_user:IuWaWbxrONoHlljztOVXt8ljXkAe0CE5@dpg-d7n4m2pf9bms738aplcg-a.singapore-postgres.render.com/clean_air_route_db
```

**Status:** ⚠️ DATABASE_URL is set locally, but **must be added to Render environment variables**

**File:** `database/.env.example`

```env
# Database Configuration
DATABASE_URL=postgresql://clean_air_route_db_user:IuWaWbxrONoHlljztOVXt8ljXkAe0CE5@dpg-d7n4m2pf9bms738aplcg-a.singapore-postgres.render.com/clean_air_route_db

# Environment
NODE_ENV=development

# Server Port
PORT=3000
```

**Status:** ⚠️ This is for Node.js, not Python backend

---

### 5. **PostgreSQL Integration Points**

All PostgreSQL-related code in the backend:

#### A. **Database Connection** (`backend/db.py`)
- Uses `psycopg2` for PostgreSQL connectivity
- SSL mode: `require` (required for Render)
- Environment variable: `DATABASE_URL`

#### B. **Health Check** (`backend/api.py`, lines 25-45)
- Tests database connectivity
- Returns JSON with connection status

#### C. **Save Routes Endpoint** (`backend/api.py`, lines 152-258)
```python
@app.route('/save-routes', methods=['POST'])
def save_routes():
    """Save multiple routes to PostgreSQL with PostGIS geometry"""
    # Uses get_db_connection()
    # Inserts into route_batches and routes tables
    # Converts coordinates to PostGIS LINESTRING
```

#### D. **Fetch Routes Endpoint** (`backend/api.py`, lines 260-324)
```python
@app.route('/routes', methods=['GET'])
def get_routes():
    """Fetch routes from PostgreSQL with optional filters"""
    # Uses RealDictCursor for JSON-friendly results
    # Supports filtering by AQI, distance, batch_id
```

#### E. **Export GeoJSON Endpoint** (`backend/api.py`, lines 326-374)
```python
@app.route('/export/geojson', methods=['GET'])
def export_geojson():
    """Export all routes as GeoJSON"""
    # Uses ST_AsGeoJSON for PostGIS geometry conversion
```

#### F. **Database Schema** (`database/schema.sql`)
```sql
-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create routes table with PostGIS geometry
CREATE TABLE IF NOT EXISTS routes (
    id SERIAL PRIMARY KEY,
    route_number INTEGER NOT NULL,
    route_type VARCHAR(50) NOT NULL,
    distance_km DECIMAL(10, 2) NOT NULL,
    travel_time_min DECIMAL(10, 2) NOT NULL,
    avg_aqi DECIMAL(5, 2) NOT NULL,
    max_aqi INTEGER NOT NULL,
    min_aqi INTEGER NOT NULL,
    exposure_score DECIMAL(12, 2) NOT NULL,
    sample_points_count INTEGER NOT NULL,
    node_count INTEGER NOT NULL,
    geometry GEOMETRY(LINESTRING, 4326) NOT NULL,
    start_lat DECIMAL(10, 6),
    start_lon DECIMAL(10, 6),
    end_lat DECIMAL(10, 6),
    end_lon DECIMAL(10, 6),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create route_batches table
CREATE TABLE IF NOT EXISTS route_batches (
    id SERIAL PRIMARY KEY,
    batch_id UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
    total_routes INTEGER NOT NULL,
    data_source VARCHAR(100),
    cache_size INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### G. **Dependencies** (`requirements.txt`)
```
psycopg2-binary==2.9.9
```

---

## Issues Identified

### Critical Issues

1. **Procfile Configuration Error**
   - Root Procfile points to non-existent `api.py`
   - Render may be deploying from root instead of `backend/` directory
   - **Fix:** Update root Procfile or configure Render to use `backend/` directory

2. **Environment Variables Not Set in Render**
   - `DATABASE_URL` exists in local `.env` but not in Render dashboard
   - `Maps_API_KEY` also needs to be added to Render
   - **Fix:** Add these variables in Render web service settings

### Secondary Issues

3. **Inconsistent Port Configuration**
   - Backend uses port 5002 locally
   - Render uses `$PORT` environment variable
   - This is actually correct for Render, but worth noting

4. **Multiple .env Files**
   - `backend/.env` (Python backend)
   - `database/.env.example` (Node.js - outdated)
   - **Recommendation:** Remove or update `database/.env.example`

---

## Recommended Fixes

### Fix 1: Update Root Procfile

**Option A:** Update root Procfile to run from backend directory
```procfile
web: cd backend && gunicorn api:app --host 0.0.0.0 --port $PORT
```

**Option B:** Configure Render to use `backend/` as root directory
- In Render dashboard, set "Root Directory" to `backend`
- Keep Procfile as: `web: gunicorn api:app --host 0.0.0.0 --port $PORT`

### Fix 2: Add Environment Variables to Render

In your Render web service dashboard, add these environment variables:

1. **DATABASE_URL**
   ```
   postgresql://clean_air_route_db_user:IuWaWbxrONoHlljztOVXt8ljXkAe0CE5@dpg-d7n4m2pf9bms738aplcg-a.singapore-postgres.render.com/clean_air_route_db
   ```

2. **Maps_API_KEY**
   ```
   AIzaSyCzMoywDG3r8V_tPln24w-vRv6Y6_i85Hw
   ```

3. **PORT**
   ```
   5002
   ```

### Fix 3: Verify Database Schema

Connect to your Render PostgreSQL database and run:

```sql
-- Check if PostGIS is enabled
SELECT PostGIS_Version();

-- Check if tables exist
\dt

-- If tables don't exist, run the schema
-- Copy contents of database/schema.sql and execute
```

---

## Complete PostgreSQL Integration Code Reference

### 1. Database Connection Module
**File:** `backend/db.py`

```python
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Get a database connection with SSL for Render PostgreSQL"""
    try:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL not set in environment variables")
        
        print(f"Connecting to database: {database_url[:20]}...")
        
        conn = psycopg2.connect(database_url, sslmode='require')
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise

def test_connection():
    """Test database connection"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.fetchone()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False
```

### 2. API Endpoints Using PostgreSQL
**File:** `backend/api.py`

**Health Check (Lines 25-45):**
```python
@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint to test PostgreSQL connection"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({
            "success": True,
            "status": "healthy",
            "database": "connected"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }), 500
```

**Save Routes (Lines 152-258):**
```python
@app.route('/save-routes', methods=['POST'])
def save_routes():
    """Save multiple routes to PostgreSQL with PostGIS geometry"""
    try:
        data = request.get_json()
        
        if not data or 'routes' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing routes data'
            }), 400
        
        routes = data['routes']
        batch_id = str(uuid.uuid4())
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Insert batch record
        cur.execute("""
            INSERT INTO route_batches (batch_id, data_source, start_lat, start_lon, end_lat, end_lon, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            RETURNING id
        """, (
            batch_id,
            data.get('data_source', 'unknown'),
            data.get('start_lat'),
            data.get('start_lon'),
            data.get('end_lat'),
            data.get('end_lon')
        ))
        
        batch_db_id = cur.fetchone()[0]
        
        # Insert each route with PostGIS geometry
        saved_routes = []
        for route in routes:
            coordinates = route.get('coordinates', [])
            if coordinates and len(coordinates) >= 2:
                coord_pairs = []
                for coord in coordinates:
                    lon = float(coord[1])
                    lat = float(coord[0])
                    coord_pairs.append(f"{lon:.6f} {lat:.6f}")
                coord_string = ', '.join(coord_pairs)
                linestring = f"LINESTRING({coord_string})"
            else:
                linestring = None
            
            analysis = route.get('analysis', {})
            
            cur.execute("""
                INSERT INTO routes (
                    route_number,
                    route_type,
                    total_distance_km,
                    total_travel_time_min,
                    average_aqi,
                    max_aqi,
                    min_aqi,
                    exposure_score,
                    geometry,
                    batch_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, ST_GeomFromText(%s, 4326), %s)
                RETURNING id
            """, (
                route.get('route_number'),
                route.get('route_type'),
                analysis.get('total_distance_km'),
                analysis.get('total_travel_time_min'),
                analysis.get('average_aqi'),
                analysis.get('max_aqi'),
                analysis.get('min_aqi'),
                analysis.get('exposure_score'),
                linestring,
                batch_id
            ))
            
            route_id = cur.fetchone()[0]
            saved_routes.append({
                'id': route_id,
                'route_number': route.get('route_number'),
                'route_type': route.get('route_type')
            })
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'batch_id': batch_id,
            'batch_db_id': batch_db_id,
            'routes_saved': len(saved_routes),
            'routes': saved_routes
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

**Fetch Routes (Lines 260-324):**
```python
@app.route('/routes', methods=['GET'])
def get_routes():
    """Fetch routes from PostgreSQL with optional filters"""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        min_aqi = request.args.get('min_aqi', type=float)
        max_aqi = request.args.get('max_aqi', type=float)
        min_distance = request.args.get('min_distance', type=float)
        max_distance = request.args.get('max_distance', type=float)
        batch_id = request.args.get('batch_id')
        
        query = """
            SELECT id, route_number, route_type, total_distance_km,
                   total_travel_time_min, average_aqi, max_aqi, min_aqi,
                   exposure_score, batch_id, created_at,
                   ST_AsText(geometry) as geometry_text
            FROM routes
            WHERE 1=1
        """
        params = []
        
        if min_aqi is not None:
            query += " AND average_aqi >= %s"
            params.append(min_aqi)
        
        if max_aqi is not None:
            query += " AND average_aqi <= %s"
            params.append(max_aqi)
        
        if min_distance is not None:
            query += " AND total_distance_km >= %s"
            params.append(min_distance)
        
        if max_distance is not None:
            query += " AND total_distance_km <= %s"
            params.append(max_distance)
        
        if batch_id:
            query += " AND batch_id = %s"
            params.append(batch_id)
        
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(query, params)
        routes = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'routes': routes,
            'count': len(routes)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

**Export GeoJSON (Lines 326-374):**
```python
@app.route('/export/geojson', methods=['GET'])
def export_geojson():
    """Export all routes as GeoJSON"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT id, route_number, route_type, total_distance_km,
                   total_travel_time_min, average_aqi, max_aqi, min_aqi,
                   exposure_score, ST_AsGeoJSON(geometry) as geometry
            FROM routes
            WHERE geometry IS NOT NULL
        """)
        
        routes = cur.fetchall()
        cur.close()
        conn.close()
        
        features = []
        for route in routes:
            features.append({
                'type': 'Feature',
                'properties': {
                    'id': route['id'],
                    'route_number': route['route_number'],
                    'route_type': route['route_type'],
                    'total_distance_km': route['total_distance_km'],
                    'total_travel_time_min': route['total_travel_time_min'],
                    'average_aqi': route['average_aqi'],
                    'max_aqi': route['max_aqi'],
                    'min_aqi': route['min_aqi'],
                    'exposure_score': route['exposure_score']
                },
                'geometry': route['geometry']
            })
        
        geojson = {
            'type': 'FeatureCollection',
            'features': features
        }
        
        return jsonify(geojson)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

### 3. Database Schema
**File:** `database/schema.sql`

```sql
-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create routes table
CREATE TABLE IF NOT EXISTS routes (
    id SERIAL PRIMARY KEY,
    route_number INTEGER NOT NULL,
    route_type VARCHAR(50) NOT NULL,
    distance_km DECIMAL(10, 2) NOT NULL,
    travel_time_min DECIMAL(10, 2) NOT NULL,
    avg_aqi DECIMAL(5, 2) NOT NULL,
    max_aqi INTEGER NOT NULL,
    min_aqi INTEGER NOT NULL,
    exposure_score DECIMAL(12, 2) NOT NULL,
    sample_points_count INTEGER NOT NULL,
    node_count INTEGER NOT NULL,
    geometry GEOMETRY(LINESTRING, 4326) NOT NULL,
    start_lat DECIMAL(10, 6),
    start_lon DECIMAL(10, 6),
    end_lat DECIMAL(10, 6),
    end_lon DECIMAL(10, 6),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create spatial index
CREATE INDEX IF NOT EXISTS idx_routes_geometry ON routes USING GIST (geometry);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_routes_avg_aqi ON routes (avg_aqi);
CREATE INDEX IF NOT EXISTS idx_routes_distance ON routes (distance_km);
CREATE INDEX IF NOT EXISTS idx_routes_created_at ON routes (created_at);

-- Create route_batches table
CREATE TABLE IF NOT EXISTS route_batches (
    id SERIAL PRIMARY KEY,
    batch_id UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
    total_routes INTEGER NOT NULL,
    data_source VARCHAR(100),
    cache_size INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add foreign key to routes table
ALTER TABLE routes ADD COLUMN IF NOT EXISTS batch_id UUID REFERENCES route_batches(batch_id) ON DELETE CASCADE;

-- Create index on batch_id
CREATE INDEX IF NOT EXISTS idx_routes_batch_id ON routes (batch_id);
```

### 4. Dependencies
**File:** `requirements.txt`

```
Flask==3.0.0
Flask-CORS==4.0.0
python-dotenv==1.0.0
requests==2.31.0
polyline==2.0.0
gunicorn==21.2.0
supabase==2.3.0
psycopg2-binary==2.9.9
```

---

## Next Steps

1. **Immediate Fix:** Update Procfile configuration (Fix 1)
2. **Add Environment Variables:** Add DATABASE_URL and Maps_API_KEY to Render dashboard (Fix 2)
3. **Verify Database:** Run schema.sql on Render PostgreSQL (Fix 3)
4. **Redeploy:** Push changes and trigger new Render deployment
5. **Test:** Verify `/health` endpoint returns proper response

---

## Expected Working State

After fixes, visiting `https://kolkata-clean-air-route.onrender.com/health` should return:

```json
{
  "success": true,
  "status": "healthy",
  "database": "connected"
}
```

And the following endpoints should work:
- `/routes/clean` - Get cleanest route
- `/routes/multi` - Get multiple routes
- `/save-routes` - Save routes to PostgreSQL
- `/routes` - Fetch saved routes
- `/export/geojson` - Export as GeoJSON
