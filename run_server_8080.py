"""
Simple direct server on port 8080 for the Snap Lotto application.
"""

from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def index():
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Snap Lotto Ticket Scanner</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
                color: #333;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1, h2 {
                color: #2c3e50;
            }
            .section {
                margin-bottom: 30px;
                padding: 15px;
                background-color: #f9f9f9;
                border-radius: 5px;
            }
            .success {
                color: #27ae60;
                font-weight: bold;
            }
            .feature-list {
                padding-left: 20px;
            }
            .feature-list li {
                margin-bottom: 10px;
            }
            .upload-container {
                border: 2px dashed #ccc;
                padding: 20px;
                text-align: center;
                margin: 20px 0;
                border-radius: 5px;
            }
            .btn {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
            }
            .btn:hover {
                background-color: #2980b9;
            }
            .lottery-numbers {
                display: flex;
                flex-wrap: wrap;
                margin-top: 15px;
            }
            .ball {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background-color: #e74c3c;
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-right: 10px;
                margin-bottom: 10px;
                font-weight: bold;
            }
            .powerball {
                background-color: #f39c12;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Snap Lotto Ticket Scanner</h1>
            <p class="success">Server is running correctly on port 8080!</p>
            
            <div class="section">
                <h2>Ticket Scanner Feature</h2>
                <p>Easily scan your lottery tickets to check if you've won!</p>
                <ul class="feature-list">
                    <li><strong>OCR Technology:</strong> Using Google Gemini for advanced image recognition</li>
                    <li><strong>Auto-fetch:</strong> Missing draw information is retrieved through OpenAI</li>
                    <li><strong>Quick Results:</strong> Instant verification against our database</li>
                    <li><strong>Self-improving:</strong> System gets smarter with each scan</li>
                </ul>
                
                <div class="upload-container">
                    <p>Upload your lottery ticket image here</p>
                    <button class="btn">Select Image</button>
                    <p><small>(Feature simulation - upload not active)</small></p>
                </div>
            </div>
            
            <div class="section">
                <h2>Latest Lottery Results</h2>
                <p><strong>Lottery Draw #2541</strong> - Date: 2025-05-14</p>
                <div class="lottery-numbers">
                    <div class="ball">09</div>
                    <div class="ball">18</div>
                    <div class="ball">19</div>
                    <div class="ball">30</div>
                    <div class="ball">31</div>
                    <div class="ball">40</div>
                    <div class="ball powerball">28</div>
                </div>
                
                <p><strong>Powerball Draw #1615</strong> - Date: 2025-05-14</p>
                <div class="lottery-numbers">
                    <div class="ball">14</div>
                    <div class="ball">17</div>
                    <div class="ball">18</div>
                    <div class="ball">33</div>
                    <div class="ball">37</div>
                    <div class="ball powerball">06</div>
                </div>
                
                <p><strong>Daily Lottery #2255</strong> - Date: 2025-05-14</p>
                <div class="lottery-numbers">
                    <div class="ball">03</div>
                    <div class="ball">04</div>
                    <div class="ball">15</div>
                    <div class="ball">20</div>
                    <div class="ball">36</div>
                </div>
            </div>
            
            <div class="section">
                <h2>Database Information</h2>
                <p>Our database contains normalized lottery data:</p>
                <ul class="feature-list">
                    <li>Numbers stored with leading zeros (e.g., "09" instead of "9")</li>
                    <li>Standardized lottery type names</li>
                    <li>Consistent data format for better analysis</li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    """)

if __name__ == "__main__":
    print("Starting server on port 8080...")
    app.run(host="0.0.0.0", port=8080, debug=False)