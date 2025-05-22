"""
Fix the port issue by running a simple Flask application on port 8080
"""

import logging
import sys
import os
import signal

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def signal_handler(signum, frame):
    """Handle termination signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)

def run_flask_directly():
    """Run the Flask application directly on port 8080"""
    try:
        from main import app
        logger.info("Successfully imported Flask app")
        logger.info("Starting Flask app on port 8080")
        app.run(host='0.0.0.0', port=8080, debug=True)
    except Exception as e:
        logger.error(f"Error starting Flask app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the Flask app directly
    run_flask_directly()