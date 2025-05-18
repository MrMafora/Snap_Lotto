"""
Direct Flask starter that binds to port 8080
This uses the Flask development server without Gunicorn
"""

import os
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Make sure we're in the correct directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Import the Flask app
try:
    from main import app
    logger.info("Successfully imported Flask app from main.py")
except Exception as e:
    logger.error(f"Failed to import Flask app: {e}")
    sys.exit(1)

if __name__ == "__main__":
    logger.info("Starting Flask application on port 8080")
    app.run(host="0.0.0.0", port=8080, debug=True, use_reloader=False)