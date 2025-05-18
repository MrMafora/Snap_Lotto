from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app
import os
import time
from werkzeug.utils import secure_filename
from models import LotteryResult, db

# Create a blueprint for the simplified scanner
simple_scanner = Blueprint('simple_scanner', __name__)

@simple_scanner.route('/simple-scanner')
def scanner_page():
    """Render the simple scanner page without any complex functionality"""
    return render_template('simple_ticket_scanner.html',
                          title="South African Lottery Ticket Scanner | Simple Version",
                          meta_description="Check if your South African lottery ticket is a winner. Our free ticket scanner uses advanced technology to analyze and verify your lottery tickets instantly.")

@simple_scanner.route('/simple-scan', methods=['POST'])
def scan_ticket():
    """Process the ticket scan without relying on complex JavaScript"""
    lottery_type = request.form.get('lottery_type', '')
    draw_number = request.form.get('draw_number', '')
    
    # Check if a file was uploaded
    if 'ticket_image' not in request.files:
        return render_template('simple_ticket_scanner.html', 
                              error="No file selected. Please upload an image file.")
    
    file = request.files['ticket_image']
    
    # Check if the file is empty
    if file.filename == '':
        return render_template('simple_ticket_scanner.html', 
                              error="No file selected. Please upload an image file.")
    
    # Process valid image file
    if file and file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
        # Generate a secure filename and save the file
        filename = secure_filename(file.filename)
        timestamp = int(time.time())
        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{timestamp}_{filename}")
        file.save(save_path)
        
        # For this simple version, we'll just return a placeholder result
        # In a full implementation, this would use OCR to extract numbers
        
        # Get some sample lottery results to display
        lottery_results = None
        if lottery_type:
            lottery_results = LotteryResult.query.filter_by(lottery_type=lottery_type).order_by(LotteryResult.draw_date.desc()).first()
        else:
            # If no lottery type specified, get the most recent result of any type
            lottery_results = LotteryResult.query.order_by(LotteryResult.draw_date.desc()).first()
        
        return render_template('scan_results.html', 
                              image_path=save_path.replace(os.getcwd(), ''),
                              lottery_type=lottery_type or "Auto-detected",
                              draw_number=draw_number or "Latest",
                              lottery_results=lottery_results)
    
    # Invalid file type
    return render_template('simple_ticket_scanner.html', 
                          error="Invalid file type. Please upload a JPG, PNG, or GIF image.")