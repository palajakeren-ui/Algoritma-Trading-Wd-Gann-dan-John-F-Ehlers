"""
Neural ODE Model Module
Neural Ordinary Differential Equations for continuous-time modeling of market dynamics.

Neural ODEs model the hidden dynamics as a continuous-time process,
making them particularly suitable for irregularly-sampled time series
and capturing smooth market transitions.
"""
import numpy as np
import pandas as pd
from loguru import logger
from typing import Dict, List, Optional, Tuple, Callable
import pickle
import os


class NeuralODEModel:
    """
    Neural ODE implementation for trading predictions.
    
    Neural ODEs define dynamics as dh/dt = f(h, t, θ) where f is a neural network.
    This allows modeling continuous-time dynamics of market states.
    """
    
    def __init__(self, config: Dict = None, model_path: str = None):
        """
        Initialize Neural ODE model.
        
        Args:
            config (Dict): Model configuration
            model_path (str): Path to saved model
        """
        self.config = config or {}
        self.model_path = model_path or "outputs/models/neural_ode_model.pkl"
        self.model = None
        self.scaler = None
        self.is_trained = False
        
        # Model parameters
        self.hidden_dim = self.config.get('hidden_dim', 64)
        self.n_layers = self.config.get('n_layers', 2)
        self.learning_rate = self.config.get('learning_rate', 0.001)
        self.n_epochs = self.config.get('epochs', 50)
        
        logger.info(f"NeuralODEModel initialized: hidden_dim={self.hidden_dim}")
    
    def _check_torch(self) -> bool:
        """Check if PyTorch and torchdiffeq are available."""
        try:
            import torch
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
        Train Neural ODE model.
        
        Args:
            X_train (pd.DataFrame): Training features
            y_train (pd.Series): Training labels
            X_val (pd.DataFrame): Validation features
            y_val (pd.Series): Validation labels
            
        Returns:
            Dict: Training metrics
        """
        logger.info(f"Training Neural ODE model with {len(X_train)} samples")
        
        # Standardize features
        self._fit_scaler(X_train)
        X_train_scaled = self._transform(X_train)
        X_val_scaled = self._transform(X_val) if X_val is not None else None
        
        if self._check_torch():
            return self._train_torch(X_train_scaled, y_train.values, X_val_scaled,
                                     y_val.values if y_val is not None else None)
        else:
            return self._train_numpy(X_train_scaled, y_train.values)
    
    def _fit_scaler(self, X: pd.DataFrame):
        """Fit feature scaler."""
        self.scaler = {
            'mean': X.mean().values,
            'std': X.std().values + 1e-8
        }
    
    def _transform(self, X: pd.DataFrame) -> np.ndarray:
        """Transform features."""
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
        """Train using PyTorch with simplified ODE approach."""
        import torch
        import torch.nn as nn
        import torch.optim as optim
        
        input_dim = X_train.shape[1]
        
        # Define ODE function network
        class ODEFunc(nn.Module):
            def __init__(self, dim, hidden_dim):
                super().__init__()
                self.net = nn.Sequential(
                    nn.Linear(dim, hidden_dim),
                    nn.Tanh(),
                    nn.Linear(hidden_dim, hidden_dim),
                    nn.Tanh(),
                    nn.Linear(hidden_dim, dim)
                )
            
            def forward(self, t, h):
                return self.net(h)
        
        # Simple Euler method ODE solver
        def ode_solve(func, h0, t_span, n_steps=10):
            dt = (t_span[1] - t_span[0]) / n_steps
            h = h0
            t = t_span[0]
            for _ in range(n_steps):
                h = h + dt * func(t, h)
                t = t + dt
            return h
        
        # Full model
        class NeuralODE(nn.Module):
            def __init__(self, input_dim, hidden_dim):
                super().__init__()
                self.encoder = nn.Linear(input_dim, hidden_dim)
                self.ode_func = ODEFunc(hidden_dim, hidden_dim)
                self.decoder = nn.Sequential(
                    nn.Linear(hidden_dim, 32),
                    nn.ReLU(),
                    nn.Linear(32, 1),
                    nn.Sigmoid()
                )
            
            def forward(self, x):
                h0 = self.encoder(x)
                h1 = ode_solve(self.ode_func, h0, (0, 1))
                return self.decoder(h1)
        
        self.model = NeuralODE(input_dim, self.hidden_dim)
        
        # Training
        criterion = nn.BCELoss()
        optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        
        X_tensor = torch.FloatTensor(X_train)
        y_tensor = torch.FloatTensor(y_train).unsqueeze(1)
        
        for epoch in range(self.n_epochs):
            self.model.train()
            optimizer.zero_grad()
            
            outputs = self.model(X_tensor)
            loss = criterion(outputs, y_tensor)
            loss.backward()
            optimizer.step()
            
            if (epoch + 1) % 10 == 0:
                logger.debug(f"Epoch {epoch+1}/{self.n_epochs}, Loss: {loss.item():.4f}")
        
        self.is_trained = True
        
        # Metrics
        with torch.no_grad():
            train_pred = self.model(X_tensor).numpy().flatten()
            train_acc = np.mean((train_pred >= 0.5) == y_train)
        
        metrics = {'train_accuracy': train_acc, 'method': 'pytorch'}
        
        if X_val is not None:
            with torch.no_grad():
                val_pred = self.model(torch.FloatTensor(X_val)).numpy().flatten()
                val_acc = np.mean((val_pred >= 0.5) == y_val)
            metrics['val_accuracy'] = val_acc
        
        logger.success(f"Neural ODE training complete. Train accuracy: {train_acc:.4f}")
        return metrics
    
    def _train_numpy(self, X_train: np.ndarray, y_train: np.ndarray) -> Dict:
        """Fallback NumPy-based training."""
        self.model = NumpyNeuralODE(
            input_dim=X_train.shape[1],
            hidden_dim=self.hidden_dim,
            learning_rate=self.learning_rate
        )
        
        self.model.train(X_train, y_train, epochs=self.n_epochs)
        self.is_trained = True
        
        train_pred = self.model.predict(X_train)
        train_acc = np.mean((train_pred >= 0.5) == y_train)
        
        return {'train_accuracy': train_acc, 'method': 'numpy'}
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Generate predictions."""
        if not self.is_trained or self.model is None:
            return np.full(len(X), 0.5)
        
        X_scaled = self._transform(X)
        
        if self._check_torch() and hasattr(self.model, 'eval'):
            import torch
            self.model.eval()
            with torch.no_grad():
                outputs = self.model(torch.FloatTensor(X_scaled))
                return outputs.numpy().flatten()
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


class NumpyNeuralODE:
    """
    NumPy-based Neural ODE implementation.
    Uses simple Euler method for ODE solving.
    """
    
    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 32,
        learning_rate: float = 0.01
    ):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.learning_rate = learning_rate
        
        # Encoder weights
        self.W_enc = np.random.randn(input_dim, hidden_dim) * 0.1
        self.b_enc = np.zeros((1, hidden_dim))
        
        # ODE function weights
        self.W_ode1 = np.random.randn(hidden_dim, hidden_dim) * 0.1
        self.b_ode1 = np.zeros((1, hidden_dim))
        self.W_ode2 = np.random.randn(hidden_dim, hidden_dim) * 0.1
        self.b_ode2 = np.zeros((1, hidden_dim))
        
        # Decoder weights
        self.W_dec = np.random.randn(hidden_dim, 1) * 0.1
        self.b_dec = np.zeros((1, 1))
    
    def _tanh(self, x: np.ndarray) -> np.ndarray:
        return np.tanh(x)
    
    def _sigmoid(self, x: np.ndarray) -> np.ndarray:
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))
    
    def _ode_func(self, h: np.ndarray) -> np.ndarray:
        """Compute dh/dt."""
        z1 = self._tanh(h @ self.W_ode1 + self.b_ode1)
        dh = z1 @ self.W_ode2 + self.b_ode2
        return dh
    
    def _ode_solve(self, h0: np.ndarray, n_steps: int = 10) -> np.ndarray:
        """Simple Euler solver."""
        dt = 1.0 / n_steps
        h = h0
        for _ in range(n_steps):
            dh = self._ode_func(h)
            h = h + dt * dh
        return h
    
    def _forward(self, X: np.ndarray) -> np.ndarray:
        """Forward pass."""
        # Encode
        h0 = X @ self.W_enc + self.b_enc
        
        # ODE solve
        h1 = self._ode_solve(h0)
        
        # Decode
        out = self._sigmoid(h1 @ self.W_dec + self.b_dec)
        return out
    
    def train(self, X: np.ndarray, y: np.ndarray, epochs: int = 50):
        """Train the network using simple gradient descent."""
        y = y.reshape(-1, 1)
        
        for epoch in range(epochs):
            # Forward
            out = self._forward(X)
            
            # Loss and gradient (simplified)
            error = out - y
            grad = error / len(X)
            
            # Simple update (approximate gradients)
            # This is a simplified version - real implementation needs backprop through ODE
            self.W_dec -= self.learning_rate * (self._ode_solve(X @ self.W_enc + self.b_enc).T @ grad)
            self.b_dec -= self.learning_rate * np.mean(grad)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate predictions."""
        return self._forward(X).flatten()


if __name__ == "__main__":
    # Test
    np.random.seed(42)
    n_samples = 500
    n_features = 15
    
    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f'feature_{i}' for i in range(n_features)]
    )
    y = pd.Series((X['feature_0'] + X['feature_1'] > 0).astype(int))
    
    # Split
    train_size = int(0.8 * n_samples)
    X_train, X_val = X[:train_size], X[train_size:]
    y_train, y_val = y[:train_size], y[train_size:]
    
    # Train
    model = NeuralODEModel({'hidden_dim': 32, 'epochs': 30})
    metrics = model.train(X_train, y_train, X_val, y_val)
    
    print("Training Metrics:")
    for k, v in metrics.items():
        print(f"  {k}: {v}")
