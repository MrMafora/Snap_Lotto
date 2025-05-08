"""
Verify the paths in the Screenshot database table and check for file existence
"""
import os
import sys
import logging
import tempfile
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_screenshot_paths():
    """
    Check if the files referenced in the Screenshot table exist on disk
    
    Returns:
        dict: Results of the check
    """
    from models import Screenshot, db
    from config import Config
    
    results = {
        'total': 0,
        'missing': 0,
        'existing': 0,
        'html_content': 0,
        'details': []
    }
    
    # Get all screenshots
    screenshots = Screenshot.query.all()
    results['total'] = len(screenshots)
    
    logger.info(f"Found {len(screenshots)} screenshots in database")
    logger.info(f"Config SCREENSHOT_DIR: {Config.SCREENSHOT_DIR}")
    
    for screenshot in screenshots:
        result = {
            'id': screenshot.id,
            'lottery_type': screenshot.lottery_type,
            'path': screenshot.path,
            'exists': False,
            'is_html': False,
            'can_recreate': False
        }
        
        # Check if path is set
        if not screenshot.path:
            logger.warning(f"Screenshot {screenshot.id} has no path set")
            result['status'] = 'no_path'
            results['missing'] += 1
            results['details'].append(result)
            continue
            
        # Check if file exists
        if os.path.exists(screenshot.path):
            logger.info(f"Screenshot file exists: {screenshot.path}")
            result['exists'] = True
            results['existing'] += 1
            
            # Check if file is HTML
            try:
                with open(screenshot.path, 'rb') as f:
                    header = f.read(50)
                    is_html = b'<!DOCTYPE html>' in header or b'<html' in header
                    
                result['is_html'] = is_html
                if is_html:
                    logger.info(f"Screenshot {screenshot.id} contains HTML content")
                    results['html_content'] += 1
            except Exception as e:
                logger.error(f"Error checking file content: {str(e)}")
        else:
            logger.warning(f"Screenshot file not found: {screenshot.path}")
            result['status'] = 'file_not_found'
            results['missing'] += 1
            
            # Check if we can recreate it
            if screenshot.url:
                result['can_recreate'] = True
                logger.info(f"Can recreate screenshot from URL: {screenshot.url}")
            
        results['details'].append(result)
    
    # Check the screenshots directory
    try:
        if os.path.exists(Config.SCREENSHOT_DIR):
            logger.info(f"SCREENSHOT_DIR exists at {Config.SCREENSHOT_DIR}")
            
            # List files in the directory
            files = os.listdir(Config.SCREENSHOT_DIR)
            logger.info(f"Found {len(files)} files in SCREENSHOT_DIR")
            
            # Check for HTML files
            html_files = [f for f in files if f.endswith('.html')]
            logger.info(f"Found {len(html_files)} HTML files in SCREENSHOT_DIR")
            
            # Check for PNG files
            png_files = [f for f in files if f.endswith('.png')]
            logger.info(f"Found {len(png_files)} PNG files in SCREENSHOT_DIR")
        else:
            logger.warning(f"SCREENSHOT_DIR does not exist: {Config.SCREENSHOT_DIR}")
    except Exception as e:
        logger.error(f"Error checking SCREENSHOT_DIR: {str(e)}")
    
    return results

def fix_missing_paths():
    """
    Fix missing screenshot paths by creating the directory if needed
    
    Returns:
        bool: True if successful, False otherwise
    """
    from config import Config
    
    try:
        # Ensure the screenshot directory exists
        if not os.path.exists(Config.SCREENSHOT_DIR):
            logger.info(f"Creating SCREENSHOT_DIR: {Config.SCREENSHOT_DIR}")
            os.makedirs(Config.SCREENSHOT_DIR, exist_ok=True)
            return True
        else:
            logger.info(f"SCREENSHOT_DIR already exists: {Config.SCREENSHOT_DIR}")
            return True
    except Exception as e:
        logger.error(f"Error creating SCREENSHOT_DIR: {str(e)}")
        return False

def regenerate_screenshots():
    """
    Regenerate missing screenshots using selenium_screenshot_manager
    
    Returns:
        dict: Results of the regeneration
    """
    from models import Screenshot, db
    from selenium_screenshot_manager import SeleniumScreenshotManager
    import concurrent.futures
    from concurrent.futures import ThreadPoolExecutor
    
    results = {
        'total': 0,
        'success': 0,
        'failed': 0,
        'details': []
    }
    
    # Get screenshots where the file doesn't exist but URL is available
    screenshots = Screenshot.query.all()
    
    # Filter screenshots to regenerate
    to_regenerate = []
    for screenshot in screenshots:
        if screenshot.url and (not screenshot.path or not os.path.exists(screenshot.path)):
            to_regenerate.append(screenshot)
    
    results['total'] = len(to_regenerate)
    logger.info(f"Found {len(to_regenerate)} screenshots to regenerate")
    
    if not to_regenerate:
        return results
    
    # Create screenshot manager
    manager = SeleniumScreenshotManager()
    
    # Function to regenerate one screenshot
    def regenerate_one(screenshot):
        try:
            logger.info(f"Regenerating screenshot for {screenshot.lottery_type} from {screenshot.url}")
            
            url = screenshot.url
            lottery_type = screenshot.lottery_type
            
            # Capture the screenshot
            result = manager.capture_screenshot(
                url=url,
                lottery_type=lottery_type,
                save_to_db=True,
                screenshot_id=screenshot.id
            )
            
            if result and result.get('success'):
                logger.info(f"Successfully regenerated screenshot: {result.get('path')}")
                return {
                    'id': screenshot.id,
                    'lottery_type': lottery_type,
                    'url': url,
                    'path': result.get('path'),
                    'status': 'success'
                }
            else:
                logger.error(f"Failed to regenerate screenshot: {result.get('error')}")
                return {
                    'id': screenshot.id,
                    'lottery_type': lottery_type,
                    'url': url,
                    'status': 'error',
                    'message': result.get('error')
                }
        except Exception as e:
            logger.error(f"Error regenerating screenshot {screenshot.id}: {str(e)}")
            return {
                'id': screenshot.id,
                'lottery_type': screenshot.lottery_type,
                'url': screenshot.url,
                'status': 'error',
                'message': str(e)
            }
    
    # Use ThreadPoolExecutor to regenerate screenshots in parallel
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_screenshot = {
            executor.submit(regenerate_one, screenshot): screenshot
            for screenshot in to_regenerate
        }
        
        for future in concurrent.futures.as_completed(future_to_screenshot):
            screenshot = future_to_screenshot[future]
            
            try:
                result = future.result()
                
                if result['status'] == 'success':
                    results['success'] += 1
                else:
                    results['failed'] += 1
                    
                results['details'].append(result)
            except Exception as e:
                logger.error(f"Error getting result for screenshot {screenshot.id}: {str(e)}")
                results['failed'] += 1
                results['details'].append({
                    'id': screenshot.id,
                    'lottery_type': screenshot.lottery_type,
                    'url': screenshot.url,
                    'status': 'error',
                    'message': str(e)
                })
    
    # Close the manager
    manager.close()
    
    # Commit database changes
    try:
        db.session.commit()
        logger.info("Database changes committed")
    except Exception as e:
        logger.error(f"Error committing database changes: {str(e)}")
        db.session.rollback()
        
    return results

def register_route():
    """
    Register a route to verify and fix screenshot paths
    
    Returns:
        bool: True if successful, False otherwise
    """
    from main import app
    from flask import jsonify, flash, redirect, url_for, session
    from flask_login import login_required, current_user
    
    @app.route('/verify-screenshot-paths', methods=['GET'])
    @login_required
    def verify_screenshot_paths():
        """Verify screenshot paths and display results"""
        if not current_user.is_admin:
            flash('You must be an admin to verify screenshot paths.', 'danger')
            return redirect(url_for('index'))
            
        try:
            results = check_screenshot_paths()
            return jsonify(results)
        except Exception as e:
            logger.error(f"Error in verify_screenshot_paths: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/regenerate-missing-screenshots', methods=['POST'])
    @login_required
    def regenerate_missing_screenshots():
        """Regenerate missing screenshots"""
        if not current_user.is_admin:
            flash('You must be an admin to regenerate screenshots.', 'danger')
            return redirect(url_for('index'))
            
        try:
            # Make sure screenshot directory exists
            fix_missing_paths()
            
            # Regenerate screenshots
            results = regenerate_screenshots()
            
            message = (f"Regenerated {results['success']} of {results['total']} screenshots. "
                      f"{results['failed']} failed.")
            
            # Store success message in session
            session['sync_status'] = {
                'status': 'success' if results['failed'] == 0 else 'warning',
                'message': message
            }
            
            flash(message, 'success' if results['failed'] == 0 else 'warning')
        except Exception as e:
            logger.error(f"Error in regenerate_missing_screenshots: {str(e)}")
            import traceback
            traceback.print_exc()
            
            flash(f'Error regenerating screenshots: {str(e)}', 'danger')
            
            # Store error message in session
            session['sync_status'] = {
                'status': 'danger',
                'message': f'Error regenerating screenshots: {str(e)}'
            }
        
        return redirect(url_for('export_screenshots'))
        
    logger.info("Routes registered successfully")
    return True

if __name__ == "__main__":
    # Run with Flask app context
    from main import app
    
    # Register the route
    try:
        register_route()
    except Exception as e:
        logger.error(f"Error registering route: {str(e)}")
    
    # Run the check
    with app.app_context():
        logger.info("Starting screenshot path verification...")
        
        # Make sure screenshot directory exists
        fix_missing_paths()
        
        # Check screenshot paths
        results = check_screenshot_paths()
        
        logger.info(f"Total screenshots: {results['total']}")
        logger.info(f"Existing files: {results['existing']}")
        logger.info(f"Missing files: {results['missing']}")
        logger.info(f"HTML content: {results['html_content']}")
        
        print(f"Total screenshots: {results['total']}")
        print(f"Existing files: {results['existing']}")
        print(f"Missing files: {results['missing']}")
        print(f"HTML content: {results['html_content']}")
        
        # If there are missing files, offer to regenerate them
        if results['missing'] > 0:
            logger.info("There are missing screenshot files")
            print("\nThere are missing screenshot files.")
            print("You can regenerate them by accessing /regenerate-missing-screenshots")
        
    print("Screenshot path verification completed")