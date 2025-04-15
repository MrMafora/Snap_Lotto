#!/bin/bash
# Script to implement the port binding solution for Replit deployment

# Display banner
echo "=============================================="
echo "  Implementing Dual Port Binding Solution"
echo "=============================================="
echo ""

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "Error: Python is required but not found."
    exit 1
fi

# Check if run_port_8080_bridge.py exists
if [ -f "run_port_8080_bridge.py" ]; then
    echo "✓ run_port_8080_bridge.py already exists"
else
    echo "Creating run_port_8080_bridge.py..."
    cat > run_port_8080_bridge.py << 'EOF'
#!/usr/bin/env python3
"""
Simple HTTP server that listens on port 8080 and redirects all requests to port 5000.
This ensures compatibility with Replit's external access requirements.
"""
import http.server
import socketserver
import threading
import time
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler('simple_8080.log')]
)
logger = logging.getLogger('port_bridge')

class RedirectHandler(http.server.BaseHTTPRequestHandler):
    def redirect_request(self):
        """Redirect all requests to the same path on port 5000"""
        try:
            self.send_response(302)
            host = self.headers.get('Host', '')
            # Replace port 8080 with 5000 in the host header
            redirect_host = host.replace(':8080', ':5000') if ':8080' in host else host
            redirect_url = f'https://{redirect_host}{self.path}'
            self.send_header('Location', redirect_url)
            self.end_headers()
            logger.info(f"Redirecting request from {host}{self.path} to {redirect_host}{self.path}")
        except Exception as e:
            logger.error(f"Error during redirect: {str(e)}")
    
    # Handle all HTTP methods
    do_GET = do_POST = do_PUT = do_DELETE = do_HEAD = do_OPTIONS = redirect_request
    
    def log_message(self, format, *args):
        """Override the default logging to use our logger"""
        logger.info(f"8080 Server: {format % args}")

def run_server():
    """Run the HTTP server on port 8080"""
    try:
        logger.info('Starting redirector server on port 8080...')
        with socketserver.TCPServer(('0.0.0.0', 8080), RedirectHandler) as server:
            logger.info('Port 8080 server started successfully. Redirecting all traffic to port 5000.')
            server.serve_forever()
    except Exception as e:
        logger.error(f'Error starting port 8080 server: {e}')
        sys.exit(1)

if __name__ == "__main__":
    run_server()
EOF
    echo "✓ Created run_port_8080_bridge.py"
fi

# Check if dual_port_binding.py exists
if [ -f "dual_port_binding.py" ]; then
    echo "✓ dual_port_binding.py already exists"
else
    echo "Creating dual_port_binding.py..."
    cat > dual_port_binding.py << 'EOF'
#!/usr/bin/env python3
"""
Combined dual port binding solution for Replit deployments.
This script handles requests on both port 5000 (main application) and port 8080 (redirecting to 5000).
"""
import http.server
import socketserver
import threading
import subprocess
import sys
import time
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('dual_port')

class RedirectHandler(http.server.BaseHTTPRequestHandler):
    """Redirect all port 8080 requests to port 5000"""
    def redirect_request(self):
        """Redirect request to port 5000"""
        try:
            self.send_response(302)
            host = self.headers.get('Host', '')
            # Replace port 8080 with 5000 in the host header
            redirect_host = host.replace(':8080', ':5000') if ':8080' in host else host
            redirect_url = f'https://{redirect_host}{self.path}'
            self.send_header('Location', redirect_url)
            self.end_headers()
            logger.info(f"Redirecting request from {host}{self.path} to {redirect_host}{self.path}")
        except Exception as e:
            logger.error(f"Error during redirect: {str(e)}")
    
    # Handle all HTTP methods
    do_GET = do_POST = do_PUT = do_DELETE = do_HEAD = do_OPTIONS = redirect_request
    
    def log_message(self, format, *args):
        """Override the default logging to use our logger"""
        logger.info(f"8080 Server: {format % args}")

def run_port_8080_server():
    """Start the port 8080 redirect server in a separate thread"""
    try:
        logger.info('Starting redirect server on port 8080...')
        with socketserver.TCPServer(('0.0.0.0', 8080), RedirectHandler) as server:
            logger.info('Port 8080 server started successfully. Redirecting all traffic to port 5000.')
            server.serve_forever()
    except Exception as e:
        logger.error(f'Error starting port 8080 server: {e}')

def start_main_application():
    """Start the main Flask application using Gunicorn on port 5000"""
    try:
        logger.info('Starting main application on port 5000 with Gunicorn...')
        # Run gunicorn with the same parameters as in the workflow configuration
        result = subprocess.run(
            ['gunicorn', '--bind', '0.0.0.0:5000', '--reuse-port', '--reload', 'main:app'],
            check=True
        )
        logger.info(f'Gunicorn process exited with code: {result.returncode}')
        return result.returncode
    except subprocess.CalledProcessError as e:
        logger.error(f'Error running Gunicorn: {e}')
        return e.returncode
    except Exception as e:
        logger.error(f'Unexpected error starting main application: {e}')
        return 1

if __name__ == "__main__":
    # Start the port 8080 server in a background thread
    port_8080_thread = threading.Thread(target=run_port_8080_server, daemon=True)
    port_8080_thread.start()
    
    # Give the 8080 server a moment to start
    time.sleep(1)
    print("Server is ready and listening on ports 5000 and 8080")
    
    try:
        # Start the main application in the main thread
        exit_code = start_main_application()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        sys.exit(0)
EOF
    echo "✓ Created dual_port_binding.py"
fi

# Check if start_app.sh exists
if [ -f "start_app.sh" ]; then
    echo "✓ start_app.sh already exists"
else
    echo "Creating start_app.sh..."
    cat > start_app.sh << 'EOF'
#!/bin/bash
# Master script to start both the port 8080 bridge and main application

# Run the port 8080 bridge in the background
echo "Starting port 8080 bridge application..."
python run_port_8080_bridge.py > port_8080.log 2>&1 &
PORT_8080_PID=$!

# Give the bridge a moment to start
sleep 1

# Start the main application with Gunicorn
echo "Starting main application on port 5000..."
exec gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
EOF
    echo "✓ Created start_app.sh"
fi

# Make all scripts executable
chmod +x run_port_8080_bridge.py
chmod +x dual_port_binding.py
chmod +x start_app.sh

echo ""
echo "All scripts are now set up and executable."
echo ""
echo "To use the dual port binding solution, update your Replit"
echo "workflow configuration to run either:"
echo ""
echo "  python dual_port_binding.py"
echo ""
echo "OR"
echo ""
echo "  bash start_app.sh"
echo ""
echo "Both options will start your application on port 5000 and"
echo "make it accessible via port 8080 for Replit WebView compatibility."
echo ""
echo "=============================================="
echo "  Setup Complete!"
echo "=============================================="