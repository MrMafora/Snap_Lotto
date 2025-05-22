#!/usr/bin/env python3
"""
Simple Flask-based port proxy that forwards requests from port 8080 to 5000.
This is a simplified alternative to the more complex proxy solutions.
"""

import logging
import requests
from flask import Flask, request, Response, stream_with_context

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('port_proxy')

# Create Flask app
app = Flask(__name__)

# Target application URL (where to forward requests)
TARGET_URL = "http://localhost:5000"

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def proxy(path):
    """
    Forward all requests to the target server.
    This handles any path and any HTTP method.
    """
    # Construct the target URL
    url = f"{TARGET_URL}/{path}"
    logger.info(f"Forwarding {request.method} request to: {url}")
    
    # Forward the request to the target server with the same method, headers and body
    try:
        # Get the request headers, excluding those that would cause issues
        headers = {key: value for key, value in request.headers if key.lower() not in 
                   ['host', 'content-length']}
        
        # Forward the request with the appropriate method
        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            params=request.args,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            stream=True
        )
        
        # Create a Flask response object from the target server's response
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for name, value in resp.raw.headers.items()
                  if name.lower() not in excluded_headers]
        
        # Stream the response back to the client
        return Response(
            stream_with_context(resp.iter_content(chunk_size=1024)),
            status=resp.status_code,
            headers=headers
        )
    
    except requests.RequestException as e:
        logger.error(f"Error forwarding request: {e}")
        return f"Error: {str(e)}", 502

if __name__ == "__main__":
    logger.info(f"Starting port proxy on port 8080, forwarding to {TARGET_URL}")
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)