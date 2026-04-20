"""
Complete Training Pipeline for LSTM AQI Prediction
Integrates data collection, preprocessing, and model training
"""

import os
import sys
import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
import argparse

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from aqi_data_collector import AQIDataCollector
from data_preprocessor import AQIDataPreprocessor
from lstm_aqi_predictor import LSTMAQIPredictor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AQITrainingPipeline:
    """
    Complete training pipeline for AQI prediction model
    """
    
    def __init__(self, config_path: str = "config/training_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize components
        self.data_collector = None
        self.preprocessor = AQIDataPreprocessor()
        self.predictor = None
        
        # Training parameters
        self.sequence_length = self.config.get('sequence_length', 24)
        self.prediction_horizon = self.config.get('prediction_horizon', 4)
        self.test_size = self.config.get('test_size', 0.2)
        self.val_size = self.config.get('val_size', 0.2)
        
        # Data paths
        self.data_path = self.config.get('data_path', 'data/aqi_data.db')
        self.model_path = self.config.get('model_path', 'models/lstm_aqi_model')
        self.results_path = self.config.get('results_path', 'results')
        
        # Create directories
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        os.makedirs(self.model_path, exist_ok=True)
        os.makedirs(self.results_path, exist_ok=True)
        
    def _load_config(self) -> Dict:
        """Load training configuration"""
        default_config = {
            'sequence_length': 24,
            'prediction_horizon': 4,
            'test_size': 0.2,
            'val_size': 0.2,
            'data_path': 'data/aqi_data.db',
            'model_path': 'models/lstm_aqi_model',
            'results_path': 'results',
            'min_data_points': 1000,
            'locations': [
                {'name': 'Central_Kolkata', 'lat': 22.5726, 'lon': 88.3639},
                {'name': 'Salt_Lake', 'lat': 22.5958, 'lon': 88.3697},
                {'name': 'Alipore', 'lat': 22.5411, 'lon': 88.3407},
                {'name': 'Sealdah', 'lat': 22.5853, 'lon': 88.3696},
                {'name': 'Howrah', 'lat': 22.6139, 'lon': 88.4016}
            ]
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded config from {self.config_path}")
                return {**default_config, **config}
            except Exception as e:
                logger.warning(f"Failed to load config: {e}. Using defaults.")
        
        # Save default config
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        logger.info(f"Created default config at {self.config_path}")
        
        return default_config
    
    def initialize_data_collector(self):
        """Initialize AQI data collector"""
        api_key = os.getenv("Maps_API_KEY")
        if not api_key:
            raise ValueError("Maps_API_KEY not found in environment variables")
        
        self.data_collector = AQIDataCollector(api_key, self.data_path)
        logger.info("Data collector initialized")
    
    def collect_training_data(self, days_back: int = 30) -> bool:
        """
        Collect historical AQI data for training
        """
        if not self.data_collector:
            self.initialize_data_collector()
        
        logger.info(f"Collecting training data for the last {days_back} days...")
        
        try:
            # Check existing data
            existing_df = self.data_collector.get_historical_data(days_back=days_back)
            logger.info(f"Found {len(existing_df)} existing records")
            
            # Collect new data if needed
            if len(existing_df) < self.config.get('min_data_points', 1000):
                logger.info("Insufficient data. Collecting new data...")
                new_data = self.data_collector.collect_all_locations()
                logger.info(f"Collected {len(new_data)} new records")
                
                # Verify data collection
                updated_df = self.data_collector.get_historical_data(days_back=days_back)
                logger.info(f"Total records after collection: {len(updated_df)}")
                
                return len(updated_df) >= self.config.get('min_data_points', 1000)
            else:
                logger.info("Sufficient existing data found")
                return True
                
        except Exception as e:
            logger.error(f"Data collection failed: {e}")
            return False
    
    def prepare_training_data(self, location: Optional[Dict] = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Prepare training data for LSTM model
        Returns: (X_train, X_test, y_train, y_test)
        """
        logger.info("Preparing training data...")
        
        # Get historical data
        if location:
            df = self.data_collector.get_historical_data(
                days_back=90,
                latitude=location['lat'],
                longitude=location['lon']
            )
        else:
            df = self.data_collector.get_historical_data(days_back=90)
        
        if len(df) == 0:
            raise ValueError("No historical data available")
        
        logger.info(f"Loaded {len(df)} historical records")
        
        # Data quality validation
        quality_report = self.preprocessor.validate_data_quality(df)
        logger.info(f"Data quality score: {quality_report['quality_score']:.1f}/100")
        
        # Clean data
        df_clean = self.preprocessor.clean_data(df)
        logger.info(f"Data after cleaning: {len(df_clean)} records")
        
        # Feature engineering
        df_featured = self.preprocessor.engineer_features(df_clean)
        logger.info(f"Data after feature engineering: {df_featured.shape}")
        
        # Prepare sequences
        X, y, timestamps = self.preprocessor.prepare_sequences(
            df_featured,
            sequence_length=self.sequence_length,
            prediction_horizon=self.prediction_horizon
        )
        
        if len(X) == 0:
            raise ValueError("No sequences generated. Check data quality and parameters.")
        
        # Split data
        n_samples = len(X)
        test_size = int(n_samples * self.test_size)
        val_size = int(n_samples * self.val_size)
        train_size = n_samples - test_size - val_size
        
        X_train = X[:train_size]
        y_train = y[:train_size]
        X_val = X[train_size:train_size+val_size]
        y_val = y[train_size:train_size+val_size]
        X_test = X[train_size+val_size:]
        y_test = y[train_size+val_size:]
        
        logger.info(f"Data split - Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
        
        # Fit scalers on training data
        self.preprocessor.fit_scalers(X_train, y_train)
        
        # Transform data
        X_train_scaled, y_train_scaled = self.preprocessor.transform_data(X_train, y_train)
        X_val_scaled, y_val_scaled = self.preprocessor.transform_data(X_val, y_val)
        X_test_scaled, y_test_scaled = self.preprocessor.transform_data(X_test, y_test)
        
        return X_train_scaled, X_test_scaled, y_train_scaled, y_test_scaled, X_val_scaled, y_val_scaled
    
    def train_model(self, X_train: np.ndarray, y_train: np.ndarray, 
                   X_val: np.ndarray, y_val: np.ndarray) -> Dict:
        """
        Train LSTM model
        """
        logger.info("Training LSTM model...")
        
        # Initialize predictor
        n_features = X_train.shape[-1]
        self.predictor = LSTMAQIPredictor(
            sequence_length=self.sequence_length,
            prediction_horizon=self.prediction_horizon,
            n_features=n_features,
            model_path=self.model_path
        )
        
        # Build model
        self.predictor.build_model()
        
        # Train model
        training_results = self.predictor.train(X_train, y_train, X_val, y_val)
        
        logger.info("Model training completed")
        return training_results
    
    def evaluate_model(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict:
        """
        Evaluate trained model
        """
        if not self.predictor:
            raise ValueError("Model not trained. Call train_model first.")
        
        logger.info("Evaluating model...")
        
        # Inverse transform for evaluation
        y_test_original = self.preprocessor.inverse_transform_target(y_test)
        
        # Evaluate model
        metrics, predictions = self.predictor.evaluate(X_test, y_test)
        
        # Inverse transform predictions
        predictions_original = self.preprocessor.inverse_transform_target(predictions)
        
        # Calculate metrics on original scale
        from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
        
        metrics_original = {
            'rmse_original': np.sqrt(mean_squared_error(y_test_original.flatten(), predictions_original.flatten())),
            'mae_original': mean_absolute_error(y_test_original.flatten(), predictions_original.flatten()),
            'r2_original': r2_score(y_test_original.flatten(), predictions_original.flatten())
        }
        
        # Combine metrics
        all_metrics = {**metrics, **metrics_original}
        
        logger.info(f"Evaluation completed - RMSE: {all_metrics['rmse_original']:.4f}, MAE: {all_metrics['mae_original']:.4f}")
        
        return all_metrics, predictions_original, y_test_original
    
    def save_results(self, metrics: Dict, predictions: np.ndarray, y_true: np.ndarray):
        """
        Save training results and metrics
        """
        logger.info("Saving results...")
        
        # Save metrics
        results = {
            'timestamp': datetime.now().isoformat(),
            'config': self.config,
            'metrics': metrics,
            'model_path': self.model_path,
            'data_path': self.data_path
        }
        
        results_file = os.path.join(self.results_path, 'training_results.json')
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Save predictions
        predictions_df = pd.DataFrame({
            'true_values': y_true.flatten(),
            'predicted_values': predictions.flatten()
        })
        predictions_file = os.path.join(self.results_path, 'predictions.csv')
        predictions_df.to_csv(predictions_file, index=False)
        
        # Save preprocessor
        preprocessor_file = os.path.join(self.model_path, 'preprocessor.joblib')
        self.preprocessor.save_preprocessor(preprocessor_file)
        
        # Save model
        self.predictor.save_model()
        
        logger.info(f"Results saved to {self.results_path}")
    
    def run_full_pipeline(self, location: Optional[Dict] = None) -> Dict:
        """
        Run complete training pipeline
        """
        logger.info("Starting full training pipeline...")
        
        try:
            # Step 1: Collect data
            if not self.collect_training_data(days_back=30):
                raise ValueError("Insufficient data collected")
            
            # Step 2: Prepare data
            X_train, X_test, y_train, y_test, X_val, y_val = self.prepare_training_data(location)
            
            # Step 3: Train model
            training_results = self.train_model(X_train, y_train, X_val, y_val)
            
            # Step 4: Evaluate model
            metrics, predictions, y_true = self.evaluate_model(X_test, y_test)
            
            # Step 5: Save results
            self.save_results(metrics, predictions, y_true)
            
            # Step 6: Generate plots
            self.predictor.plot_training_history(
                save_path=os.path.join(self.results_path, 'training_history.png')
            )
            self.predictor.plot_predictions(
                y_true, predictions, n_samples=5,
                save_path=os.path.join(self.results_path, 'predictions_plot.png')
            )
            
            final_results = {
                'status': 'success',
                'training_results': training_results,
                'evaluation_metrics': metrics,
                'data_shape': {
                    'train': X_train.shape,
                    'val': X_val.shape,
                    'test': X_test.shape
                },
                'model_path': self.model_path,
                'results_path': self.results_path
            }
            
            logger.info("Training pipeline completed successfully")
            return final_results
            
        except Exception as e:
            logger.error(f"Training pipeline failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def train_multiple_locations(self) -> Dict:
        """
        Train models for multiple locations
        """
        logger.info("Training models for multiple locations...")
        
        all_results = {}
        
        for location in self.config['locations']:
            logger.info(f"Training for location: {location['name']}")
            
            # Update model path for this location
            location_model_path = os.path.join(self.model_path, location['name'])
            self.model_path = location_model_path
            
            # Run pipeline for this location
            result = self.run_full_pipeline(location)
            all_results[location['name']] = result
            
            logger.info(f"Completed training for {location['name']}")
        
        # Save combined results
        combined_results_file = os.path.join(self.results_path, 'multi_location_results.json')
        with open(combined_results_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        logger.info("Multi-location training completed")
        return all_results

def main():
    """Main function for running training pipeline"""
    parser = argparse.ArgumentParser(description='AQI LSTM Training Pipeline')
    parser.add_argument('--config', type=str, default='config/training_config.json',
                       help='Path to training configuration file')
    parser.add_argument('--location', type=str, default=None,
                       help='Train for specific location only')
    parser.add_argument('--multi-location', action='store_true',
                       help='Train for multiple locations')
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = AQITrainingPipeline(args.config)
    
    if args.multi_location:
        # Train for multiple locations
        results = pipeline.train_multiple_locations()
    elif args.location:
        # Train for specific location
        location = next((loc for loc in pipeline.config['locations'] 
                        if loc['name'] == args.location), None)
        if location:
            results = pipeline.run_full_pipeline(location)
        else:
            logger.error(f"Location '{args.location}' not found in config")
            results = {'status': 'error', 'error': f'Location {args.location} not found'}
    else:
        # Train with all data
        results = pipeline.run_full_pipeline()
    
    # Print results
    print("\n" + "="*50)
    print("TRAINING PIPELINE RESULTS")
    print("="*50)
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
