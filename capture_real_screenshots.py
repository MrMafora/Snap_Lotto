"""
Capture real screenshots from the National Lottery website.

This script uses Playwright to:
1. Capture real screenshots from the official lottery websites
2. Update the database with the correct paths
3. Provide a clean API for downloading these screenshots
"""
import os
import sys
import logging
import time
import tempfile
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
SCREENSHOT_DIR = 'screenshots'
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
TIMEOUT = 30000  # 30 seconds timeout

async def capture_screenshot_with_playwright(url, output_path, lottery_type=None):
    """
    Capture a screenshot using Playwright
    
    Args:
        url (str): URL to capture
        output_path (str): Where to save the screenshot
        lottery_type (str, optional): Type of lottery for logging
        
    Returns:
        bool: Success status
    """
    try:
        from playwright.async_api import async_playwright
        
        logger.info(f"Capturing screenshot for {lottery_type} from {url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            page = await context.new_page()
            
            # Set default timeout
            page.set_default_timeout(TIMEOUT)
            
            # Add cookies to bypass any simple protections
            await page.context.add_cookies([
                {
                    'name': 'cookies_accepted', 
                    'value': 'true', 
                    'domain': '.nationallottery.co.za', 
                    'path': '/'
                }
            ])
            
            # Navigate to the URL
            logger.info(f"Navigating to {url}")
            await page.goto(url, wait_until='networkidle')
            
            # Wait for content to be fully loaded
            await page.wait_for_load_state('networkidle')
            
            # Wait a bit more for any dynamic content
            await page.wait_for_timeout(2000)
            
            # Take the screenshot
            logger.info(f"Taking screenshot of {url}")
            await page.screenshot(path=output_path, full_page=True)
            
            # Close browser
            await browser.close()
            
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                logger.info(f"Screenshot captured successfully: {output_path}")
                return True
            else:
                logger.error(f"Screenshot file is missing or too small: {output_path}")
                return False
            
    except Exception as e:
        logger.error(f"Error capturing screenshot with Playwright: {str(e)}")
        return False

def sync_wrapper_for_capture(url, output_path, lottery_type=None):
    """
    Synchronous wrapper for the async Playwright function
    
    Args:
        url (str): URL to capture
        output_path (str): Where to save the screenshot
        lottery_type (str, optional): Type of lottery for logging
        
    Returns:
        bool: Success status
    """
    import asyncio
    
    try:
        # Run the async function in the event loop
        return asyncio.run(capture_screenshot_with_playwright(url, output_path, lottery_type))
    except Exception as e:
        logger.error(f"Error in sync wrapper: {str(e)}")
        return False

def capture_screenshot_by_id(screenshot_id):
    """
    Capture a single screenshot by its ID
    
    Args:
        screenshot_id (int): ID of the screenshot to capture
        
    Returns:
        dict: Result of the operation
    """
    try:
        from main import app
        from models import Screenshot, db
        
        with app.app_context():
            # Get the screenshot
            screenshot = Screenshot.query.get(screenshot_id)
            
            if not screenshot:
                logger.error(f"Screenshot with ID {screenshot_id} not found")
                return {'status': 'error', 'message': f'Screenshot with ID {screenshot_id} not found'}
            
            # Skip if URL is missing
            if not screenshot.url:
                logger.warning(f"Screenshot {screenshot.id} has no URL")
                return {'status': 'error', 'message': f'Screenshot has no URL'}
            
            # Generate output path
            timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            clean_lottery_type = screenshot.lottery_type.replace(' ', '_').lower()
            filename = f"{timestamp_str}_{clean_lottery_type}.png"
            output_path = os.path.join(SCREENSHOT_DIR, filename)
            
            # Capture the screenshot
            success = sync_wrapper_for_capture(
                screenshot.url,
                output_path,
                screenshot.lottery_type
            )
            
            if success:
                # Update the database record
                screenshot.path = output_path
                screenshot.timestamp = datetime.now()
                db.session.commit()
                
                logger.info(f"Successfully captured screenshot for {screenshot.lottery_type}")
                return {'status': 'success', 'path': output_path, 'lottery_type': screenshot.lottery_type}
            else:
                logger.error(f"Failed to capture screenshot for {screenshot.lottery_type}")
                return {'status': 'error', 'message': f'Failed to capture screenshot for {screenshot.lottery_type}'}
    
    except Exception as e:
        logger.error(f"Error capturing screenshot by ID {screenshot_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'status': 'error', 'message': str(e)}

def capture_screenshots_from_database():
    """
    Capture screenshots for all URLs in the database
    
    Returns:
        dict: Results of the operation
    """
    try:
        from main import app
        from models import Screenshot, db
        
        results = {
            'total': 0,
            'success': 0,
            'failed': 0
        }
        
        with app.app_context():
            # Get all screenshots
            screenshots = Screenshot.query.all()
            results['total'] = len(screenshots)
            
            for screenshot in screenshots:
                # Skip if URL is missing
                if not screenshot.url:
                    logger.warning(f"Screenshot {screenshot.id} has no URL")
                    results['failed'] += 1
                    continue
                
                # Generate output path
                timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                clean_lottery_type = screenshot.lottery_type.replace(' ', '_').lower()
                filename = f"{timestamp_str}_{clean_lottery_type}.png"
                output_path = os.path.join(SCREENSHOT_DIR, filename)
                
                # Capture the screenshot
                success = sync_wrapper_for_capture(
                    screenshot.url,
                    output_path,
                    screenshot.lottery_type
                )
                
                if success:
                    # Update the database record
                    screenshot.path = output_path
                    screenshot.timestamp = datetime.now()
                    db.session.commit()
                    
                    results['success'] += 1
                    logger.info(f"Updated screenshot for {screenshot.lottery_type}")
                else:
                    results['failed'] += 1
                    logger.error(f"Failed to capture screenshot for {screenshot.lottery_type}")
        
        return results
    
    except Exception as e:
        logger.error(f"Error in capture_screenshots_from_database: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'total': 0,
            'success': 0,
            'failed': 0,
            'error': str(e)
        }

def add_download_route_to_app():
    """
    Add a route to the Flask app for screenshot downloads
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from main import app
        from flask import send_file, flash, redirect, url_for
        from flask_login import login_required
        from models import Screenshot
        
        @app.route('/download-screenshot/<int:screenshot_id>')
        @login_required
        def download_screenshot(screenshot_id):
            """
            Download a screenshot as an attachment
            
            Args:
                screenshot_id (int): ID of the screenshot
                
            Returns:
                Response: File download response
            """
            try:
                # Get the screenshot
                screenshot = Screenshot.query.get_or_404(screenshot_id)
                
                # Create a proper filename for the download
                filename = f"{screenshot.lottery_type.replace(' ', '_')}_{screenshot.timestamp.strftime('%Y%m%d')}.png"
                
                # Check if file exists and has content
                if screenshot.path and os.path.exists(screenshot.path) and os.path.getsize(screenshot.path) > 0:
                    # Get directory and basename
                    directory = os.path.dirname(screenshot.path)
                    basename = os.path.basename(screenshot.path)
                    
                    # Use send_from_directory for reliable delivery
                    return app.send_from_directory(
                        directory, 
                        basename,
                        as_attachment=True,
                        download_name=filename,
                        mimetype='image/png'
                    )
                else:
                    # If file is missing, redirect to the capture route
                    flash(f"Screenshot file not found. Please capture screenshots first.", "warning")
                    return redirect(url_for('export_screenshots'))
                    
            except Exception as e:
                logger.error(f"Error downloading screenshot {screenshot_id}: {str(e)}")
                flash(f"Error downloading screenshot: {str(e)}", "danger")
                return redirect(url_for('export_screenshots'))
        
        logger.info("Screenshot download route added successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error adding download route: {str(e)}")
        return False

def add_capture_route_to_app():
    """
    Add a route to the Flask app for capturing screenshots
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from main import app
        from flask import flash, redirect, url_for
        from flask_login import login_required, current_user
        
        @app.route('/capture-real-screenshots', methods=['GET', 'POST'])
        @login_required
        def capture_real_screenshots_route():
            """Route to capture real screenshots"""
            # Admin check
            if not current_user.is_admin:
                flash('You must be an admin to access this feature.', 'danger')
                return redirect(url_for('index'))
                
            # Capture screenshots
            results = capture_screenshots_from_database()
            
            # Flash message with results
            if 'error' in results:
                flash(f"Error capturing screenshots: {results['error']}", "danger")
            else:
                flash(f"Captured {results['success']} of {results['total']} screenshots. {results['failed']} failed.", 
                     "success" if results['failed'] == 0 else "warning")
            
            # Redirect back to export screenshots page
            return redirect(url_for('export_screenshots'))
        
        logger.info("Screenshot capture route added successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error adding capture route: {str(e)}")
        return False

def update_download_links():
    """
    Update download links in the template
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        template_path = 'templates/export_screenshots.html'
        
        # Read the template file
        with open(template_path, 'r') as f:
            content = f.read()
        
        # Replace the download link
        alt_pattern = "url_for('view_screenshot'"
        if alt_pattern in content:
            updated_content = content.replace(alt_pattern, "url_for('download_screenshot'")
            
            # Write the updated content back to the file
            with open(template_path, 'w') as f:
                f.write(updated_content)
                
            logger.info("Download links updated in template")
            return True
        else:
            logger.error("No suitable download link pattern found in template")
            return False
            
    except Exception as e:
        logger.error(f"Error updating download links: {str(e)}")
        return False

def add_capture_button_to_template():
    """
    Add a capture button to the export_screenshots.html template
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        template_path = 'templates/export_screenshots.html'
        
        # Read the template file
        with open(template_path, 'r') as f:
            content = f.read()
        
        # Find the right location to insert our button
        button_pattern = '<form action="{{ url_for(\'sync_all_screenshots\') }}" method="POST">'
        capture_button = """<form action="{{ url_for('capture_real_screenshots_route') }}" method="POST" class="mt-2">
                                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                                        <button type="submit" class="btn btn-sm btn-success">
                                            <i class="fas fa-camera me-1"></i> Capture Fresh Screenshots
                                        </button>
                                    </form>"""
        
        if button_pattern in content:
            # Insert our button after the existing one
            updated_content = content.replace(
                button_pattern, 
                button_pattern + '\n                                    </form>\n                                    ' + capture_button
            )
            
            # Write the updated content back to the file
            with open(template_path, 'w') as f:
                f.write(updated_content)
                
            logger.info("Capture button added to template")
            return True
        else:
            logger.error("Could not find location to add capture button")
            return False
            
    except Exception as e:
        logger.error(f"Error adding capture button: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        logger.info("Setting up real screenshot capture system...")
        
        # First, ensure we have required packages
        try:
            import playwright
            logger.info("Playwright is already installed")
        except ImportError:
            logger.info("Installing Playwright...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
            subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
            logger.info("Playwright installed successfully")
        
        # Add the download route
        download_success = add_download_route_to_app()
        logger.info(f"Added download route: {download_success}")
        
        # Add the capture route
        capture_success = add_capture_route_to_app()
        logger.info(f"Added capture route: {capture_success}")
        
        # Update the download links
        links_success = update_download_links()
        logger.info(f"Updated download links: {links_success}")
        
        # Add capture button to template
        button_success = add_capture_button_to_template()
        logger.info(f"Added capture button: {button_success}")
        
        # Capture screenshots now
        logger.info("Capturing screenshots...")
        results = capture_screenshots_from_database()
        
        if 'error' in results:
            logger.error(f"Error during initial capture: {results['error']}")
            print(f"Error during initial capture: {results['error']}")
        else:
            logger.info(f"Initial capture results: {results['success']} successful, {results['failed']} failed")
            print(f"Initial capture results: {results['success']} successful, {results['failed']} failed")
        
        print("Real screenshot capture system set up successfully")
        
    except Exception as e:
        logger.error(f"Unhandled error: {str(e)}")
        print(f"Error: {str(e)}")
        sys.exit(1)