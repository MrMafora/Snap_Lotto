#!/usr/bin/env python3
"""
Simple HTTP server binding directly to port 8080 with minimal dependencies.
"""
import http.server
import socketserver
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='simple_8080.log'
)

# Define handler
class SimpleHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health' or self.path == '/health_check':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = '{"status": "ok", "message": "Port 8080 is accessible"}'
            self.wfile.write(response.encode('utf-8'))
        else:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            response = '<html><body><h1>Port 8080 is working!</h1><p>This is a simple server running on port 8080.</p></body></html>'
            self.wfile.write(response.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override the default logging to use our logger"""
        logging.info(f"{self.client_address[0]} - {format % args}")

def run_server(port=8080):
    PORT = port
    server_address = ('0.0.0.0', PORT)
    
    # Create server
    logging.info(f"Starting server on port {PORT}")
    httpd = socketserver.TCPServer(server_address, SimpleHandler)
    
    # Serve until process is killed
    logging.info(f"Server is running on port {PORT}")
    print(f"Server is running on port {PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logging.info("Server shutdown requested")
    finally:
        httpd.server_close()
        logging.info("Server shut down")

if __name__ == "__main__":
    run_server()