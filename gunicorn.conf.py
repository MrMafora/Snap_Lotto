
"""
Gunicorn configuration file with optimized settings
"""
import os
import sys
import logging
import multiprocessing

# Setup logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('gunicorn.conf')

# Bind to port 5000 (matches workflow configuration)
bind = "0.0.0.0:5000"

# SECURITY FIX: Limit workers to prevent resource exhaustion attacks
workers = 2  # Fixed to safe number instead of multiplying CPU count
worker_class = "sync"
threads = 4
worker_connections = 1000
timeout = 120
keepalive = 2

# Performance settings
max_requests = 1000
max_requests_jitter = 50
graceful_timeout = 30

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Pre-load application to improve startup time
preload_app = True
