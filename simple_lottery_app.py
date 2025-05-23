"""
Simple lottery data platform application that runs directly on port 8080.
This is a clean implementation to fix the white screen issue.
"""
import os
from flask import Flask, render_template_string

# Create the application
app = Flask(__name__)

@app.route('/')
def home():
    """Homepage with basic lottery platform information"""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Lottery Data Platform</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 0;
                background-color: #f4f6f9;
                color: #333;
            }
            .container {
                max-width: 1000px;
                margin: 0 auto;
                padding: 20px;
            }
            header {
                background-color: #2c3e50;
                color: white;
                padding: 1rem;
                text-align: center;
            }
            .content {
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                padding: 20px;
                margin-top: 20px;
            }
            h1, h2, h3 {
                color: #2c3e50;
            }
            .success-message {
                background-color: #d4edda;
                color: #155724;
                padding: 15px;
                border-radius: 4px;
                margin-bottom: 20px;
                border-left: 5px solid #28a745;
            }
        </style>
    </head>
    <body>
        <header>
            <h1>Lottery Data Platform</h1>
            <p>Your comprehensive source for lottery results and analysis</p>
        </header>
        
        <div class="container">
            <div class="success-message">
                <strong>Success!</strong> The application is now running properly.
            </div>
            
            <div class="content">
                <h2>Welcome to the Lottery Data Platform</h2>
                <p>This platform provides comprehensive lottery data intelligence through:</p>
                <ul>
                    <li>Automated screenshot collection and processing</li>
                    <li>Intelligent data analysis of lottery results</li>
                    <li>Advanced monitoring capabilities</li>
                    <li>Sophisticated draw verification tools</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """)

# Run the application
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)