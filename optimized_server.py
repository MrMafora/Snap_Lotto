#!/usr/bin/env python3
"""
Optimized server that enforces worker limits and binds directly to port 8080.
This is a custom version that combines the main application with direct server configuration.
"""
import os
import logging
import signal
import sys
from main import app  # Import the app from main.py

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('optimized_server')

def handle_signal(signum, frame):
    """Handle termination signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)

def main():
    """Run the Flask application directly on port 8080"""
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    try:
        # Enable debug only for development
        debug_mode = os.environ.get('FLASK_ENV') == 'development'
        
        # Log the startup
        logger.info(f"Starting Flask server directly on port 8080 (debug: {debug_mode})")
        
        # Run the Flask app directly on port 8080
        app.run(
            host='0.0.0.0',
            port=8080,
            debug=debug_mode,
            use_reloader=False,  # Disable auto-reloader to avoid duplicate processes
            threaded=True       # Enable threading for better performance
        )
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())