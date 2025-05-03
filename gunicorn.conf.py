
"""
SIMPLIFIED Gunicorn configuration file for Snap Lotto
- Binds directly to port 5000 (Replit handles the forwarding to port 8080)
- No need for separate port proxy processes
"""
import multiprocessing
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('gunicorn.conf')

# IMPORTANT: We bind directly to port 5000 and Replit handles the forwarding
# This eliminates the need for separate proxy processes
bind = "0.0.0.0:5000"

# Optimize worker count (use fewer workers for faster startup)
workers = 3  # Fixed number instead of dynamic calculation

# Use gthread worker class for better performance with Flask
worker_class = "gthread"
threads = 4

# Connection settings
timeout = 120
keepalive = 2

# Performance optimizations
max_requests = 1000
max_requests_jitter = 50
graceful_timeout = 30

# Logging configuration
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "info"

# Enable automatic SSL handling for Replit
forwarded_allow_ips = '*'
secure_scheme_headers = {
    'X-Forwarded-Proto': 'https'
}

logger.info("Gunicorn configured with simplified settings - direct binding to port 5000")
