"""
Predictive AQI Service for Enhanced Route Calculation
Integrates LSTM predictions with existing route calculation system
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import joblib
from dataclasses import dataclass

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_aqi_service import find_best_routes as google_find_best_routes
from aqi_data_collector import AQIDataCollector
from lstm_aqi_predictor import LSTMAQIPredictor
from data_preprocessor import AQIDataPreprocessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PredictedAQIPoint:
    """Data structure for predicted AQI at a location"""
    latitude: float
    longitude: float
    current_aqi: float
    predicted_aqi: Dict[int, float]  # horizon -> predicted_aqi
    confidence: float
    timestamp: datetime

class PredictiveAQIService:
    """
    Service for predictive AQI-based route calculation
    """
    
    def __init__(self, model_path: str = "models/lstm_aqi_model"):
        self.model_path = model_path
        self.predictor = None
        self.preprocessor = None
        self.data_collector = None
        
        # Prediction parameters
        self.prediction_horizons = [1, 4, 24]  # hours
        self.confidence_threshold = 0.7
        
        # Cache for predictions
        self.prediction_cache = {}
        self.cache_ttl = 3600  # 1 hour
        
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize LSTM models and preprocessor"""
        try:
            # Load preprocessor
            preprocessor_path = os.path.join(self.model_path, 'preprocessor.joblib')
            if os.path.exists(preprocessor_path):
                self.preprocessor = AQIDataPreprocessor.load_preprocessor(preprocessor_path)
                logger.info("Preprocessor loaded successfully")
            else:
                logger.warning("Preprocessor not found. Using default preprocessing.")
                self.preprocessor = AQIDataPreprocessor()
            
            # Load LSTM predictor
            if os.path.exists(os.path.join(self.model_path, 'lstm_aqi_model.h5')):
                self.predictor = LSTMAQIPredictor.load_model(self.model_path)
                logger.info("LSTM predictor loaded successfully")
            else:
                logger.warning("LSTM model not found. Predictions will be disabled.")
            
            # Initialize data collector
            api_key = os.getenv("Maps_API_KEY")
            if api_key:
                self.data_collector = AQIDataCollector(api_key)
                logger.info("Data collector initialized")
            else:
                logger.warning("Maps_API_KEY not found. Current AQI collection disabled.")
                
        except Exception as e:
            logger.error(f"Failed to initialize models: {e}")
    
    def get_current_aqi(self, latitude: float, longitude: float) -> Optional[float]:
        """Get current AQI for a location"""
        if not self.data_collector:
            return None
        
        try:
            data_point = self.data_collector.fetch_aqi_data(latitude, longitude)
            return data_point.aqi if data_point else None
        except Exception as e:
            logger.error(f"Failed to get current AQI: {e}")
            return None
    
    def predict_aqi(self, latitude: float, longitude: float, 
                   horizons: List[int] = None) -> Dict[int, float]:
        """
        Predict AQI for given location and time horizons
        """
        if not self.predictor or not self.preprocessor:
            logger.warning("Predictive models not available")
            return {}
        
        if horizons is None:
            horizons = self.prediction_horizons
        
        # Check cache
        cache_key = f"{latitude:.4f}_{longitude:.4f}"
        if cache_key in self.prediction_cache:
            cache_entry = self.prediction_cache[cache_key]
            if datetime.now().timestamp() - cache_entry['timestamp'] < self.cache_ttl:
                return cache_entry['predictions']
        
        try:
            # Get historical data for this location
            df = self.data_collector.get_historical_data(
                days_back=7,
                latitude=latitude,
                longitude=longitude
            )
            
            if len(df) < 24:  # Need at least 24 hours of data
                logger.warning(f"Insufficient historical data for ({latitude}, {longitude})")
                return {}
            
            # Preprocess data
            df_clean = self.preprocessor.clean_data(df)
            df_featured = self.preprocessor.engineer_features(df_clean)
            
            # Prepare sequence
            X, _, _ = self.preprocessor.prepare_sequences(
                df_featured,
                sequence_length=self.predictor.sequence_length,
                prediction_horizon=max(horizons)
            )
            
            if len(X) == 0:
                logger.warning(f"No sequences generated for ({latitude}, {longitude})")
                return {}
            
            # Use the latest sequence for prediction
            latest_sequence = X[-1:].copy()
            latest_sequence_scaled, _ = self.preprocessor.transform_data(latest_sequence)
            
            # Make predictions
            predictions_scaled = self.predictor.predict(latest_sequence_scaled)
            
            # Inverse transform predictions
            predictions_original = self.preprocessor.inverse_transform_target(predictions_scaled)
            
            # Extract predictions for requested horizons
            result = {}
            for horizon in horizons:
                if horizon <= len(predictions_original[0]):
                    result[horizon] = float(predictions_original[0][horizon-1])
            
            # Cache results
            self.prediction_cache[cache_key] = {
                'predictions': result,
                'timestamp': datetime.now().timestamp()
            }
            
            logger.info(f"Predictions for ({latitude}, {longitude}): {result}")
            return result
            
        except Exception as e:
            logger.error(f"Prediction failed for ({latitude}, {longitude}): {e}")
            return {}
    
    def get_predicted_aqi_points(self, coordinates: List[Tuple[float, float]], 
                                horizons: List[int] = None) -> List[PredictedAQIPoint]:
        """
        Get predicted AQI for multiple points along a route
        """
        if horizons is None:
            horizons = self.prediction_horizons
        
        predicted_points = []
        
        for lat, lon in coordinates:
            current_aqi = self.get_current_aqi(lat, lon)
            predicted_aqi = self.predict_aqi(lat, lon, horizons)
            
            # Calculate confidence based on data availability and prediction consistency
            confidence = self._calculate_prediction_confidence(current_aqi, predicted_aqi)
            
            point = PredictedAQIPoint(
                latitude=lat,
                longitude=lon,
                current_aqi=current_aqi or 0,
                predicted_aqi=predicted_aqi,
                confidence=confidence,
                timestamp=datetime.now()
            )
            
            predicted_points.append(point)
        
        return predicted_points
    
    def _calculate_prediction_confidence(self, current_aqi: Optional[float], 
                                      predicted_aqi: Dict[int, float]) -> float:
        """Calculate confidence score for predictions"""
        if not predicted_aqi:
            return 0.0
        
        if current_aqi is None:
            # No current data, lower confidence
            return 0.5
        
        # Check prediction consistency across horizons
        if len(predicted_aqi) > 1:
            values = list(predicted_aqi.values())
            std_dev = np.std(values)
            mean_val = np.mean(values)
            
            # Higher confidence for consistent predictions
            consistency_score = max(0, 1 - (std_dev / (mean_val + 1e-8)))
        else:
            consistency_score = 0.8
        
        # Check if predictions are reasonable
        reasonableness_score = 1.0
        for horizon, pred_aqi in predicted_aqi.items():
            if pred_aqi < 0 or pred_aqi > 500:
                reasonableness_score *= 0.5
        
        return min(1.0, consistency_score * reasonableness_score)
    
    def calculate_predictive_route_score(self, route_coords: List[Tuple[float, float]], 
                                       prediction_horizon: int = 4) -> Dict:
        """
        Calculate route score using predicted AQI values
        """
        predicted_points = self.get_predicted_aqi_points(route_coords, [prediction_horizon])
        
        if not predicted_points:
            return {'error': 'No predictions available'}
        
        # Extract predicted AQI values
        predicted_aqi_values = []
        confidences = []
        
        for point in predicted_points:
            if prediction_horizon in point.predicted_aqi:
                predicted_aqi_values.append(point.predicted_aqi[prediction_horizon])
                confidences.append(point.confidence)
        
        if not predicted_aqi_values:
            return {'error': f'No predictions for horizon {prediction_horizon}'}
        
        # Calculate metrics
        avg_predicted_aqi = np.mean(predicted_aqi_values)
        max_predicted_aqi = np.max(predicted_aqi_values)
        min_predicted_aqi = np.min(predicted_aqi_values)
        avg_confidence = np.mean(confidences)
        
        # Calculate exposure score (similar to current system but with predictions)
        exposure_score = len(predicted_aqi_values) * (1.05 ** avg_predicted_aqi)
        
        return {
            'avg_predicted_aqi': avg_predicted_aqi,
            'max_predicted_aqi': max_predicted_aqi,
            'min_predicted_aqi': min_predicted_aqi,
            'avg_confidence': avg_confidence,
            'exposure_score': exposure_score,
            'prediction_horizon': prediction_horizon,
            'num_points': len(predicted_aqi_values)
        }
    
    def find_predictive_routes(self, origin_lat: float, origin_lon: float,
                              dest_lat: float, dest_lon: float,
                              prediction_horizon: int = 4) -> Dict:
        """
        Find routes using predictive AQI values
        """
        logger.info(f"Finding predictive routes with {prediction_horizon}h horizon")
        
        try:
            # Get routes from existing service
            base_routes = google_find_best_routes(origin_lat, origin_lon, dest_lat, dest_lon)
            
            if "error" in base_routes:
                return base_routes
            
            # Calculate predictive scores for each route
            enhanced_routes = {}
            
            # Process fast route
            if 'fast_route' in base_routes:
                fast_coords = [(coord[0], coord[1]) for coord in base_routes['fast_route']['coordinates']]
                fast_score = self.calculate_predictive_route_score(fast_coords, prediction_horizon)
                
                enhanced_routes['fast_route'] = {
                    **base_routes['fast_route'],
                    'predictive_score': fast_score,
                    'route_type': f"fastest_{prediction_horizon}h_predicted"
                }
            
            # Process clean route
            if 'clean_route' in base_routes:
                clean_coords = [(coord[0], coord[1]) for coord in base_routes['clean_route']['coordinates']]
                clean_score = self.calculate_predictive_route_score(clean_coords, prediction_horizon)
                
                enhanced_routes['clean_route'] = {
                    **base_routes['clean_route'],
                    'predictive_score': clean_score,
                    'route_type': f"cleanest_{prediction_horizon}h_predicted"
                }
            
            # Process additional routes
            if 'additional_routes' in base_routes:
                enhanced_additional = []
                for i, route in enumerate(base_routes['additional_routes']):
                    route_coords = [(coord[0], coord[1]) for coord in route['coordinates']]
                    route_score = self.calculate_predictive_route_score(route_coords, prediction_horizon)
                    
                    enhanced_route = {
                        **route,
                        'predictive_score': route_score,
                        'route_type': f"alternative_{i+1}_{prediction_horizon}h_predicted"
                    }
                    enhanced_additional.append(enhanced_route)
                
                enhanced_routes['additional_routes'] = enhanced_additional
            
            # Add predictive comparison
            if 'fast_route' in enhanced_routes and 'clean_route' in enhanced_routes:
                fast_score = enhanced_routes['fast_route']['predictive_score']['exposure_score']
                clean_score = enhanced_routes['clean_route']['predictive_score']['exposure_score']
                
                exposure_reduction = ((fast_score - clean_score) / fast_score * 100) if fast_score > 0 else 0
                
                enhanced_routes['predictive_comparison'] = {
                    'exposure_reduction_percent': round(exposure_reduction, 1),
                    'prediction_horizon': prediction_horizon,
                    'avg_confidence': (
                        enhanced_routes['fast_route']['predictive_score']['avg_confidence'] +
                        enhanced_routes['clean_route']['predictive_score']['avg_confidence']
                    ) / 2
                }
            
            return {
                **enhanced_routes,
                'status': 'success',
                'data_source': 'predictive_aqi_lstm',
                'prediction_horizon': prediction_horizon,
                'model_info': {
                    'model_path': self.model_path,
                    'horizons_available': self.prediction_horizons
                }
            }
            
        except Exception as e:
            logger.error(f"Predictive route finding failed: {e}")
            return {'error': str(e)}
    
    def compare_current_vs_predicted(self, origin_lat: float, origin_lon: float,
                                   dest_lat: float, dest_lon: float,
                                   prediction_horizon: int = 4) -> Dict:
        """
        Compare current AQI routing vs predicted AQI routing
        """
        logger.info("Comparing current vs predicted routing")
        
        try:
            # Get current routing
            current_routes = google_find_best_routes(origin_lat, origin_lon, dest_lat, dest_lon)
            
            # Get predicted routing
            predicted_routes = self.find_predictive_routes(
                origin_lat, origin_lon, dest_lat, dest_lon, prediction_horizon
            )
            
            if "error" in current_routes or "error" in predicted_routes:
                return {'error': 'Failed to get route comparisons'}
            
            comparison = {
                'current_routing': {
                    'fast_exposure_score': current_routes['fast_route']['analysis']['exposure_score'],
                    'clean_exposure_score': current_routes['clean_route']['analysis']['exposure_score'],
                    'fast_avg_aqi': current_routes['fast_route']['analysis']['average_aqi'],
                    'clean_avg_aqi': current_routes['clean_route']['analysis']['average_aqi']
                },
                'predicted_routing': {
                    'fast_exposure_score': predicted_routes['fast_route']['predictive_score']['exposure_score'],
                    'clean_exposure_score': predicted_routes['clean_route']['predictive_score']['exposure_score'],
                    'fast_avg_aqi': predicted_routes['fast_route']['predictive_score']['avg_predicted_aqi'],
                    'clean_avg_aqi': predicted_routes['clean_route']['predictive_score']['avg_predicted_aqi'],
                    'avg_confidence': predicted_routes['predictive_comparison']['avg_confidence']
                },
                'prediction_horizon': prediction_horizon,
                'comparison_timestamp': datetime.now().isoformat()
            }
            
            # Calculate differences
            comparison['differences'] = {
                'fast_aqi_change': (
                    comparison['predicted_routing']['fast_avg_aqi'] - 
                    comparison['current_routing']['fast_avg_aqi']
                ),
                'clean_aqi_change': (
                    comparison['predicted_routing']['clean_avg_aqi'] - 
                    comparison['current_routing']['clean_avg_aqi']
                ),
                'fast_exposure_change': (
                    comparison['predicted_routing']['fast_exposure_score'] - 
                    comparison['current_routing']['fast_exposure_score']
                ),
                'clean_exposure_change': (
                    comparison['predicted_routing']['clean_exposure_score'] - 
                    comparison['current_routing']['clean_exposure_score']
                )
            }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Route comparison failed: {e}")
            return {'error': str(e)}

def main():
    """Test predictive AQI service"""
    service = PredictiveAQIService()
    
    # Test prediction
    lat, lon = 22.5726, 88.3639  # Central Kolkata
    predictions = service.predict_aqi(lat, lon, [1, 4, 24])
    print(f"Predictions for ({lat}, {lon}): {predictions}")
    
    # Test route calculation
    origin_lat, origin_lon = 22.5726, 88.3639
    dest_lat, dest_lon = 22.5958, 88.3697
    
    routes = service.find_predictive_routes(
        origin_lat, origin_lon, dest_lat, dest_lon, prediction_horizon=4
    )
    
    print("Predictive routes:")
    if 'predictive_comparison' in routes:
        print(f"Exposure reduction: {routes['predictive_comparison']['exposure_reduction_percent']}%")
    
    # Test comparison
    comparison = service.compare_current_vs_predicted(
        origin_lat, origin_lon, dest_lat, dest_lon, prediction_horizon=4
    )
    
    print("Current vs Predicted comparison:")
    if 'differences' in comparison:
        print(f"Fast route AQI change: {comparison['differences']['fast_aqi_change']:.1f}")
        print(f"Clean route AQI change: {comparison['differences']['clean_aqi_change']:.1f}")

if __name__ == "__main__":
    main()
