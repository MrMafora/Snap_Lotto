"""
Extremely simple Flask application entry point.
This is designed to start quickly and expose port 5000 for Replit's preview feature.
"""
from flask import Flask, redirect

# Create a very minimal Flask application
app = Flask(__name__)

@app.route('/')
def index():
    """Redirect to the main application after Replit detects the port"""
    return redirect('/redirect-to-main-app')

@app.route('/redirect-to-main-app')
def redirect_to_main():
    """This page will redirect to the main app once it's loaded"""
    return """
    <html>
    <head>
        <title>Lottery App Loading...</title>
        <meta http-equiv="refresh" content="1;url=/app">
        <style>
            body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
            .loader { border: 16px solid #f3f3f3; border-top: 16px solid #3498db; border-radius: 50%; width: 120px; height: 120px; animation: spin 2s linear infinite; margin: 0 auto; }
            @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        </style>
    </head>
    <body>
        <h1>Lottery Application Loading...</h1>
        <div class="loader"></div>
        <p>Please wait while we load the full application...</p>
    </body>
    </html>
    """

@app.route('/app')
def main_app():
    """Import and run the main app here"""
    import main
    return main.index()

if __name__ == "__main__":
    print("Starting minimal Flask application on port 5000...")
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)