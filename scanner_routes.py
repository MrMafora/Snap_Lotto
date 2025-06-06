"""
Scanner Routes Module for Lottery Ticket Processing
Provides web interface for uploading and processing lottery tickets with Google Gemini 2.5 Pro
"""

import os
import json
import base64
import logging
from datetime import datetime
from flask import render_template, request, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
import google.generativeai as genai
import PIL.Image
import io
import re

logger = logging.getLogger(__name__)

def register_scanner_routes(app):
    """Register scanner routes with the Flask app"""
    
    @app.route('/ticket-scanner')
    def ticket_scanner():
        """Ticket scanner page for uploading lottery tickets"""
        return render_template('scanner/ticket_scanner.html')
    
    @app.route('/admin/scan-ticket')
    def admin_scan_ticket():
        """Admin ticket scanner page"""
        return render_template('admin/scan_ticket.html')
    
    @app.route('/api/scan-ticket', methods=['POST'])
    def api_scan_ticket():
        """API endpoint for processing uploaded ticket images"""
        try:
            if 'ticket_image' not in request.files:
                return jsonify({'error': 'No file uploaded'}), 400
            
            file = request.files['ticket_image']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Save uploaded file
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_filename = f"ticket_{timestamp}_{filename}"
            file_path = os.path.join('uploads', safe_filename)
            
            # Ensure uploads directory exists
            os.makedirs('uploads', exist_ok=True)
            file.save(file_path)
            
            # Process with Google Gemini 2.5 Pro
            genai.configure(api_key=os.environ.get('GOOGLE_API_KEY_SNAP_LOTTERY'))
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            # Load image
            image = PIL.Image.open(file_path)
            
            prompt = """Extract lottery ticket data from this South African lottery ticket. 

CRITICAL INSTRUCTIONS:
1. Find ALL number rows - each row has main numbers
2. Find any bonus/powerball numbers for each row
3. Identify the lottery type (PowerBall, Lotto, Daily Lotto, etc.)
4. Extract draw date and draw number if visible
5. Return exactly this JSON format:

{
    "lottery_type": "PowerBall",
    "all_lines": [
        [9, 15, 37, 39, 50],
        [12, 26, 31, 32, 47]
    ],
    "all_powerball": ["7", "12"],
    "powerball_plus_included": "YES",
    "draw_date": "21/03/25",
    "draw_number": "1599",
    "ticket_cost": "R30.00"
}

Extract ALL visible data accurately."""
            
            response = model.generate_content([image, prompt])
            response_text = response.text
            
            logger.info(f"Gemini response: {response_text}")
            
            # Extract and clean JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group()
                # Fix leading zeros in JSON (05 -> "05")
                json_text = re.sub(r'(\[|\,)\s*0(\d)', r'\1"0\2"', json_text)
                ticket_data = json.loads(json_text)
                
                # Clean up the file
                os.remove(file_path)
                
                return jsonify({
                    'success': True,
                    'data': ticket_data,
                    'message': 'Ticket processed successfully'
                })
            else:
                return jsonify({'error': 'Could not extract ticket data'}), 400
                
        except Exception as e:
            logger.error(f"Error processing ticket: {e}")
            # Clean up file if it exists
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            return jsonify({'error': f'Processing error: {str(e)}'}), 500
    
    logger.info("Scanner routes registered successfully")