
"""
Gunicorn configuration file with optimized settings
"""
import multiprocessing
import logging

logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('gunicorn.conf')

bind = "0.0.0.0:8080"

# Reduce worker count for faster startup
workers = 4  # Reduced from dynamic calculation
worker_class = "sync"
threads = 4
worker_connections = 1000
timeout = 120
keepalive = 2

# Performance optimizations
max_requests = 1000
max_requests_jitter = 50
graceful_timeout = 30

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Enable preload for better memory usage
preload_app = True
