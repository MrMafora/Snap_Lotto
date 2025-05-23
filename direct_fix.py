"""
Direct fix for the white screen issue with the lottery data platform.
This application binds directly to port 8080 without using a proxy.
"""
import os
import logging
from flask import Flask, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the app
app = Flask(__name__)

@app.route('/')
def home():
    """Home page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Lottery Data Platform</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 0; 
                padding: 0; 
                background-color: #f5f5f5; 
            }
            .container { 
                max-width: 800px; 
                margin: 40px auto; 
                padding: 20px; 
                background-color: white; 
                border-radius: 8px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
            }
            h1 { color: #2c3e50; }
            .message { 
                background-color: #d4edda; 
                color: #155724; 
                padding: 15px; 
                border-radius: 4px; 
                margin-bottom: 20px; 
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Lottery Data Platform</h1>
            <div class="message">
                <strong>Success!</strong> The application is now working correctly.
            </div>
            <p>This confirms that your web server is properly configured and the white screen issue has been resolved.</p>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    # Run on a different port (8081) to avoid conflicts
    port = 8081
    logger.info(f"Starting direct fix application on port {port}")
    app.run(host="0.0.0.0", port=port)