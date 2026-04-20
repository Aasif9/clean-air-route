from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import sys
import os
import json
from datetime import datetime
from supabase import create_client, Client

# Add backend directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_aqi_service import find_best_routes as google_find_best_routes
from simple_multi_route import find_multi_routes

load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
# Use service role key for backend operations (bypasses RLS)
supabase: Client = create_client(supabase_url, supabase_service_key)

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "Kolkata AQI Routing - Google Live API Version"

@app.route('/routes/clean')
def get_clean_route():
    """Get cleanest route between two points — now powered by Google APIs."""
    try:
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
        print(f"[API] Multi-route request received: {dict(request.args)}")
        
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
                            'calculated_at': datetime.now().isoformat()
                        })
                    }
                    
                    save_result = supabase.table('navigation_routes').insert(route_record).execute()
                    if save_result.data:
                        print(f"[API] Saved route {i+1} to Supabase: {save_result.data[0]['id']}")
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

@app.route('/users/create', methods=['POST'])
def create_user():
    """Create a user profile"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        email = data.get('email')
        full_name = data.get('full_name')
        
        if not user_id:
            return jsonify({'error': 'Missing user_id'}), 400
        
        user_record = {
            'id': user_id,
            'email': email,
            'full_name': full_name
        }
        
        result = supabase.table('user_profiles').insert(user_record).execute()
        
        if result.data:
            return jsonify({'success': True, 'user_id': result.data[0]['id']})
        else:
            return jsonify({'error': 'Failed to create user'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/routes/save', methods=['POST'])
def save_route():
    """Save a route to Supabase"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        route_data = data.get('route_data')
        
        if not user_id or not route_data:
            return jsonify({'error': 'Missing user_id or route_data'}), 400
        
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

@app.route('/routes/history/<user_id>')
def get_route_history(user_id):
    """Get route history for a user from Supabase"""
    try:
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

@app.route('/test')
def test_system():
    """Test system with sample Kolkata coordinates"""
    return get_clean_route()

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
