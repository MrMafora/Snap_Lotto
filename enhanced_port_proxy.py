#!/usr/bin/env python3
"""
Enhanced Flask-based port proxy with improved reliability and health checks.
This proxy binds to port 8080 and forwards all requests to the main application on port 5000.
Features:
- Self-healing connection handling
- Health monitoring
- Multiple service checking
- Connection pooling for performance
"""
import os
import sys
import time
import logging
import socket
import requests
import threading
from urllib.parse import urlparse
from flask import Flask, request, Response, jsonify
import atexit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('enhanced_port_proxy')

# Create Flask app
app = Flask(__name__)

# Target service details
TARGET_HOST = "localhost"
TARGET_PORT = 5000
TARGET_URL = f"http://{TARGET_HOST}:{TARGET_PORT}"
PROXY_PORT = int(os.environ.get('PORT', 8080))

# Health check status
service_status = {
    'target_service_available': False,
    'last_checked': None,
    'connection_errors': 0,
    'status': 'starting'
}

# Connection pool for improved performance
session = requests.Session()

def is_service_ready(host, port, timeout=1):
    """Check if the target service is running"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except socket.error:
        return False

def check_service_health():
    """Check service health and update status"""
    global service_status
    
    try:
        is_available = is_service_ready(TARGET_HOST, TARGET_PORT)
        service_status['target_service_available'] = is_available
        service_status['last_checked'] = time.time()
        
        if is_available:
            # Try an actual HTTP request to verify full stack
            try:
                resp = session.get(f"{TARGET_URL}/health_port_check", timeout=2)
                if resp.status_code == 200:
                    service_status['status'] = 'healthy'
                    service_status['connection_errors'] = 0
                else:
                    service_status['status'] = 'degraded'
            except:
                service_status['status'] = 'degraded'
        else:
            service_status['status'] = 'unavailable'
            service_status['connection_errors'] += 1
    except Exception as e:
        logger.error(f"Error checking service health: {e}")
        service_status['status'] = 'error'
        service_status['connection_errors'] += 1

def service_health_monitor():
    """Background thread to monitor service health"""
    while True:
        check_service_health()
        time.sleep(10)  # Check every 10 seconds

def wait_for_service():
    """Wait for the target service to become available"""
    max_retries = 30
    retry_count = 0
    
    logger.info(f"Waiting for service at {TARGET_HOST}:{TARGET_PORT}...")
    
    while retry_count < max_retries:
        if is_service_ready(TARGET_HOST, TARGET_PORT):
            logger.info(f"Service at {TARGET_HOST}:{TARGET_PORT} is ready")
            check_service_health()  # Update health status
            return True
        
        retry_count += 1
        time.sleep(1)
    
    logger.error(f"Service at {TARGET_HOST}:{TARGET_PORT} did not become available after {max_retries} seconds")
    return False

@app.route('/proxy_health', methods=['GET'])
def health_check():
    """Health check endpoint for the proxy itself"""
    return jsonify({
        'proxy': {
            'status': 'running',
            'port': PROXY_PORT,
            'uptime': time.time() - app.config.get('start_time', time.time())
        },
        'target_service': service_status
    })

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def proxy(path):
    """Forward all requests to the target service"""
    # Skip proxying for the health check endpoint
    if path == 'proxy_health':
        return health_check()
        
    target_url = f"{TARGET_URL}/{path}"
    
    # Check if target service is available
    if not service_status['target_service_available']:
        # Quick check before returning error
        if is_service_ready(TARGET_HOST, TARGET_PORT):
            service_status['target_service_available'] = True
            service_status['status'] = 'recovering'
        else:
            return "Target service unavailable", 503
    
    # Forward the request
    try:
        # Get the original request headers
        headers = {key: value for key, value in request.headers}
        
        # Delete host header to avoid conflicts
        if 'Host' in headers:
            del headers['Host']
        
        # Add X-Forwarded headers
        headers['X-Forwarded-For'] = request.remote_addr
        headers['X-Forwarded-Proto'] = request.scheme
        headers['X-Forwarded-Host'] = request.host
        
        # Forward the request to the target
        resp = session.request(
            method=request.method,
            url=target_url,
            headers=headers,
            params=request.args,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            timeout=90  # Significantly increased timeout for data-intensive operations
        )
        
        # Create a Flask response
        response = Response(
            resp.content,
            status=resp.status_code
        )
        
        # Add response headers
        for key, value in resp.headers.items():
            response.headers[key] = value
        
        return response
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error forwarding request to {target_url}: {e}")
        service_status['connection_errors'] += 1
        
        # Recheck service health
        check_service_health()
        
        error_message = "Error connecting to application server"
        if service_status['connection_errors'] > 5:
            error_message += " (Service may be down or restarting)"
        
        return error_message, 503

def cleanup():
    """Cleanup resources on shutdown"""
    logger.info("Shutting down enhanced port proxy")
    session.close()

if __name__ == "__main__":
    # Register cleanup handler
    atexit.register(cleanup)
    
    # Wait for the target service to be ready
    if not wait_for_service():
        sys.exit(1)
    
    # Start the health monitor thread
    monitor_thread = threading.Thread(target=service_health_monitor, daemon=True)
    monitor_thread.start()
    
    # Store start time
    app.config['start_time'] = time.time()
    
    # Start the proxy server
    logger.info(f"Starting enhanced proxy server on port {PROXY_PORT}")
    app.run(host='0.0.0.0', port=PROXY_PORT)