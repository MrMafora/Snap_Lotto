# Gunicorn configuration file
# https://docs.gunicorn.org/en/stable/configure.html

import multiprocessing
import os

# Determine if we're in production or development
is_production = os.environ.get('ENVIRONMENT') == 'production'

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 if is_production else 2
worker_class = "gthread"  # Using threads for better I/O performance
threads = 4  # Number of threads per worker
worker_connections = 1000
timeout = 60 if is_production else 30  # Longer timeout in production
keepalive = 5 if is_production else 2

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Logging
errorlog = "-"
loglevel = "warning" if is_production else "info"  # Less verbose in production
accesslog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = None

# Server hooks
def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_fork(server, worker):
    pass

def pre_exec(server):
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def worker_abort(worker):
    worker.log.info("worker received SIGABRT signal")

def worker_exit(server, worker):
    server.log.info("Worker exited (pid: %s)", worker.pid)