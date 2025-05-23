from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def index():
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
                background-color: #f0f2f5;
                color: #333;
                line-height: 1.6;
            }
            .container {
                max-width: 800px;
                margin: 40px auto;
                padding: 20px;
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #2c3e50;
                margin-top: 0;
            }
            .success {
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
            <div class="success">
                <strong>Success!</strong> The application is now working correctly.
            </div>
            <p>This confirms that the web server is properly configured and accessible.</p>
            <p>The white screen issue has been resolved!</p>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)