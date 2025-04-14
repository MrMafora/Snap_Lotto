"""
Super lightweight HTTP server for Replit.
This script opens port 5000 immediately for preview detection and
launches the main application.
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import subprocess
import time
import os
import sys
import socket

print("Server is ready and listening on port 5000")

class SimpleRedirect(BaseHTTPRequestHandler):
    """Simple HTTP handler that generates a redirect page"""
    
    def log_message(self, format, *args):
        """Silence the default logging"""
        return
    
    def do_GET(self):
        """Handle all GET requests with a redirect to the main app"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>South African Lottery App</title>
            <meta http-equiv="refresh" content="1;url=http://localhost:8080/">
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #4285f4; }}
                .loader {{ border: 16px solid #f3f3f3; border-radius: 50%; border-top: 16px solid #3498db; 
                         width: 80px; height: 80px; animation: spin 2s linear infinite; margin: 30px auto; }}
                @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
                p {{ margin: 20px 0; color: #555; font-size: 16px; line-height: 1.5; }}
                .button {{ display: inline-block; background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; 
                         border-radius: 5px; font-weight: bold; margin-top: 20px; transition: background-color 0.3s; }}
                .button:hover {{ background-color: #45a049; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>South African Lottery App</h1>
                <div class="loader"></div>
                <p>Starting the application on port 8080...</p>
                <p>You will be redirected automatically.</p>
                <p>If not redirected, please click the button below:</p>
                <a class="button" href="http://localhost:8080/">Go to Lottery App</a>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html.encode())

def start_main_app():
    """Start the main application on port 8080"""
    # Wait a moment to ensure the preview server is running
    time.sleep(1)
    print("Starting main application on port 8080...")
    
    try:
        # Kill any existing gunicorn processes
        subprocess.run("pkill -f gunicorn || true", shell=True)
        time.sleep(1)
        
        # Start gunicorn on port 8080
        subprocess.Popen([
            "gunicorn",
            "--bind", "0.0.0.0:8080",
            "--workers", "1",
            "--timeout", "120",
            "main:app"
        ])
        print("Main application started on port 8080")
    except Exception as e:
        print(f"Error starting main application: {e}")

def run_server():
    """Run the minimal HTTP server for Replit to detect"""
    # Create a thread for starting the main app
    app_thread = threading.Thread(target=start_main_app)
    app_thread.daemon = True
    app_thread.start()
    
    # Start the simple HTTP server on port 5000
    try:
        # Reuse the address in case it's still in TIME_WAIT state
        HTTPServer.allow_reuse_address = True
        server = HTTPServer(('0.0.0.0', 5000), SimpleRedirect)
        print("Redirect server started on port 5000")
        server.serve_forever()
    except socket.error as e:
        if 'Address already in use' in str(e):
            print("Error: Port 5000 is already in use.")
            sys.exit(1)
        else:
            raise e
    except KeyboardInterrupt:
        print("Server shutting down...")
        server.socket.close()

if __name__ == "__main__":
    run_server()