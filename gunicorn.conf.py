"""
Gunicorn configuration for both development and deployment
This ensures consistent binding across environments
"""

# Binding
bind = "0.0.0.0:8080"

# Worker settings
workers = 4
worker_class = "sync"
threads = 2
timeout = 120

# Server mechanics
graceful_timeout = 30
keepalive = 5
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Auto-reload on code changes
reload = True

# Additional settings for production
worker_tmp_dir = "/dev/shm"