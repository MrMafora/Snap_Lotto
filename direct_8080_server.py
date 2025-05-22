"""
Direct server that runs the application on port 8080 without proxies
"""
import os
import logging
from flask import Flask

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create a basic Flask app for testing
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
        <head>
            <title>Snap Lotto Test Page</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 40px;
                    line-height: 1.6;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                }
                h1 {
                    color: #2c3e50;
                }
                .success {
                    color: green;
                    font-weight: bold;
                }
                .section {
                    margin: 20px 0;
                    padding: 15px;
                    background-color: #f9f9f9;
                    border-radius: 5px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Snap Lotto Test Page</h1>
                <p class="success">If you can see this page, your server is running correctly on port 8080!</p>
                
                <div class="section">
                    <h2>Lottery Ticket Scanner</h2>
                    <p>Our ticket scanner feature is set up with both API keys:</p>
                    <ul>
                        <li>Google Gemini API for OCR capabilities</li>
                        <li>OpenAI for retrieving missing draw information</li>
                    </ul>
                    <p>The scanner can extract ticket information and check it against our database.</p>
                </div>
                
                <div class="section">
                    <h2>Database Status</h2>
                    <p>Our database contains correctly formatted lottery data:</p>
                    <ul>
                        <li>Numbers stored as strings with leading zeros where needed</li>
                        <li>Normalized lottery types (Lottery, Powerball, Daily Lottery)</li>
                        <li>Recent draws available for verification</li>
                    </ul>
                </div>
            </div>
        </body>
    </html>
    """

if __name__ == "__main__":
    # Run the app on port 8080
    logger.info("Starting test server on port 8080")
    app.run(host="0.0.0.0", port=8080, debug=True)