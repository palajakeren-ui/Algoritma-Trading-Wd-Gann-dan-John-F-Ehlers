"""
ML Transformer Model Module
Transformer architecture for time series
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from loguru import logger

try:
    import tensorflow as tf
    from tensorflow.keras.models import Model
    from tensorflow.keras.layers import (
        Input, Dense, Dropout, LayerNormalization,
        MultiHeadAttention, GlobalAveragePooling1D
    )
    HAS_TF = True
except ImportError:
    HAS_TF = False


class TransformerBlock(tf.keras.layers.Layer if HAS_TF else object):
    """Transformer block with multi-head attention"""
    
    def __init__(self, embed_dim: int, num_heads: int, ff_dim: int, dropout: float = 0.1):
        if HAS_TF:
            super().__init__()
            self.att = MultiHeadAttention(num_heads=num_heads, key_dim=embed_dim)
            self.ffn = tf.keras.Sequential([
                Dense(ff_dim, activation='relu'),
                Dense(embed_dim)
            ])
            self.layernorm1 = LayerNormalization(epsilon=1e-6)
            self.layernorm2 = LayerNormalization(epsilon=1e-6)
            self.dropout1 = Dropout(dropout)
            self.dropout2 = Dropout(dropout)
    
    def call(self, inputs, training=None):
        attn_output = self.att(inputs, inputs)
        attn_output = self.dropout1(attn_output, training=training)
        out1 = self.layernorm1(inputs + attn_output)
        ffn_output = self.ffn(out1)
        ffn_output = self.dropout2(ffn_output, training=training)
        return self.layernorm2(out1 + ffn_output)


class TransformerModel:
    """
    Transformer model for time series prediction.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.model = None
        self.sequence_length = self.config.get('sequence_length', 60)
        
        logger.info("TransformerModel initialized")
    
    def build_model(
        self,
        input_shape: Tuple[int, int],
        num_heads: int = 4,
        ff_dim: int = 64,
        num_blocks: int = 2,
        dropout: float = 0.1
    ):
        """Build Transformer model"""
        if not HAS_TF:
            logger.error("TensorFlow not installed")
            return
        
        seq_len, features = input_shape
        
        inputs = Input(shape=input_shape)
        x = inputs
        
        # Project to embed dimension
        embed_dim = 32
        x = Dense(embed_dim)(x)
        
        # Transformer blocks
        for _ in range(num_blocks):
            x = TransformerBlock(embed_dim, num_heads, ff_dim, dropout)(x)
        
        # Global pooling and output
        x = GlobalAveragePooling1D()(x)
        x = Dropout(dropout)(x)
        x = Dense(25, activation='relu')(x)
        outputs = Dense(1)(x)
        
        self.model = Model(inputs, outputs)
        self.model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        
        logger.info(f"Transformer model built with {num_blocks} blocks")
    
    def prepare_data(self, df: pd.DataFrame, target_col: str = 'close') -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for transformer"""
        data = df.values
        target_idx = df.columns.get_loc(target_col) if target_col in df.columns else -1
        
        X, y = [], []
        for i in range(self.sequence_length, len(data)):
            X.append(data[i-self.sequence_length:i])
            y.append(data[i, target_idx])
        
        return np.array(X), np.array(y)
    
    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        epochs: int = 50,
        batch_size: int = 32,
        validation_split: float = 0.2
    ) -> Dict:
        """Train transformer model"""
        if not HAS_TF or self.model is None:
            return {'error': 'Model not ready'}
        
        early_stop = tf.keras.callbacks.EarlyStopping(
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
        
        return {
            'loss': history.history['loss'][-1],
            'val_loss': history.history['val_loss'][-1],
            'epochs': len(history.history['loss'])
        }
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate predictions"""
        if self.model is None:
            return np.array([])
        return self.model.predict(X, verbose=0).flatten()
    
    def save(self, filepath: str):
        """Save model"""
        if self.model:
            self.model.save(filepath)
    
    def load(self, filepath: str):
        """Load model"""
        if HAS_TF:
            self.model = tf.keras.models.load_model(filepath)
