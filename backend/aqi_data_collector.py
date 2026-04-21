"""
AQI Data Collector for Predictive Modeling
Collects and stores historical AQI data for LSTM training
"""

import os
import time
import json
import sqlite3
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class AQIDataPoint:
    """Data structure for AQI measurements"""
    latitude: float
    longitude: float
    aqi: float
    timestamp: datetime
    pm25: Optional[float] = None
    pm10: Optional[float] = None
    o3: Optional[float] = None
    no2: Optional[float] = None
    so2: Optional[float] = None
    co: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for database storage"""
        return {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'aqi': self.aqi,
            'timestamp': self.timestamp.isoformat(),
            'pm25': self.pm25,
            'pm10': self.pm10,
            'o3': self.o3,
            'no2': self.no2,
            'so2': self.so2,
            'co': self.co
        }

class AQIDataCollector:
    """
    Collects AQI data from Google Air Quality API
    Stores historical data for LSTM model training
    """
    
    def __init__(self, api_key: str, db_path: str = "aqi_data.db"):
        self.api_key = api_key
        self.db_path = db_path
        self.aqi_api_url = "https://airquality.googleapis.com/v1/currentConditions:lookup"
        
        # Initialize database
        self._init_database()
        
        # Define Kolkata monitoring locations (strategic points)
        self.kolkata_locations = [
            (22.5726, 88.3639),  # Central Kolkata
            (22.5958, 88.3697),  # Salt Lake
            (22.5411, 88.3407),  # Alipore
            (22.5853, 88.3696),  # Sealdah
            (22.6139, 88.4016),  # Howrah
            (22.5186, 88.3525),  # Behala
            (22.6084, 88.3949),  # Shibpur
            (22.5658, 88.3629),  # Park Street
            (22.5975, 88.4149),  # Garia
            (22.5274, 88.3295),  # Tollygunge
        ]
        
    def _init_database(self):
        """Initialize SQLite database for AQI data storage"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create AQI measurements table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS aqi_measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    aqi REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    pm25 REAL,
                    pm10 REAL,
                    o3 REAL,
                    no2 REAL,
                    so2 REAL,
                    co REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(latitude, longitude, timestamp)
                )
            ''')
            
            # Create indexes for better query performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_location_timestamp 
                ON aqi_measurements(latitude, longitude, timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON aqi_measurements(timestamp)
            ''')
            
            conn.commit()
            conn.close()
            logger.info(f"Database initialized: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def fetch_aqi_data(self, latitude: float, longitude: float) -> Optional[AQIDataPoint]:
        """
        Fetch current AQI data from Google API
        """
        try:
            response = requests.post(
                self.aqi_api_url,
                params={"key": self.api_key},
                json={
                    "location": {"latitude": latitude, "longitude": longitude},
                    "universalAqi": True,
                    "extraComputations": ["LOCAL_AQI", "POLLUTANT_CONCENTRATION"],
                },
                timeout=10
            )
            
            if response.status_code != 200:
                logger.warning(f"API request failed: {response.status_code}")
                return None
            
            data = response.json()
            
            # Extract AQI value
            aqi = data["indexes"][0]["aqi"]
            
            # Extract pollutant concentrations if available
            pollutants = {}
            if "pollutants" in data:
                for pollutant in data["pollutants"]:
                    code = pollutant.get("code", "")
                    concentration = pollutant.get("concentration", {})
                    if "value" in concentration:
                        pollutants[code] = concentration["value"]
            
            return AQIDataPoint(
                latitude=latitude,
                longitude=longitude,
                aqi=float(aqi),
                timestamp=datetime.now(),
                pm25=pollutants.get("PM2.5"),
                pm10=pollutants.get("PM10"),
                o3=pollutants.get("O3"),
                no2=pollutants.get("NO2"),
                so2=pollutants.get("SO2"),
                co=pollutants.get("CO")
            )
            
        except Exception as e:
            logger.error(f"Failed to fetch AQI data for ({latitude}, {longitude}): {e}")
            return None
    
    def store_aqi_data(self, data_point: AQIDataPoint) -> bool:
        """
        Store AQI data point in database
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO aqi_measurements 
                (latitude, longitude, aqi, timestamp, pm25, pm10, o3, no2, so2, co)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data_point.latitude,
                data_point.longitude,
                data_point.aqi,
                data_point.timestamp.isoformat(),
                data_point.pm25,
                data_point.pm10,
                data_point.o3,
                data_point.no2,
                data_point.so2,
                data_point.co
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to store AQI data: {e}")
            return False
    
    def collect_all_locations(self) -> List[AQIDataPoint]:
        """
        Collect AQI data from all predefined Kolkata locations
        """
        collected_data = []
        
        for lat, lon in self.kolkata_locations:
            logger.info(f"Collecting AQI data for location: ({lat}, {lon})")
            
            data_point = self.fetch_aqi_data(lat, lon)
            if data_point:
                if self.store_aqi_data(data_point):
                    collected_data.append(data_point)
                    logger.info(f"Stored AQI data: AQI={data_point.aqi}")
                else:
                    logger.warning(f"Failed to store data for ({lat}, {lon})")
            else:
                logger.warning(f"No data received for ({lat}, {lon})")
            
            # Add delay to avoid rate limiting
            time.sleep(0.5)
        
        logger.info(f"Collected {len(collected_data)} AQI measurements")
        return collected_data
    
    def get_historical_data(self, 
                          days_back: int = 30,
                          latitude: Optional[float] = None,
                          longitude: Optional[float] = None) -> pd.DataFrame:
        """
        Retrieve historical AQI data for model training
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Build query based on parameters
            query = "SELECT * FROM aqi_measurements WHERE timestamp >= ?"
            params = [(datetime.now() - timedelta(days=days_back)).isoformat()]
            
            if latitude and longitude:
                query += " AND latitude = ? AND longitude = ?"
                params.extend([latitude, longitude])
            
            query += " ORDER BY timestamp ASC"
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            logger.info(f"Retrieved {len(df)} historical records")
            return df
            
        except Exception as e:
            logger.error(f"Failed to retrieve historical data: {e}")
            return pd.DataFrame()
    
    def get_training_sequences(self, 
                             sequence_length: int = 24,
                             prediction_horizon: int = 4,
                             location: Optional[Tuple[float, float]] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate training sequences for LSTM model
        Returns (X, y) where X is input sequence and y is target values
        """
        df = self.get_historical_data(days_back=90, latitude=location[0], longitude=location[1] if location else None)
        
        if len(df) < sequence_length + prediction_horizon:
            logger.warning(f"Insufficient data: need {sequence_length + prediction_horizon}, got {len(df)}")
            return np.array([]), np.array([])
        
        # Create sequences
        sequences = []
        targets = []
        
        for i in range(len(df) - sequence_length - prediction_horizon + 1):
            # Input sequence
            seq = df.iloc[i:i+sequence_length][['aqi', 'pm25', 'pm10', 'o3', 'no2', 'so2', 'co']].values
            sequences.append(seq)
            
            # Target (future AQI values)
            target = df.iloc[i+sequence_length:i+sequence_length+prediction_horizon]['aqi'].values
            targets.append(target)
        
        X = np.array(sequences)
        y = np.array(targets)
        
        logger.info(f"Generated {len(sequences)} training sequences")
        logger.info(f"Input shape: {X.shape}, Target shape: {y.shape}")
        
        return X, y
    
    def start_continuous_collection(self, interval_minutes: int = 60):
        """
        Start continuous AQI data collection
        """
        logger.info(f"Starting continuous collection every {interval_minutes} minutes")
        
        while True:
            try:
                start_time = time.time()
                
                # Collect data from all locations
                self.collect_all_locations()
                
                # Calculate sleep time
                elapsed = time.time() - start_time
                sleep_time = max(0, (interval_minutes * 60) - elapsed)
                
                logger.info(f"Next collection in {sleep_time/60:.1f} minutes")
                time.sleep(sleep_time)
                
            except KeyboardInterrupt:
                logger.info("Stopping continuous collection")
                break
            except Exception as e:
                logger.error(f"Error in continuous collection: {e}")
                time.sleep(300)  # Wait 5 minutes before retrying

def main():
    """Main function for testing the data collector"""
    api_key = os.getenv("Maps_API_KEY")
    if not api_key:
        logger.error("Maps_API_KEY not found in environment variables")
        return
    
    collector = AQIDataCollector(api_key)
    
    # Test data collection
    logger.info("Testing AQI data collection...")
    data_points = collector.collect_all_locations()
    
    # Test historical data retrieval
    logger.info("Testing historical data retrieval...")
    historical_df = collector.get_historical_data(days_back=7)
    logger.info(f"Historical data shape: {historical_df.shape}")
    
    # Test sequence generation
    logger.info("Testing training sequence generation...")
    X, y = collector.get_training_sequences(sequence_length=24, prediction_horizon=4)
    logger.info(f"Training sequences - X: {X.shape}, y: {y.shape}")

if __name__ == "__main__":
    main()
