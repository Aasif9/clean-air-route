"""
Predictive AQI API Endpoints
REST API for LSTM-based AQI prediction and intelligent routing
"""

import os
import sys
import json
import logging
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from predictive_aqi_service import PredictiveAQIService
from training_pipeline import AQITrainingPipeline

load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize predictive service
predictive_service = PredictiveAQIService()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def home():
    """API health check and information"""
    return jsonify({
        "service": "Predictive AQI Routing API",
        "version": "2.0",
        "description": "LSTM-based AQI prediction for intelligent route planning",
        "features": [
            "Multi-horizon AQI prediction",
            "Predictive route calculation", 
            "Current vs predicted comparison",
            "Model training endpoints"
        ],
        "status": "active",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/health')
def health_check():
    """Detailed health check"""
    model_status = "loaded" if predictive_service.predictor else "not_loaded"
    preprocessor_status = "loaded" if predictive_service.preprocessor else "not_loaded"
    data_collector_status = "initialized" if predictive_service.data_collector else "not_initialized"
    
    return jsonify({
        "status": "healthy",
        "components": {
            "lstm_model": model_status,
            "preprocessor": preprocessor_status,
            "data_collector": data_collector_status
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/aqi/predict')
def predict_aqi():
    """Predict AQI for a specific location and time horizons"""
    try:
        # Get parameters
        latitude = float(request.args.get('lat'))
        longitude = float(request.args.get('lon'))
        horizons_str = request.args.get('horizons', '1,4,24')
        horizons = [int(h.strip()) for h in horizons_str.split(',')]
        
        logger.info(f"AQI prediction request: ({latitude}, {longitude}), horizons: {horizons}")
        
        # Get current AQI
        current_aqi = predictive_service.get_current_aqi(latitude, longitude)
        
        # Get predictions
        predictions = predictive_service.predict_aqi(latitude, longitude, horizons)
        
        if not predictions:
            return jsonify({
                'error': 'No predictions available',
                'message': 'Insufficient historical data or model not loaded'
            }), 404
        
        response = {
            'location': {
                'latitude': latitude,
                'longitude': longitude
            },
            'current_aqi': current_aqi,
            'predicted_aqi': predictions,
            'horizons_requested': horizons,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response)
        
    except ValueError as e:
        return jsonify({'error': f'Invalid parameters: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"AQI prediction failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/routes/predictive')
def get_predictive_routes():
    """Get routes using predicted AQI values"""
    try:
        # Get route parameters
        start_lat = float(request.args.get('start_lat'))
        start_lon = float(request.args.get('start_lon'))
        end_lat = float(request.args.get('end_lat'))
        end_lon = float(request.args.get('end_lon'))
        prediction_horizon = int(request.args.get('horizon', 4))
        
        logger.info(f"Predictive route request: ({start_lat}, {start_lon}) → ({end_lat}, {end_lon}), horizon: {prediction_horizon}h")
        
        # Get predictive routes
        result = predictive_service.find_predictive_routes(
            start_lat, start_lon, end_lat, end_lon, prediction_horizon
        )
        
        if "error" in result:
            return jsonify(result), 404
        
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({'error': f'Invalid parameters: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Predictive route calculation failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/routes/compare')
def compare_current_vs_predicted():
    """Compare current AQI routing vs predicted AQI routing"""
    try:
        # Get route parameters
        start_lat = float(request.args.get('start_lat'))
        start_lon = float(request.args.get('start_lon'))
        end_lat = float(request.args.get('end_lat'))
        end_lon = float(request.args.get('end_lon'))
        prediction_horizon = int(request.args.get('horizon', 4))
        
        logger.info(f"Route comparison request: ({start_lat}, {start_lon}) → ({end_lat}, {end_lon}), horizon: {prediction_horizon}h")
        
        # Get comparison
        result = predictive_service.compare_current_vs_predicted(
            start_lat, start_lon, end_lat, end_lon, prediction_horizon
        )
        
        if "error" in result:
            return jsonify(result), 404
        
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({'error': f'Invalid parameters: {str(e)}'}), 400
    except Exception as e:
        logger.error(f"Route comparison failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/model/train', methods=['POST'])
def train_model():
    """Trigger model training"""
    try:
        # Get training parameters from request body
        data = request.get_json() or {}
        config_path = data.get('config_path', 'config/training_config.json')
        location = data.get('location')
        multi_location = data.get('multi_location', False)
        
        logger.info(f"Model training request: config={config_path}, location={location}, multi_location={multi_location}")
        
        # Initialize training pipeline
        pipeline = AQITrainingPipeline(config_path)
        
        # Run training
        if multi_location:
            results = pipeline.train_multiple_locations()
        elif location:
            location_config = next((loc for loc in pipeline.config['locations'] 
                                  if loc['name'] == location), None)
            if location_config:
                results = pipeline.run_full_pipeline(location_config)
            else:
                return jsonify({'error': f'Location {location} not found'}), 404
        else:
            results = pipeline.run_full_pipeline()
        
        return jsonify({
            'status': 'training_completed',
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Model training failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/model/status')
def get_model_status():
    """Get model training and performance status"""
    try:
        model_path = predictive_service.model_path
        
        # Check if model files exist
        model_exists = os.path.exists(os.path.join(model_path, 'lstm_aqi_model.h5'))
        config_exists = os.path.exists(os.path.join(model_path, 'model_config.json'))
        preprocessor_exists = os.path.exists(os.path.join(model_path, 'preprocessor.joblib'))
        
        # Load training results if available
        results_path = os.path.join(predictive_service.model_path, '..', 'results', 'training_results.json')
        training_results = {}
        
        if os.path.exists(results_path):
            with open(results_path, 'r') as f:
                training_results = json.load(f)
        
        status = {
            'model_loaded': predictive_service.predictor is not None,
            'preprocessor_loaded': predictive_service.preprocessor is not None,
            'data_collector_ready': predictive_service.data_collector is not None,
            'files_exist': {
                'model': model_exists,
                'config': config_exists,
                'preprocessor': preprocessor_exists
            },
            'training_results': training_results,
            'model_path': model_path,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Model status check failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/collect', methods=['POST'])
def collect_data():
    """Trigger data collection"""
    try:
        # Get parameters
        data = request.get_json() or {}
        hours = data.get('hours', 1)
        continuous = data.get('continuous', False)
        
        logger.info(f"Data collection request: hours={hours}, continuous={continuous}")
        
        if not predictive_service.data_collector:
            return jsonify({'error': 'Data collector not initialized'}), 500
        
        if continuous:
            # Start continuous collection (this would run in background)
            return jsonify({
                'message': 'Continuous collection started',
                'note': 'This would run in background with proper setup'
            })
        else:
            # Collect data for specified hours
            collected_data = []
            for _ in range(hours):
                data_points = predictive_service.data_collector.collect_all_locations()
                collected_data.extend(data_points)
            
            return jsonify({
                'status': 'collection_completed',
                'data_points_collected': len(collected_data),
                'hours_processed': hours,
                'timestamp': datetime.now().isoformat()
            })
        
    except Exception as e:
        logger.error(f"Data collection failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/status')
def get_data_status():
    """Get data collection status"""
    try:
        if not predictive_service.data_collector:
            return jsonify({'error': 'Data collector not initialized'}), 500
        
        # Get data statistics
        df = predictive_service.data_collector.get_historical_data(days_back=30)
        
        if len(df) == 0:
            return jsonify({
                'total_records': 0,
                'date_range': None,
                'locations': [],
                'message': 'No historical data available'
            })
        
        # Calculate statistics
        stats = {
            'total_records': len(df),
            'date_range': {
                'start': df['timestamp'].min().isoformat() if 'timestamp' in df.columns else None,
                'end': df['timestamp'].max().isoformat() if 'timestamp' in df.columns else None
            },
            'locations': df[['latitude', 'longitude']].drop_duplicates().to_dict('records') if 'latitude' in df.columns else [],
            'aqi_stats': {
                'mean': float(df['aqi'].mean()) if 'aqi' in df.columns else None,
                'min': float(df['aqi'].min()) if 'aqi' in df.columns else None,
                'max': float(df['aqi'].max()) if 'aqi' in df.columns else None
            } if 'aqi' in df.columns else None,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Data status check failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Legacy endpoints for backward compatibility
@app.route('/routes/clean')
def legacy_clean_route():
    """Legacy endpoint - redirects to current AQI routing"""
    from enhanced_aqi_service import find_best_routes
    
    try:
        start_lat = float(request.args.get('start_lat'))
        start_lon = float(request.args.get('start_lon'))
        end_lat = float(request.args.get('end_lat'))
        end_lon = float(request.args.get('end_lon'))
        
        result = find_best_routes(start_lat, start_lon, end_lat, end_lon)
        
        if "error" in result:
            return jsonify({'error': result["error"]}), 404
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/routes/multi')
def legacy_multi_route():
    """Legacy endpoint - redirects to multi-route API"""
    from simple_multi_route import find_multi_routes
    
    try:
        start_lat = float(request.args.get('start_lat'))
        start_lon = float(request.args.get('start_lon'))
        end_lat = float(request.args.get('end_lat'))
        end_lon = float(request.args.get('end_lon'))
        
        result = find_multi_routes(start_lat, start_lon, end_lat, end_lon)
        
        if "error" in result:
            return jsonify({'error': result["error"]}), 404
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def main():
    """Main function to run the API server"""
    port = int(os.environ.get('PORT', 5003))
    
    print("=" * 60)
    print("🤖 Predictive AQI Routing API Server")
    print("=" * 60)
    print(f"🚀 Server starting on port {port}")
    print(f"📍 Environment: {'Production' if os.getenv('FLASK_ENV') == 'production' else 'Development'}")
    print(f"🧠 Model Status: {'Loaded' if predictive_service.predictor else 'Not Loaded'}")
    print(f"📊 Data Collector: {'Ready' if predictive_service.data_collector else 'Not Ready'}")
    print()
    print("🔗 Available Endpoints:")
    print("  GET  /api/health                    - Health check")
    print("  GET  /api/aqi/predict              - AQI prediction")
    print("  GET  /api/routes/predictive         - Predictive routing")
    print("  GET  /api/routes/compare            - Current vs predicted comparison")
    print("  POST /api/model/train               - Train model")
    print("  GET  /api/model/status             - Model status")
    print("  POST /api/data/collect              - Collect data")
    print("  GET  /api/data/status               - Data status")
    print()
    print("🔗 Legacy Endpoints:")
    print("  GET  /routes/clean                  - Current AQI routing")
    print("  GET  /routes/multi                  - Multi-route API")
    print("=" * 60)
    
    app.run(debug=False, host='0.0.0.0', port=port)

if __name__ == '__main__':
    main()
