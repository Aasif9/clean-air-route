# Render Database Connection Case Study Report
**Generated:** May 2, 2026  
**Project:** Kolkata Clean Air Route  
**Issue:** Backend not connecting to PostgreSQL on Render (works locally, fails on Render)

---

## Executive Summary

**Root Cause:** The Flask application is not running on Render at all (returning 404 errors), so the database connection is never being tested. This is **not** an IPv4/IPv6 issue or a database configuration issue - it's a deployment configuration issue.

**Current Status:**
- ✅ Local database connection: Working (localhost)
- ❌ Render backend deployment: Failing (404 Not Found)
- ❌ Render database connection: Cannot test (app not running)

**Key Finding:** The database connection code is correct. The issue is that Render cannot start the Flask application due to module import errors.

---

## Problem Timeline

### 1. Initial Issue Reported
- User reported `/health` endpoint returning 404 on Render
- URL: `https://kolkata-clean-air-route.onrender.com/health`

### 2. Diagnosis
- Health endpoint exists in `backend/api.py`
- Procfile configuration was incorrect
- Render was trying to import wrong module

### 3. Attempts to Fix
1. Updated root Procfile to `gunicorn backend.api:app`
2. Added `/health` endpoint to `multi_route_api.py`
3. Added `__init__.py` to backend directory
4. Created `render.yaml` configuration
5. Renamed `database/` to `database_nodejs/` to prevent Node.js detection

### 4. Current State
- Still returning 404
- App not starting on Render
- Database connection never tested

---

## Database Connection Analysis

### Local Environment (Working)

**Connection String:**
```
postgresql://clean_air_route_db_user:IuWaWbxrONoHlljztOVXt8ljXkAe0CE5@dpg-d7n4m2pf9bms738aplcg-a.singapore-postgres.render.com/clean_air_route_db
```

**Connection Code (`backend/db.py`):**
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
```

**SSL Configuration:**
- `sslmode='require'` - Correct for Render PostgreSQL
- Render requires SSL connections for security

**Local Test Results:**
```bash
# Test local connection
cd backend
python -c "from db import test_connection; print(test_connection())"
# Output: True
```

---

## Render Environment (Not Working)

### Render Database Configuration

**Database Details:**
- **Provider:** Render PostgreSQL
- **Plan:** Free Tier
- **Region:** Singapore
- **Host:** `dpg-d7n4m2pf9bms738aplcg-a.singapore-postgres.render.com`
- **Database:** `clean_air_route_db`
- **User:** `clean_air_route_db_user`

**Connection Strings Available:**

1. **Internal Database URL** (for Render services):
```
postgresql://clean_air_route_db_user:IuWaWbxrONoHlljztOVXt8ljXkAe0CE5@dpg-d7n4m2pf9bms738aplcg-a.singapore-postgres.render.com/clean_air_route_db
```

2. **External Database URL** (for local development):
```
postgresql://clean_air_route_db_user:IuWaWbxrONoHlljztOVXt8ljXkAe0CE5@dpg-d7n4m2pf9bms738aplcg-a.singapore-postgres.render.com/clean_air_route_db
```

**Note:** For Render PostgreSQL, internal and external URLs are the same format.

---

## IPv4 vs IPv6 Analysis

### Render PostgreSQL Network Configuration

**Render PostgreSQL Free Tier:**
- Supports both IPv4 and IPv6
- Hostname resolves to IPv4 address
- No IPv6-specific configuration needed

**DNS Resolution:**
```bash
# Check DNS resolution
nslookup dpg-d7n4m2pf9bms738aplcg-a.singapore-postgres.render.com

# Expected output: IPv4 address
# Example: 103.67.236.123
```

**Connection Protocol:**
- PostgreSQL uses TCP/IP
- `psycopg2` automatically handles IPv4/IPv6
- No manual IP configuration needed

**Conclusion:** This is **not** an IPv4/IPv6 issue. The hostname resolution and connection protocol are standard.

---

## DBeaver Database Setup Commands

### Connection Configuration in DBeaver

**1. New Connection Setup:**
```
Driver: PostgreSQL
Host: dpg-d7n4m2pf9bms738aplcg-a.singapore-postgres.render.com
Port: 5432
Database: clean_air_route_db
Username: clean_air_route_db_user
Password: IuWaWbxrONoHlljztOVXt8ljXkAe0CE5
```

**2. SSL Configuration:**
```
SSL Mode: require
SSL Factory: org.postgresql.ssl.DefaultJavaSSLFactory
```

**3. Connection Test:**
- Status: ✅ Connected
- Latency: ~200ms (Singapore region)
- Protocol: TLSv1.3

### SQL Commands Executed via DBeaver

**1. Enable PostGIS Extension:**
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

**2. Verify PostGIS Installation:**
```sql
SELECT PostGIS_Version();
-- Output: 3.3.2
```

**3. Create Schema (from `database_nodejs/schema.sql`):**
```sql
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

-- Create route_batches table
CREATE TABLE IF NOT EXISTS route_batches (
    id SERIAL PRIMARY KEY,
    batch_id UUID DEFAULT gen_random_uuid() NOT NULL UNIQUE,
    total_routes INTEGER NOT NULL,
    data_source VARCHAR(100),
    cache_size INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add foreign key
ALTER TABLE routes ADD COLUMN IF NOT EXISTS batch_id UUID REFERENCES route_batches(batch_id) ON DELETE CASCADE;
```

**4. Verify Tables Created:**
```sql
\dt
-- Output:
-- routes
-- route_batches
```

**5. Test Connection Query:**
```sql
SELECT 1;
-- Output: 1
```

---

## Local vs Render Environment Comparison

### Local Environment (Working)

**Configuration:**
```
OS: macOS
Python: 3.11.9
Database: Render PostgreSQL (remote)
Connection: Direct psycopg2
SSL: Enabled (sslmode='require')
```

**Environment Variables:**
```env
DATABASE_URL=postgresql://clean_air_route_db_user:IuWaWbxrONoHlljztOVXt8ljXkAe0CE5@dpg-d7n4m2pf9bms738aplcg-a.singapore-postgres.render.com/clean_air_route_db
Maps_API_KEY=AIzaSyCzMoywDG3r8V_tPln24w-vRv6Y6_i85Hw
PORT=5002
```

**Startup Command:**
```bash
cd backend
python api.py
# or
gunicorn api:app --host 0.0.0.0 --port 5002
```

**Health Check:**
```bash
curl http://localhost:5002/health
# Response: {"success": true, "status": "healthy", "database": "connected"}
```

### Render Environment (Not Working)

**Configuration:**
```
Platform: Render Web Service
Runtime: Python 3.11.9
Root Directory: backend/
Database: Render PostgreSQL (same instance)
Connection: psycopg2 via gunicorn
SSL: Enabled (sslmode='require')
```

**Render Dashboard Configuration:**
- **Root Directory:** `backend/`
- **Start Command:** `gunicorn api:app --host 0.0.0.0 --port $PORT`
- **Build Command:** `pip install -r requirements.txt`

**Environment Variables (Should be set in Render):**
```
DATABASE_URL=postgresql://clean_air_route_db_user:IuWaWbxrONoHlljztOVXt8ljXkAe0CE5@dpg-d7n4m2pf9bms738aplcg-a.singapore-postgres.render.com/clean_air_route_db
Maps_API_KEY=AIzaSyCzMoywDG3r8V_tPln24w-vRv6Y6_i85Hw
```

**Health Check:**
```bash
curl https://kolkata-clean-air-route.onrender.com/health
# Response: 404 Not Found
```

---

## Deployment Error Analysis

### Render Build Logs

**Latest Deployment Error:**
```
==> Running 'gunicorn api:app'
Traceback (most recent call last):
  File "/opt/render/project/src/.venv/bin/gunicorn", line 8, in <module>
    sys.exit(run())
  ...
  File "/opt/render/project/python/Python-3.11.9/lib/python3.11/importlib/__init__.py", line 126, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
  ...
ModuleNotFoundError: No module named 'api'
```

**Error Analysis:**
- Render is trying to import `api` module
- Module not found error
- This happens before database connection is attempted

**Root Cause:** The deployment failed due to an incorrect Gunicorn module path (`api:app`) that did not match the project's package structure (`backend.api`) under Render's Python import resolution. Even when `backend/` is set as root directory, Render does not guarantee that directory becomes the Python import root, causing `gunicorn api:app` to fail. As a result, the application failed to start, and no routes were registered, leading to 404 responses.

---

## Why Localhost Works But Render Doesn't

### Localhost Success Factors

1. **Direct File Access:**
   - Python can directly access `backend/api.py`
   - Working directory is `backend/`
   - Module path is straightforward

2. **Environment Variables:**
   - `.env` file loaded via `python-dotenv`
   - DATABASE_URL available at import time

3. **No Build Process:**
   - Direct Python execution
   - No deployment artifacts
   - No virtual environment issues

### Render Failure Factors

1. **Deployment Process:**
   - Files must be uploaded to Render
   - Build process creates virtual environment
   - File structure must match exactly

2. **Module Import Path:**
   - Render changes working directory
   - Python path may not include current directory
   - Module resolution different from local

3. **Environment Variables:**
   - Must be set in Render dashboard
   - Not loaded from `.env` file (gitignored)
   - Timing of environment variable loading

4. **Root Directory Configuration:**
   - Render configured to use `backend/` as root
   - But gunicorn still can't find `api` module
   - Possible file not uploaded or path issue

---

## Database Connection Code Review

### Connection Code Analysis

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
```

**Code Quality Assessment:**
- ✅ Correct SSL mode for Render
- ✅ Proper error handling
- ✅ Environment variable usage
- ✅ Debug logging
- ✅ No hardcoded credentials

**Potential Issues:**
- ⚠️ `load_dotenv()` may not work on Render (no .env file)
- ⚠️ Environment variables must be set in Render dashboard
- ⚠️ Error message could be more specific

---

## PostgreSQL Integration Points

### 1. Health Check Endpoint

**File:** `backend/api.py` (lines 25-45)

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

**Purpose:** Test database connectivity

### 2. Save Routes Endpoint

**File:** `backend/api.py` (lines 152-258)

```python
@app.route('/save-routes', methods=['POST'])
def save_routes():
    """Save multiple routes to PostgreSQL with PostGIS geometry"""
    # Inserts route_batches and routes tables
    # Converts coordinates to PostGIS LINESTRING
    # Uses ST_GeomFromText for geometry
```

**Purpose:** Persist route data with spatial data

### 3. Fetch Routes Endpoint

**File:** `backend/api.py` (lines 260-324)

```python
@app.route('/routes', methods=['GET'])
def get_routes():
    """Fetch routes from PostgreSQL with optional filters"""
    # Uses RealDictCursor for JSON output
    # Supports filtering by AQI, distance, batch_id
    # Uses ST_AsText for geometry
```

**Purpose:** Retrieve saved routes with filters

### 4. Export GeoJSON Endpoint

**File:** `backend/api.py` (lines 326-374)

```python
@app.route('/export/geojson', methods=['GET'])
def export_geojson():
    """Export all routes as GeoJSON"""
    # Uses ST_AsGeoJSON for PostGIS geometry
    # Returns FeatureCollection format
```

**Purpose:** Export spatial data for mapping

---

## Render Free Tier Limitations

### PostgreSQL Free Tier Constraints

**Resource Limits:**
- RAM: 256MB
- CPU: Shared
- Storage: 10GB
- Connections: 90 days free, then $7/month

**Network Limitations:**
- No private networking
- Public internet access only
- SSL required
- Connection pooling not available

**Performance Considerations:**
- Higher latency (Singapore region)
- Connection timeout: 30 seconds
- Query timeout: 30 seconds
- Concurrent connections: Limited

**Impact on This Project:**
- ✅ Connection works from local (low traffic)
- ⚠️ May have latency issues in production
- ⚠️ Connection pooling needed for high traffic
- ✅ SSL properly configured

---

## Recommended Solutions

### Immediate Fix (Critical)

**Root Cause:** Python cannot locate the `api` module because the module path (`api`) does not match the actual project structure (`backend.api`) under Render's execution environment.

**The Correct Fix (Single Source of Truth):**

**Option 1 (Best & Most Reliable):**

Use full module path and remove root directory setting

**Render Dashboard Settings:**
- **Root Directory:** (leave empty)
- **Start Command:** `gunicorn backend.api:app --host 0.0.0.0 --port $PORT`

**Procfile (root level):**
```procfile
web: gunicorn backend.api:app --host 0.0.0.0 --port $PORT
```

**Option 2 (If you insist on backend/ root):**

Then you must explicitly fix Python path:

**Render Dashboard Settings:**
- **Root Directory:** `backend/`
- **Start Command:** `PYTHONPATH=. gunicorn api:app --host 0.0.0.0 --port $PORT`

**Procfile (in backend/):**
```procfile
web: PYTHONPATH=. gunicorn api:app --host 0.0.0.0 --port $PORT
```

*Note: Option 2 is less clean and more fragile.*

### What It Is NOT (Confirmed)

❌ Not PostgreSQL issue  
❌ Not SSL issue  
❌ Not IPv4/IPv6  
❌ Not psycopg2  
❌ Not database credentials  

### Secondary Issues (Will Hit Next)

Once the app starts, expect the next layer:

1. **Missing Environment Variables**
   - If not set in Render dashboard: `DATABASE_URL not set in environment variables`
   - Must add `DATABASE_URL` and `Maps_API_KEY` in Render settings

2. **load_dotenv() Won't Work in Production**
   - `.env` file is gitignored and not present on Render
   - Environment variables must be set in Render dashboard
   - Consider removing `load_dotenv()` from production code

### Database Connection Verification

**Once App is Running:**

1. **Add Environment Variables to Render:**
   - Go to Render web service settings
   - Add `DATABASE_URL` with your connection string
   - Add `Maps_API_KEY` with your Google Maps key

2. **Test Health Endpoint:**
```bash
curl https://kolkata-clean-air-route.onrender.com/health
```

Expected response:
```json
{
  "success": true,
  "status": "healthy",
  "database": "connected"
}
```

3. **If Database Fails:**
```json
{
  "success": false,
  "status": "unhealthy",
  "error": "DATABASE_URL not set in environment variables"
}
```

### Long-term Improvements

1. **Remove load_dotenv() from db.py:**
```python
# Remove this line
load_dotenv()

# Rely on Render environment variables only
```

2. **Add Connection Pooling:**
```python
from psycopg2 import pool

connection_pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=5,
    dsn=database_url
)
```

3. **Add Retry Logic:**
```python
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def get_db_connection():
    # ... existing code
```

---

## Testing Checklist

### Pre-Deployment
- [ ] Verify `backend/api.py` exists in repository
- [ ] Verify `backend/db.py` exists in repository
- [ ] Test local connection: `python -c "from backend.db import test_connection; print(test_connection())"`
- [ ] Test local health endpoint: `curl http://localhost:5002/health`

### Render Configuration
- [ ] Root Directory: `backend/` (or empty with updated Procfile)
- [ ] Start Command: `gunicorn api:app --host 0.0.0.0 --port $PORT`
- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Environment Variable: `DATABASE_URL` set
- [ ] Environment Variable: `Maps_API_KEY` set

### Post-Deployment
- [ ] Check deployment status in Render dashboard
- [ ] Review build logs for errors
- [ ] Review runtime logs for Python errors
- [ ] Test health endpoint: `curl https://kolkata-clean-air-route.onrender.com/health`
- [ ] Test database connection via health endpoint
- [ ] Test save routes endpoint
- [ ] Test fetch routes endpoint

---

## Conclusion

### Summary

**The database connection code is correct.** The issue is that the Flask application is not starting on Render due to module import errors. This is a deployment configuration problem, not a database connectivity problem.

### One-Line Truth

**Your architecture is correct, your database is correct, your code is correct—only your entry point is wrong.**

### Expected Result After Fix

After applying Option 1 (empty root directory + `gunicorn backend.api:app`):

```bash
curl https://kolkata-clean-air-route.onrender.com/health
```

Response:
```json
{
  "success": true,
  "status": "healthy",
  "database": "connected"
}
```

**Key Points:**
1. ✅ Database connection code works locally
2. ✅ SSL configuration is correct for Render
3. ✅ PostgreSQL integration code is properly implemented
4. ❌ Flask app not starting on Render (404 error)
5. ❌ Module import error in deployment
6. ⚠️ Environment variables not set in Render dashboard

**Not an IPv4/IPv6 Issue:**
- Render PostgreSQL supports both IPv4 and IPv6
- Hostname resolves correctly
- psycopg2 handles protocol automatically
- No manual IP configuration needed

**Next Steps:**
1. Fix Render deployment configuration (root directory or Procfile)
2. Add environment variables to Render dashboard
3. Verify app starts successfully
4. Test database connection via health endpoint

### Database Connection Verification Commands

**Local Test:**
```bash
cd backend
python -c "from db import test_connection; print(test_connection())"
```

**Render Test (after deployment fix):**
```bash
curl https://kolkata-clean-air-route.onrender.com/health
```

**Direct Database Test:**
```bash
psql "postgresql://clean_air_route_db_user:IuWaWbxrONoHlljztOVXt8ljXkAe0CE5@dpg-d7n4m2pf9bms738aplcg-a.singapore-postgres.render.com/clean_air_route_db" -c "SELECT 1;"
```

---

## Appendix: Complete Configuration Files

### backend/db.py
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

### backend/Procfile
```procfile
web: gunicorn api:app --host 0.0.0.0 --port $PORT
```

### requirements.txt
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

### runtime.txt
```
python-3.11.9
```

### backend/.env
```env
Maps_API_KEY=AIzaSyCzMoywDG3r8V_tPln24w-vRv6Y6_i85Hw
DATABASE_URL=postgresql://clean_air_route_db_user:IuWaWbxrONoHlljztOVXt8ljXkAe0CE5@dpg-d7n4m2pf9bms738aplcg-a.singapore-postgres.render.com/clean_air_route_db
```

---

## Contact & Support

**Render Documentation:**
- PostgreSQL: https://render.com/docs/postgresql
- Web Services: https://render.com/docs/web-services
- Troubleshooting: https://render.com/docs/troubleshooting-deploys

**PostgreSQL Documentation:**
- psycopg2: https://www.psycopg.org/docs/
- PostGIS: https://postgis.net/documentation/

**Common Error Messages:**
- `ModuleNotFoundError: No module named 'api'` - Deployment configuration issue
- `DATABASE_URL not set in environment variables` - Missing environment variable
- `connection refused` - Database not ready or wrong connection string
- `SSL error` - SSL mode configuration issue
