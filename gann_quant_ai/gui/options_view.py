"""
Options View Module
Interface for Options Chain and Greeks
"""
from loguru import logger

class OptionsView:
    """View for Options Data."""
    def __init__(self):
        logger.info("GUI: OptionsView initialized")
        
    def show_chain(self, chain_data):
        print("Displaying options chain...")
