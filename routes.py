"""
Routes for the Snap Lotto application
"""
from flask import render_template, jsonify

def register_routes(app):
    """Register all application routes"""
    
    @app.route('/')
    def index():
        return render_template('deployment_test.html')
    
    @app.route('/health')
    def health():
        return jsonify({"status": "ok"})
        
    # Additional routes can be registered here
    # but we'll keep it simple for deployment