"""
Direct application bootstrap for Replit deployment.
This script starts the app on port 8080 directly without requiring a proxy.
"""
import os
import sys
import logging
import threading
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def stop_running_processes():
    """Stop any processes that might be running on port 8080"""
    try:
        # Try to kill processes on port 8080
        os.system("kill $(lsof -t -i:8080) 2>/dev/null || true")
        logger.info("Attempted to stop processes on port 8080")
        time.sleep(2)  # Give processes time to stop
    except Exception as e:
        logger.error(f"Error stopping processes: {e}")

def start_application():
    """Start the application directly on port 8080"""
    logger.info("Starting application on port 8080...")
    
    # Import the app after clearing the port
    from main import app
    
    # Repl.it expects web apps to listen on 0.0.0.0:8080
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Using port {port}")
    
    # Start the app
    app.run(host="0.0.0.0", port=port, debug=True)

if __name__ == "__main__":
    # Try to free port 8080 first
    stop_running_processes()
    
    # Start the application
    start_application()