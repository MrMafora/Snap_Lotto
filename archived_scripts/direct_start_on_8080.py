#!/usr/bin/env python3
"""
Direct application starter for proper port binding
Ensures the application binds to port 8080 with high priority
"""

import sys
import os
import signal
import multiprocessing
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('direct_start_8080')

def run_application():
    """Run the gunicorn server directly on port 8080"""
    import gunicorn.app.base
    
    # Force bind to port 8080 with highest priority
    os.environ['PORT'] = '8080'
    os.environ['GUNICORN_PORT'] = '8080'
    os.environ['FLASK_RUN_PORT'] = '8080'
    os.environ['SERVER_PORT'] = '8080'
    
    # Override any command-line arguments to ensure our settings take priority
    class StandaloneApplication(gunicorn.app.base.BaseApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super().__init__()

        def load_config(self):
            # Load configuration, overriding any command-line arguments
            for key, value in self.options.items():
                self.cfg.set(key.lower(), value)

        def load(self):
            return self.application
    
    # Import the Flask app lazily to allow environment variables to take effect
    from main import app
    
    # Define the options directly
    options = {
        'bind': '0.0.0.0:8080',
        'workers': 2,
        'worker_class': 'gthread',
        'threads': 2,
        'timeout': 60,
        'reload': True,
        'loglevel': 'info'
    }
    
    logger.info(f"Starting application on port 8080")
    
    # Run the application
    StandaloneApplication(app, options).run()

def handle_signal(signum, frame):
    """Handle termination signals"""
    logger.info(f"Received signal {signum}, shutting down")
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    # Start the application
    run_application()