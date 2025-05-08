"""
Comprehensive fix for screenshot rendering issues.

This module provides tools to:
1. Identify HTML files saved with .png extension
2. Convert HTML files to valid PNG images
3. Update filesystem paths and database records
"""
import os
import logging
import tempfile
import subprocess
import mimetypes
import glob
from datetime import datetime

# Flask imports for app context
try:
    from flask import current_app
    from models import db, Screenshot
except ImportError:
    current_app = None

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/fix_screenshot_rendering.log'
)
logger = logging.getLogger('fix_screenshot_rendering')

def check_file_type(filepath):
    """
    Check the actual content type of a file by examining its content
    
    Args:
        filepath (str): Path to the file
        
    Returns:
        str: Detected MIME type
    """
    if not os.path.exists(filepath):
        logger.warning(f"File not found: {filepath}")
        return "unknown"
        
    try:
        # Read the first few bytes to detect file type
        with open(filepath, 'rb') as f:
            header = f.read(50)
            
        # Check for PNG signature
        if header.startswith(b'\x89PNG\r\n\x1a\n'):
            logger.debug(f"PNG signature detected in {filepath}")
            return "image/png"
            
        # Check for JPEG signature
        if header.startswith(b'\xff\xd8'):
            logger.debug(f"JPEG signature detected in {filepath}")
            return "image/jpeg"
            
        # Check for HTML content
        if b'<!DOCTYPE html>' in header or b'<html' in header:
            logger.debug(f"HTML content detected in {filepath}")
            return "text/html"
            
        # Check for plain text
        try:
            text_content = header.decode('utf-8')
            if all(ord(c) < 128 for c in text_content):
                logger.debug(f"Plain text content detected in {filepath}")
                return "text/plain"
        except UnicodeDecodeError:
            pass
            
        # Default to application/octet-stream for binary data
        return "application/octet-stream"
    except Exception as e:
        logger.error(f"Error checking file type for {filepath}: {str(e)}")
        return "unknown"

def convert_html_to_png(html_path, output_path=None):
    """
    Convert HTML content to PNG using wkhtmltoimage
    
    Args:
        html_path (str): Path to HTML file
        output_path (str, optional): Path for output PNG file
        
    Returns:
        str: Path to the generated PNG file or None if failed
    """
    try:
        # Create output path if not provided
        if not output_path:
            output_path = html_path.rsplit('.', 1)[0] + '.png'
            
        # Check if wkhtmltoimage is available
        try:
            subprocess.run(['which', 'wkhtmltoimage'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            logger.error("wkhtmltoimage not found on system")
            return None
            
        # Run conversion with wkhtmltoimage
        logger.info(f"Converting {html_path} to PNG using wkhtmltoimage")
        result = subprocess.run(
            [
                'wkhtmltoimage',
                '--quality', '100',
                '--width', '1200',
                '--height', '1500',
                '--javascript-delay', '2000',  # Wait for JavaScript execution
                '--no-stop-slow-scripts',      # Don't stop slow running JavaScript
                '--quiet',                      # Reduce output
                html_path,
                output_path
            ],
            check=True,
            capture_output=True,
            timeout=30  # Set a reasonable timeout
        )
        
        # Verify the output file exists and has content
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            logger.info(f"Successfully converted {html_path} to {output_path}")
            return output_path
        else:
            logger.error(f"Conversion failed or produced empty file: {output_path}")
            return None
            
    except subprocess.CalledProcessError as e:
        logger.error(f"wkhtmltoimage error: {e.stderr.decode('utf-8')}")
        return None
    except subprocess.TimeoutExpired as e:
        logger.error(f"wkhtmltoimage timeout: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error converting HTML to PNG: {str(e)}")
        return None

def fix_all_screenshots():
    """
    Comprehensive fix for all screenshot rendering issues
    
    Returns:
        dict: Results of the fix operation
    """
    results = {
        'success': False,
        'total': 0,
        'fixed': 0,
        'errors': 0,
        'details': []
    }
    
    try:
        # Get all screenshots from database
        screenshots = Screenshot.query.all()
        results['total'] = len(screenshots)
        
        for screenshot in screenshots:
            if not screenshot.path or not os.path.exists(screenshot.path):
                results['details'].append({
                    'lottery_type': screenshot.lottery_type,
                    'status': 'error',
                    'message': 'Screenshot file not found'
                })
                results['errors'] += 1
                continue
                
            # Check the actual file type
            file_type = check_file_type(screenshot.path)
            _, ext = os.path.splitext(screenshot.path)
            
            # Fix files with wrong extension
            if file_type == 'text/html' and ext.lower() == '.png':
                logger.info(f"Found HTML content with .png extension: {screenshot.path}")
                
                # Generate temporary filenames
                temp_html_path = None
                temp_png_path = None
                
                try:
                    # Create temporary HTML file
                    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp_html:
                        temp_html_path = temp_html.name
                        
                        # Read HTML content from original file
                        with open(screenshot.path, 'r') as f:
                            html_content = f.read()
                            
                        # Write HTML content to temporary file
                        temp_html.write(html_content.encode('utf-8'))
                        
                    # Create temporary PNG file name
                    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_png:
                        temp_png_path = temp_png.name
                    
                    # Convert HTML to PNG
                    png_path = convert_html_to_png(temp_html_path, temp_png_path)
                    
                    if png_path and os.path.exists(png_path):
                        # Replace original file with the converted PNG
                        os.replace(png_path, screenshot.path)
                        logger.info(f"Replaced HTML content with PNG image: {screenshot.path}")
                        
                        results['details'].append({
                            'lottery_type': screenshot.lottery_type,
                            'status': 'success',
                            'message': 'Converted HTML to PNG'
                        })
                        results['fixed'] += 1
                    else:
                        # Fallback: Rename HTML file with .png extension to .txt
                        new_path = screenshot.path.rsplit('.', 1)[0] + '.txt'
                        os.rename(screenshot.path, new_path)
                        screenshot.path = new_path
                        logger.info(f"Renamed HTML file with .png extension to .txt: {new_path}")
                        
                        results['details'].append({
                            'lottery_type': screenshot.lottery_type,
                            'status': 'partial',
                            'message': 'Renamed HTML file with .png extension to .txt'
                        })
                        results['fixed'] += 1
                        
                finally:
                    # Clean up temporary files
                    for path in [temp_html_path, temp_png_path]:
                        if path and os.path.exists(path):
                            try:
                                os.unlink(path)
                            except:
                                pass
            
            elif file_type == 'text/html' and ext.lower() == '.txt':
                # Fix HTML files with .txt extension by converting to PNG
                logger.info(f"Found HTML content with .txt extension: {screenshot.path}")
                
                # Generate PNG path
                png_path = screenshot.path.rsplit('.', 1)[0] + '.png'
                
                # Convert HTML to PNG
                converted_path = convert_html_to_png(screenshot.path, png_path)
                
                if converted_path and os.path.exists(converted_path):
                    # Update database record to point to new PNG file
                    screenshot.path = converted_path
                    logger.info(f"Converted HTML file to PNG: {converted_path}")
                    
                    results['details'].append({
                        'lottery_type': screenshot.lottery_type,
                        'status': 'success',
                        'message': 'Converted HTML file with .txt extension to PNG'
                    })
                    results['fixed'] += 1
                else:
                    results['details'].append({
                        'lottery_type': screenshot.lottery_type,
                        'status': 'error',
                        'message': 'Failed to convert HTML file to PNG'
                    })
                    results['errors'] += 1
            
            elif file_type == 'image/png' and ext.lower() != '.png':
                # Fix PNG files with wrong extension
                logger.info(f"Found PNG content with wrong extension: {screenshot.path}")
                
                # Generate correct path
                new_path = screenshot.path.rsplit('.', 1)[0] + '.png'
                
                # Rename file
                os.rename(screenshot.path, new_path)
                screenshot.path = new_path
                logger.info(f"Renamed PNG file to have .png extension: {new_path}")
                
                results['details'].append({
                    'lottery_type': screenshot.lottery_type,
                    'status': 'success',
                    'message': 'Renamed PNG file to have .png extension'
                })
                results['fixed'] += 1
                
        # Commit changes to database
        db.session.commit()
        
        # Update success status
        results['success'] = True
        
    except Exception as e:
        logger.error(f"Error fixing screenshots: {str(e)}")
        results['error'] = str(e)
        db.session.rollback()
        
    return results

if __name__ == "__main__":
    from main import app
    
    # Run the fix with app context
    with app.app_context():
        logger.info("Starting screenshot rendering fix...")
        results = fix_all_screenshots()
        
        # Log results
        logger.info(f"Fixed {results['fixed']} of {results['total']} screenshots")
        logger.info(f"Errors: {results['errors']}")