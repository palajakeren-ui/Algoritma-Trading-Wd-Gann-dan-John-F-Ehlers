from loguru import logger
import pandas as pd
from typing import Dict, Optional

from core.feature_builder import FeatureBuilder
from models.ml_randomforest import RandomForestModel
# Import other models like XGBoost, LSTM as they are created

class MLEngine:
    """
    Orchestrates the machine learning workflow, including feature building,
    training, and prediction.
    """
    def __init__(self, config: Dict):
        self.config = config
        self.ml_config = config.get("ml_config", {})
        self.feature_builder = FeatureBuilder(config)
        self.model = self._get_model()

    def _get_model(self):
        """Initializes the ML model based on the configuration."""
        model_name = self.ml_config.get("active_model", "ml_randomforest")
        model_path = self.ml_config.get("model_paths", {}).get(model_name)

        logger.info(f"Initializing ML model: {model_name}")

        if model_name == "ml_randomforest":
            # Pass hyperparameters from config to the model
            params = self.ml_config.get("training", {}).get("random_forest_params", {})
            return RandomForestModel(model_path=model_path, **params)
            
        elif model_name == "ml_xgboost":
            from models.ml_xgboost import XGBoostModel
            params = self.ml_config.get("training", {}).get("xgboost_params", {})
            return XGBoostModel(config=self.config)
            
        elif model_name == "ml_lstm":
            from models.ml_lstm import LSTMModel
            params = self.ml_config.get("training", {}).get("lstm_params", {})
            return LSTMModel(config=self.config)

        # Add logic for other models (XGBoost, etc.) here
        else:
            logger.error(f"Unsupported ML model '{model_name}' specified in config.")
            return RandomForestModel(model_path=model_path) # Fallback

    def train_model(
        self,
        price_data: pd.DataFrame,
        gann_levels: Optional[Dict],
        astro_events: Optional[pd.DataFrame]
    ):
        """
        Builds features and trains the ML model.
        """
        logger.info("--- Starting ML Model Training Workflow ---")
        # 1. Build features
        features_df = self.feature_builder.build_features(price_data, gann_levels, astro_events)

        if features_df.empty:
            logger.error("Feature building resulted in an empty DataFrame. Aborting training.")
            return

        # 2. Train model
        accuracy, report = self.model.train(features_df)

        print("\n--- Model Evaluation Report ---")
        print(f"Test Set Accuracy: {accuracy:.4f}")
        print(report)
        print("-------------------------------")
        logger.info("--- ML Model Training Workflow Finished ---")

    def get_predictions(
        self,
        price_data: pd.DataFrame,
        gann_levels: Optional[Dict],
        astro_events: Optional[pd.DataFrame]
    ) -> Optional[pd.DataFrame]:
        """
        Builds features for the latest data and returns model predictions.
        """
        logger.info("Generating ML predictions...")

        try:
            self.model.load_model()
        except RuntimeError as e:
            logger.error(f"Failed to load model for prediction: {e}")
            return None

        if self.model.model is None:
            return None

        # 1. Build features (Note: Target will be NaN for the last row, which is fine)
        features_df = self.feature_builder.build_features(price_data, gann_levels, astro_events)

        if features_df.empty:
            logger.warning("Could not build features for prediction.")
            return None

        # 2. Make predictions
        # We only need features, not the target, for prediction
        X = features_df.drop('target', axis=1, errors='ignore')

        predictions = self.model.predict(X)

        logger.success(f"Successfully generated {len(predictions)} ML predictions.")
        return predictions
