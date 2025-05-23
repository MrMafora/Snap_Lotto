"""
Application module for the lottery data app.
This file is designed to be imported by Gunicorn when starting the application.
"""
from flask import Flask, render_template, redirect, url_for
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the app
app = Flask(__name__)

# Set secret key from environment variable
app.secret_key = os.environ.get("SESSION_SECRET", "lottery-scraper-default-secret")

@app.route('/')
def index():
    """Temporary index page while fixing the main application"""
    return """
    <html>
        <head>
            <title>Lottery Data Platform</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                h1 { color: #2c3e50; }
                .container { max-width: 800px; margin: 0 auto; }
                .btn { 
                    display: inline-block; 
                    padding: 10px 20px; 
                    background-color: #3498db; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin-top: 20px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Lottery Data Platform</h1>
                <p>The application is now running! This temporary page confirms the server is working correctly.</p>
                <p>We're currently fixing the main application interface. Please check back shortly.</p>
                <a href="/test" class="btn">Test Connection</a>
            </div>
        </body>
    </html>
    """
    
@app.route('/test')
def test():
    """Test page to verify routing is working"""
    return """
    <html>
        <head>
            <title>Connection Test | Lottery Data Platform</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                h1 { color: #2c3e50; }
                .success { color: #27ae60; font-weight: bold; }
                .container { max-width: 800px; margin: 0 auto; }
                .btn { 
                    display: inline-block; 
                    padding: 10px 20px; 
                    background-color: #3498db; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin-top: 20px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Connection Test</h1>
                <p class="success">✓ Success! The application routing is working correctly.</p>
                <p>This confirms that the web server is correctly handling requests and responses.</p>
                <a href="/" class="btn">Back to Home</a>
            </div>
        </body>
    </html>
    """

# Add more necessary routes here as needed

if __name__ == "__main__":
    # Only used for direct execution, not when run with Gunicorn
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)