import os

# Cloud Run provides PORT environment variable
port = int(os.environ.get('PORT', 8080))
bind = f"0.0.0.0:{port}"
workers = 2
worker_class = "sync"
timeout = 120
keepalive = 2
max_requests = 500
preload_app = True

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "lottery_app"