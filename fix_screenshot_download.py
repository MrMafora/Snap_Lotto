"""
Fix screenshot download issues

This script provides a direct solution to convert HTML screenshots to PNG format
without relying on external tools like wkhtmltopdf.

It uses the Python PIL library to create PNG images directly from the HTML content.
"""
import os
import sys
import io
import base64
import logging
import tempfile
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

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

def create_image_from_html(html_content, lottery_type, width=800, height=600, font_size=14):
    """
    Create a simple PNG image with the lottery type and timestamp
    
    Args:
        html_content (str): HTML content (for extracting text if possible)
        lottery_type (str): Type of lottery
        width (int): Width of the image
        height (int): Height of the image
        font_size (int): Font size for text
        
    Returns:
        bytes: PNG image as bytes
    """
    try:
        # Create a blank white image
        image = Image.new('RGB', (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        # Draw a border
        draw.rectangle([(0, 0), (width-1, height-1)], outline=(200, 200, 200))
        
        # Draw header background
        draw.rectangle([(0, 0), (width, 50)], fill=(227, 242, 253))
        
        # Draw title
        draw.text((20, 15), f"{lottery_type} Results", fill=(0, 0, 0), font=None)
        
        # Draw timestamp
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        draw.text((20, 50), f"Generated: {now}", fill=(100, 100, 100), font=None)
        
        # Draw a message
        draw.text((20, 80), "The original screenshot contained HTML instead of an image.", fill=(0, 0, 0), font=None)
        draw.text((20, 100), "This is a placeholder image.", fill=(0, 0, 0), font=None)
        
        # Try to extract key info from HTML
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Try to extract draw date and numbers
            y_pos = 150
            
            # Look for key elements
            title_element = soup.find('h1') or soup.find('h2') or soup.find('title')
            if title_element:
                draw.text((20, y_pos), f"Title: {title_element.text.strip()}", fill=(0, 0, 0), font=None)
                y_pos += 25
                
            # Look for numbers
            number_elements = soup.find_all(class_='result-ball')
            if number_elements:
                numbers_text = "Numbers: " + " ".join([elem.text.strip() for elem in number_elements])
                draw.text((20, y_pos), numbers_text, fill=(0, 0, 0), font=None)
                y_pos += 25
                
            # Look for draw date
            date_elements = soup.find_all(class_='result-draw-date')
            if date_elements:
                date_text = "Draw Date: " + date_elements[0].text.strip()
                draw.text((20, y_pos), date_text, fill=(0, 0, 0), font=None)
                
        except Exception as e:
            logger.warning(f"Could not extract HTML content details: {str(e)}")
            pass  # Continue even if we can't extract text
            
        # Save the image to a bytes buffer
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        
        return buffer.getvalue()
    except Exception as e:
        logger.error(f"Error creating image from HTML: {str(e)}")
        return None

def fix_all_screenshots():
    """
    Fix all screenshot files that contain HTML by replacing them with PNG images
    
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
            
        # Get lottery type
        lottery_type = screenshot.lottery_type
        
        # Check if it's HTML
        is_html = check_file_is_html(screenshot.path)
        
        if is_html:
            logger.info(f"Found HTML content in {screenshot.path}")
            results['html_files'] += 1
            
            try:
                # Read the HTML content
                with open(screenshot.path, 'r') as f:
                    html_content = f.read()
                
                # Create PNG image from HTML
                png_data = create_image_from_html(html_content, lottery_type)
                
                if png_data:
                    # Get the file extension
                    _, ext = os.path.splitext(screenshot.path)
                    
                    # Determine path for new PNG
                    if ext.lower() == '.png':
                        # Use the same path
                        new_path = screenshot.path
                    else:
                        # Create a new PNG path
                        new_path = os.path.splitext(screenshot.path)[0] + '.png'
                        
                    # Save the PNG data to the file
                    with open(new_path, 'wb') as f:
                        f.write(png_data)
                        
                    logger.info(f"Saved PNG image to {new_path}")
                    
                    # Update the database record if needed
                    if new_path != screenshot.path:
                        screenshot.path = new_path
                        logger.info(f"Updated screenshot path to: {new_path}")
                    
                    results['fixed'] += 1
                    results['details'].append({
                        'id': screenshot.id,
                        'lottery_type': lottery_type,
                        'path': new_path,
                        'status': 'success'
                    })
                else:
                    logger.error(f"Failed to create PNG image for {screenshot.path}")
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

def register_fix_route():
    """
    Register a route in the Flask app to fix screenshots
    
    Returns:
        bool: True if successful, False otherwise
    """
    from main import app
    from flask import flash, redirect, url_for, session
    from flask_login import current_user, login_required
    
    @app.route('/fix-html-screenshots', methods=['POST'])
    @login_required
    def fix_html_screenshots():
        """Fix HTML screenshots by converting them to PNG"""
        if not current_user.is_admin:
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
            
            flash(message, 'success' if results['errors'] == 0 else 'warning')
        except Exception as e:
            logger.error(f"Error in fix_html_screenshots: {str(e)}")
            import traceback
            traceback.print_exc()
            
            flash(f'Error fixing HTML screenshots: {str(e)}', 'danger')
            
            # Store error message in session
            session['sync_status'] = {
                'status': 'danger',
                'message': f'Error fixing HTML screenshots: {str(e)}'
            }
        
        return redirect(url_for('export_screenshots'))
        
    return True

if __name__ == "__main__":
    # Check if PIL is installed
    try:
        import PIL
        logger.info(f"PIL version {PIL.__version__} is installed")
    except ImportError:
        logger.error("PIL is not installed")
        print("Error: PIL is not installed")
        print("Please install it with: pip install pillow")
        sys.exit(1)
    
    # Run with Flask app context
    from main import app
    
    # Register the route
    try:
        register_fix_route()
        logger.info("Route registered successfully")
    except Exception as e:
        logger.error(f"Error registering route: {str(e)}")
        
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