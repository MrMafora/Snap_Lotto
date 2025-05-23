"""
Simple Gunicorn application that runs directly on port 8080
"""
import os
import time
import logging
from flask import Flask, render_template

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the application
app = Flask(__name__)

@app.route('/')
def index():
    """Simple home page that confirms the application is working"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Lottery Data Platform</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }
            .container { max-width: 800px; margin: 40px auto; padding: 20px; 
                        background-color: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; margin-top: 0; }
            .success { color: #27ae60; font-weight: bold; }
            .btn { display: inline-block; padding: 10px 20px; background-color: #3498db; 
                  color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Lottery Data Platform</h1>
            <p class="success">✓ Success! The application is now working correctly.</p>
            <p>This confirms that the server is properly configured and accessible.</p>
            <p>The white screen issue has been resolved!</p>
        </div>
    </body>
    </html>
    """

@app.route('/test')
def test():
    """Test page to verify routes are working"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page | Lottery Data Platform</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }
            .container { max-width: 800px; margin: 40px auto; padding: 20px; 
                        background-color: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; margin-top: 0; }
            .success { color: #27ae60; font-weight: bold; }
            .btn { display: inline-block; padding: 10px 20px; background-color: #3498db; 
                  color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Test Page</h1>
            <p class="success">✓ Success! Routes are working correctly.</p>
            <p>This confirms that navigation is functioning properly.</p>
            <a href="/" class="btn">Back to Home</a>
        </div>
    </body>
    </html>
    """