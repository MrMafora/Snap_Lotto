#!/usr/bin/env python3
from flask import Flask, render_template, jsonify
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the Flask application
app = Flask(__name__)

# Configure the app
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'lottery-scraper-default-secret')

@app.route('/')
def index():
    """Home page"""
    return "Lottery Scraper App is running!"

@app.route('/ticket-scanner')
def ticket_scanner():
    """Ticket scanning page"""
    return "Ticket Scanner Page - Coming Soon"

@app.route('/results')
def results():
    """Results page"""
    return "Lottery Results - Coming Soon"

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    return jsonify({
        'status': 'running',
        'message': 'The Lottery Scraper API is running.'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)