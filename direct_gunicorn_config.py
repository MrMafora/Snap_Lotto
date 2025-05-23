"""
Gunicorn configuration for direct port 8080 binding
"""
import os
import multiprocessing

# Bind directly to port 8080 for public access
bind = "0.0.0.0:8080"

# Set number of workers based on cores
workers = multiprocessing.cpu_count() * 2 + 1

# Use threads for better handling of concurrent requests
worker_class = "gthread"
threads = 2

# Timeout settings
timeout = 120
keepalive = 5

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "info"

# Load application
wsgi_app = "direct_lottery_app:app"