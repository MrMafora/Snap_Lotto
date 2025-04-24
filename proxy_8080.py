#!/usr/bin/env python3
import socketserver
import http.server
import urllib.request
import urllib.error
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('proxy')

# Configuration
SOURCE_PORT = 8080  # Port to listen on
TARGET_PORT = 5000  # Port to forward to

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self): self._forward_request('GET')
    def do_POST(self): self._forward_request('POST')
    def do_HEAD(self): self._forward_request('HEAD')
    def do_PUT(self): self._forward_request('PUT')
    def do_DELETE(self): self._forward_request('DELETE')
    def do_OPTIONS(self): self._forward_request('OPTIONS')
    def do_PATCH(self): self._forward_request('PATCH')
    
    def _forward_request(self, method):
        target_url = f'http://127.0.0.1:{TARGET_PORT}{self.path}'
        logger.info(f"Forwarding {method} request to {target_url}")
        
        try:
            # Get request body for methods that may have a body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            
            # Create request
            req = urllib.request.Request(target_url, data=body, method=method)
            
            # Copy all headers except those that might cause issues
            for header, value in self.headers.items():
                if header.lower() not in ('host', 'content-length'):
                    req.add_header(header, value)
            
            # Set content type if it exists
            content_type = self.headers.get('Content-Type')
            if content_type and body:
                req.add_header('Content-Type', content_type)
            
            # Forward request
            response = urllib.request.urlopen(req, timeout=10)
            
            # Set response status
            self.send_response(response.status)
            
            # Forward response headers
            for header, value in response.getheaders():
                self.send_header(header, value)
            self.end_headers()
            
            # Forward response body for methods that expect it
            if method != 'HEAD':
                self.wfile.write(response.read())
        except Exception as e:
            logger.error(f"Proxy error: {str(e)}")
            self.send_response(502)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            
            error_message = f"""
            <html>
            <head><title>Proxy Error</title></head>
            <body>
                <h1>Proxy Error</h1>
                <p>The proxy server could not connect to the application server.</p>
                <p>Error: {str(e)}</p>
            </body>
            </html>
            """
            self.wfile.write(error_message.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info("%s - %s", self.address_string(), format % args)

def main():
    try:
        # Use ThreadingTCPServer for better performance
        socketserver.ThreadingTCPServer.allow_reuse_address = True
        httpd = socketserver.ThreadingTCPServer(("", SOURCE_PORT), ProxyHandler)
        
        logger.info(f"Starting proxy server on port {SOURCE_PORT} → {TARGET_PORT}")
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Proxy server stopped by user")
    except Exception as e:
        logger.error(f"Error starting proxy: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())