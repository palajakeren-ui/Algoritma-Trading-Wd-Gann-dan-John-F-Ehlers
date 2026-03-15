"""
AI View Module
Interface for AI model interaction
"""
from loguru import logger

class AIView:
    """View for AI/ML controls and visualization."""
    def __init__(self, controller=None):
        self.controller = controller
        logger.info("GUI: AIView initialized")

    def show_predictions(self, predictions):
        print(f"Displaying {len(predictions)} predictions")
