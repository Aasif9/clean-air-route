"""
LSTM-based AQI Prediction Model
Advanced deep learning architecture for air quality forecasting with attention mechanisms
"""

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models, callbacks, optimizers
import numpy as np
import pandas as pd
from typing import Tuple, Dict, List, Optional
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
import logging
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LSTMAQIPredictor:
    """
    Advanced LSTM model for AQI prediction with attention mechanisms
    """
    
    def __init__(self, 
                 sequence_length: int = 24,
                 prediction_horizon: int = 4,
                 n_features: int = 7,
                 model_path: str = "models/lstm_aqi_model"):
        
        self.sequence_length = sequence_length
        self.prediction_horizon = prediction_horizon
        self.n_features = n_features
        self.model_path = model_path
        
        self.model = None
        self.history = None
        self.is_trained = False
        
        # Model hyperparameters
        self.lstm_units = [128, 64, 32]
        self.dropout_rate = 0.2
        self.learning_rate = 0.001
        self.batch_size = 32
        self.epochs = 100
        
        # Create model directory
        os.makedirs(model_path, exist_ok=True)
        
    def build_model(self) -> keras.Model:
        """
        Build advanced LSTM architecture with attention mechanism
        """
        logger.info("Building LSTM model architecture...")
        
        # Input layer
        input_layer = layers.Input(shape=(self.sequence_length, self.n_features), name='input_layer')
        
        # First LSTM layer with return sequences for attention
        lstm1 = layers.LSTM(
            self.lstm_units[0], 
            return_sequences=True,
            dropout=self.dropout_rate,
            recurrent_dropout=self.dropout_rate,
            name='lstm_1'
        )(input_layer)
        
        # Layer normalization
        norm1 = layers.LayerNormalization(name='norm_1')(lstm1)
        
        # Second LSTM layer
        lstm2 = layers.LSTM(
            self.lstm_units[1],
            return_sequences=True,
            dropout=self.dropout_rate,
            recurrent_dropout=self.dropout_rate,
            name='lstm_2'
        )(norm1)
        
        # Layer normalization
        norm2 = layers.LayerNormalization(name='norm_2')(lstm2)
        
        # Self-attention mechanism
        attention = layers.MultiHeadAttention(
            num_heads=8,
            key_dim=self.lstm_units[1] // 8,
            dropout=self.dropout_rate,
            name='self_attention'
        )(norm2, norm2)
        
        # Add residual connection
        attention_norm = layers.LayerNormalization(name='attention_norm')(attention + norm2)
        
        # Third LSTM layer
        lstm3 = layers.LSTM(
            self.lstm_units[2],
            return_sequences=False,
            dropout=self.dropout_rate,
            recurrent_dropout=self.dropout_rate,
            name='lstm_3'
        )(attention_norm)
        
        # Dense layers for processing
        dense1 = layers.Dense(64, activation='relu', name='dense_1')(lstm3)
        dropout1 = layers.Dropout(self.dropout_rate, name='dropout_1')(dense1)
        
        dense2 = layers.Dense(32, activation='relu', name='dense_2')(dropout1)
        dropout2 = layers.Dropout(self.dropout_rate, name='dropout_2')(dense2)
        
        # Output layer - multi-horizon predictions
        output_layer = layers.Dense(
            self.prediction_horizon, 
            activation='linear', 
            name='output'
        )(dropout2)
        
        # Create model
        model = keras.Model(inputs=input_layer, outputs=output_layer, name='LSTM_AQI_Predictor')
        
        # Compile model
        optimizer = optimizers.Adam(learning_rate=self.learning_rate)
        model.compile(
            optimizer=optimizer,
            loss='mse',
            metrics=['mae', 'mape']
        )
        
        # Print model summary
        model.summary()
        
        self.model = model
        return model
    
    def build_callbacks(self) -> List[callbacks.Callback]:
        """
        Build training callbacks for better model performance
        """
        callback_list = []
        
        # Early stopping
        early_stopping = callbacks.EarlyStopping(
            monitor='val_loss',
            patience=15,
            restore_best_weights=True,
            verbose=1
        )
        callback_list.append(early_stopping)
        
        # Reduce learning rate on plateau
        reduce_lr = callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=7,
            min_lr=1e-7,
            verbose=1
        )
        callback_list.append(reduce_lr)
        
        # Model checkpoint
        checkpoint_path = os.path.join(self.model_path, 'best_model.h5')
        model_checkpoint = callbacks.ModelCheckpoint(
            filepath=checkpoint_path,
            monitor='val_loss',
            save_best_only=True,
            save_weights_only=False,
            verbose=1
        )
        callback_list.append(model_checkpoint)
        
        # CSV logger
        csv_logger = callbacks.CSVLogger(
            filename=os.path.join(self.model_path, 'training_log.csv'),
            append=True
        )
        callback_list.append(csv_logger)
        
        return callback_list
    
    def train(self, 
              X_train: np.ndarray, 
              y_train: np.ndarray,
              X_val: Optional[np.ndarray] = None,
              y_val: Optional[np.ndarray] = None,
              validation_split: float = 0.2) -> Dict:
        """
        Train the LSTM model
        """
        if self.model is None:
            self.build_model()
        
        logger.info(f"Training model - X_train: {X_train.shape}, y_train: {y_train.shape}")
        
        # Prepare validation data
        if X_val is None and y_val is None:
            validation_data = None
            validation_split = validation_split
        else:
            validation_data = (X_val, y_val)
            validation_split = 0.0
        
        # Build callbacks
        callback_list = self.build_callbacks()
        
        # Train model
        start_time = datetime.now()
        
        self.history = self.model.fit(
            X_train, y_train,
            validation_data=validation_data,
            validation_split=validation_split,
            epochs=self.epochs,
            batch_size=self.batch_size,
            callbacks=callback_list,
            verbose=1
        )
        
        training_time = datetime.now() - start_time
        logger.info(f"Training completed in {training_time}")
        
        # Evaluate model
        if validation_data:
            val_loss, val_mae, val_mape = self.model.evaluate(X_val, y_val, verbose=0)
            logger.info(f"Validation - Loss: {val_loss:.4f}, MAE: {val_mae:.4f}, MAPE: {val_mape:.4f}")
        
        self.is_trained = True
        
        return {
            'training_time': str(training_time),
            'history': self.history.history,
            'validation_metrics': {
                'val_loss': val_loss if validation_data else None,
                'val_mae': val_mae if validation_data else None,
                'val_mape': val_mape if validation_data else None
            }
        }
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions using trained model
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        logger.info(f"Making predictions for input shape: {X.shape}")
        
        predictions = self.model.predict(X, verbose=0)
        
        logger.info(f"Predictions generated with shape: {predictions.shape}")
        return predictions
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict:
        """
        Evaluate model performance
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first.")
        
        logger.info(f"Evaluating model - X_test: {X_test.shape}, y_test: {y_test.shape}")
        
        # Make predictions
        y_pred = self.predict(X_test)
        
        # Calculate metrics
        metrics = {}
        
        # Overall metrics
        metrics['rmse'] = np.sqrt(mean_squared_error(y_test.flatten(), y_pred.flatten()))
        metrics['mae'] = mean_absolute_error(y_test.flatten(), y_pred.flatten())
        metrics['r2'] = r2_score(y_test.flatten(), y_pred.flatten())
        
        # Horizon-specific metrics
        for h in range(self.prediction_horizon):
            y_true_h = y_test[:, h]
            y_pred_h = y_pred[:, h]
            
            metrics[f'horizon_{h+1}_rmse'] = np.sqrt(mean_squared_error(y_true_h, y_pred_h))
            metrics[f'horizon_{h+1}_mae'] = mean_absolute_error(y_true_h, y_pred_h)
            metrics[f'horizon_{h+1}_r2'] = r2_score(y_true_h, y_pred_h)
        
        logger.info(f"Evaluation completed - RMSE: {metrics['rmse']:.4f}, MAE: {metrics['mae']:.4f}, R²: {metrics['r2']:.4f}")
        
        return metrics, y_pred
    
    def plot_training_history(self, save_path: Optional[str] = None):
        """
        Plot training history
        """
        if self.history is None:
            logger.warning("No training history available")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Loss plot
        axes[0, 0].plot(self.history.history['loss'], label='Training Loss')
        if 'val_loss' in self.history.history:
            axes[0, 0].plot(self.history.history['val_loss'], label='Validation Loss')
        axes[0, 0].set_title('Model Loss')
        axes[0, 0].set_xlabel('Epoch')
        axes[0, 0].set_ylabel('Loss')
        axes[0, 0].legend()
        axes[0, 0].grid(True)
        
        # MAE plot
        axes[0, 1].plot(self.history.history['mae'], label='Training MAE')
        if 'val_mae' in self.history.history:
            axes[0, 1].plot(self.history.history['val_mae'], label='Validation MAE')
        axes[0, 1].set_title('Model MAE')
        axes[0, 1].set_xlabel('Epoch')
        axes[0, 1].set_ylabel('MAE')
        axes[0, 1].legend()
        axes[0, 1].grid(True)
        
        # MAPE plot
        axes[1, 0].plot(self.history.history['mape'], label='Training MAPE')
        if 'val_mape' in self.history.history:
            axes[1, 0].plot(self.history.history['val_mape'], label='Validation MAPE')
        axes[1, 0].set_title('Model MAPE')
        axes[1, 0].set_xlabel('Epoch')
        axes[1, 0].set_ylabel('MAPE')
        axes[1, 0].legend()
        axes[1, 0].grid(True)
        
        # Learning rate plot
        if 'lr' in self.history.history:
            axes[1, 1].plot(self.history.history['lr'], label='Learning Rate')
            axes[1, 1].set_title('Learning Rate')
            axes[1, 1].set_xlabel('Epoch')
            axes[1, 1].set_ylabel('Learning Rate')
            axes[1, 1].legend()
            axes[1, 1].grid(True)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Training history plot saved to {save_path}")
        
        plt.show()
    
    def plot_predictions(self, 
                        y_true: np.ndarray, 
                        y_pred: np.ndarray,
                        n_samples: int = 5,
                        save_path: Optional[str] = None):
        """
        Plot predictions vs actual values
        """
        fig, axes = plt.subplots(min(n_samples, 3), 2, figsize=(15, 5 * min(n_samples, 3)))
        
        if n_samples == 1:
            axes = axes.reshape(1, -1)
        
        for i in range(min(n_samples, len(y_true))):
            # Time series plot
            axes[i, 0].plot(y_true[i], 'b-', label='Actual', linewidth=2)
            axes[i, 0].plot(y_pred[i], 'r--', label='Predicted', linewidth=2)
            axes[i, 0].set_title(f'Sample {i+1}: Time Series')
            axes[i, 0].set_xlabel('Time Steps')
            axes[i, 0].set_ylabel('AQI')
            axes[i, 0].legend()
            axes[i, 0].grid(True)
            
            # Scatter plot
            axes[i, 1].scatter(y_true[i], y_pred[i], alpha=0.6)
            axes[i, 1].plot([y_true[i].min(), y_true[i].max()], 
                           [y_true[i].min(), y_true[i].max()], 'r--', linewidth=2)
            axes[i, 1].set_title(f'Sample {i+1}: Predicted vs Actual')
            axes[i, 1].set_xlabel('Actual AQI')
            axes[i, 1].set_ylabel('Predicted AQI')
            axes[i, 1].grid(True)
            
            # Calculate R² for this sample
            r2 = r2_score(y_true[i], y_pred[i])
            axes[i, 1].text(0.05, 0.95, f'R² = {r2:.3f}', 
                          transform=axes[i, 1].transAxes, 
                          bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.5))
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Predictions plot saved to {save_path}")
        
        plt.show()
    
    def save_model(self, save_path: Optional[str] = None):
        """
        Save trained model and metadata
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Cannot save.")
        
        if save_path is None:
            save_path = self.model_path
        
        # Save model
        model_file = os.path.join(save_path, 'lstm_aqi_model.h5')
        self.model.save(model_file)
        
        # Save model configuration
        config = {
            'sequence_length': self.sequence_length,
            'prediction_horizon': self.prediction_horizon,
            'n_features': self.n_features,
            'lstm_units': self.lstm_units,
            'dropout_rate': self.dropout_rate,
            'learning_rate': self.learning_rate,
            'batch_size': self.batch_size,
            'epochs': self.epochs
        }
        
        config_file = os.path.join(save_path, 'model_config.json')
        joblib.dump(config, config_file)
        
        logger.info(f"Model saved to {save_path}")
    
    @classmethod
    def load_model(cls, load_path: str):
        """
        Load trained model
        """
        # Load configuration
        config_file = os.path.join(load_path, 'model_config.json')
        config = joblib.load(config_file)
        
        # Create instance
        predictor = cls(
            sequence_length=config['sequence_length'],
            prediction_horizon=config['prediction_horizon'],
            n_features=config['n_features'],
            model_path=load_path
        )
        
        # Load model
        model_file = os.path.join(load_path, 'lstm_aqi_model.h5')
        predictor.model = keras.models.load_model(model_file)
        predictor.is_trained = True
        
        logger.info(f"Model loaded from {load_path}")
        return predictor

def main():
    """Test the LSTM AQI predictor"""
    # Generate sample data
    np.random.seed(42)
    n_samples = 1000
    
    X = np.random.randn(n_samples, 24, 7)  # 24 hours, 7 features
    y = np.random.randn(n_samples, 4)     # 4-hour prediction horizon
    
    # Split data
    split_idx = int(0.8 * n_samples)
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]
    
    # Create and train model
    predictor = LSTMAQIPredictor(
        sequence_length=24,
        prediction_horizon=4,
        n_features=7
    )
    
    # Build model
    predictor.build_model()
    
    # Train model
    training_results = predictor.train(X_train, y_train, X_val, y_val)
    
    # Evaluate model
    metrics, predictions = predictor.evaluate(X_val, y_val)
    
    print("Evaluation Metrics:")
    for key, value in metrics.items():
        print(f"{key}: {value:.4f}")
    
    # Plot results
    predictor.plot_training_history()
    predictor.plot_predictions(y_val, predictions, n_samples=3)
    
    # Save model
    predictor.save_model()
    
    logger.info("LSTM AQI Predictor test completed successfully")

if __name__ == "__main__":
    main()
