from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os

from simple_multi_route import find_multi_routes

load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "Kolkata AQI Multi-Route System - Version 2.0"

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
