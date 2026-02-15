import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from loguru import logger
import joblib
from typing import Tuple

class RandomForestModel:
    """
    A wrapper for a scikit-learn RandomForestClassifier.
    """
    def __init__(self, model_path: str = "models/randomforest_model.pkl", **params):
        """
        Initializes the model.

        Args:
            model_path (str): Path to save/load the trained model.
            **params: Hyperparameters for the RandomForestClassifier.
        """
        self.model_path = model_path
        self.model = RandomForestClassifier(**params)
        logger.info(f"RandomForestModel initialized. Path: {self.model_path}")

    def train(self, features: pd.DataFrame) -> Tuple[float, str]:
        """
        Trains the model on the provided feature set.

        Args:
            features (pd.DataFrame): The DataFrame containing features and the 'target' column.

        Returns:
            Tuple[float, str]: A tuple of (accuracy, classification_report_string).
        """
        if 'target' not in features.columns:
            raise ValueError("Feature DataFrame must contain a 'target' column.")

        X = features.drop('target', axis=1)
        y = features['target']

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        logger.info(f"Training model on {len(X_train)} samples...")
        self.model.fit(X_train, y_train)

        # Evaluate on the test set
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred)

        logger.success(f"Model training complete. Test Accuracy: {accuracy:.4f}")

        # Save the trained model
        self.save_model()

        return accuracy, report

    def predict(self, features: pd.DataFrame) -> pd.DataFrame:
        """
        Makes predictions on new data. Returns probabilities for each class.

        Args:
            features (pd.DataFrame): The features to predict on (without the 'target' column).

        Returns:
            pd.DataFrame: DataFrame with prediction probabilities and the final prediction.
        """
        if self.model is None:
            raise RuntimeError("Model is not trained or loaded. Call train() or load_model() first.")

        # Ensure columns are in the same order as during training
        X = features[self.model.feature_names_in_]

        probabilities = self.model.predict_proba(X)
        predictions = self.model.predict(X)

        results = pd.DataFrame({
            'prob_down': probabilities[:, 0],
            'prob_up': probabilities[:, 1],
            'prediction': predictions
        }, index=features.index)

        return results

    def save_model(self):
        """Saves the trained model to the specified path."""
        logger.info(f"Saving model to {self.model_path}...")
        joblib.dump(self.model, self.model_path)
        logger.success("Model saved successfully.")

    def load_model(self):
        """Loads a pre-trained model from the specified path."""
        try:
            logger.info(f"Loading model from {self.model_path}...")
            self.model = joblib.load(self.model_path)
            logger.success("Model loaded successfully.")
        except FileNotFoundError:
            logger.error(f"Model file not found at {self.model_path}.")
            self.model = None
