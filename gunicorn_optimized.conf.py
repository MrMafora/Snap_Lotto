"""
Optimized Gunicorn configuration with strict worker limits
"""
import os
import logging
import multiprocessing

# Set up logging
logger = logging.getLogger('gunicorn.conf')

# Strictly limit the number of workers to avoid resource contention
# We'll use just 2 workers for maximum stability
workers = 2

# Worker class - use sync for simplicity and stability
worker_class = 'sync'

# Threads per worker - use 2 threads per worker
threads = 2

# Bind directly to port 8080
bind = '0.0.0.0:8080'

# Timeouts
timeout = 120
keep_alive = 5
graceful_timeout = 10

# Security settings
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Logging configuration
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Lifecycle hooks
def on_starting(server):
    """Log server startup"""
    logger.info("Starting gunicorn with optimized settings on port 8080")
    logger.info(f"Using {workers} workers with {threads} threads each")

def on_exit(server):
    """Log server shutdown"""
    logger.info("Shutting down gunicorn")