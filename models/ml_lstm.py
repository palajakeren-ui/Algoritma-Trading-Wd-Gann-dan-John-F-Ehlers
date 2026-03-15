"""
ML LSTM Model Module
LSTM neural network for sequence prediction
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from loguru import logger

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping
    HAS_TF = True
except ImportError:
    HAS_TF = False
    logger.warning("TensorFlow not installed")


class LSTMModel:
    """
    LSTM model for time series prediction.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.model = None
        self.sequence_length = self.config.get('sequence_length', 60)
        self.scaler = None
        
        logger.info("LSTMModel initialized")
    
    def build_model(self, input_shape: Tuple[int, int], output_size: int = 1) -> None:
        """Build LSTM architecture"""
        if not HAS_TF:
            logger.error("TensorFlow not installed")
            return
        
        self.model = Sequential([
            LSTM(50, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(25, activation='relu'),
            Dense(output_size)
        ])
        
        self.model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        logger.info(f"LSTM model built with input shape {input_shape}")
    
    def prepare_sequences(
        self,
        data: np.ndarray,
        target_col: int = -1
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare sequences for LSTM"""
        X, y = [], []
        
        for i in range(self.sequence_length, len(data)):
            X.append(data[i-self.sequence_length:i])
            y.append(data[i, target_col])
        
        return np.array(X), np.array(y)
    
    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        epochs: int = 50,
        batch_size: int = 32,
        validation_split: float = 0.2
    ) -> Dict:
        """Train LSTM model"""
        if not HAS_TF or self.model is None:
            return {'error': 'Model not ready'}
        
        early_stop = EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        )
        
        history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            callbacks=[early_stop],
            verbose=0
        )
        
        final_loss = history.history['loss'][-1]
        final_val_loss = history.history['val_loss'][-1]
        
        logger.info(f"LSTM trained - Loss: {final_loss:.4f}, Val Loss: {final_val_loss:.4f}")
        
        return {
            'loss': final_loss,
            'val_loss': final_val_loss,
            'epochs_trained': len(history.history['loss'])
        }
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict future values"""
        if self.model is None:
            return np.array([])
        return self.model.predict(X, verbose=0)
    
    def predict_next(self, recent_data: np.ndarray, steps: int = 1) -> List[float]:
        """Predict next n steps"""
        predictions = []
        current_sequence = recent_data.copy()
        
        for _ in range(steps):
            pred = self.model.predict(current_sequence.reshape(1, *current_sequence.shape), verbose=0)
            predictions.append(float(pred[0, 0]))
            
            # Roll sequence
            current_sequence = np.roll(current_sequence, -1, axis=0)
            current_sequence[-1] = pred[0]
        
        return predictions
    
    def save(self, filepath: str):
        """Save model"""
        if self.model is not None:
            self.model.save(filepath)
            logger.info(f"LSTM saved to {filepath}")
    
    def load(self, filepath: str):
        """Load model"""
        if HAS_TF:
            self.model = tf.keras.models.load_model(filepath)
            logger.info(f"LSTM loaded from {filepath}")
