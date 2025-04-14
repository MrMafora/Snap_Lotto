"""
Minimal HTTP server script that instantly opens port 5000 and redirects to port 8080
"""
import http.server
import socketserver
import threading
import time
import subprocess
import os

class RedirectHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(302)
        self.send_header('Location', 'http://localhost:8080' + self.path)
        self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress logging for cleaner output
        return

# Print this message exactly for Replit port detection
print("Server is ready and listening on port 5000")

def start_main_app():
    """Start the main application on port 8080"""
    time.sleep(1)
    subprocess.run(["pkill", "-f", "gunicorn"])
    time.sleep(1)
    subprocess.Popen(["gunicorn", "--bind", "0.0.0.0:8080", "--config", "gunicorn.conf.py", "main:app"])

# Start the main app in a background thread
thread = threading.Thread(target=start_main_app)
thread.daemon = True
thread.start()

# Start the redirect server on port 5000
with socketserver.TCPServer(("0.0.0.0", 5000), RedirectHandler) as httpd:
    httpd.serve_forever()