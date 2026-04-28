from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import sys
import os
import uuid
from psycopg2.extras import RealDictCursor

# Add backend directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_aqi_service import find_best_routes as google_find_best_routes
from simple_multi_route import find_multi_routes
from db import get_db_connection

load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "Kolkata AQI Routing - Google Live API Version"

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

@app.route('/routes/clean')
def get_clean_route():
    """Get cleanest route between two points — now powered by Google APIs."""
    try:
        # Validate required parameters
        required_params = ['start_lat', 'start_lon', 'end_lat', 'end_lon']
        missing_params = [param for param in required_params if not request.args.get(param)]
        
        if missing_params:
            return jsonify({
                'error': f'Missing required parameters: {", ".join(missing_params)}',
                'example': '/routes/clean?start_lat=22.5726&start_lon=88.3639&end_lat=22.5958&end_lon=88.3697'
            }), 400
        
        start_lat = float(request.args.get('start_lat'))
        start_lon = float(request.args.get('start_lon'))
        end_lat = float(request.args.get('end_lat'))
        end_lon = float(request.args.get('end_lon'))
        # pollution_factor param kept for API compatibility but no longer used
        # — scoring is now handled by exponential formula in google_aqi_service.py

        result = google_find_best_routes(start_lat, start_lon, end_lat, end_lon)

        if "error" in result:
            return jsonify({'error': result["error"]}), 404

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/routes/multi')
def get_multi_routes():
    """Get multiple route options between two points and save to Supabase"""
    try:
        # Validate required parameters
        required_params = ['start_lat', 'start_lon', 'end_lat', 'end_lon']
        missing_params = [param for param in required_params if not request.args.get(param)]
        
        if missing_params:
            return jsonify({
                'error': f'Missing required parameters: {", ".join(missing_params)}',
                'example': '/routes/multi?start_lat=22.5726&start_lon=88.3639&end_lat=22.5958&end_lon=88.3697'
            }), 400
        
        start_lat = float(request.args.get('start_lat'))
        start_lon = float(request.args.get('start_lon'))
        end_lat = float(request.args.get('end_lat'))
        end_lon = float(request.args.get('end_lon'))
        
        # Get user_id from query parameter (for now, use a default)
        user_id = request.args.get('user_id', 'anonymous_user')
        
        print(f"[API] Received multi-route request: ({start_lat:.4f}, {start_lon:.4f}) → ({end_lat:.4f}, {end_lon:.4f})")
        
        result = find_multi_routes(start_lat, start_lon, end_lat, end_lon)
        
        if "error" in result:
            print(f"[API] Error: {result['error']}")
            return jsonify({'error': result["error"]}), 404
        
        print(f"[API] Returning {result['total_routes']} routes")
        
        # Automatically save routes to Supabase
        if result.get('routes') and user_id != 'anonymous_user':
            try:
                for i, route in enumerate(result['routes']):
                    route_data = {
                        'start_lat': start_lat,
                        'start_lon': start_lon,
                        'end_lat': end_lat,
                        'end_lon': end_lon,
                        'route_type': f"route_{i+1}",
                        **route
                    }
                    saved_route = supabase_service.save_route(user_id, route_data)
                    if saved_route:
                        print(f"[API] Saved route {i+1} to Supabase: {saved_route['id']}")
            except Exception as save_error:
                print(f"[API] Warning: Failed to save to Supabase: {save_error}")
        
        return jsonify(result)

    except Exception as e:
        print(f"[API] Exception: {e}")
        return jsonify({'error': str(e)}), 500

    

@app.route('/stations')
def get_stations():
    """Return placeholder for station compatibility"""
    return jsonify({
        'stations': [],
        'total_stations': 0,
        'aqi_range': [0, 0],
        'average_aqi': 0,
        'message': 'Using Google Live API - no fixed stations needed'
    })

@app.route('/test')
def test_system():
    """Test system with sample Kolkata coordinates"""
    return get_clean_route()

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
        
        # First, insert batch record
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
        
        # Insert each route
        saved_routes = []
        for route in routes:
            # Convert coordinates to LINESTRING for PostGIS
            # Coordinates format: [[lat, lon], [lat, lon], ...]
            # PostGIS expects: LINESTRING(lon lat, lon lat, ...)
            coordinates = route.get('coordinates', [])
            if coordinates and len(coordinates) >= 2:
                # Format each coordinate as "lon lat" with proper precision
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

@app.route('/routes', methods=['GET'])
def get_routes():
    """Fetch routes from PostgreSQL with optional filters"""
    try:
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        min_aqi = request.args.get('min_aqi', type=float)
        max_aqi = request.args.get('max_aqi', type=float)
        min_distance = request.args.get('min_distance', type=float)
        max_distance = request.args.get('max_distance', type=float)
        batch_id = request.args.get('batch_id')
        
        # Build query
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

if __name__ == '__main__':
    api_key = os.getenv("Maps_API_KEY")
    if not api_key or api_key == "YOUR_KEY_HERE":
        print("⚠️  WARNING: Maps_API_KEY not set in .env file")
        print("Please set your Google Maps API key in the .env file")
        print("Get your key from: https://console.cloud.google.com/")
    else:
        print("✅ Google Maps API key loaded")
    
    print("Starting Google Live API server on http://localhost:5002")
    print("Test endpoints:")
    print("  http://localhost:5002/")
    print("  http://localhost:5002/routes/clean?start_lat=22.5750&start_lon=88.3500&end_lat=22.5800&end_lon=88.3800")
    
    app.run(debug=True, host='0.0.0.0', port=5002)
