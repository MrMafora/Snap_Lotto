"""
Direct application entry point that binds to port 8080.
This version doesn't require a port proxy and directly uses the port 8080.
"""
import os
import sys
import logging
from main import app

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Get port from environment or use 8080 as default
    port = int(os.environ.get("PORT", 8080))
    
    logger.info(f"Starting application directly on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)