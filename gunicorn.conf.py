import os

bind = f"0.0.0.0:{os.environ.get('PORT', 8080)}"
workers = 2
worker_class = "gthread"
threads = 2
timeout = 0
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
worker_connections = 1000
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

# Worker restarts
max_worker_connections = 1000
worker_tmp_dir = "/dev/shm"

# SSL (if certificates are available)
if os.path.exists("/etc/ssl/certs/lottery.crt"):
    keyfile = "/etc/ssl/private/lottery.key"
    certfile = "/etc/ssl/certs/lottery.crt"