"""
Simple Flask application that runs directly on port 8080 for Replit compatibility.
"""
from flask import Flask, redirect, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    """Redirect to the main application on port 5000"""
    host = request.host.replace(':8080', ':5000') if ':8080' in request.host else request.host
    return redirect(f'https://{host}/')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "port": 8080})

@app.route('/<path:path>')
def catch_all(path):
    """Redirect all paths to the main application"""
    host = request.host.replace(':8080', ':5000') if ':8080' in request.host else request.host
    return redirect(f'https://{host}/{path}')

if __name__ == '__main__':
    print("Starting Flask application on port 8080...")
    app.run(host='0.0.0.0', port=8080)