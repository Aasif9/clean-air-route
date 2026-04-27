# Clean Air Route Database

PostgreSQL + PostGIS backend for storing and managing Clean Air Route data.

## Features

- ✅ Store routes with PostGIS LINESTRING geometry
- ✅ Save route analytics (AQI, distance, exposure score, etc.)
- ✅ Batch grouping for related routes
- ✅ RESTful API with validation
- ✅ Export to JSON, GeoJSON, and CSV
- ✅ Spatial indexing for fast geo queries
- ✅ Filter routes by AQI, distance, batch ID

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Set Up Database

Create a PostgreSQL database with PostGIS enabled:

```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

Run the schema:

```bash
psql -d your_database -f schema.sql
```

### 3. Configure Environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` with your database connection string:

```env
DATABASE_URL=postgresql://username:password@host:port/database
NODE_ENV=development
PORT=3000
```

### 4. Start the Server

```bash
npm start
```

For development with auto-reload:

```bash
npm run dev
```

## API Endpoints

### POST /save-routes

Save multiple routes to the database.

**Request Body:**
```json
{
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
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully saved 3 routes",
  "batch_id": "abc-123-def-456",
  "routes": [
    { "id": 1, "route_number": 1, "route_type": "route_1" }
  ]
}
```

### GET /routes

Fetch stored routes with optional filters.

**Query Parameters:**
- `limit`: Number of routes (default: 50)
- `offset`: Pagination offset (default: 0)
- `min_aqi`: Minimum average AQI
- `max_aqi`: Maximum average AQI
- `min_distance`: Minimum distance (km)
- `max_distance`: Maximum distance (km)
- `batch_id`: Filter by batch ID

**Example:**
```bash
curl "http://localhost:3000/routes?min_aqi=50&max_aqi=70&limit=10"
```

**Response:**
```json
{
  "success": true,
  "count": 10,
  "routes": [
    {
      "id": 1,
      "route_number": 1,
      "route_type": "route_1",
      "distance_km": 6.52,
      "travel_time_min": 21.4,
      "avg_aqi": 68.0,
      "max_aqi": 73,
      "min_aqi": 64,
      "exposure_score": 35490.6,
      "sample_points_count": 7,
      "node_count": 64,
      "batch_id": "abc-123",
      "created_at": "2024-04-26T00:00:00Z",
      "geometry": {
        "type": "LineString",
        "coordinates": [[88.36487, 22.59592], [88.36518, 22.59583]]
      }
    }
  ]
}
```

### GET /routes/:id

Fetch a single route by ID.

### GET /export/json

Export all routes as JSON.

### GET /export/geojson

Export all routes as GeoJSON FeatureCollection.

**Response:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [[88.36487, 22.59592], [88.36518, 22.59583]]
      },
      "properties": {
        "id": 1,
        "route_number": 1,
        "route_type": "route_1",
        "distance_km": 6.52,
        "avg_aqi": 68.0
      }
    }
  ]
}
```

### GET /export/csv

Export all routes as CSV file.

### GET /batches

Fetch all route batches.

### GET /health

Health check endpoint.

## Database Schema

### routes table

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| route_number | INTEGER | Route number (1, 2, 3) |
| route_type | VARCHAR(50) | Route type identifier |
| distance_km | DECIMAL | Distance in kilometers |
| travel_time_min | DECIMAL | Travel time in minutes |
| avg_aqi | DECIMAL | Average AQI |
| max_aqi | INTEGER | Maximum AQI |
| min_aqi | INTEGER | Minimum AQI |
| exposure_score | DECIMAL | Exposure score |
| sample_points_count | INTEGER | Number of AQI samples |
| node_count | INTEGER | Number of route nodes |
| geometry | GEOMETRY | PostGIS LINESTRING |
| batch_id | UUID | Foreign key to route_batches |
| start_lat | DECIMAL | Start latitude |
| start_lon | DECIMAL | Start longitude |
| end_lat | DECIMAL | End latitude |
| end_lon | DECIMAL | End longitude |
| created_at | TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

### route_batches table

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| batch_id | UUID | Unique batch identifier |
| total_routes | INTEGER | Number of routes in batch |
| data_source | VARCHAR(100) | Source of route data |
| cache_size | INTEGER | Cache size at time of request |
| created_at | TIMESTAMP | Creation timestamp |

## Deployment

### Render Deployment

See [RENDER_SETUP.md](./RENDER_SETUP.md) for detailed instructions.

1. Create PostgreSQL database on Render
2. Enable PostGIS extension
3. Run schema migration
4. Deploy Node.js backend as Web Service
5. Add DATABASE_URL environment variable

### Local Development

1. Install PostgreSQL with PostGIS
2. Create database: `createdb clean_air_routes`
3. Enable PostGIS: `psql -d clean_air_routes -c "CREATE EXTENSION postgis;"`
4. Run schema: `psql -d clean_air_routes -f schema.sql`
5. Configure `.env` file
6. Start server: `npm start`

## Integration with Frontend

Add this function to your frontend:

```javascript
async function saveRoutes(routeData) {
  const response = await fetch('https://your-api.onrender.com/save-routes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(routeData)
  });
  return await response.json();
}
```

Call it after route calculation:

```javascript
const data = await this.api.getMultiRoutes(startLat, startLon, endLat, endLon);
await saveRoutes({
  ...data,
  start_lat: startLat,
  start_lon: startLon,
  end_lat: endLat,
  end_lon: endLon
});
```

## Testing

### Test Health Check
```bash
curl http://localhost:3000/health
```

### Test Save Routes
```bash
curl -X POST http://localhost:3000/save-routes \
  -H "Content-Type: application/json" \
  -d @test-data.json
```

### Test Fetch Routes
```bash
curl http://localhost:3000/routes
```

### Test Export GeoJSON
```bash
curl http://localhost:3000/export/geojson > routes.geojson
```

## License

MIT
