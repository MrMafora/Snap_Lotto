"""
Routes for the lottery ticket scanner functionality.
Handles ticket uploads, processing, and result display.
"""

import os
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, current_app, flash, redirect, url_for, session
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user

# Import our OCR integrations and scanner
from ocr_integrations import get_scanner
from models import db, LotteryResult, APIRequestLog

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Blueprint
scanner_bp = Blueprint('scanner', __name__)

# Constants
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    """Check if a file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@scanner_bp.route('/scan-ticket', methods=['GET', 'POST'])
def scan_ticket():
    """Render ticket scanning page or process uploaded ticket"""
    # GET request - render the upload form
    if request.method == 'GET':
        # Check if we have any API keys configured
        gemini_available = bool(os.environ.get('GEMINI_API_KEY'))
        openai_available = bool(os.environ.get('OPENAI_API_KEY'))
        
        api_available = gemini_available or openai_available
        
        if not api_available:
            flash("Ticket scanning temporarily unavailable. Please check back later.", "warning")
        
        return render_template('scanner/scan_ticket.html', 
                              api_available=api_available,
                              gemini_available=gemini_available,
                              openai_available=openai_available)
    
    # POST request - handle file upload and processing
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
    
    if file and allowed_file(file.filename):
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            flash(f"File too large. Maximum file size is {MAX_FILE_SIZE/1024/1024}MB", "error")
            return redirect(request.url)
        
        # Secure the filename and save the file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{filename}"
        
        # Ensure upload directory exists
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        
        # Save the file
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # Process the ticket image
        try:
            scanner = get_scanner()
            result = scanner.process_ticket(file_path)
            
            if result.get('success'):
                # Store the result in session for display
                session['scan_result'] = result
                return redirect(url_for('scanner.scan_results'))
            else:
                flash(f"Failed to process ticket: {result.get('error', 'Unknown error')}", "error")
                return render_template('scanner/scan_error.html', error=result.get('error'))
                
        except Exception as e:
            logger.error(f"Error processing ticket: {str(e)}")
            flash(f"Error processing ticket: {str(e)}", "error")
            return render_template('scanner/scan_error.html', error=str(e))
    
    # Default fallback - should not reach here
    flash("An unexpected error occurred", "error")
    return redirect(request.url)

@scanner_bp.route('/scan-results')
def scan_results():
    """Display ticket scanning results"""
    # Get results from session
    result = session.get('scan_result')
    
    if not result:
        flash("No scan results available. Please scan a ticket first.", "warning")
        return redirect(url_for('scanner.scan_ticket'))
    
    return render_template('scanner/scan_results.html', result=result)

@scanner_bp.route('/api/scan-ticket', methods=['POST'])
def api_scan_ticket():
    """API endpoint for ticket scanning"""
    # Check if file was uploaded
    if 'ticket_image' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    
    file = request.files['ticket_image']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': f"File type not allowed. Please upload one of: {', '.join(ALLOWED_EXTENSIONS)}"}), 400
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        return jsonify({'success': False, 'error': f"File too large. Maximum file size is {MAX_FILE_SIZE/1024/1024}MB"}), 400
    
    # Secure the filename and save the file
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{filename}"
    
    # Ensure upload directory exists
    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    
    # Save the file
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)
    
    # Process the ticket image
    try:
        scanner = get_scanner()
        result = scanner.process_ticket(file_path)
        
        # If processing failed
        if not result.get('success'):
            return jsonify({
                'success': False, 
                'error': result.get('error', 'Unknown error')
            }), 400
        
        # Return successful result
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error processing ticket: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@scanner_bp.route('/api/scanner-status')
def api_scanner_status():
    """Check if the scanner is available and which OCR providers are configured"""
    gemini_available = bool(os.environ.get('GEMINI_API_KEY'))
    openai_available = bool(os.environ.get('OPENAI_API_KEY'))
    
    scanner_status = {
        'available': gemini_available or openai_available,
        'providers': {
            'gemini': gemini_available,
            'openai': openai_available
        }
    }
    
    return jsonify(scanner_status)

@scanner_bp.route('/admin/api-logs')
@login_required
def api_logs():
    """Admin view for API request logs"""
    if not current_user.is_admin:
        flash("You don't have permission to access this page", "error")
        return redirect(url_for('index'))
    
    # Get logs from database
    logs = APIRequestLog.query.order_by(APIRequestLog.created_at.desc()).limit(100).all()
    
    return render_template('admin/api_logs.html', logs=logs)

def register_scanner_routes(app):
    """Register scanner routes with the app"""
    app.register_blueprint(scanner_bp)
    logger.info("Scanner routes registered")