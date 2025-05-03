"""
Optimized Gunicorn configuration file for improved performance
"""
import multiprocessing
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('gunicorn.conf')

# Bind directly to port 8080 instead of port 5000
bind = "0.0.0.0:8080"

# Worker settings - use fewer workers to avoid resource contention
# Just 4 workers maximum, or fewer on small machines
workers = min(4, multiprocessing.cpu_count())

# Use threads for better memory efficiency
worker_class = "gthread"
threads = 2

# Keep-alive settings for better performance
keepalive = 30

# Timeout settings (in seconds)
timeout = 60
graceful_timeout = 60

# Disable access logging for better performance
accesslog = None

# Set error log to standard error
errorlog = "-"

# Preload the application to save memory
preload_app = True

# Reduce max requests before worker restart to help with memory leaks
max_requests = 1000
max_requests_jitter = 100

# Reduce server header to simplify responses
server_tokens = False

def on_starting(server):
    """Log server startup"""
    logger.info("Starting optimized Gunicorn server")

def on_exit(server):
    """Log server shutdown"""
    logger.info("Shutting down optimized Gunicorn server")