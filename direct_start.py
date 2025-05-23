"""
Direct application starter that binds to port 8080 directly
This bypasses the need for a port proxy
"""
import os
import logging
from flask import Flask

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a minimal test app
app = Flask(__name__)

@app.route('/')
def home():
    """Simple test endpoint"""
    return """
    <html>
        <head>
            <title>Lottery Data Platform</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                h1 { color: #2c3e50; }
                .container { max-width: 800px; margin: 0 auto; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Lottery Data Platform</h1>
                <p>The application is working correctly! This is a direct connection to port 8080.</p>
                <p>You can now proceed to use the full application.</p>
            </div>
        </body>
    </html>
    """

if __name__ == "__main__":
    # Get the port from environment or use 8080
    port = int(os.environ.get("PORT", 8080))
    
    logger.info(f"Starting direct application on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)