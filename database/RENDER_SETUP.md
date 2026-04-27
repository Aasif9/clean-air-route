# Render PostgreSQL Setup Guide

This guide will help you set up PostgreSQL with PostGIS on Render and connect it to your Flask backend.

## Step 1: Create PostgreSQL Database on Render

1. **Log in to Render** at [render.com](https://render.com)

2. **Create a new PostgreSQL database:**
   - Click "New +" in the dashboard
   - Select "PostgreSQL"
   - Choose a name (e.g., `clean-air-route-db`)
   - Select a region (choose closest to your backend)
   - Select a database plan:
     - **Free**: 90 days, then $7/month (good for development)
     - **Basic**: $7/month (recommended for production)
   - Click "Create Database"

3. **Wait for database to be ready:**
   - Render will provision the database (takes 1-2 minutes)
   - You'll see a "Ready" status when complete

## Step 2: Enable PostGIS Extension

1. **Connect to your database:**
   - Go to your PostgreSQL instance in Render
   - Click "Connect" button
   - Copy the "Internal Database URL" or "External Database URL"

2. **Connect using psql (terminal):**
   ```bash
   psql "postgresql://username:password@host:port/database"
   ```
   
   Or use the Render web shell:
   - Click "Shell" in your PostgreSQL dashboard
   - This opens a web-based terminal

3. **Enable PostGIS:**
   ```sql
   CREATE EXTENSION IF NOT EXISTS postgis;
   ```
   
4. **Verify PostGIS is installed:**
   ```sql
   SELECT PostGIS_Version();
   ```
   
   You should see version information like `3.3.2`

## Step 3: Run Schema Migration

1. **Copy the schema:**
   - Open `database/schema.sql` from your project
   - Copy the entire SQL content

2. **Run the schema in psql:**
   ```bash
   psql "postgresql://username:password@host:port/database" -f schema.sql
   ```
   
   Or paste the SQL directly into the Render web shell

3. **Verify tables were created:**
   ```sql
   \dt
   ```
   
   You should see:
   - `routes`
   - `route_batches`

4. **Verify PostGIS column:**
   ```sql
   \d routes
   ```
   
   Check that `geometry` column has type `geometry(LINESTRING,4326)`

## Step 4: Deploy Flask Backend to Render

### Option A: Deploy as a Web Service

1. **Create a new Web Service:**
   - Click "New +" in Render
   - Select "Web Service"
   - Connect your GitHub repository
   - Select the `backend` folder or root directory
   - Configure:
     - **Name**: `clean-air-route-api`
     - **Region**: Same as your database
     - **Branch**: `main`
     - **Runtime**: Python
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn api:app`

2. **Add Environment Variables:**
   - In your web service settings, add:
     - `DATABASE_URL`: Your PostgreSQL connection string
     - `Maps_API_KEY`: Your Google Maps API key
     - `PORT`: `5002`

3. **Deploy:**
   - Click "Create Web Service"
   - Render will build and deploy your backend

### Option B: Run Locally (Development)

1. **Install dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Create `.env` file:**
   ```env
   DATABASE_URL=postgresql://username:password@host:port/database
   Maps_API_KEY=YOUR_KEY_HERE
   PORT=5002
   ```

3. **Start the server:**
   ```bash
   python api.py
   ```

## Step 5: Get Your Database Connection String

1. **From Render Dashboard:**
   - Go to your PostgreSQL instance
   - Click "Connect"
   - Copy the "Internal Database URL" (for Render services)
   - Or copy "External Database URL" (for local development)

2. **Format:**
   ```
   postgresql://username:password@host:port/database
   ```

3. **Add to Environment Variables:**
   - For Render web service: Add in dashboard
   - For local: Add to `.env` file

## Step 6: Test the API

### Test Health Check
```bash
curl http://localhost:5002/health
# or for production:
curl https://your-app.onrender.com/health
```

Expected response:
```json
{
  "success": true,
  "status": "healthy",
  "database": "connected"
}
```

### Test Save Routes
```bash
curl -X POST http://localhost:5002/save-routes \
  -H "Content-Type: application/json" \
  -d '{
    "routes": [
      {
        "route_number": 1,
        "route_type": "route_1",
        "analysis": {
          "average_aqi": 68.0,
          "exposure_score": 35490.6,
          "max_aqi": 73,
          "min_aqi": 64,
          "sample_points_count": 7,
          "total_distance_km": 6.52,
          "total_travel_time_min": 21.4
        },
        "coordinates": [[22.59592,88.36487],[22.59583,88.36518]],
        "node_count": 64
      }
    ],
    "data_source": "google_multi_route",
    "start_lat": 22.59592,
    "start_lon": 88.36487,
    "end_lat": 22.55211,
    "end_lon": 88.36356
  }'
```

### Test Fetch Routes
```bash
curl http://localhost:5002/routes
```

### Test Export GeoJSON
```bash
curl http://localhost:5002/export/geojson > routes.geojson
```

## Step 7: Integrate with Your Frontend (Vercel)

### Add Save Function to Frontend

```javascript
async function saveRoutes(routeData) {
  try {
    const response = await fetch('http://localhost:5002/save-routes', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(routeData)
    });

    const result = await response.json();

    if (result.success) {
      console.log(`✅ Saved ${result.routes.length} routes`);
      console.log(`Batch ID: ${result.batch_id}`);
    } else {
      console.error('❌ Failed to save routes:', result.error);
    }

    return result;
  } catch (error) {
    console.error('Error saving routes:', error);
  }
}
```

### Call After Route Calculation

In your `calculateRoutes()` function in `frontend/index.html`:

```javascript
async calculateRoutes() {
  // ... existing code ...
  
  const data = await this.api.getMultiRoutes(startLat, startLon, endLat, endLon);
  
  // Save routes to database
  await saveRoutes({
    ...data,
    start_lat: startLat,
    start_lon: startLon,
    end_lat: endLat,
    end_lon: endLon
  });
  
  // ... rest of existing code ...
}
```

## API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/save-routes` | POST | Save multiple routes |
| `/routes` | GET | Fetch routes with filters |
| `/routes/:id` | GET | Fetch single route by ID |
| `/export/json` | GET | Export all routes as JSON |
| `/export/geojson` | GET | Export as GeoJSON |
| `/export/csv` | GET | Export as CSV |
| `/batches` | GET | Fetch all route batches |

## Query Parameters for `/routes`

- `limit`: Number of routes to return (default: 50)
- `offset`: Offset for pagination (default: 0)
- `min_aqi`: Filter by minimum average AQI
- `max_aqi`: Filter by maximum average AQI
- `min_distance`: Filter by minimum distance (km)
- `max_distance`: Filter by maximum distance (km)
- `batch_id`: Filter by batch ID

### Example Queries

```bash
# Get routes with AQI between 50 and 70
curl "https://your-app.onrender.com/routes?min_aqi=50&max_aqi=70"

# Get routes shorter than 10km
curl "https://your-app.onrender.com/routes?max_distance=10"

# Get routes from a specific batch
curl "https://your-app.onrender.com/routes?batch_id=abc-123"

# Pagination
curl "https://your-app.onrender.com/routes?limit=10&offset=20"
```

## Troubleshooting

### Connection Issues

**Error: "Connection refused"**
- Check DATABASE_URL is correct
- Verify database is in "Ready" state
- Ensure region matches between web service and database

**Error: "PostGIS extension not found"**
- Connect to database and run: `CREATE EXTENSION postgis;`
- Verify with: `SELECT PostGIS_Version();`

### SSL Issues

**Error: "self-signed certificate"**
- The backend handles this with: `ssl: { rejectUnauthorized: false }`
- For production, use a proper SSL certificate

### Permission Issues

**Error: "permission denied"**
- Check database user has CREATE, INSERT, SELECT permissions
- Grant permissions if needed:
  ```sql
  GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
  GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_user;
  ```

## Cost Considerations

### Render Pricing (as of 2024)

**PostgreSQL:**
- Free: 90 days, then $7/month
- Basic: $7/month (256MB RAM, 10GB storage)
- Standard: $20/month (1GB RAM, 25GB storage)

**Web Service:**
- Free: Not available for Node.js
- Starter: $7/month (512MB RAM, 0.1 CPU)
- Standard: $25/month (2GB RAM, 1 CPU)

**Estimated Monthly Cost:**
- Development: $7 (database only, local backend)
- Production: $14 (database + web service)

## Security Best Practices

1. **Never commit `.env` file** to Git
2. **Use environment variables** for sensitive data
3. **Enable SSL** for database connections
4. **Add rate limiting** to prevent abuse
5. **Validate all input** (already implemented with Joi)
6. **Use read-only users** for frontend queries

## Next Steps

1. ✅ Create PostgreSQL database on Render
2. ✅ Enable PostGIS extension
3. ✅ Run schema migration
4. ✅ Deploy Node.js backend
5. ✅ Test API endpoints
6. ✅ Integrate with frontend
7. 🔄 Add authentication (optional)
8. 🔄 Add analytics dashboard (optional)
9. 🔄 Set up automated backups (optional)

## Additional Resources

- [Render PostgreSQL Documentation](https://render.com/docs/postgresql)
- [PostGIS Documentation](https://postgis.net/documentation/)
- [Node.js pg Library](https://node-postgres.com/)
- [Express.js Documentation](https://expressjs.com/)
