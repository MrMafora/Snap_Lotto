
import os
import multiprocessing

# Server socket - Use PORT environment variable
bind = f"0.0.0.0:{os.environ.get('PORT', 8080)}"
backlog = 2048

# Worker processes - ultra-optimized for minimal memory
workers = 1
worker_class = "gthread" 
threads = 1
worker_connections = 200
max_requests = 200
max_requests_jitter = 10
preload_app = True

# Timeout settings - optimized for memory efficiency
timeout = 30
keepalive = 1
graceful_timeout = 15

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "sa-lottery-app"

# Environment
raw_env = [
    f"PORT={os.environ.get('PORT', 8080)}"
]
