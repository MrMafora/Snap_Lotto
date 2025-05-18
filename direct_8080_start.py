"""
Direct launcher for the application on port 8080
This script starts the Flask application directly on port 8080 without requiring a proxy
"""

import sys
import signal
import os
import subprocess
from gunicorn.app.base import BaseApplication
import gunicorn.app.base
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def handle_signal(signum, frame):
    """Handle termination signals to exit gracefully"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)

class StandaloneApplication(gunicorn.app.base.BaseApplication):
    """Custom Gunicorn application for standalone operation"""
    
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        """Load configuration settings"""
        for key, value in self.options.items():
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key.lower(), value)

    def load(self):
        """Load the application"""
        return self.application

def run_application():
    """Run the application directly on port 8080"""
    # This ensures we import the app from the correct location
    logger.info("Starting application directly on port 8080")
    
    # Import the Flask app
    from main import app
    
    # Configure Gunicorn options
    options = {
        'bind': '0.0.0.0:8080',
        'workers': 4,
        'worker_class': 'gthread',
        'threads': 4,
        'timeout': 120,
        'reload': True,
        'preload_app': False,
        'accesslog': '-',
        'loglevel': 'info',
    }
    
    # Run the application with Gunicorn
    StandaloneApplication(app, options).run()

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    # Start the application
    run_application()