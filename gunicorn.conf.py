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

# Bind to port 8080
bind = "0.0.0.0:8080"

# Optimize worker configuration
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync" # Changed from 'gthread'
threads = 4
worker_connections = 1000 # Retained from original
timeout = 120 # Updated timeout from original
keepalive = 2 # Retained from original

# Performance settings
max_requests = 1000 # Retained from original
max_requests_jitter = 50 # Retained from original
graceful_timeout = 30 # Retained from original

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Pre-load application to improve startup time
preload_app = True # Retained from original