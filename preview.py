"""
A minimal Flask application for previewing the lottery app.
This is a temporary solution to fix Replit preview.
"""
from flask import Flask, redirect, render_template_string
import os
import subprocess
import threading
import time

app = Flask(__name__)

# Flag to track if the main app is started
main_app_started = False

def start_main_app():
    """Start the main application in a separate process"""
    global main_app_started
    if not main_app_started:
        try:
            print("Starting main lottery application...")
            # Kill any existing gunicorn processes
            subprocess.run("pkill -f gunicorn || true", shell=True)
            time.sleep(1)
            
            # Start gunicorn with the main app
            cmd = "gunicorn --bind 0.0.0.0:8080 --workers 1 main:app"
            subprocess.Popen(cmd, shell=True)
            main_app_started = True
            print("Main application started on port 8080")
        except Exception as e:
            print(f"Error starting main app: {e}")

@app.route('/')
def index():
    """Home page with redirect to the main app"""
    # Start the main app in a background thread if it's not already running
    if not main_app_started:
        thread = threading.Thread(target=start_main_app)
        thread.daemon = True
        thread.start()
    
    # Return a loading page that will redirect to the main app
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>South African Lottery App</title>
        <meta http-equiv="refresh" content="5;url=https://{{ replit_slug }}.{{ replit_user }}.repl.co:8080">
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 40px; margin: 0; background-color: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; margin-bottom: 20px; }
            .loader { border: 16px solid #f3f3f3; border-top: 16px solid #3498db; border-radius: 50%; width: 120px; height: 120px; animation: spin 2s linear infinite; margin: 30px auto; }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
            p { color: #666; line-height: 1.6; margin-bottom: 15px; font-size: 16px; }
            .button { display: inline-block; background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; font-weight: bold; margin-top: 20px; }
            .button:hover { background-color: #45a049; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>South African Lottery App</h1>
            <div class="loader"></div>
            <p>The application is starting up. Please wait a moment...</p>
            <p>You will be automatically redirected to the main application in 5 seconds.</p>
            <p>If you're not redirected, please click the button below:</p>
            <a class="button" href="https://{{ replit_slug }}.{{ replit_user }}.repl.co:8080">Go to Lottery App</a>
        </div>
    </body>
    </html>
    """, replit_slug=os.environ.get('REPL_SLUG', 'repl'), 
        replit_user=os.environ.get('REPL_OWNER', 'user'))

if __name__ == '__main__':
    # Print this exact message to help Replit detect the port
    print("Server is ready and listening on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=False)