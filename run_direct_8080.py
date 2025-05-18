"""
Direct port 8080 starter for Snap Lotto application.
This script starts the application directly on port 8080 without requiring a port proxy.
"""

import os
import sys
import signal
import subprocess
import logging
from gunicorn.app.base import BaseApplication
import gunicorn.app.base

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def signal_handler(signum, frame):
    """Handle termination signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)

class DirectApplication(gunicorn.app.base.BaseApplication):
    """Direct application runner for Gunicorn"""
    
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        """Load configuration from options"""
        for key, value in self.options.items():
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key.lower(), value)

    def load(self):
        """Load application"""
        return self.application

def run_direct():
    """Run the application directly on port 8080"""
    try:
        logger.info("Starting application directly on port 8080")
        
        # Import main app
        from main import app
        
        # Configure Gunicorn
        options = {
            'bind': '0.0.0.0:8080',
            'workers': 2,
            'worker_class': 'gthread',
            'threads': 4,
            'timeout': 120,
            'reload': True,
            'reuse_port': True,
            'accesslog': '-',
            'errorlog': '-',
            'loglevel': 'info',
        }
        
        # Start the application
        DirectApplication(app, options).run()
        
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run application directly on port 8080
    run_direct()