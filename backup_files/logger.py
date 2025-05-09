"""
Logging utility module for the application.
Provides consistent logging configuration across modules.
"""

import logging
import sys

def setup_logger(name, level=logging.INFO):
    """
    Set up a logger with consistent formatting
    
    Args:
        name (str): Logger name, usually __name__
        level (int, optional): Logging level. Defaults to logging.INFO.
        
    Returns:
        logging.Logger: Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Check if logger already has handlers to avoid duplicate handlers
    if not logger.handlers:
        # Create handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
    
    return logger