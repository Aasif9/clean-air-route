from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
import json
from datetime import datetime
from supabase import create_client, Client

from simple_multi_route import find_multi_routes

load_dotenv()

# Initialize Supabase client with transaction pooler configuration
supabase_url = os.getenv("SUPABASE_URL")
supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Validate Supabase configuration
if not supabase_url:
    print("⚠️  WARNING: SUPABASE_URL not found in environment variables")
if not supabase_service_key:
    print("⚠️  WARNING: SUPABASE_SERVICE_ROLE_KEY not found in environment variables")

# Use service role key for backend operations (bypasses RLS)
if supabase_url and supabase_service_key:
    supabase: Client = create_client(supabase_url, supabase_service_key)
    
    # Test Supabase connection on startup
    try:
        test_result = supabase.table('navigation_routes').select('count').limit(1).execute()
        print("✅ Supabase connection established successfully")
    except Exception as e:
        print(f"⚠️  Warning: Supabase connection failed: {e}")
        print("Route saving functionality will be limited")
else:
    supabase = None
    print("⚠️  Supabase client not initialized - route saving disabled")

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "Kolkata AQI Multi-Route System - Version 2.0"

@app.route('/routes/multi')
def get_multi_routes():
    """Get multiple route options between two points and save to Supabase"""
    try:
        start_lat = float(request.args.get('start_lat'))
        start_lon = float(request.args.get('start_lon'))
        end_lat = float(request.args.get('end_lat'))
        end_lon = float(request.args.get('end_lon'))
        
        # Get user_id from query parameter and convert to UUID format if needed
        user_id = request.args.get('user_id', 'anonymous_user')
        print(f"[API] Original user_id: {user_id}")
        
        # Convert non-UUID user IDs to a valid UUID format for Supabase
        if user_id != 'anonymous_user' and not user_id.startswith('00000000-0000-0000-0000-'):
            # Generate a deterministic UUID based on the user_id string
            import hashlib
            hash_object = hashlib.md5(user_id.encode())
            hex_dig = hash_object.hexdigest()
            # Convert to UUID format
            uuid_user_id = f"{hex_dig[0:8]}-{hex_dig[8:12]}-{hex_dig[12:16]}-{hex_dig[16:20]}-{hex_dig[20:32]}"
            print(f"[API] Converted user_id {user_id} to UUID {uuid_user_id}")
            user_id = uuid_user_id
        
        print(f"[API] Received route request: ({start_lat:.4f}, {start_lon:.4f}) → ({end_lat:.4f}, {end_lon:.4f})")
        
        result = find_multi_routes(start_lat, start_lon, end_lat, end_lon)
        
        if "error" in result:
            print(f"[API] Error: {result['error']}")
            return jsonify({'error': result["error"]}), 404
        
        print(f"[API] Returning {result['total_routes']} routes")
        
        # Automatically save routes to Supabase with retry logic for transaction pooler
        if result.get('routes') and user_id != 'anonymous_user' and supabase:
            saved_count = 0
            for i, route in enumerate(result['routes']):
                route_data = {
                    'start_lat': start_lat,
                    'start_lon': start_lon,
                    'end_lat': end_lat,
                    'end_lon': end_lon,
                    'start_address': f"Point {i+1} Start",
                    'end_address': f"Point {i+1} End",
                    'route_type': route.get('route_type', f"route_{i+1}"),
                    'coordinates': route.get('coordinates', []),
                    'analysis': route.get('analysis', {}),
                    'node_count': route.get('node_count', 0)
                }
                
                # Prepare data for Supabase (matching the table schema)
                route_record = {
                    'user_id': user_id,
                    'start_lat': route_data['start_lat'],
                    'start_lon': route_data['start_lon'], 
                    'end_lat': route_data['end_lat'],
                    'end_lon': route_data['end_lon'],
                    'start_address': route_data['start_address'],
                    'end_address': route_data['end_address'],
                    'route_type': route_data['route_type'],
                    'total_distance_km': route_data['analysis'].get('total_distance_km', 0),
                    'total_time_min': route_data['analysis'].get('total_travel_time_min', 0),
                    'average_aqi': route_data['analysis'].get('average_aqi', 0),
                    'min_aqi': route_data['analysis'].get('min_aqi', 0),
                    'max_aqi': route_data['analysis'].get('max_aqi', 0),
                    'exposure_score': route_data['analysis'].get('exposure_score', 0),
                    'coordinates': json.dumps(route_data['coordinates']),
                    'route_metadata': json.dumps({
                        'node_count': route_data['node_count'],
                        'calculated_at': datetime.now().isoformat(),
                        'saved_via': 'transaction_pooler'
                    })
                }
                
                # Retry logic for transaction pooler
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        save_result = supabase.table('navigation_routes').insert(route_record).execute()
                        if save_result.data:
                            print(f"[API] Saved route {i+1} to Supabase (attempt {attempt + 1}): {save_result.data[0]['id']}")
                            saved_count += 1
                            break
                        else:
                            print(f"[API] No data returned from Supabase (attempt {attempt + 1})")
                    except Exception as save_error:
                        print(f"[API] Save attempt {attempt + 1} failed: {save_error}")
                        if attempt == max_retries - 1:
                            print(f"[API] Failed to save route {i+1} after {max_retries} attempts")
                        else:
                            # Brief delay before retry (transaction pooler optimization)
                            import time
                            time.sleep(0.1)
            
            print(f"[API] Successfully saved {saved_count}/{len(result['routes'])} routes to Supabase")
        
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

@app.route('/routes/history/<user_id>')
def get_route_history(user_id):
    """Get route history for a user from Supabase"""
    try:
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 500
            
        # Convert non-UUID user IDs to UUID format
        if not user_id.startswith('00000000-0000-0000-0000-'):
            import hashlib
            hash_object = hashlib.md5(user_id.encode())
            hex_dig = hash_object.hexdigest()
            uuid_user_id = f"{hex_dig[0:8]}-{hex_dig[8:12]}-{hex_dig[12:16]}-{hex_dig[16:20]}-{hex_dig[20:32]}"
            user_id = uuid_user_id
        
        # Query Supabase for user's routes
        result = supabase.table('navigation_routes').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
        
        if result.data:
            routes = result.data
            print(f"[API] Retrieved {len(routes)} routes for user {user_id} from Supabase")
            return jsonify({'routes': routes})
        else:
            print(f"[API] No routes found for user {user_id}")
            return jsonify({'routes': []})
        
    except Exception as e:
        print(f"[API] Error retrieving route history from Supabase: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/routes/history')
def get_all_routes():
    """Get all saved routes from Supabase (admin endpoint)"""
    try:
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 500
            
        # Query all routes from Supabase
        result = supabase.table('navigation_routes').select('*').order('created_at', desc=True).execute()
        
        if result.data:
            all_routes = result.data
            return jsonify({'routes': all_routes, 'total_routes': len(all_routes)})
        else:
            return jsonify({'routes': [], 'total_routes': 0})
        
    except Exception as e:
        print(f"[API] Error retrieving all routes from Supabase: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/routes/save', methods=['POST'])
def save_route():
    """Save a route to Supabase"""
    try:
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 500
            
        data = request.get_json()
        user_id = data.get('user_id')
        route_data = data.get('route_data')
        
        if not user_id or not route_data:
            return jsonify({'error': 'Missing user_id or route_data'}), 400
        
        # Convert non-UUID user IDs to UUID format
        if not user_id.startswith('00000000-0000-0000-0000-'):
            import hashlib
            hash_object = hashlib.md5(user_id.encode())
            hex_dig = hash_object.hexdigest()
            uuid_user_id = f"{hex_dig[0:8]}-{hex_dig[8:12]}-{hex_dig[12:16]}-{hex_dig[16:20]}-{hex_dig[20:32]}"
            user_id = uuid_user_id
        
        # Prepare data for Supabase (matching the table schema)
        route_record = {
            'user_id': user_id,
            'start_lat': route_data.get('start_lat', 0),
            'start_lon': route_data.get('start_lon', 0), 
            'end_lat': route_data.get('end_lat', 0),
            'end_lon': route_data.get('end_lon', 0),
            'start_address': route_data.get('start_address', ''),
            'end_address': route_data.get('end_address', ''),
            'route_type': route_data.get('route_type', 'unknown'),
            'total_distance_km': route_data.get('analysis', {}).get('total_distance_km', 0),
            'total_time_min': route_data.get('analysis', {}).get('total_travel_time_min', 0),
            'average_aqi': route_data.get('analysis', {}).get('average_aqi', 0),
            'min_aqi': route_data.get('analysis', {}).get('min_aqi', 0),
            'max_aqi': route_data.get('analysis', {}).get('max_aqi', 0),
            'exposure_score': route_data.get('analysis', {}).get('exposure_score', 0),
            'coordinates': json.dumps(route_data.get('coordinates', [])),
            'route_metadata': json.dumps({
                'node_count': route_data.get('node_count', 0),
                'calculated_at': datetime.now().isoformat()
            })
        }
        
        # Save to Supabase
        result = supabase.table('navigation_routes').insert(route_record).execute()
        
        if result.data:
            print(f"[API] Saved route to Supabase for user {user_id}: {route_record['route_type']} - {route_record['total_distance_km']}km")
            return jsonify({
                'success': True,
                'message': 'Route saved successfully to Supabase',
                'route_id': result.data[0]['id']
            })
        else:
            print(f"[API] Supabase error: {result}")
            return jsonify({'error': 'Failed to save route to Supabase'}), 500
        
    except Exception as e:
        print(f"[API] Error saving route to Supabase: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/test')
def test_system():
    """Test system with sample Kolkata coordinates"""
    return get_multi_routes()

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
