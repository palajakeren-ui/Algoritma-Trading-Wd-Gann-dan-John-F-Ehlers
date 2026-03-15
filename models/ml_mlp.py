"""
MLP (Multi-Layer Perceptron) Neural Network Model
Deep learning model for trading signal predictions.
"""
import numpy as np
import pandas as pd
from loguru import logger
from typing import Dict, List, Optional, Tuple
import pickle
import os


class MLPModel:
    """
    Multi-Layer Perceptron neural network for trading predictions.
    
    This implementation can use either PyTorch, TensorFlow, or a pure
    NumPy fallback for maximum compatibility.
    """
    
    def __init__(self, config: Dict = None, model_path: str = None):
        """
        Initialize MLP model.
        
        Args:
            config (Dict): Model configuration
            model_path (str): Path to saved model
        """
        self.config = config or {}
        self.model_path = model_path or "outputs/models/mlp_model.pkl"
        self.model = None
        self.scaler = None
        self.is_trained = False
        
        # Architecture parameters
        self.hidden_layers = self.config.get('hidden_layers', [128, 64, 32])
        self.dropout_rate = self.config.get('dropout_rate', 0.3)
        self.learning_rate = self.config.get('learning_rate', 0.001)
        self.n_epochs = self.config.get('epochs', 100)
        self.batch_size = self.config.get('batch_size', 32)
        
        logger.info(f"MLPModel initialized with layers: {self.hidden_layers}")
    
    def _check_torch(self) -> bool:
        """Check if PyTorch is available."""
        try:
            import torch
            return True
        except ImportError:
            return False
    
    def _check_sklearn(self) -> bool:
        """Check if sklearn is available."""
        try:
            from sklearn.neural_network import MLPClassifier
            return True
        except ImportError:
            return False
    
    def train(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame = None,
        y_val: pd.Series = None
    ) -> Dict:
        """
        Train MLP model.
        
        Args:
            X_train (pd.DataFrame): Training features
            y_train (pd.Series): Training labels
            X_val (pd.DataFrame): Validation features
            y_val (pd.Series): Validation labels
            
        Returns:
            Dict: Training metrics
        """
        logger.info(f"Training MLP model with {len(X_train)} samples")
        
        # Standardize features
        self._fit_scaler(X_train)
        X_train_scaled = self._transform(X_train)
        X_val_scaled = self._transform(X_val) if X_val is not None else None
        
        if self._check_torch():
            return self._train_torch(X_train_scaled, y_train.values, X_val_scaled, 
                                     y_val.values if y_val is not None else None)
        elif self._check_sklearn():
            return self._train_sklearn(X_train_scaled, y_train.values)
        else:
            return self._train_numpy(X_train_scaled, y_train.values)
    
    def _fit_scaler(self, X: pd.DataFrame):
        """Fit feature scaler."""
        self.scaler = {
            'mean': X.mean().values,
            'std': X.std().values + 1e-8
        }
    
    def _transform(self, X: pd.DataFrame) -> np.ndarray:
        """Transform features using fitted scaler."""
        if X is None:
            return None
        return (X.values - self.scaler['mean']) / self.scaler['std']
    
    def _train_torch(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray = None,
        y_val: np.ndarray = None
    ) -> Dict:
        """Train using PyTorch."""
        import torch
        import torch.nn as nn
        import torch.optim as optim
        from torch.utils.data import TensorDataset, DataLoader
        
        # Build model
        layers = []
        input_dim = X_train.shape[1]
        
        for hidden_dim in self.hidden_layers:
            layers.append(nn.Linear(input_dim, hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(self.dropout_rate))
            input_dim = hidden_dim
        
        layers.append(nn.Linear(input_dim, 1))
        layers.append(nn.Sigmoid())
        
        self.model = nn.Sequential(*layers)
        
        # Training setup
        criterion = nn.BCELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        
        # Data loaders
        train_dataset = TensorDataset(
            torch.FloatTensor(X_train),
            torch.FloatTensor(y_train).unsqueeze(1)
        )
        train_loader = DataLoader(train_dataset, batch_size=self.batch_size, shuffle=True)
        
        # Training loop
        best_loss = float('inf')
        patience_counter = 0
        
        for epoch in range(self.n_epochs):
            self.model.train()
            epoch_loss = 0
            
            for batch_X, batch_y in train_loader:
                optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()
            
            avg_loss = epoch_loss / len(train_loader)
            
            # Validation
            if X_val is not None:
                self.model.eval()
                with torch.no_grad():
                    val_outputs = self.model(torch.FloatTensor(X_val))
                    val_loss = criterion(val_outputs, torch.FloatTensor(y_val).unsqueeze(1))
                
                if val_loss < best_loss:
                    best_loss = val_loss.item()
                    patience_counter = 0
                else:
                    patience_counter += 1
                
                if patience_counter >= 10:
                    logger.info(f"Early stopping at epoch {epoch}")
                    break
            
            if (epoch + 1) % 20 == 0:
                logger.debug(f"Epoch {epoch+1}/{self.n_epochs}, Loss: {avg_loss:.4f}")
        
        self.is_trained = True
        
        # Calculate final metrics
        train_pred = self.predict(pd.DataFrame(X_train))
        train_acc = np.mean((train_pred >= 0.5) == y_train)
        
        metrics = {'train_accuracy': train_acc, 'method': 'pytorch'}
        
        if X_val is not None:
            val_pred = self.predict(pd.DataFrame(X_val))
            val_acc = np.mean((val_pred >= 0.5) == y_val)
            metrics['val_accuracy'] = val_acc
        
        logger.success(f"MLP training complete. Train accuracy: {train_acc:.4f}")
        return metrics
    
    def _train_sklearn(self, X_train: np.ndarray, y_train: np.ndarray) -> Dict:
        """Train using sklearn MLPClassifier."""
        from sklearn.neural_network import MLPClassifier
        
        self.model = MLPClassifier(
            hidden_layer_sizes=tuple(self.hidden_layers),
            activation='relu',
            solver='adam',
            alpha=0.001,
            batch_size=self.batch_size,
            learning_rate_init=self.learning_rate,
            max_iter=self.n_epochs,
            early_stopping=True,
            validation_fraction=0.1,
            random_state=42,
            verbose=False
        )
        
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        train_acc = self.model.score(X_train, y_train)
        
        logger.success(f"MLP training (sklearn) complete. Train accuracy: {train_acc:.4f}")
        return {'train_accuracy': train_acc, 'method': 'sklearn'}
    
    def _train_numpy(self, X_train: np.ndarray, y_train: np.ndarray) -> Dict:
        """Fallback training using pure NumPy."""
        # Simple neural network from scratch
        self.model = NumpyMLP(
            input_dim=X_train.shape[1],
            hidden_dims=self.hidden_layers,
            learning_rate=self.learning_rate
        )
        
        self.model.train(X_train, y_train, epochs=self.n_epochs)
        self.is_trained = True
        
        train_pred = self.model.predict(X_train)
        train_acc = np.mean((train_pred >= 0.5) == y_train)
        
        logger.success(f"MLP training (numpy) complete. Train accuracy: {train_acc:.4f}")
        return {'train_accuracy': train_acc, 'method': 'numpy'}
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Generate predictions.
        
        Args:
            X (pd.DataFrame): Features
            
        Returns:
            np.ndarray: Prediction probabilities
        """
        if not self.is_trained or self.model is None:
            return np.full(len(X), 0.5)
        
        X_scaled = self._transform(X)
        
        if self._check_torch() and hasattr(self.model, 'eval'):
            import torch
            self.model.eval()
            with torch.no_grad():
                outputs = self.model(torch.FloatTensor(X_scaled))
                return outputs.numpy().flatten()
        elif hasattr(self.model, 'predict_proba'):
            return self.model.predict_proba(X_scaled)[:, 1]
        else:
            return self.model.predict(X_scaled)
    
    def save_model(self, path: str = None):
        """Save model to disk."""
        save_path = path or self.model_path
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        with open(save_path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'config': self.config
            }, f)
        
        logger.info(f"Model saved to {save_path}")
    
    def load_model(self, path: str = None):
        """Load model from disk."""
        load_path = path or self.model_path
        
        if not os.path.exists(load_path):
            return False
        
        with open(load_path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.scaler = data.get('scaler')
            self.config = data.get('config', {})
        
        self.is_trained = True
        return True


class NumpyMLP:
    """Pure NumPy MLP implementation."""
    
    def __init__(
        self,
        input_dim: int,
        hidden_dims: List[int],
        learning_rate: float = 0.01
    ):
        self.learning_rate = learning_rate
        self.weights = []
        self.biases = []
        
        # Initialize weights
        dims = [input_dim] + hidden_dims + [1]
        for i in range(len(dims) - 1):
            # Xavier initialization
            scale = np.sqrt(2.0 / (dims[i] + dims[i+1]))
            self.weights.append(np.random.randn(dims[i], dims[i+1]) * scale)
            self.biases.append(np.zeros((1, dims[i+1])))
    
    def _relu(self, x: np.ndarray) -> np.ndarray:
        return np.maximum(0, x)
    
    def _relu_derivative(self, x: np.ndarray) -> np.ndarray:
        return (x > 0).astype(float)
    
    def _sigmoid(self, x: np.ndarray) -> np.ndarray:
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))
    
    def _forward(self, X: np.ndarray) -> Tuple[List[np.ndarray], np.ndarray]:
        """Forward pass."""
        activations = [X]
        current = X
        
        for i, (W, b) in enumerate(zip(self.weights, self.biases)):
            z = current @ W + b
            
            if i < len(self.weights) - 1:
                current = self._relu(z)
            else:
                current = self._sigmoid(z)
            
            activations.append(current)
        
        return activations, current
    
    def train(self, X: np.ndarray, y: np.ndarray, epochs: int = 100):
        """Train the network."""
        y = y.reshape(-1, 1)
        
        for epoch in range(epochs):
            # Forward pass
            activations, output = self._forward(X)
            
            # Backward pass
            error = output - y
            
            for i in reversed(range(len(self.weights))):
                if i == len(self.weights) - 1:
                    delta = error
                else:
                    delta = error * self._relu_derivative(activations[i+1])
                
                dW = activations[i].T @ delta / len(X)
                db = np.mean(delta, axis=0, keepdims=True)
                
                self.weights[i] -= self.learning_rate * dW
                self.biases[i] -= self.learning_rate * db
                
                if i > 0:
                    error = delta @ self.weights[i].T
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate predictions."""
        _, output = self._forward(X)
        return output.flatten()


if __name__ == "__main__":
    # Test
    np.random.seed(42)
    n_samples = 1000
    n_features = 20
    
    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f'feature_{i}' for i in range(n_features)]
    )
    y = pd.Series((X['feature_0'] + X['feature_1'] * 0.5 > 0).astype(int))
    
    # Split
    train_size = int(0.8 * n_samples)
    X_train, X_val = X[:train_size], X[train_size:]
    y_train, y_val = y[:train_size], y[train_size:]
    
    # Train
    model = MLPModel({'hidden_layers': [64, 32], 'epochs': 50})
    metrics = model.train(X_train, y_train, X_val, y_val)
    
    print("Training Metrics:")
    for k, v in metrics.items():
        print(f"  {k}: {v}")
    
    # Predict
    predictions = model.predict(X_val)
    print(f"\nPrediction range: [{predictions.min():.4f}, {predictions.max():.4f}]")
