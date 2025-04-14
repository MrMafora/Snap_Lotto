"""
A special minimal server designed to solve Replit port detection issues.
This server responds immediately to port detection and then launches the main app.
"""
from flask import Flask, redirect, send_from_directory
import threading
import time
import subprocess
import socket
import os
import sys
import signal

# Create simple Flask app for initial port detection
app = Flask(__name__)

# Flag to track if the main server has been started
main_server_started = False

def kill_existing_processes():
    """Kill any existing servers on port 5000"""
    try:
        # Find and kill any processes using port 5000
        subprocess.run("pkill -f gunicorn", shell=True)
        time.sleep(1)
    except Exception as e:
        print(f"Error killing processes: {e}")

def start_main_server():
    """Start the main application server"""
    global main_server_started
    
    if not main_server_started:
        print("Starting main application server...")
        # Start gunicorn directly with specific parameters for faster startup
        cmd = [
            "gunicorn",
            "--bind", "0.0.0.0:8080",  # Use a different port
            "--workers", "1",
            "--timeout", "120",
            "--access-logfile", "-",
            "--error-logfile", "-",
            "main:app"
        ]
        
        # Start the server process
        try:
            subprocess.Popen(cmd)
            main_server_started = True
            print("Main server started on port 8080")
        except Exception as e:
            print(f"Error starting main server: {e}")

@app.route('/')
def index():
    """Home page that launches the main server on first visit"""
    # Start the main server if it hasn't been started yet
    if not main_server_started:
        threading.Thread(target=start_main_server).start()
    
    # Show a loading page that will redirect to the main app
    return """
    <html>
    <head>
        <title>Lottery App - Loading</title>
        <meta http-equiv="refresh" content="5;url=http://localhost:8080/">
        <style>
            body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; background-color: #f5f5f5; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; background-color: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; }
            .loader { border: 16px solid #f3f3f3; border-top: 16px solid #3498db; border-radius: 50%; width: 80px; height: 80px; animation: spin 2s linear infinite; margin: 30px auto; }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            p { color: #666; font-size: 16px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>South African Lottery App</h1>
            <div class="loader"></div>
            <p>Starting the application...</p>
            <p>You will be redirected automatically in 5 seconds.</p>
            <p>If not redirected, <a href="http://localhost:8080/">click here</a>.</p>
        </div>
    </body>
    </html>
    """

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

def main():
    """Main entry point"""
    # Kill any existing processes using our ports
    kill_existing_processes()
    
    # Print specifically this line for Replit port detection
    print("Server is ready and listening on port 5000")
    
    # Start Flask on port 5000 for Replit to detect
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == "__main__":
    main()