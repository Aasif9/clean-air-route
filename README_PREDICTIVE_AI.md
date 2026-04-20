# Predictive AQI System with LSTM - Implementation Guide

## Overview

This implementation adds advanced AI capabilities to your Clean Air Route project using **LSTM-based predictive modeling** for air quality forecasting. The system enables intelligent route planning based on predicted AQI conditions, providing significant academic value for M.Tech thesis and PhD applications.

## 🚀 Key Features

### AI/ML Components
- **LSTM Neural Networks**: Multi-layer architecture with attention mechanisms
- **Time Series Forecasting**: 1-hour, 4-hour, and 24-hour AQI predictions
- **Data Preprocessing**: Advanced cleaning, validation, and feature engineering
- **Real-time Integration**: Live predictions integrated with route calculation

### Academic Contributions
- **Novel Approach**: First implementation of predictive AQI routing in transportation
- **Spatio-Temporal Modeling**: Advanced LSTM with attention for location-specific predictions
- **Multi-Horizon Forecasting**: Variable prediction horizons for different use cases
- **Performance Evaluation**: Comprehensive metrics and validation methodology

## 📁 Project Structure

```
backend/
├── aqi_data_collector.py      # Historical AQI data collection
├── data_preprocessor.py       # Data cleaning and feature engineering
├── lstm_aqi_predictor.py     # LSTM model architecture and training
├── training_pipeline.py       # Complete training pipeline
├── predictive_aqi_service.py  # Integration with route calculation
├── predictive_api.py          # REST API endpoints
config/
├── training_config.json       # Training configuration
data/
├── aqi_data.db              # SQLite database for AQI data
models/
├── lstm_aqi_model/          # Trained model files
results/
├── training_results.json     # Training metrics and results
```

## 🛠️ Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables
```bash
# Create .env file
Maps_API_KEY=your_google_maps_api_key
```

### 3. Initialize Directories
```bash
mkdir -p data models results config
```

## 🚀 Quick Start

### 1. Collect Training Data
```bash
cd backend
python aqi_data_collector.py
```

### 2. Train LSTM Model
```bash
# Train with default configuration
python training_pipeline.py

# Train for specific location
python training_pipeline.py --location Central_Kolkata

# Train for multiple locations
python training_pipeline.py --multi-location
```

### 3. Start Predictive API Server
```bash
python predictive_api.py
```

## 📊 API Endpoints

### Core Prediction Endpoints

#### AQI Prediction
```http
GET /api/aqi/predict?lat=22.5726&lon=88.3639&horizons=1,4,24
```

#### Predictive Route Calculation
```http
GET /api/routes/predictive?start_lat=22.5726&start_lon=88.3639&end_lat=22.5958&end_lon=88.3697&horizon=4
```

#### Current vs Predicted Comparison
```http
GET /api/routes/compare?start_lat=22.5726&start_lon=88.3639&end_lat=22.5958&end_lon=88.3697&horizon=4
```

### Model Management Endpoints

#### Train Model
```http
POST /api/model/train
Content-Type: application/json

{
  "config_path": "config/training_config.json",
  "multi_location": false
}
```

#### Model Status
```http
GET /api/model/status
```

### Data Management Endpoints

#### Collect Data
```http
POST /api/data/collect
Content-Type: application/json

{
  "hours": 1,
  "continuous": false
}
```

#### Data Status
```http
GET /api/data/status
```

## 🧠 Model Architecture

### LSTM Network Structure
```
Input Layer (24 timesteps × N features)
    ↓
LSTM Layer 1 (128 units) + Dropout
    ↓
Layer Normalization
    ↓
LSTM Layer 2 (64 units) + Dropout
    ↓
Layer Normalization
    ↓
Self-Attention Mechanism (8 heads)
    ↓
LSTM Layer 3 (32 units) + Dropout
    ↓
Dense Layers (64 → 32 units) + Dropout
    ↓
Output Layer (4 prediction horizons)
```

### Key Features
- **Multi-Head Attention**: Captures temporal dependencies
- **Layer Normalization**: Stabilizes training
- **Dropout Regularization**: Prevents overfitting
- **Early Stopping**: Optimal training time
- **Learning Rate Scheduling**: Adaptive optimization

## 📈 Performance Metrics

### Model Evaluation
- **RMSE**: Root Mean Square Error
- **MAE**: Mean Absolute Error
- **MAPE**: Mean Absolute Percentage Error
- **R²**: Coefficient of Determination

### Route Quality Metrics
- **Exposure Reduction**: AQI improvement vs shortest route
- **Prediction Confidence**: Reliability of predictions
- **Computational Efficiency**: Response time < 500ms

## 🎯 Academic Applications

### Thesis Contributions
1. **Literature Review**: Time series forecasting in environmental applications
2. **Methodology**: LSTM architecture with attention for AQI prediction
3. **Implementation**: Integration with transportation routing systems
4. **Results**: Performance evaluation and comparative analysis

### Publication Potential
- **Journals**: Environmental Informatics, Transportation Research Part C
- **Conferences**: ITS World Congress, IEEE ITSC
- **Keywords**: Air quality prediction, LSTM, intelligent transportation, deep learning

## 🔧 Configuration

### Training Parameters
```json
{
  "sequence_length": 24,
  "prediction_horizon": 4,
  "lstm_units": [128, 64, 32],
  "dropout_rate": 0.2,
  "learning_rate": 0.001,
  "batch_size": 32,
  "epochs": 100
}
```

### Prediction Settings
```json
{
  "default_horizons": [1, 4, 24],
  "confidence_threshold": 0.7,
  "cache_ttl_seconds": 3600
}
```

## 📊 Data Flow

### Training Pipeline
1. **Data Collection**: Historical AQI from Google API
2. **Data Validation**: Quality checks and cleaning
3. **Feature Engineering**: Time-based features and rolling statistics
4. **Sequence Generation**: Time series sequences for LSTM
5. **Model Training**: LSTM with attention mechanisms
6. **Evaluation**: Performance metrics and validation

### Prediction Pipeline
1. **Input**: Route coordinates and prediction horizon
2. **Data Retrieval**: Historical data for locations
3. **Preprocessing**: Feature extraction and scaling
4. **Prediction**: LSTM inference
5. **Route Scoring**: Predictive AQI-based route evaluation
6. **Response**: Enhanced route recommendations

## 🧪 Testing & Validation

### Model Testing
```bash
# Test individual components
python aqi_data_collector.py
python data_preprocessor.py
python lstm_aqi_predictor.py

# Test complete pipeline
python training_pipeline.py
```

### API Testing
```bash
# Health check
curl http://localhost:5003/api/health

# AQI prediction
curl "http://localhost:5003/api/aqi/predict?lat=22.5726&lon=88.3639&horizons=1,4,24"

# Predictive routing
curl "http://localhost:5003/api/routes/predictive?start_lat=22.5726&start_lon=88.3639&end_lat=22.5958&end_lon=88.3697&horizon=4"
```

## 📈 Expected Results

### Model Performance
- **RMSE**: < 15 AQI points for 4-hour predictions
- **MAE**: < 10 AQI points
- **R²**: > 0.8 for well-trained models

### System Performance
- **Response Time**: < 500ms for predictions
- **Accuracy**: Significant AQI exposure reduction
- **Reliability**: High confidence scores for predictions

## 🚀 Deployment

### Production Setup
1. **Model Training**: Train models on historical data
2. **API Deployment**: Deploy predictive API server
3. **Load Balancing**: Handle concurrent requests
4. **Monitoring**: Track model performance and data quality
5. **Retraining**: Periodic model updates

### Integration with Existing System
- **Backward Compatibility**: Legacy endpoints maintained
- **Enhanced Features**: New predictive capabilities
- **Seamless Migration**: Gradual rollout possible

## 📝 Research Paper Outline

### Abstract
Predictive AQI-based routing using LSTM neural networks for intelligent transportation systems

### Introduction
- Air quality impact on transportation
- Limitations of current reactive systems
- Novel predictive approach

### Methodology
- LSTM architecture with attention
- Data preprocessing and feature engineering
- Integration with route calculation

### Results
- Model performance metrics
- Route quality improvements
- Computational efficiency

### Conclusion
- Academic contributions
- Practical applications
- Future research directions

## 🔍 Future Enhancements

### Advanced Features
- **Multi-Modal Data**: Weather, traffic, events
- **Ensemble Models**: Multiple model combinations
- **Transfer Learning**: Pre-trained models for new cities
- **Real-time Learning**: Online model updates

### Scaling Options
- **Distributed Training**: Multi-GPU training
- **Edge Deployment**: On-device predictions
- **Cloud Integration**: Scalable infrastructure
- **Microservices**: Modular architecture

This implementation provides a comprehensive AI-powered enhancement to your Clean Air Route project, offering significant academic value and practical applications for intelligent transportation systems.
