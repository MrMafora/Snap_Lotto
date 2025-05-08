"""
Create manual screenshots from HTML content.

This script:
1. Takes each screenshot file in the database
2. Checks if it contains HTML instead of a proper image
3. Creates a proper PNG screenshot using a reliable method
4. Updates the database records
"""
import os
import sys
import logging
import tempfile
import subprocess
import shutil
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_file_is_html(filepath):
    """
    Check if a file contains HTML content
    
    Args:
        filepath (str): Path to the file
        
    Returns:
        bool: True if the file contains HTML, False otherwise
    """
    if not os.path.exists(filepath):
        return False
        
    try:
        with open(filepath, 'rb') as f:
            header = f.read(50)
            
        # Check for HTML content
        return b'<!DOCTYPE html>' in header or b'<html' in header
    except Exception as e:
        logger.error(f"Error checking if file is HTML: {str(e)}")
        return False

def create_html_file(content, output_path=None):
    """
    Create an HTML file from content
    
    Args:
        content (str): HTML content
        output_path (str, optional): Path to save the HTML file
        
    Returns:
        str: Path to the HTML file
    """
    if not output_path:
        fd, output_path = tempfile.mkstemp(suffix='.html')
        os.close(fd)
        
    try:
        with open(output_path, 'w') as f:
            f.write(content)
        return output_path
    except Exception as e:
        logger.error(f"Error creating HTML file: {str(e)}")
        return None

def convert_html_to_png(html_path, output_path=None):
    """
    Convert HTML file to PNG using wkhtmltoimage
    
    Args:
        html_path (str): Path to HTML file
        output_path (str, optional): Path to save the PNG file
        
    Returns:
        str: Path to the PNG file or None if failed
    """
    if not output_path:
        fd, output_path = tempfile.mkstemp(suffix='.png')
        os.close(fd)
        
    # Define command with options for better rendering
    cmd = [
        'wkhtmltoimage',
        '--quality', '100',
        '--width', '1200',
        '--height', '1500',
        '--javascript-delay', '2000',  # Wait for JS to execute
        '--no-stop-slow-scripts',      # Don't stop slow running JS
        '--enable-javascript',         # Make sure JS is enabled
        '--disable-smart-width',       # Use specified width
        '--zoom', '1.2',               # Slightly larger rendering
        html_path,
        output_path
    ]
    
    try:
        # Run the command
        logger.info(f"Converting {html_path} to {output_path}")
        subprocess.run(cmd, check=True, capture_output=True, timeout=30)
        
        # Check if output file exists and has content
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            logger.info(f"Successfully converted to PNG: {output_path}")
            return output_path
        else:
            logger.error(f"PNG file is empty or doesn't exist: {output_path}")
            return None
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running wkhtmltoimage: {e.stderr.decode('utf-8')}")
        return None
    except Exception as e:
        logger.error(f"Error converting HTML to PNG: {str(e)}")
        return None

def fix_all_screenshots():
    """
    Fix all screenshot files that contain HTML
    
    Returns:
        dict: Results of the fix
    """
    from models import Screenshot, db
    
    results = {
        'total': 0,
        'html_files': 0,
        'fixed': 0,
        'errors': 0,
        'details': []
    }
    
    # Get all screenshots
    screenshots = Screenshot.query.all()
    results['total'] = len(screenshots)
    
    for screenshot in screenshots:
        if not screenshot.path or not os.path.exists(screenshot.path):
            logger.warning(f"Screenshot file not found: {screenshot.id}")
            results['errors'] += 1
            continue
            
        # Get source URL and type
        url = screenshot.url
        lottery_type = screenshot.lottery_type
        
        # Check if it's HTML
        is_html = check_file_is_html(screenshot.path)
        
        if is_html:
            logger.info(f"Found HTML content in {screenshot.path}")
            results['html_files'] += 1
            
            try:
                # Create a backup of the original file
                backup_path = f"{screenshot.path}.bak"
                shutil.copy2(screenshot.path, backup_path)
                
                # Read the HTML content
                with open(screenshot.path, 'r') as f:
                    html_content = f.read()
                
                # Save to a temporary HTML file
                temp_html_path = create_html_file(html_content)
                
                if temp_html_path:
                    # Try to convert to PNG
                    png_path = convert_html_to_png(temp_html_path)
                    
                    if png_path:
                        # Get the file extension
                        _, ext = os.path.splitext(screenshot.path)
                        
                        # If the original file has a PNG extension, replace it
                        if ext.lower() == '.png':
                            # Copy the new PNG to the original path
                            shutil.copy2(png_path, screenshot.path)
                            logger.info(f"Replaced HTML with PNG at same path: {screenshot.path}")
                        else:
                            # Create a new PNG file
                            new_path = os.path.splitext(screenshot.path)[0] + '.png'
                            shutil.copy2(png_path, new_path)
                            
                            # Update the database record
                            screenshot.path = new_path
                            logger.info(f"Updated screenshot path to: {new_path}")
                        
                        results['fixed'] += 1
                        results['details'].append({
                            'id': screenshot.id,
                            'lottery_type': lottery_type,
                            'old_path': screenshot.path,
                            'new_path': screenshot.path if ext.lower() == '.png' else new_path,
                            'status': 'success'
                        })
                        
                        # Clean up temporary files
                        if os.path.exists(temp_html_path):
                            os.unlink(temp_html_path)
                        if os.path.exists(png_path):
                            os.unlink(png_path)
                    else:
                        logger.error(f"Failed to convert HTML to PNG for {screenshot.path}")
                        results['errors'] += 1
                        results['details'].append({
                            'id': screenshot.id,
                            'lottery_type': lottery_type,
                            'path': screenshot.path,
                            'status': 'error',
                            'message': 'Failed to convert HTML to PNG'
                        })
                else:
                    logger.error(f"Failed to create temporary HTML file for {screenshot.path}")
                    results['errors'] += 1
            except Exception as e:
                logger.error(f"Error processing HTML screenshot {screenshot.path}: {str(e)}")
                results['errors'] += 1
                results['details'].append({
                    'id': screenshot.id,
                    'lottery_type': lottery_type,
                    'path': screenshot.path,
                    'status': 'error',
                    'message': str(e)
                })
    
    # Commit database changes
    try:
        db.session.commit()
        logger.info("Database changes committed")
    except Exception as e:
        logger.error(f"Error committing database changes: {str(e)}")
        db.session.rollback()
        results['errors'] += 1
        
    return results

def add_route_to_app():
    """
    Add a route to the Flask app to run the fix
    
    Returns:
        bool: True if successful, False otherwise
    """
    from main import app
    
    @app.route('/fix-html-screenshots', methods=['POST'])
    def fix_html_screenshots():
        """Fix HTML screenshots by converting them to PNG"""
        from flask import flash, redirect, url_for, session
        from flask_login import current_user
        
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You must be an admin to fix screenshots.', 'danger')
            return redirect(url_for('index'))
            
        try:
            results = fix_all_screenshots()
            
            message = (f"Fixed {results['fixed']} of {results['html_files']} HTML screenshots. "
                       f"{results['errors']} errors occurred.")
            
            # Store success message in session
            session['sync_status'] = {
                'status': 'success' if results['errors'] == 0 else 'warning',
                'message': message
            }
        except Exception as e:
            logger.error(f"Error in fix_html_screenshots: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Store error message in session
            session['sync_status'] = {
                'status': 'danger',
                'message': f'Error fixing HTML screenshots: {str(e)}'
            }
        
        return redirect(url_for('export_screenshots'))
        
    return True

if __name__ == "__main__":
    # Check if wkhtmltoimage is installed
    try:
        subprocess.run(['which', 'wkhtmltoimage'], check=True, capture_output=True)
        logger.info("wkhtmltoimage is installed")
    except subprocess.CalledProcessError:
        logger.error("wkhtmltoimage is not installed")
        print("Error: wkhtmltoimage is not installed")
        print("Please install it with: apt-get install wkhtmltopdf")
        sys.exit(1)
    
    # Run with Flask app context
    from main import app
    
    # Register the route
    add_route_to_app()
    
    # Run the fix
    with app.app_context():
        logger.info("Starting screenshot fix...")
        results = fix_all_screenshots()
        
        logger.info(f"Total screenshots: {results['total']}")
        logger.info(f"HTML files found: {results['html_files']}")
        logger.info(f"Fixed: {results['fixed']}")
        logger.info(f"Errors: {results['errors']}")
        
        print(f"Total screenshots: {results['total']}")
        print(f"HTML files found: {results['html_files']}")
        print(f"Fixed: {results['fixed']}")
        print(f"Errors: {results['errors']}")
        
    print("Screenshot fix completed")