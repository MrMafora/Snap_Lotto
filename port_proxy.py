#!/usr/bin/env python3
"""
Simple HTTP proxy that forwards requests from port 8080 to port 5000
"""
import http.server
import socketserver
import urllib.request
import urllib.error
import sys
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='proxy.log',
    filemode='a'
)
logger = logging.getLogger('proxy')

# Also log to console
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logger.addHandler(console)

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self._forward_request('GET')
        
    def do_POST(self):
        self._forward_request('POST')
        
    def do_HEAD(self):
        self._forward_request('HEAD')
        
    def do_PUT(self):
        self._forward_request('PUT')
        
    def do_DELETE(self):
        self._forward_request('DELETE')
        
    def do_OPTIONS(self):
        self._forward_request('OPTIONS')
        
    def do_PATCH(self):
        self._forward_request('PATCH')
        
    def _forward_request(self, method):
        target_url = f'http://localhost:5000{self.path}'
        logger.info(f'Forwarding {method} request from port 8080 to {target_url}')
        
        try:
            # Get the request body if necessary
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            
            # Create the request
            req = urllib.request.Request(target_url, data=body, method=method)
            
            # Copy request headers
            for header, value in self.headers.items():
                if header.lower() not in ('host', 'content-length'):
                    req.add_header(header, value)
            
            # Send the request to port 5000
            response = urllib.request.urlopen(req, timeout=30)
            
            # Send the response status code
            self.send_response(response.status)
            
            # Send the response headers
            for header, value in response.getheaders():
                if header.lower() != 'transfer-encoding':  # Skip chunked encoding
                    self.send_header(header, value)
            self.end_headers()
            
            # Send the response body
            if method != 'HEAD':
                self.wfile.write(response.read())
                
        except Exception as e:
            logger.error(f'Error forwarding request: {e}')
            self.send_response(502)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            
            error_message = f"""
            <html>
            <head><title>Proxy Error</title></head>
            <body>
                <h1>Proxy Error</h1>
                <p>Error: {str(e)}</p>
            </body>
            </html>
            """
            self.wfile.write(error_message.encode('utf-8'))
    
    def log_message(self, format, *args):
        logger.info('%s - %s', self.address_string(), format % args)

def main():
    max_retries = 5
    retry_count = 0
    retry_delay = 5  # seconds
    
    while retry_count < max_retries:
        try:
            # Allow socket reuse
            socketserver.TCPServer.allow_reuse_address = True
            
            # Create and start the server
            with socketserver.ThreadingTCPServer(('0.0.0.0', 8080), ProxyHandler) as httpd:
                logger.info('Starting proxy server on port 8080 forwarding to port 5000')
                logger.info('Listening on ALL interfaces (0.0.0.0) for better connectivity')
                httpd.serve_forever()
        except KeyboardInterrupt:
            logger.info('Proxy server stopped by user')
            return 0
        except OSError as e:
            if e.errno == 98:  # Address already in use
                logger.error(f"Port 8080 is already in use. Trying to kill existing process...")
                # Try to kill any process using port 8080
                try:
                    import subprocess
                    subprocess.run(["pkill", "-f", "port_proxy.py"], check=False)
                    time.sleep(1)  # Wait a bit for the process to be killed
                    logger.info("Attempting to restart proxy after killing process...")
                    retry_count += 1
                    time.sleep(retry_delay)
                    continue
                except Exception as kill_error:
                    logger.error(f"Failed to kill existing process: {kill_error}")
            logger.error(f"Socket error: {e}")
            retry_count += 1
            time.sleep(retry_delay)
        except Exception as e:
            logger.error(f'Error starting proxy server: {e}')
            retry_count += 1
            time.sleep(retry_delay)
            
    logger.error(f"Failed to start proxy after {max_retries} attempts. Giving up.")
    return 1

if __name__ == '__main__':
    sys.exit(main())