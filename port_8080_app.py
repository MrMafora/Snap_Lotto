"""
Minimal Flask application that exclusively binds to port 8080.
This can be run alongside our main application to provide dual-port functionality.
"""
from flask import Flask, redirect, url_for

app = Flask(__name__)

@app.route('/')
def index():
    """Redirect to the main application on port 5000"""
    return """
    <html>
        <head>
            <title>Port 8080 Bridge</title>
            <meta http-equiv="refresh" content="0;url=http://localhost:5000/">
            <style>
                body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
                .container { max-width: 800px; margin: 0 auto; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Port 8080 Bridge is Active</h1>
                <p>This is the port 8080 bridge for the lottery application.</p>
                <p>You are being redirected to the main application...</p>
            </div>
        </body>
    </html>
    """

@app.route('/<path:subpath>')
def proxy(subpath):
    """Proxy all other requests to the main application on port 5000"""
    return redirect(f"http://localhost:5000/{subpath}")

if __name__ == '__main__':
    print("Starting Port 8080 Bridge Application...")
    app.run(host='0.0.0.0', port=8080)