"""
Direct Lottery Data Platform application that runs on port 8080.
This is a standalone version that will work without a port proxy.
"""
import os
import logging
from flask import Flask, jsonify

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def home():
    """Home page showing the application is working"""
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
            <p>You should now be able to see the application instead of a white screen.</p>
            <a href="/health" class="btn">Check System Status</a>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health():
    """Health check endpoint to verify the application is working"""
    return jsonify({
        "status": "healthy",
        "message": "Lottery Data Platform is running correctly",
        "version": "1.0.0"
    })

if __name__ == "__main__":
    # Get port from environment or use 8080 as default
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting direct lottery application on port {port}")
    app.run(host="0.0.0.0", port=port)