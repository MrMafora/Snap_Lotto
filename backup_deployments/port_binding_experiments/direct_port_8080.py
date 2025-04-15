"""
DIRECT PORT 8080 BINDING FOR REPLIT

This is a direct binding solution that starts the Flask application
directly on port 8080 without relying on proxies or redirects.
"""
import os
import logging
import importlib.util
import sys
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def start_app():
    """Start the Flask application directly on port 8080"""
    try:
        # Import the app from main.py
        spec = importlib.util.spec_from_file_location("main", "main.py")
        main_module = importlib.util.module_from_spec(spec)
        sys.modules["main"] = main_module
        spec.loader.exec_module(main_module)
        
        # Get the app from main.py
        app = main_module.app
        
        # Run the Flask app directly on port 8080
        logger.info("Starting Flask application on port 8080")
        app.run(host='0.0.0.0', port=8080, debug=True, use_reloader=False)
    except Exception as e:
        logger.error(f"Error starting Flask application: {e}")
        return False
    
    return True

if __name__ == "__main__":
    logger.info("Starting direct port 8080 binding")
    start_app()