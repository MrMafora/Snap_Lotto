#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
import os
import logging
import json
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create the Flask application
app = Flask(__name__)

# Configure the app
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'lottery-scraper-default-secret')
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    """Home page showing lottery results and ticket scanning feature"""
    try:
        # In this simplified version, we don't fetch results from the database
        return render_template('index_simple.html')
    except Exception as e:
        logger.error(f"Error loading index page: {str(e)}")
        return "Lottery Scraper App is running!"

@app.route('/ticket-scanner')
def ticket_scanner():
    """Ticket scanning page"""
    try:
        return render_template('ticket_scanner_simple.html')
    except Exception as e:
        logger.error(f"Error loading ticket scanner page: {str(e)}")
        return "Ticket Scanner - Coming Soon"

@app.route('/scan-ticket', methods=['POST'])
def scan_ticket():
    """Process a ticket scanning request"""
    if 'ticket_image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    
    file = request.files['ticket_image']
    
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
    
    if file:
        # Save the file temporarily
        filename = f"ticket_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Get form data
        lottery_type = request.form.get('lottery_type', '')
        draw_number = request.form.get('draw_number', '')
        
        # For this simplified version, we'll just return mock results
        # In the full version, we would process the ticket with OCR
        mock_result = {
            'status': 'success',
            'ticket': {
                'lottery_type': lottery_type or 'Lotto',
                'draw_number': draw_number or '2425',
                'draw_date': '2025-04-09',
                'numbers': [5, 12, 23, 33, 38, 42]
            },
            'winning': {
                'numbers': [5, 11, 23, 31, 35, 42],
                'bonus': [17]
            },
            'matches': {
                'count': 3,
                'matched_numbers': [5, 23, 42]
            },
            'prize': None
        }
        
        # Clean up the uploaded file
        try:
            os.remove(filepath)
        except:
            pass
            
        return jsonify(mock_result)

@app.route('/results')
def results():
    """Results page"""
    try:
        return render_template('results_simple.html')
    except Exception as e:
        logger.error(f"Error loading results page: {str(e)}")
        return "Lottery Results - Coming Soon"

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    return jsonify({
        'status': 'running',
        'message': 'The Lottery Scraper API is running.'
    })

@app.route('/api/visualization-data')
def visualization_data():
    """API endpoint for visualization data"""
    data_type = request.args.get('data_type', '')
    
    if data_type == 'numbers_frequency':
        # Mock data for the visualization
        return jsonify({
            'labels': list(range(1, 50)),
            'datasets': [{
                'data': [5, 8, 12, 7, 9, 15, 11, 6, 10, 8, 9, 7, 13, 10, 6, 8, 9, 7, 6, 5, 
                         7, 11, 8, 9, 10, 7, 8, 5, 6, 9, 10, 11, 7, 8, 9, 6, 5, 7, 8, 13,
                         9, 7, 6, 5, 8, 9, 10, 8, 7]
            }]
        })
    elif data_type == 'winners_by_division':
        # Mock data for the visualization
        return jsonify({
            'labels': ['Division 1', 'Division 2', 'Division 3', 'Division 4', 'Division 5'],
            'datasets': [{
                'data': [2, 15, 124, 587, 1923]
            }]
        })
    else:
        return jsonify({
            'error': 'Invalid data type requested'
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)