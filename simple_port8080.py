#!/usr/bin/env python3
"""
Simple HTTP server binding to port 8080 for Replit deployment.
"""
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello from port 8080! The server is running."

@app.route('/health')
def health():
    return {"status": "ok", "message": "Port 8080 server is up and running"}, 200

if __name__ == "__main__":
    print("Starting server on port 8080...")
    app.run(host="0.0.0.0", port=8080, debug=True)