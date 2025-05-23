"""
Simple Flask application that runs directly on port 8080.
This is a basic version to ensure the app is visible.
"""
from flask import Flask
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the app
app = Flask(__name__)

@app.route('/')
def index():
    """Simple home page"""
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
            <p>This simplified version confirms that the server is properly configured and accessible.</p>
            <p>We can now proceed with implementing the full functionality of your lottery data platform.</p>
        </div>
    </body>
    </html>
    """

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting simple application on port {port}")
    app.run(host="0.0.0.0", port=port)