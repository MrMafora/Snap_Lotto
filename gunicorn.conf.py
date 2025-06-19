
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

# Bind to port 5000 with proper reuse settings
bind = "0.0.0.0:5000"
reuse_port = True

# Single worker to prevent conflicts during startup
workers = 1
worker_class = "sync"
timeout = 60
keepalive = 2

# Performance settings
max_requests = 500
max_requests_jitter = 25
graceful_timeout = 15

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Disable preload to avoid conflicts
preload_app = False

# Daemon settings
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None
