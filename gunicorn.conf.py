
"""
Gunicorn configuration file
"""
import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('gunicorn.conf')

# Always bind to port 8080
bind = "0.0.0.0:8080"

# Worker configuration
workers = 2
worker_class = "gthread"
threads = 2
timeout = 60

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

def on_starting(server):
    """Log server startup"""
    logger.info("Starting Gunicorn server on port 8080")

def post_fork(server, worker):
    """Log worker startup"""
    logger.info(f"Worker {worker.pid} forked")
