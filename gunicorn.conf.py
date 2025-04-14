# Gunicorn configuration file
# https://docs.gunicorn.org/en/stable/configure.html

import multiprocessing
import os

# Determine if we're in production or development
is_production = os.environ.get('ENVIRONMENT') == 'production'

# Server socket - bind immediately for Replit detection
bind = "0.0.0.0:5000"
backlog = 2048

# Import socket for immediate port binding
import socket
import threading
import sys

# Global socket to keep reference
_replit_socket = None

# Open port immediately for Replit detection
def open_port_immediately():
    global _replit_socket
    try:
        # Create a socket with reuse_addr option
        _replit_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _replit_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Try to bind to port 5000 - this may fail if gunicorn is already binding
        try:
            _replit_socket.bind(('0.0.0.0', 5000))
            _replit_socket.listen(1)
            print("Port 5000 immediately opened for Replit detection")
            sys.stdout.flush()
            
            # Store socket reference to avoid garbage collection
            socket_ref = _replit_socket
            
            # Don't close the socket - keep it open until gunicorn takes over
            # We'll handle connections to show a loading message
            def handle_connections():
                # Local reference to avoid None issues
                sock = socket_ref
                if not sock:
                    return
                    
                try:
                    while sock:
                        try:
                            client, _ = sock.accept()
                            response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
                            response += "<html><body><h1>Application is starting...</h1></body></html>"
                            client.send(response.encode())
                            client.close()
                        except Exception as e:
                            # Socket likely taken over by gunicorn or closed
                            print(f"Socket handler stopping: {e}")
                            break
                except Exception:
                    # Catch any other exceptions
                    pass
            
            # Start handling connections in a separate thread
            conn_thread = threading.Thread(target=handle_connections)
            conn_thread.daemon = True
            conn_thread.start()
            
        except OSError as e:
            # Socket already in use - gunicorn probably already has it
            print(f"Port 5000 already in use (probably by gunicorn): {e}")
            sys.stdout.flush()
            
    except Exception as e:
        print(f"Immediate port opening error: {e}")
        sys.stdout.flush()

# Try to open port immediately during module load
try:
    immediate_thread = threading.Thread(target=open_port_immediately)
    immediate_thread.daemon = True
    immediate_thread.start()
except:
    # Silently continue if this fails
    pass

# Worker processes - keep minimum for faster startup in Replit
workers = 1  # Use only 1 worker for faster startup
worker_class = "sync"  # Simplest worker type for faster startup
threads = 1  # Minimum threads for faster startup
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
    # Close our manual socket if it's open
    global _replit_socket
    if _replit_socket is not None:
        try:
            _replit_socket.close()
            print("Closed manual socket handoff to gunicorn")
            # Set to None after closing
            _replit_socket = None
        except Exception as e:
            print(f"Error closing socket: {e}")
            pass
    
    # Print a message that Replit can detect to know the server is ready
    print("Server is ready and listening on port 5000")
    sys.stdout.flush()
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def worker_abort(worker):
    worker.log.info("worker received SIGABRT signal")

def worker_exit(server, worker):
    server.log.info("Worker exited (pid: %s)", worker.pid)