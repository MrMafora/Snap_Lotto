#!/usr/bin/env python3
"""
Simple Flask-based port proxy that binds directly to port 8080
and forwards all requests to the main application on port 5000.
"""
import os
import sys
import time
import logging
import socket
import requests
from urllib.parse import urlparse
from flask import Flask, request, Response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('flask_port_proxy')

# Create Flask app
app = Flask(__name__)

# Target service details
TARGET_HOST = "localhost"
TARGET_PORT = 5000
TARGET_URL = f"http://{TARGET_HOST}:{TARGET_PORT}"

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

def wait_for_service():
    """Wait for the target service to become available"""
    max_retries = 30
    retry_count = 0
    
    logger.info(f"Waiting for service at {TARGET_HOST}:{TARGET_PORT}...")
    
    while retry_count < max_retries:
        if is_service_ready(TARGET_HOST, TARGET_PORT):
            logger.info(f"Service at {TARGET_HOST}:{TARGET_PORT} is ready")
            return True
        
        retry_count += 1
        time.sleep(1)
    
    logger.error(f"Service at {TARGET_HOST}:{TARGET_PORT} did not become available after {max_retries} seconds")
    return False

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def proxy(path):
    """Forward all requests to the target service"""
    target_url = f"{TARGET_URL}/{path}"
    
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
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            params=request.args,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            timeout=10
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
        logger.error(f"Error forwarding request: {e}")
        return f"Error forwarding request: {e}", 503

if __name__ == "__main__":
    # Wait for the target service to be ready
    if not wait_for_service():
        sys.exit(1)
    
    # Start the proxy server
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting proxy server on port {port}")
    app.run(host='0.0.0.0', port=port)