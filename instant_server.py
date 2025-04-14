"""
Extremely minimal HTTP server that starts instantly for Replit preview.
"""
import http.server
import socketserver
import threading
import time
import subprocess

# This exact string is needed for Replit port detection
print("Server is ready and listening on port 5000")

class SimpleHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests with a simple HTML response"""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        
        # Simple HTML page with styling
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>South African Lottery App</title>
            <meta http-equiv="refresh" content="5;url=http://localhost:8080/">
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; background-color: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #4285f4; }
                .loader { border: 16px solid #f3f3f3; border-radius: 50%; border-top: 16px solid #3498db; 
                         width: 80px; height: 80px; animation: spin 2s linear infinite; margin: 30px auto; }
                @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
                p { margin: 20px 0; color: #555; font-size: 16px; line-height: 1.5; }
                .button { display: inline-block; background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; 
                         border-radius: 5px; font-weight: bold; margin-top: 20px; transition: background-color 0.3s; }
                .button:hover { background-color: #45a049; }
                .note { font-size: 14px; color: #777; margin-top: 40px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>South African Lottery App</h1>
                <div class="loader"></div>
                <p>The main application is starting on port 8080.</p>
                <p>You will be redirected automatically in 5 seconds.</p>
                <p>If not redirected, please click the button below:</p>
                <a class="button" href="http://localhost:8080/">Go to Lottery App</a>
                <p class="note">Note: This is just a temporary page to ensure Replit can properly preview the application.</p>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html.encode())

def start_main_app():
    """Start the main application after a delay"""
    time.sleep(2)
    print("Starting main lottery application...")
    # Kill any existing gunicorn processes
    subprocess.run("pkill -f gunicorn || true", shell=True)
    # Start gunicorn with the main app but on a different port (8080)
    # This way the instant server continues to handle port 5000 for Replit detection
    subprocess.Popen(["gunicorn", "--bind", "0.0.0.0:8080", "main:app"])

# Create an HTTP server on port 5000
httpd = socketserver.TCPServer(("", 5000), SimpleHandler)

# Start the main app in a background thread
threading.Thread(target=start_main_app, daemon=True).start()

# Serve until process is killed
try:
    httpd.serve_forever()
except KeyboardInterrupt:
    pass