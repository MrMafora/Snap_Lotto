#!/usr/bin/env python3
"""
Direct application entry point that binds to port 8080.
This version doesn't require a port proxy and directly uses port 8080.
"""
import os
import logging
import signal
import sys
from main import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('direct_start')

def handle_signal(signum, frame):
    """Handle termination signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)

def main():
    """Main entry point for direct Flask server"""
    logger.info("Starting direct Flask server on port 8080")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    try:
        # Run Flask directly on port 8080
        app.run(host='0.0.0.0', port=8080, debug=True)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())