"""
Gunicorn configuration file with optimized settings
"""

import multiprocessing
import os

# Server socket - use PORT environment variable for Cloud Run, fallback to 8080
bind = f"0.0.0.0:{os.environ.get('PORT', 8080)}"
backlog = 2048

# Worker processes
workers = min(multiprocessing.cpu_count() * 2 + 1, 4)
worker_class = "gthread"
worker_connections = 1000
threads = 2
max_requests = 1000
max_requests_jitter = 50

# Timeouts
timeout = 30
keepalive = 5
graceful_timeout = 30

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "lottery_app"

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Preload application
preload_app = True

# Worker restarts
max_worker_connections = 1000
worker_tmp_dir = "/dev/shm"

# SSL (if certificates are available)
if os.path.exists("/etc/ssl/certs/lottery.crt"):
    keyfile = "/etc/ssl/private/lottery.key"
    certfile = "/etc/ssl/certs/lottery.crt"