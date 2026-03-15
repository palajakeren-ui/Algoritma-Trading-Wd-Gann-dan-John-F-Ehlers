"""
Scanner View Module
Interface for Market Scanner
"""
from loguru import logger

class ScannerView:
    """View for Market Scanner results."""
    def __init__(self):
        logger.info("GUI: ScannerView initialized")
        
    def show_results(self, scan_results):
        print(f"Showing {len(scan_results)} scan results...")
