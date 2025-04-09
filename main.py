"""
Main application entry point
"""
import os
from flask import Flask, render_template, redirect, url_for, request, jsonify

# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "development-secret-key")

# Create upload directory if it doesn't exist
os.makedirs(os.path.join(os.getcwd(), 'uploads'), exist_ok=True)

# Basic routes for deployment testing
@app.route('/')
def index():
    """Deployment test home page"""
    return render_template('deployment_test.html')

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok"})

@app.route('/about')
def about():
    """About page with app description"""
    return render_template('about.html')

# This section only runs when the file is executed directly, not when imported by gunicorn
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
