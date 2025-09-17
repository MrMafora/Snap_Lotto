
import os

# Cloud Run provides PORT environment variable
port = int(os.environ.get('PORT', 8080))
bind = f"0.0.0.0:{port}"
workers = 1
worker_class = "sync"
timeout = 300
keepalive = 2
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "sa_lottery_app"

# Worker settings for Cloud Run
worker_tmp_dir = "/dev/shm"
worker_connections = 1000
