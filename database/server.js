require('dotenv').config();
const express = require('express');
const { Pool } = require('pg');
const cors = require('cors');
const Joi = require('joi');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json({ limit: '10mb' }));

// PostgreSQL connection
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});

// Test database connection
pool.on('connect', () => {
  console.log('✅ Connected to PostgreSQL database');
});

pool.on('error', (err) => {
  console.error('❌ Unexpected error on idle client', err);
  process.exit(-1);
});

// Validation schema for route data
const routeSchema = Joi.object({
  route_number: Joi.number().integer().required(),
  route_type: Joi.string().required(),
  analysis: Joi.object({
    average_aqi: Joi.number().required(),
    exposure_score: Joi.number().required(),
    max_aqi: Joi.number().integer().required(),
    min_aqi: Joi.number().integer().required(),
    sample_points_count: Joi.number().integer().required(),
    total_distance_km: Joi.number().required(),
    total_travel_time_min: Joi.number().required()
  }).required(),
  coordinates: Joi.array().items(
    Joi.array().items(Joi.number()).length(2)
  ).min(2).required(),
  node_count: Joi.number().integer().required()
});

const saveRoutesSchema = Joi.object({
  routes: Joi.array().items(routeSchema).min(1).required(),
  data_source: Joi.string().optional(),
  cache_stats: Joi.object({
    cache_size: Joi.number().integer().optional()
  }).optional(),
  start_lat: Joi.number().optional(),
  start_lon: Joi.number().optional(),
  end_lat: Joi.number().optional(),
  end_lon: Joi.number().optional()
});

/**
 * Convert coordinates array to PostGIS LINESTRING format
 * @param {Array} coordinates - Array of [lat, lng] pairs
 * @returns {String} LINESTRING in WKT format
 */
function coordsToLineString(coordinates) {
  // PostGIS expects: LINESTRING(lng1 lat1, lng2 lat2, ...)
  // Note: order is longitude first, then latitude
  return `LINESTRING(${coordinates.map(c => `${c[1]} ${c[0]}`).join(', ')})`;
}

/**
 * Validate coordinates are within valid ranges
 */
function validateCoordinates(lat, lon) {
  if (lat < -90 || lat > 90) return false;
  if (lon < -180 || lon > 180) return false;
  return true;
}

/**
 * POST /save-routes
 * Save multiple routes to the database
 */
app.post('/save-routes', async (req, res) => {
  const client = await pool.connect();
  
  try {
    // Validate request body
    const { error, value } = saveRoutesSchema.validate(req.body);
    if (error) {
      return res.status(400).json({
        success: false,
        error: 'Validation error',
        details: error.details
      });
    }

    const { routes, data_source, cache_stats, start_lat, start_lon, end_lat, end_lon } = value;

    // Validate start/end coordinates if provided
    if (start_lat && !validateCoordinates(start_lat, start_lon)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid start coordinates'
      });
    }
    if (end_lat && !validateCoordinates(end_lat, end_lon)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid end coordinates'
      });
    }

    await client.query('BEGIN');

    // Create a batch record
    const batchResult = await client.query(
      `INSERT INTO route_batches (total_routes, data_source, cache_size)
       VALUES ($1, $2, $3)
       RETURNING id, batch_id`,
      [routes.length, data_source || 'unknown', cache_stats?.cache_size || 0]
    );

    const { batch_id } = batchResult.rows[0];

    // Insert each route
    const insertedRoutes = [];
    for (const route of routes) {
      const { route_number, route_type, analysis, coordinates, node_count } = route;
      const lineString = coordsToLineString(coordinates);

      const result = await client.query(
        `INSERT INTO routes (
          route_number, route_type, distance_km, travel_time_min,
          avg_aqi, max_aqi, min_aqi, exposure_score, sample_points_count,
          node_count, geometry, batch_id, start_lat, start_lon, end_lat, end_lon
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
          ST_GeomFromText($11, 4326), $12, $13, $14, $15, $16)
        RETURNING id`,
        [
          route_number,
          route_type,
          analysis.total_distance_km,
          analysis.total_travel_time_min,
          analysis.average_aqi,
          analysis.max_aqi,
          analysis.min_aqi,
          analysis.exposure_score,
          analysis.sample_points_count,
          node_count,
          lineString,
          batch_id,
          start_lat,
          start_lon,
          end_lat,
          end_lon
        ]
      );

      insertedRoutes.push({
        id: result.rows[0].id,
        route_number,
        route_type
      });
    }

    await client.query('COMMIT');

    res.status(201).json({
      success: true,
      message: `Successfully saved ${routes.length} routes`,
      batch_id,
      routes: insertedRoutes
    });

  } catch (error) {
    await client.query('ROLLBACK');
    console.error('Error saving routes:', error);
    res.status(500).json({
      success: false,
      error: 'Database error',
      message: error.message
    });
  } finally {
    client.release();
  }
});

/**
 * GET /routes
 * Fetch stored routes with optional filters
 */
app.get('/routes', async (req, res) => {
  try {
    const {
      limit = 50,
      offset = 0,
      min_aqi,
      max_aqi,
      min_distance,
      max_distance,
      batch_id
    } = req.query;

    let query = `
      SELECT 
        id, route_number, route_type, distance_km, travel_time_min,
        avg_aqi, max_aqi, min_aqi, exposure_score, sample_points_count,
        node_count, batch_id, created_at,
        ST_AsGeoJSON(geometry) as geometry_geojson,
        start_lat, start_lon, end_lat, end_lon
      FROM routes
      WHERE 1=1
    `;
    
    const params = [];
    let paramIndex = 1;

    if (min_aqi) {
      query += ` AND avg_aqi >= $${paramIndex}`;
      params.push(min_aqi);
      paramIndex++;
    }

    if (max_aqi) {
      query += ` AND avg_aqi <= $${paramIndex}`;
      params.push(max_aqi);
      paramIndex++;
    }

    if (min_distance) {
      query += ` AND distance_km >= $${paramIndex}`;
      params.push(min_distance);
      paramIndex++;
    }

    if (max_distance) {
      query += ` AND distance_km <= $${paramIndex}`;
      params.push(max_distance);
      paramIndex++;
    }

    if (batch_id) {
      query += ` AND batch_id = $${paramIndex}`;
      params.push(batch_id);
      paramIndex++;
    }

    query += ` ORDER BY created_at DESC LIMIT $${paramIndex} OFFSET $${paramIndex + 1}`;
    params.push(parseInt(limit), parseInt(offset));

    const result = await pool.query(query, params);

    // Parse GeoJSON geometry
    const routes = result.rows.map(row => ({
      ...row,
      geometry: JSON.parse(row.geometry_geojson),
      geometry_geojson: undefined
    }));

    res.json({
      success: true,
      count: routes.length,
      routes
    });

  } catch (error) {
    console.error('Error fetching routes:', error);
    res.status(500).json({
      success: false,
      error: 'Database error',
      message: error.message
    });
  }
});

/**
 * GET /routes/:id
 * Fetch a single route by ID
 */
app.get('/routes/:id', async (req, res) => {
  try {
    const { id } = req.params;

    const result = await pool.query(
      `SELECT 
        id, route_number, route_type, distance_km, travel_time_min,
        avg_aqi, max_aqi, min_aqi, exposure_score, sample_points_count,
        node_count, batch_id, created_at,
        ST_AsGeoJSON(geometry) as geometry_geojson,
        start_lat, start_lon, end_lat, end_lon
      FROM routes
      WHERE id = $1`,
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        error: 'Route not found'
      });
    }

    const route = result.rows[0];
    route.geometry = JSON.parse(route.geometry_geojson);
    delete route.geometry_geojson;

    res.json({
      success: true,
      route
    });

  } catch (error) {
    console.error('Error fetching route:', error);
    res.status(500).json({
      success: false,
      error: 'Database error',
      message: error.message
    });
  }
});

/**
 * GET /export/json
 * Export all routes as JSON
 */
app.get('/export/json', async (req, res) => {
  try {
    const result = await pool.query(
      `SELECT 
        row_to_json(t) as route_json
      FROM (
        SELECT 
          id, route_number, route_type, distance_km, travel_time_min,
          avg_aqi, max_aqi, min_aqi, exposure_score, sample_points_count,
          node_count, batch_id, created_at,
          ST_AsGeoJSON(geometry) as geometry,
          start_lat, start_lon, end_lat, end_lon
        FROM routes
      ) t`
    );

    const routes = result.rows.map(row => {
      const route = row.route_json;
      route.geometry = JSON.parse(route.geometry);
      return route;
    });

    res.json({
      success: true,
      count: routes.length,
      routes
    });

  } catch (error) {
    console.error('Error exporting JSON:', error);
    res.status(500).json({
      success: false,
      error: 'Database error',
      message: error.message
    });
  }
});

/**
 * GET /export/geojson
 * Export all routes as GeoJSON FeatureCollection
 */
app.get('/export/geojson', async (req, res) => {
  try {
    const result = await pool.query(
      `SELECT 
        id, route_number, route_type, distance_km, travel_time_min,
        avg_aqi, max_aqi, min_aqi, exposure_score, sample_points_count,
        node_count, batch_id, created_at,
        ST_AsGeoJSON(geometry) as geometry,
        start_lat, start_lon, end_lat, end_lon
      FROM routes`
    );

    const features = result.rows.map(row => ({
      type: 'Feature',
      geometry: JSON.parse(row.geometry),
      properties: {
        id: row.id,
        route_number: row.route_number,
        route_type: row.route_type,
        distance_km: row.distance_km,
        travel_time_min: row.travel_time_min,
        avg_aqi: row.avg_aqi,
        max_aqi: row.max_aqi,
        min_aqi: row.min_aqi,
        exposure_score: row.exposure_score,
        sample_points_count: row.sample_points_count,
        node_count: row.node_count,
        batch_id: row.batch_id,
        created_at: row.created_at,
        start_lat: row.start_lat,
        start_lon: row.start_lon,
        end_lat: row.end_lat,
        end_lon: row.end_lon
      }
    }));

    const geojson = {
      type: 'FeatureCollection',
      features
    };

    res.json(geojson);

  } catch (error) {
    console.error('Error exporting GeoJSON:', error);
    res.status(500).json({
      success: false,
      error: 'Database error',
      message: error.message
    });
  }
});

/**
 * GET /export/csv
 * Export all routes as CSV
 */
app.get('/export/csv', async (req, res) => {
  try {
    const result = await pool.query(
      `SELECT 
        id, route_number, route_type, distance_km, travel_time_min,
        avg_aqi, max_aqi, min_aqi, exposure_score, sample_points_count,
        node_count, batch_id, created_at,
        start_lat, start_lon, end_lat, end_lon
      FROM routes`
    );

    if (result.rows.length === 0) {
      return res.status(404).json({
        success: false,
        error: 'No routes to export'
      });
    }

    // Convert to CSV
    const headers = Object.keys(result.rows[0]).join(',');
    const rows = result.rows.map(row => 
      Object.values(row).map(val => 
        typeof val === 'string' ? `"${val}"` : val
      ).join(',')
    );

    const csv = [headers, ...rows].join('\n');

    res.setHeader('Content-Type', 'text/csv');
    res.setHeader('Content-Disposition', 'attachment; filename=routes.csv');
    res.send(csv);

  } catch (error) {
    console.error('Error exporting CSV:', error);
    res.status(500).json({
      success: false,
      error: 'Database error',
      message: error.message
    });
  }
});

/**
 * GET /batches
 * Fetch all route batches
 */
app.get('/batches', async (req, res) => {
  try {
    const result = await pool.query(
      `SELECT 
        id, batch_id, total_routes, data_source, cache_size, created_at
      FROM route_batches
      ORDER BY created_at DESC`
    );

    res.json({
      success: true,
      count: result.rows.length,
      batches: result.rows
    });

  } catch (error) {
    console.error('Error fetching batches:', error);
    res.status(500).json({
      success: false,
      error: 'Database error',
      message: error.message
    });
  }
});

/**
 * GET /health
 * Health check endpoint
 */
app.get('/health', async (req, res) => {
  try {
    await pool.query('SELECT 1');
    res.json({
      success: true,
      status: 'healthy',
      database: 'connected'
    });
  } catch (error) {
    res.status(503).json({
      success: false,
      status: 'unhealthy',
      database: 'disconnected'
    });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
  console.log(`📊 Health check: http://localhost:${PORT}/health`);
});
