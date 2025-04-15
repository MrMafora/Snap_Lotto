"""
Gunicorn configuration for both development and deployment
This ensures consistent binding across environments
"""

# Import os to access environment variables
import os
import sys
import threading
import time
import signal
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('gunicorn.conf')

# Determine binding based on environment
environment = os.environ.get('ENVIRONMENT', 'development')

# Primary binding
if environment.lower() == 'production':
    # Production environment uses port 8080 for Replit deployment
    bind = "0.0.0.0:8080"
    primary_port = 8080
else:
    # Development environment uses port 5000
    bind = "0.0.0.0:5000"
    primary_port = 5000

# Worker settings
workers = 4
worker_class = "sync"
threads = 2
timeout = 120

# Server mechanics
graceful_timeout = 30
keepalive = 5
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Auto-reload on code changes
reload = True

# Additional settings for production
worker_tmp_dir = "/dev/shm"

# Start port bridge if needed
def start_bridge():
    """
    If we're on port 5000, start a bridge to handle port 8080 requests.
    If we're on port 8080, we don't need a bridge since we're already on the right port.
    """
    # Only start bridge when running on port 5000 (development mode)
    if primary_port == 5000:
        try:
            import bridge
            logger.info("Starting port 8080 bridge to forward to port 5000...")
            
            # Start bridge in a new thread
            bridge_thread = threading.Thread(target=bridge.run_bridge, daemon=True)
            bridge_thread.start()
            logger.info("Port 8080 bridge started successfully")
            
            # Store the bridge thread so it doesn't get garbage collected
            return bridge_thread
        except Exception as e:
            logger.error(f"Error starting bridge: {str(e)}")
    else:
        logger.info(f"Running on port {primary_port}, no bridge needed")
    
    return None

# Make sure we start the bridge when gunicorn runs
bridge_thread = None

def post_fork(server, worker):
    """
    Start the port bridge in the first worker process.
    This ensures we only start the bridge once.
    """
    global bridge_thread
    
    # Only start in first worker
    if worker.age == 0 and server.proc_name == "gunicorn" and bridge_thread is None:
        bridge_thread = start_bridge()

def child_exit(server, worker):
    """
    Clean up when worker exits
    """
    pass