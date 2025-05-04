#!/usr/bin/env python3
"""
Direct Flask server launcher for development
Directly runs the Flask app with Flask's development server on port 8080
This is more reliable for debugging, though not recommended for production.
"""
import os
import logging
from main import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('direct_flask_server')

if __name__ == "__main__":
    logger.info("Starting Flask development server on port 8080")
    # Run the Flask app directly on port 8080
    app.run(host='0.0.0.0', port=8080, debug=True)