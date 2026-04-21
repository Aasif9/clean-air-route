"""
Data Preprocessing and Validation Pipeline for LSTM AQI Prediction
Handles data cleaning, validation, feature engineering, and sequence preparation
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.impute import SimpleImputer
from typing import Tuple, Dict, List, Optional
import logging
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AQIDataPreprocessor:
    """
    Comprehensive data preprocessing pipeline for AQI prediction
    """
    
    def __init__(self):
        self.scaler_features = StandardScaler()
        self.scaler_target = MinMaxScaler()
        self.feature_columns = ['aqi', 'pm25', 'pm10', 'o3', 'no2', 'so2', 'co']
        self.target_column = 'aqi'
        self.is_fitted = False
        
        # Data quality thresholds
        self.aqi_range = (0, 500)  # Valid AQI range
        self.pm25_range = (0, 500)  # Valid PM2.5 range (μg/m³)
        self.pm10_range = (0, 600)  # Valid PM10 range (μg/m³)
        
    def validate_data_quality(self, df: pd.DataFrame) -> Dict:
        """
        Validate data quality and generate quality report
        """
        logger.info("Validating data quality...")
        
        report = {
            'total_records': len(df),
            'missing_values': {},
            'outliers': {},
            'invalid_ranges': {},
            'duplicate_records': 0,
            'quality_score': 0.0
        }
        
        # Check missing values
        for col in self.feature_columns:
            if col in df.columns:
                missing = df[col].isnull().sum()
                report['missing_values'][col] = {
                    'count': missing,
                    'percentage': (missing / len(df)) * 100
                }
        
        # Check for invalid ranges
        for col in df.columns:
            if col == 'aqi' and col in df.columns:
                invalid = df[(df[col] < self.aqi_range[0]) | (df[col] > self.aqi_range[1])]
                report['invalid_ranges'][col] = len(invalid)
            elif col == 'pm25' and col in df.columns:
                invalid = df[(df[col] < self.pm25_range[0]) | (df[col] > self.pm25_range[1])]
                report['invalid_ranges'][col] = len(invalid)
            elif col == 'pm10' and col in df.columns:
                invalid = df[(df[col] < self.pm10_range[0]) | (df[col] > self.pm10_range[1])]
                report['invalid_ranges'][col] = len(invalid)
        
        # Check for duplicates
        if 'timestamp' in df.columns and 'latitude' in df.columns and 'longitude' in df.columns:
            duplicates = df.duplicated(subset=['timestamp', 'latitude', 'longitude']).sum()
            report['duplicate_records'] = duplicates
        
        # Calculate quality score (0-100)
        total_issues = sum(report['missing_values'].values()) + sum(report['invalid_ranges'].values()) + report['duplicate_records']
        max_possible_issues = len(df) * len(self.feature_columns)
        report['quality_score'] = max(0, 100 - (total_issues / max_possible_issues) * 100)
        
        logger.info(f"Data quality score: {report['quality_score']:.1f}/100")
        return report
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and preprocess AQI data
        """
        logger.info("Starting data cleaning...")
        initial_count = len(df)
        
        # Make a copy to avoid modifying original
        df_clean = df.copy()
        
        # Convert timestamp to datetime if not already
        if 'timestamp' in df_clean.columns:
            df_clean['timestamp'] = pd.to_datetime(df_clean['timestamp'])
        
        # Remove duplicates
        if 'timestamp' in df_clean.columns and 'latitude' in df_clean.columns and 'longitude' in df_clean.columns:
            df_clean = df_clean.drop_duplicates(subset=['timestamp', 'latitude', 'longitude'], keep='last')
        
        # Remove invalid AQI values
        if 'aqi' in df_clean.columns:
            df_clean = df_clean[(df_clean['aqi'] >= self.aqi_range[0]) & (df_clean['aqi'] <= self.aqi_range[1])]
        
        # Remove invalid PM values
        if 'pm25' in df_clean.columns:
            df_clean = df_clean[(df_clean['pm25'] >= self.pm25_range[0]) & (df_clean['pm25'] <= self.pm25_range[1])]
        
        if 'pm10' in df_clean.columns:
            df_clean = df_clean[(df_clean['pm10'] >= self.pm10_range[0]) & (df_clean['pm10'] <= self.pm10_range[1])]
        
        # Handle missing values using interpolation and imputation
        for col in self.feature_columns:
            if col in df_clean.columns:
                # Sort by timestamp for proper interpolation
                if 'timestamp' in df_clean.columns:
                    df_clean = df_clean.sort_values('timestamp')
                
                # Linear interpolation for small gaps
                df_clean[col] = df_clean[col].interpolate(method='linear', limit=3)
                
                # Forward fill for remaining gaps
                df_clean[col] = df_clean[col].fillna(method='ffill', limit=2)
                
                # Backward fill for remaining gaps
                df_clean[col] = df_clean[col].fillna(method='bfill', limit=2)
                
                # Mean imputation for any remaining missing values
                if df_clean[col].isnull().any():
                    mean_val = df_clean[col].mean()
                    df_clean[col] = df_clean[col].fillna(mean_val)
        
        # Remove rows with all NaN values in feature columns
        feature_cols_present = [col for col in self.feature_columns if col in df_clean.columns]
        df_clean = df_clean.dropna(subset=feature_cols_present, how='all')
        
        final_count = len(df_clean)
        logger.info(f"Data cleaning completed: {initial_count} -> {final_count} records ({final_count/initial_count*100:.1f}% retained)")
        
        return df_clean
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create additional features for better model performance
        """
        logger.info("Engineering features...")
        
        df_features = df.copy()
        
        # Ensure timestamp is datetime
        if 'timestamp' in df_features.columns:
            df_features['timestamp'] = pd.to_datetime(df_features['timestamp'])
            
            # Time-based features
            df_features['hour'] = df_features['timestamp'].dt.hour
            df_features['day_of_week'] = df_features['timestamp'].dt.dayofweek
            df_features['month'] = df_features['timestamp'].dt.month
            df_features['is_weekend'] = (df_features['day_of_week'] >= 5).astype(int)
            
            # Cyclical encoding for time features
            df_features['hour_sin'] = np.sin(2 * np.pi * df_features['hour'] / 24)
            df_features['hour_cos'] = np.cos(2 * np.pi * df_features['hour'] / 24)
            df_features['day_sin'] = np.sin(2 * np.pi * df_features['day_of_week'] / 7)
            df_features['day_cos'] = np.cos(2 * np.pi * df_features['day_of_week'] / 7)
            df_features['month_sin'] = np.sin(2 * np.pi * df_features['month'] / 12)
            df_features['month_cos'] = np.cos(2 * np.pi * df_features['month'] / 12)
        
        # Pollutant ratios and interactions
        if 'pm25' in df_features.columns and 'pm10' in df_features.columns:
            df_features['pm25_pm10_ratio'] = df_features['pm25'] / (df_features['pm10'] + 1e-8)
        
        if 'no2' in df_features.columns and 'o3' in df_features.columns:
            df_features['no2_o3_ratio'] = df_features['no2'] / (df_features['o3'] + 1e-8)
        
        # AQI categories (one-hot encoding)
        if 'aqi' in df_features.columns:
            df_features['aqi_category'] = pd.cut(
                df_features['aqi'], 
                bins=[0, 50, 100, 150, 200, 300, 500],
                labels=['Good', 'Moderate', 'Unhealthy_Sensitive', 'Unhealthy', 'Very_Unhealthy', 'Hazardous']
            )
            
            # One-hot encode AQI categories
            aqi_dummies = pd.get_dummies(df_features['aqi_category'], prefix='aqi')
            df_features = pd.concat([df_features, aqi_dummies], axis=1)
        
        # Rolling statistics (if we have enough data)
        if len(df_features) > 24:  # Need at least 24 hours for rolling stats
            df_features = df_features.sort_values('timestamp')
            
            for col in ['aqi', 'pm25', 'pm10']:
                if col in df_features.columns:
                    df_features[f'{col}_rolling_6h'] = df_features[col].rolling(window=6, min_periods=1).mean()
                    df_features[f'{col}_rolling_12h'] = df_features[col].rolling(window=12, min_periods=1).mean()
                    df_features[f'{col}_rolling_24h'] = df_features[col].rolling(window=24, min_periods=1).mean()
        
        logger.info(f"Feature engineering completed. New shape: {df_features.shape}")
        return df_features
    
    def prepare_sequences(self, 
                         df: pd.DataFrame,
                         sequence_length: int = 24,
                         prediction_horizon: int = 4,
                         target_column: str = 'aqi') -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Prepare sequences for LSTM training
        Returns: (X, y, timestamps)
        """
        logger.info(f"Preparing sequences - Length: {sequence_length}, Horizon: {prediction_horizon}")
        
        # Ensure we have enough data
        if len(df) < sequence_length + prediction_horizon:
            raise ValueError(f"Insufficient data: need {sequence_length + prediction_horizon}, got {len(df)}")
        
        # Sort by timestamp
        if 'timestamp' in df.columns:
            df = df.sort_values('timestamp')
        
        # Select feature columns (exclude non-numeric columns)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        feature_cols = [col for col in numeric_cols if col not in ['id', 'created_at']]
        
        # Prepare feature matrix
        feature_matrix = df[feature_cols].values
        
        # Prepare target matrix
        if target_column in df.columns:
            target_idx = feature_cols.index(target_column)
        else:
            raise ValueError(f"Target column '{target_column}' not found in data")
        
        # Create sequences
        sequences = []
        targets = []
        timestamps = []
        
        for i in range(len(df) - sequence_length - prediction_horizon + 1):
            # Input sequence
            seq = feature_matrix[i:i+sequence_length]
            sequences.append(seq)
            
            # Target sequence (future values)
            target = feature_matrix[i+sequence_length:i+sequence_length+prediction_horizon, target_idx]
            targets.append(target)
            
            # Timestamp for prediction start
            if 'timestamp' in df.columns:
                timestamps.append(df.iloc[i+sequence_length]['timestamp'])
        
        X = np.array(sequences)
        y = np.array(targets)
        timestamps = np.array(timestamps)
        
        logger.info(f"Generated {len(sequences)} sequences")
        logger.info(f"X shape: {X.shape}, y shape: {y.shape}")
        
        return X, y, timestamps
    
    def fit_scalers(self, X: np.ndarray, y: np.ndarray):
        """
        Fit scalers on training data
        """
        logger.info("Fitting scalers...")
        
        # Reshape X for scaling (samples * timesteps, features)
        X_reshaped = X.reshape(-1, X.shape[-1])
        self.scaler_features.fit(X_reshaped)
        
        # Reshape y for scaling
        y_reshaped = y.reshape(-1, 1)
        self.scaler_target.fit(y_reshaped)
        
        self.is_fitted = True
        logger.info("Scalers fitted successfully")
    
    def transform_data(self, X: np.ndarray, y: Optional[np.ndarray] = None) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """
        Transform data using fitted scalers
        """
        if not self.is_fitted:
            raise ValueError("Scalers not fitted. Call fit_scalers first.")
        
        # Transform features
        original_shape = X.shape
        X_reshaped = X.reshape(-1, X.shape[-1])
        X_scaled = self.scaler_features.transform(X_reshaped)
        X_scaled = X_scaled.reshape(original_shape)
        
        # Transform target if provided
        y_scaled = None
        if y is not None:
            original_y_shape = y.shape
            y_reshaped = y.reshape(-1, 1)
            y_scaled = self.scaler_target.transform(y_reshaped)
            y_scaled = y_scaled.reshape(original_y_shape)
        
        return X_scaled, y_scaled
    
    def inverse_transform_target(self, y_scaled: np.ndarray) -> np.ndarray:
        """
        Inverse transform target values
        """
        if not self.is_fitted:
            raise ValueError("Scalers not fitted.")
        
        original_shape = y_scaled.shape
        y_reshaped = y_scaled.reshape(-1, 1)
        y_original = self.scaler_target.inverse_transform(y_reshaped)
        return y_original.reshape(original_shape)
    
    def get_feature_names(self) -> List[str]:
        """
        Get feature names after preprocessing
        """
        if not self.is_fitted:
            return []
        
        # This would be set during fitting in a real implementation
        return self.feature_columns
    
    def save_preprocessor(self, filepath: str):
        """
        Save preprocessor state
        """
        import joblib
        joblib.dump(self, filepath)
        logger.info(f"Preprocessor saved to {filepath}")
    
    @classmethod
    def load_preprocessor(cls, filepath: str):
        """
        Load preprocessor state
        """
        import joblib
        preprocessor = joblib.load(filepath)
        logger.info(f"Preprocessor loaded from {filepath}")
        return preprocessor

def main():
    """Test the preprocessor"""
    # Create sample data for testing
    dates = pd.date_range(start='2024-01-01', periods=100, freq='H')
    sample_data = pd.DataFrame({
        'timestamp': dates,
        'latitude': [22.5726] * 100,
        'longitude': [88.3639] * 100,
        'aqi': np.random.normal(100, 30, 100),
        'pm25': np.random.normal(50, 15, 100),
        'pm10': np.random.normal(80, 20, 100),
        'o3': np.random.normal(40, 10, 100),
        'no2': np.random.normal(30, 8, 100),
        'so2': np.random.normal(10, 3, 100),
        'co': np.random.normal(1, 0.3, 100)
    })
    
    # Add some missing values and outliers
    sample_data.loc[10:15, 'pm25'] = np.nan
    sample_data.loc[20, 'aqi'] = 600  # Outlier
    
    # Test preprocessing
    preprocessor = AQIDataPreprocessor()
    
    # Validate data
    quality_report = preprocessor.validate_data_quality(sample_data)
    print("Quality Report:", quality_report)
    
    # Clean data
    cleaned_data = preprocessor.clean_data(sample_data)
    print(f"Data shape after cleaning: {cleaned_data.shape}")
    
    # Engineer features
    featured_data = preprocessor.engineer_features(cleaned_data)
    print(f"Data shape after feature engineering: {featured_data.shape}")
    
    # Prepare sequences
    X, y, timestamps = preprocessor.prepare_sequences(
        featured_data, 
        sequence_length=24, 
        prediction_horizon=4
    )
    print(f"Sequences - X: {X.shape}, y: {y.shape}")
    
    # Fit scalers
    preprocessor.fit_scalers(X, y)
    
    # Transform data
    X_scaled, y_scaled = preprocessor.transform_data(X, y)
    print(f"Scaled data - X: {X_scaled.shape}, y: {y_scaled.shape}")
    
    logger.info("Preprocessor test completed successfully")

if __name__ == "__main__":
    main()
