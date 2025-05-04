#!/usr/bin/env python3
"""
Direct launcher for port 8080 with no configuration overrides
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
logger = logging.getLogger('direct_8080')

def handle_signal(signum, frame):
    """Handle termination signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    logger.info("Starting direct Flask server on port 8080")
    # Run Flask directly on port 8080, with much smaller worker count
    app.run(host='0.0.0.0', port=8080, debug=True, threaded=True)