from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
import sys
import uuid
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_multi_route import find_multi_routes
from db import get_db_connection

load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "Kolkata AQI Multi-Route System - Version 2.0"

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

@app.route('/routes/multi')
def get_multi_routes():
    """Get multiple route options between two points"""
    try:
        start_lat = float(request.args.get('start_lat'))
        start_lon = float(request.args.get('start_lon'))
        end_lat = float(request.args.get('end_lat'))
        end_lon = float(request.args.get('end_lon'))
        
        print(f"[API] Received route request: ({start_lat:.4f}, {start_lon:.4f}) → ({end_lat:.4f}, {end_lon:.4f})")
        
        result = find_multi_routes(start_lat, start_lon, end_lat, end_lon)
        
        if "error" in result:
            print(f"[API] Error: {result['error']}")
            return jsonify({'error': result["error"]}), 404
        
        print(f"[API] Returning {result['total_routes']} routes")
        return jsonify(result)

    except Exception as e:
        print(f"[API] Exception: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/routes/clean')
def get_clean_route():
    """Legacy endpoint - redirects to multi-route"""
    return get_multi_routes()

@app.route('/stations')
def get_stations():
    """Return compatibility info"""
    return jsonify({
        'stations': [],
        'total_stations': 0,
        'aqi_range': [0, 0],
        'average_aqi': 0,
        'message': 'Using Google Live Multi-Route API'
    })

@app.route('/test')
def test_system():
    """Test system with sample Kolkata coordinates"""
    return get_multi_routes()

@app.route('/save-routes', methods=['POST'])
def save_routes():
    """Save multiple routes to PostgreSQL with PostGIS geometry and coordinate order preservation"""
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
            
            # Insert route with coordinates as JSONB
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
                    coordinates,
                    batch_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, ST_GeomFromText(%s, 4326), %s::jsonb, %s)
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
                json.dumps(coordinates) if coordinates else None,
                batch_id
            ))
            
            route_id = cur.fetchone()[0]
            
            # Insert individual coordinate points to preserve order
            for point_order, coord in enumerate(coordinates):
                lat = float(coord[0])
                lng = float(coord[1])
                cur.execute("""
                    INSERT INTO route_points (route_id, point_order, lat, lng)
                    VALUES (%s, %s, %s, %s)
                """, (route_id, point_order, lat, lng))
            
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    api_key = os.getenv("Maps_API_KEY")
    if not api_key or api_key == "YOUR_KEY_HERE":
        print("⚠️  WARNING: Maps_API_KEY not set in .env file")
    else:
        print("✅ Google Maps API key loaded")
    
    print("Starting Multi-Route API server")
    print(f"Port: {port}")
    print("Endpoints:")
    print("  /routes/multi")
    print("  /routes/clean (legacy)")
    print("  /test")
    
    app.run(debug=False, host='0.0.0.0', port=port)
