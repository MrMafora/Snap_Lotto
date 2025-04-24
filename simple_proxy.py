#!/usr/bin/env python3
import http.server
import socketserver
import urllib.request
import sys
import signal
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('proxy')

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self): self._handle_request('GET')
    def do_POST(self): self._handle_request('POST')
    def do_HEAD(self): self._handle_request('HEAD')
    def do_PUT(self): self._handle_request('PUT')
    def do_DELETE(self): self._handle_request('DELETE')
    def do_OPTIONS(self): self._handle_request('OPTIONS')
    def do_PATCH(self): self._handle_request('PATCH')
    
    def _handle_request(self, method):
        """Forward all requests to port 5000"""
        target_url = f'http://localhost:5000{self.path}'
        
        try:
            # Get the body for methods that might have one
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None
            
            # Create the request
            req = urllib.request.Request(target_url, data=body, method=method)
            
            # Copy headers, except those that might cause issues
            for header, value in self.headers.items():
                if header.lower() not in ('host', 'content-length'):
                    req.add_header(header, value)
            
            # Send the request
            with urllib.request.urlopen(req, timeout=10) as response:
                # Copy response code
                self.send_response(response.status)
                
                # Copy headers
                for header, value in response.getheaders():
                    if header.lower() != 'transfer-encoding':  # Skip chunked encoding
                        self.send_header(header, value)
                self.end_headers()
                
                # Copy body for methods that return one
                if method != 'HEAD':
                    self.wfile.write(response.read())
                    
        except Exception as e:
            logger.error(f"Error proxying request: {e}")
            self.send_response(502)  # Bad Gateway
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            
            error_page = f"""
            <html>
            <head><title>Proxy Error</title></head>
            <body>
                <h1>Proxy Error</h1>
                <p>The proxy server could not complete your request.</p>
                <p>Error: {str(e)}</p>
            </body>
            </html>
            """
            self.wfile.write(error_page.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override to use our logger"""
        logger.info("%s - %s", self.address_string(), format % args)

def handle_signal(signum, frame):
    """Handle termination signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

def main():
    """Main entry point"""
    try:
        # Allow the server to reuse the address
        socketserver.TCPServer.allow_reuse_address = True
        
        # Create and start the server
        with socketserver.ThreadingTCPServer(("", 8080), ProxyHandler) as httpd:
            logger.info("Starting proxy server on port 8080 forwarding to port 5000")
            httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Proxy server stopped by user")
    except Exception as e:
        logger.error(f"Error starting proxy server: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
