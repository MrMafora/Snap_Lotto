"""
Simple direct port proxy that binds to port 8080 and forwards to port 5000.
This version is simplified for reliability.
"""
import os
import logging
from flask import Flask, request, Response
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Target application
TARGET_URL = "http://localhost:5000"

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def proxy(path):
    """Forward all requests to the target application"""
    target_url = f"{TARGET_URL}/{path}"
    
    try:
        logger.info(f"Forwarding {request.method} request to {target_url}")
        
        # Forward the request to the target
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers={key: value for key, value in request.headers if key != 'Host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            timeout=30
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
        
    except requests.exceptions.ConnectionError:
        return "<h1>Lottery Data Platform</h1><p>The main application is not available. Please try again in a moment.</p>", 503
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        return f"<h1>Proxy Error</h1><p>Error details: {e}</p>", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting direct port proxy on port {port}")
    app.run(host="0.0.0.0", port=port)