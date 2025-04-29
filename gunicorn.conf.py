
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

# Bind directly to port 8080
bind = "0.0.0.0:8080"

# Optimize worker configuration 
workers = multiprocessing.cpu_count() * 2 + 1
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
