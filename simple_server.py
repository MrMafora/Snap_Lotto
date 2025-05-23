"""
Simple standalone Flask server on port 8080 for testing
"""
import os
import logging
from flask import Flask, render_template

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create app
app = Flask(__name__)

@app.route('/')
def index():
    """Simple home page"""
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
                <p>This simple server is working correctly on port 8080!</p>
                <p>We'll use this to transition to the full application.</p>
            </div>
        </body>
    </html>
    """

if __name__ == "__main__":
    # Run on port 8080
    port = 8080
    logger.info(f"Starting simple server on port {port}")
    app.run(host="0.0.0.0", port=port)