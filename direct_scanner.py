"""
Simple Direct Lottery Ticket Scanner

This module provides a simplified ticket scanning route that works reliably
with direct file uploads without requiring complex JavaScript.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
import os
import time
from werkzeug.utils import secure_filename
from models import db, LotteryResult

direct_scanner = Blueprint('direct_scanner', __name__)

@direct_scanner.route('/direct-scanner')
def scanner_page():
    """Render the simplified direct scanner page"""
    return render_template('direct_ticket_scanner.html',
                          title="South African Lottery Ticket Scanner | Direct Scanner",
                          meta_description="Check if your South African lottery ticket is a winner with our reliable scanner.")

@direct_scanner.route('/process-ticket', methods=['POST'])
def process_ticket():
    """Process the uploaded ticket image and display results"""
    # Get form data
    lottery_type = request.form.get('lottery_type', '')
    draw_number = request.form.get('draw_number', '')
    
    # Check if a file was uploaded
    if 'ticket_image' not in request.files:
        return render_template('direct_ticket_scanner.html', 
                              error="No file selected. Please upload an image file.")
    
    file = request.files['ticket_image']
    
    # Check if the file is empty
    if file.filename == '':
        return render_template('direct_ticket_scanner.html', 
                              error="No file selected. Please upload an image file.")
    
    # Check if the file is a valid image
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    file_ext = os.path.splitext(file.filename)[1].lower() if file.filename else ''
    
    if file and file_ext in valid_extensions:
        # Create a secure filename and save the file
        filename = secure_filename(file.filename)
        timestamp = int(time.time())
        upload_folder = os.path.join(os.getcwd(), 'uploads')
        
        # Ensure upload directory exists
        os.makedirs(upload_folder, exist_ok=True)
        
        # Save the file
        save_path = os.path.join(upload_folder, f"{timestamp}_{filename}")
        file.save(save_path)
        
        # Get lottery result for display
        lottery_results = None
        if lottery_type:
            lottery_results = LotteryResult.query.filter_by(lottery_type=lottery_type).order_by(LotteryResult.draw_date.desc()).first()
        else:
            # If no lottery type specified, get the most recent result of any type
            lottery_results = LotteryResult.query.order_by(LotteryResult.draw_date.desc()).first()
        
        # Render results template
        return render_template('scan_results.html', 
                              image_path=save_path.replace(os.getcwd(), ''),
                              lottery_type=lottery_type or "Auto-detected",
                              draw_number=draw_number or "Latest",
                              lottery_results=lottery_results)
    
    # Invalid file type
    return render_template('direct_ticket_scanner.html', 
                          error="Invalid file type. Please upload a JPG, PNG, or GIF image.")