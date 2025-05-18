"""
Simple Flask application to demonstrate the lottery ticket scanner functionality.
This version focuses only on the core scanner features without the complexity.
"""

import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create the Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "lottery-scanner-demo-secret")

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if a file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """Homepage with scanner access"""
    return render_template('simple_scanner.html')

@app.route('/scan-ticket', methods=['GET', 'POST'])
def scan_ticket():
    """Handle ticket scanning"""
    # Check API keys availability
    gemini_available = bool(os.environ.get('GEMINI_API_KEY'))
    openai_available = bool(os.environ.get('OPENAI_API_KEY'))
    
    # For GET requests, show the upload form
    if request.method == 'GET':
        return render_template('simple_scanner.html', 
                              gemini_available=gemini_available,
                              openai_available=openai_available)
    
    # For POST requests, process the uploaded file
    if 'ticket_image' not in request.files:
        flash("No file uploaded", "error")
        return redirect(request.url)
    
    file = request.files['ticket_image']
    
    if file.filename == '':
        flash("No file selected", "error")
        return redirect(request.url)
    
    if not allowed_file(file.filename):
        flash(f"File type not allowed. Please upload one of: {', '.join(ALLOWED_EXTENSIONS)}", "error")
        return redirect(request.url)
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        flash(f"File too large. Maximum file size is {MAX_FILE_SIZE/1024/1024}MB", "error")
        return redirect(request.url)
    
    # Save the file
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{filename}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    # In a real implementation, we would process the ticket with OCR here
    # For this demo, we'll simulate a successful scan
    
    # Simulate ticket data extraction
    ticket_data = {
        "success": True,
        "lottery_type": "Lottery",
        "draw_number": "2541",
        "draw_date": "2025-05-14",
        "ticket_numbers": ["09", "18", "19", "30", "31", "40"],
        "bonus_number": "28"
    }
    
    # Simulate winning data
    winning_data = {
        "success": True,
        "lottery_type": "Lottery",
        "draw_number": "2541",
        "draw_date": "2025-05-14",
        "winning_numbers": ["09", "18", "19", "30", "31", "40"],
        "bonus_number": "28"
    }
    
    # Simulate comparison
    matches = 6  # All numbers match in this example
    result = {
        "success": True,
        "ticket_data": ticket_data,
        "winning_data": winning_data,
        "matches": matches,
        "bonus_matched": True,
        "prize_tier": "Jackpot",
        "estimated_prize": "R10,000,000"
    }
    
    # Store the result in session
    session['scan_result'] = result
    
    # Redirect to results page
    return redirect(url_for('scan_results'))

@app.route('/scan-results')
def scan_results():
    """Display scan results"""
    result = session.get('scan_result')
    
    if not result:
        flash("No scan results available. Please scan a ticket first.", "warning")
        return redirect(url_for('scan_ticket'))
    
    return render_template('simple_results.html', result=result)

@app.route('/api-status')
def api_status():
    """Check API status"""
    gemini_available = bool(os.environ.get('GEMINI_API_KEY'))
    openai_available = bool(os.environ.get('OPENAI_API_KEY'))
    
    status = {
        "gemini_available": gemini_available,
        "openai_available": openai_available
    }
    
    return jsonify(status)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting application on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)