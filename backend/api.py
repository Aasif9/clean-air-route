from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import sys
import os

# Add backend directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_aqi_service import find_best_routes as google_find_best_routes

load_dotenv()

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
