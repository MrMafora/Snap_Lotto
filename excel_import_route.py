"""
Flask route handlers for Excel import functionality.
This module provides routes that can be registered with a Flask application
to enable Excel import functionality through the web interface.
"""
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple
from werkzeug.utils import secure_filename

from flask import Blueprint, request, redirect, url_for, flash, render_template, jsonify
from flask_login import login_required, current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a Blueprint for Excel import routes
excel_import_bp = Blueprint('excel_import', __name__)

def register_excel_import_routes(app, db):
    """
    Register Excel import routes with the Flask application.
    
    Args:
        app: Flask application
        db: SQLAlchemy database object
    """
    # Register the blueprint
    app.register_blueprint(excel_import_bp)
    
    # Store app and db objects for access in route handlers
    excel_import_bp.app = app
    excel_import_bp.db = db
    
    logger.info("Excel import routes registered")

@excel_import_bp.route('/import-excel', methods=['GET', 'POST'])
@login_required
def import_excel():
    """
    Route handler for importing Excel files.
    GET: Display the upload form
    POST: Process the uploaded file
    """
    # Make sure the user is an admin
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
        flash('You must be an admin to import data.', 'danger')
        return redirect(url_for('index'))
    
    app = excel_import_bp.app
    
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'excel_file' not in request.files:
            flash('No file selected.', 'danger')
            return redirect(request.url)
            
        file = request.files['excel_file']
        
        # Check if the file is valid
        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(request.url)
            
        # Get the sheet name if specified
        sheet_name = request.form.get('sheet_name', None)
        if sheet_name and sheet_name.strip() == '':
            sheet_name = None
            
        # Save the file to a temporary location
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_import_{timestamp}_{filename}")
        
        try:
            file.save(temp_filepath)
            logger.info(f"Saved uploaded file to {temp_filepath}")
            
            # Import the data using our improved import function
            from integrate_excel_import import run_import
            
            success_count, error_count, error_messages = run_import(temp_filepath, sheet_name)
            
            # Clean up the temporary file
            try:
                os.remove(temp_filepath)
                logger.info(f"Removed temporary file {temp_filepath}")
            except Exception as e:
                logger.warning(f"Could not remove temporary file {temp_filepath}: {str(e)}")
            
            # Report results
            if error_count > 0:
                flash(f"Import completed with {error_count} errors. {success_count} records imported successfully.", 'warning')
                for msg in error_messages[:5]:  # Show first 5 errors
                    flash(msg, 'danger')
                    
                if len(error_messages) > 5:
                    flash(f"... and {len(error_messages) - 5} more errors. See log for details.", 'danger')
            else:
                flash(f"Import completed successfully! {success_count} records imported.", 'success')
                
            # Redirect to the import history page
            return redirect(url_for('import_history'))
            
        except Exception as e:
            logger.error(f"Error during Excel import: {str(e)}")
            flash(f"Error during import: {str(e)}", 'danger')
            return redirect(request.url)
    
    # GET request - display the upload form
    return render_template(
        'import_excel.html',
        title='Import Excel Data',
        active_page='import_excel'
    )

@excel_import_bp.route('/api/excel-sheets', methods=['POST'])
@login_required
def list_excel_sheets():
    """
    API endpoint to list the sheets in an Excel file.
    
    Expected POST data:
    - excel_file: The Excel file to process
    
    Returns:
    - JSON with sheet names
    """
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
        
    if 'excel_file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
        
    file = request.files['excel_file']
    
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
        
    app = excel_import_bp.app
    
    # Save the file to a temporary location
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_sheets_{timestamp}_{filename}")
    
    try:
        file.save(temp_filepath)
        logger.info(f"Saved uploaded file to {temp_filepath}")
        
        # Read the sheets
        import pandas as pd
        excel_file = pd.ExcelFile(temp_filepath)
        sheets = excel_file.sheet_names
        
        # Clean up the temporary file
        try:
            os.remove(temp_filepath)
        except Exception as e:
            logger.warning(f"Could not remove temporary file {temp_filepath}: {str(e)}")
            
        return jsonify({'sheets': sheets})
        
    except Exception as e:
        logger.error(f"Error reading Excel sheets: {str(e)}")
        return jsonify({'error': f"Error reading Excel file: {str(e)}"}), 500

@excel_import_bp.route('/api/excel-preview', methods=['POST'])
@login_required
def preview_excel():
    """
    API endpoint to preview the contents of an Excel file.
    
    Expected POST data:
    - excel_file: The Excel file to process
    - sheet_name: (Optional) The name of the sheet to preview
    
    Returns:
    - JSON with preview data
    """
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
        
    if 'excel_file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
        
    file = request.files['excel_file']
    
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400
        
    sheet_name = request.form.get('sheet_name', None)
    if sheet_name and sheet_name.strip() == '':
        sheet_name = None
        
    app = excel_import_bp.app
    
    # Save the file to a temporary location
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_preview_{timestamp}_{filename}")
    
    try:
        file.save(temp_filepath)
        logger.info(f"Saved uploaded file to {temp_filepath}")
        
        # Import the improved Excel functions
        from improved_excel_import import extract_lottery_data
        
        try:
            # Extract data
            df, column_mapping = extract_lottery_data(temp_filepath, sheet_name)
            
            # Prepare preview data (first 10 rows)
            preview_data = []
            for _, row in df.head(10).iterrows():
                row_data = {}
                for col in df.columns:
                    row_data[str(col)] = str(row[col]) if pd.notna(row[col]) else ''
                preview_data.append(row_data)
                
            response = {
                'success': True,
                'preview': preview_data,
                'columns': list(df.columns),
                'column_mapping': column_mapping,
                'total_rows': len(df)
            }
        except Exception as e:
            logger.error(f"Error extracting data: {str(e)}")
            response = {
                'success': False,
                'error': f"Error extracting data: {str(e)}"
            }
            
        # Clean up the temporary file
        try:
            os.remove(temp_filepath)
        except Exception as e:
            logger.warning(f"Could not remove temporary file {temp_filepath}: {str(e)}")
            
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error previewing Excel file: {str(e)}")
        return jsonify({'error': f"Error previewing Excel file: {str(e)}"}), 500