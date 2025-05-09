"""
Simple standalone file upload test script
This is used to diagnose issues with the file upload functionality
"""
import os
import io
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = 'upload-test-secret-key'

# Set upload folder
UPLOAD_FOLDER = 'upload_test_files'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Routes
@app.route('/')
def index():
    """Redirect to upload test page"""
    return redirect(url_for('upload_test'))

@app.route('/upload-test', methods=['GET', 'POST'])
def upload_test():
    """Simple isolated test for file uploads"""
    if request.method == 'POST':
        # Log all request details
        logger.info(f"Upload test request received: {request.method}")
        logger.info(f"Request content type: {request.content_type}")
        logger.info(f"Request files keys: {list(request.files.keys()) if request.files else 'No files'}")
        logger.info(f"Request form keys: {list(request.form.keys()) if request.form else 'No form data'}")
        
        # Check if file is included in the request
        if 'test_image' not in request.files:
            logger.error("No test_image in request.files")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    "status": "error",
                    "message": "No file uploaded",
                    "details": {
                        "files": list(request.files.keys()) if request.files else 'No files',
                        "form": list(request.form.keys()) if request.form else 'No form data'
                    }
                }), 400
            else:
                flash("No file selected", "danger")
                return redirect(url_for('upload_test'))
        
        file = request.files['test_image']
        logger.info(f"Received file: {file.filename}, Content type: {file.content_type}")
        
        # If user does not select file, browser also submits an empty part without filename
        if file.filename == '':
            logger.error("Empty filename submitted")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    "status": "error",
                    "message": "No file selected"
                }), 400
            else:
                flash("No file selected", "danger")
                return redirect(url_for('upload_test'))
        
        # Get the test type
        test_type = request.form.get('test_type', 'basic')
        
        try:
            # Read the file data
            image_data = file.read()
            file_size = len(image_data)
            logger.info(f"Read file data successfully, file size: {file_size} bytes")
            
            if file_size == 0:
                logger.error("File data is empty")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        "status": "error",
                        "message": "Empty file uploaded"
                    }), 400
                else:
                    flash("Empty file uploaded", "danger")
                    return redirect(url_for('upload_test'))
            
            # Save the file for verification if not using AJAX
            if test_type == 'basic':
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                with open(filepath, 'wb') as f:
                    f.write(image_data)
                logger.info(f"File saved to {filepath}")
            
            # Process successful upload
            result = {
                "status": "success",
                "message": "File uploaded successfully",
                "details": {
                    "filename": file.filename,
                    "content_type": file.content_type,
                    "file_size": file_size,
                    "test_type": test_type
                }
            }
            
            # Return JSON for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(result)
            
            # For normal form submissions, render the template with success message
            flash(f"File '{file.filename}' uploaded successfully ({file_size} bytes)", "success")
            return render_template('simple_upload_test.html', result=result)
                
        except Exception as e:
            logger.exception(f"Error processing upload: {str(e)}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    "status": "error",
                    "message": f"Error processing upload: {str(e)}"
                }), 500
            else:
                flash(f"Error processing upload: {str(e)}", "danger")
                return redirect(url_for('upload_test'))
    
    # GET request - show the upload form
    return render_template('simple_upload_test.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7000, debug=True)