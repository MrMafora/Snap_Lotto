"""
Minimal HTTP Server for Port 8080 using only standard library.
"""
import http.server
import socketserver
import threading
import time
import sys

# Define a simple HTTP handler
class SimpleHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Lottery Data Intelligence Platform</title>
            <meta http-equiv="refresh" content="0;url=https://same-domain:5000/">
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; text-align: center; }
                h1 { color: #4a89dc; }
            </style>
        </head>
        <body>
            <h1>Lottery Data Intelligence Platform</h1>
            <p>Redirecting to main application...</p>
            <script>
                window.location.href = window.location.href.replace(':8080', ':5000');
            </script>
        </body>
        </html>
        """)

    def log_message(self, format, *args):
        # Suppress log messages for cleaner output
        return

# Main function to start the server
def run_server():
    try:
        # Try to create the server on port 8080
        handler = SimpleHandler
        httpd = socketserver.TCPServer(("0.0.0.0", 8080), handler)
        
        # Start the server
        print(f"Minimal HTTP server started on port 8080")
        httpd.serve_forever()
    except Exception as e:
        print(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_server()