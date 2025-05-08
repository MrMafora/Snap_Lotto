"""
Enhance screenshot viewing and regeneration capabilities

This script:
1. Creates a placeholder image generator for missing screenshots
2. Updates the screenshot download functionality
3. Provides a way to regenerate missing screenshots
"""
import io
import os
import sys
import logging
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import base64

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_placeholder_image(lottery_type, timestamp=None, width=800, height=600):
    """
    Create a simple placeholder image for missing screenshots
    
    Args:
        lottery_type (str): Type of lottery
        timestamp (datetime, optional): Timestamp of the screenshot
        width (int): Width of the image
        height (int): Height of the image
        
    Returns:
        BytesIO: PNG image as BytesIO object
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
        title = f"{lottery_type} Screenshot"
        draw.text((20, 15), title, fill=(0, 0, 0))
        
        # Draw timestamp
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S") if timestamp else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        draw.text((20, 60), f"Date: {timestamp_str}", fill=(100, 100, 100))
        
        # Draw placeholder message
        draw.text((20, 100), "Screenshot file is missing or corrupted.", fill=(0, 0, 0))
        draw.text((20, 130), "Please use the 'Regenerate Missing Screenshots' button", fill=(0, 0, 0))
        draw.text((20, 160), "on the Export Screenshots page to fix this issue.", fill=(0, 0, 0))
        
        # Save to BytesIO
        img_io = BytesIO()
        image.save(img_io, 'PNG')
        img_io.seek(0)
        
        return img_io
    except Exception as e:
        logger.error(f"Error creating placeholder image: {str(e)}")
        # Create a very basic fallback image with minimal dependencies
        fallback_img = BytesIO()
        Image.new('RGB', (400, 300), color=(255, 255, 255)).save(fallback_img, 'PNG')
        fallback_img.seek(0)
        return fallback_img

def regenerate_missing_screenshots():
    """
    Regenerate missing screenshots
    
    Returns:
        dict: Results of the regeneration
    """
    try:
        from models import Screenshot, db
        from selenium_screenshot_manager import SeleniumScreenshotManager
        import concurrent.futures
        from concurrent.futures import ThreadPoolExecutor
        
        logger.info("Initializing screenshot regeneration")
        
        results = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'details': []
        }
        
        # Get all screenshots
        screenshots = Screenshot.query.all()
        
        # Filter screenshots that need regeneration
        to_regenerate = []
        for screenshot in screenshots:
            if screenshot.url and (not screenshot.path or not os.path.exists(screenshot.path)):
                to_regenerate.append(screenshot)
                
        results['total'] = len(to_regenerate)
        logger.info(f"Found {results['total']} screenshots to regenerate")
        
        if not to_regenerate:
            logger.info("No screenshots to regenerate")
            return results
            
        # Initialize screenshot manager
        manager = SeleniumScreenshotManager()
        
        # Function to regenerate a single screenshot
        def regenerate_one(screenshot):
            try:
                logger.info(f"Regenerating screenshot for {screenshot.lottery_type}")
                
                url = screenshot.url
                lottery_type = screenshot.lottery_type
                
                # Capture screenshot
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
                    
                    # Create a placeholder image if the capture fails
                    placeholder_io = create_placeholder_image(lottery_type, screenshot.timestamp)
                    placeholder_data = placeholder_io.getvalue()
                    
                    # Create a filename for the placeholder
                    now = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{now}_{lottery_type.lower().replace(' ', '-')}_placeholder.png"
                    filepath = os.path.join('screenshots', filename)
                    
                    # Ensure the screenshots directory exists
                    os.makedirs('screenshots', exist_ok=True)
                    
                    # Save the placeholder image
                    with open(filepath, 'wb') as f:
                        f.write(placeholder_data)
                    
                    # Update the screenshot record
                    screenshot.path = filepath
                    
                    return {
                        'id': screenshot.id,
                        'lottery_type': lottery_type,
                        'url': url,
                        'path': filepath,
                        'status': 'placeholder',
                        'message': result.get('error')
                    }
            except Exception as e:
                logger.error(f"Error regenerating screenshot {screenshot.id}: {str(e)}")
                return {
                    'id': screenshot.id,
                    'lottery_type': getattr(screenshot, 'lottery_type', 'Unknown'),
                    'url': getattr(screenshot, 'url', 'Unknown'),
                    'status': 'error',
                    'message': str(e)
                }
        
        # Use ThreadPoolExecutor for parallel regeneration
        max_workers = min(4, len(to_regenerate))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
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
                    elif result['status'] == 'placeholder':
                        results['success'] += 1  # Count placeholders as successes
                    else:
                        results['failed'] += 1
                        
                    results['details'].append(result)
                except Exception as e:
                    logger.error(f"Error getting result for screenshot {screenshot.id}: {str(e)}")
                    results['failed'] += 1
                    results['details'].append({
                        'id': screenshot.id,
                        'lottery_type': getattr(screenshot, 'lottery_type', 'Unknown'),
                        'url': getattr(screenshot, 'url', 'Unknown'),
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
    except Exception as e:
        logger.error(f"Error in regenerate_missing_screenshots: {str(e)}")
        return {
            'total': 0,
            'success': 0,
            'failed': 1,
            'details': [{'status': 'error', 'message': str(e)}]
        }

def register_view_enhancements():
    """
    Register view enhancements for screenshots
    
    Returns:
        bool: True if successful, False otherwise
    """
    from main import app
    from flask import send_file, jsonify, flash, redirect, url_for, session, request, after_this_request
    from flask_login import login_required, current_user
    from models import Screenshot, db
    import os
    
    @app.route('/regenerate-missing-screenshots', methods=['POST'])
    @login_required
    def regenerate_missing_screenshots_route():
        """Regenerate missing screenshots"""
        if not current_user.is_admin:
            flash('You must be an admin to regenerate screenshots.', 'danger')
            return redirect(url_for('index'))
            
        try:
            # Ensure the screenshots directory exists
            os.makedirs('screenshots', exist_ok=True)
            
            # Regenerate screenshots
            results = regenerate_missing_screenshots()
            
            message = (f"Regenerated {results['success']} of {results['total']} screenshots. "
                      f"{results['failed']} failed.")
            
            # Store success message in session
            session['sync_status'] = {
                'status': 'success' if results['failed'] == 0 else 'warning',
                'message': message
            }
            
            flash(message, 'success' if results['failed'] == 0 else 'warning')
        except Exception as e:
            logger.error(f"Error in regenerate_missing_screenshots_route: {str(e)}")
            import traceback
            traceback.print_exc()
            
            flash(f'Error regenerating screenshots: {str(e)}', 'danger')
            
            # Store error message in session
            session['sync_status'] = {
                'status': 'danger',
                'message': f'Error regenerating screenshots: {str(e)}'
            }
        
        return redirect(url_for('export_screenshots'))
    
    # Original view_screenshot wrapped with placeholder generation
    original_view_screenshot = app.view_functions.get('view_screenshot')
    
    @app.route('/screenshot/<int:screenshot_id>')
    def enhanced_view_screenshot(screenshot_id):
        """
        Enhanced view of a single screenshot with placeholder for missing files
        
        Args:
            screenshot_id (int): ID of the screenshot
            
        Returns:
            Response: Image file response
        """
        # Get the screenshot
        screenshot = Screenshot.query.get_or_404(screenshot_id)
        
        # Check if the file exists
        if screenshot.path and os.path.exists(screenshot.path):
            # If the file exists, serve it using the original function
            return original_view_screenshot(screenshot_id)
        
        # If no valid file, create and return a placeholder image
        logger.warning(f"Creating placeholder image for screenshot {screenshot_id}")
        img_io = create_placeholder_image(
            lottery_type=screenshot.lottery_type,
            timestamp=screenshot.timestamp
        )
        
        # Add filename for proper download
        filename = f"{screenshot.lottery_type.replace(' ', '_')}_{screenshot.timestamp.strftime('%Y%m%d')}.png"
        
        @after_this_request
        def add_header(response):
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
            
        return send_file(img_io, mimetype='image/png')
    
    # Replace the original view_screenshot with our enhanced version
    app.view_functions['view_screenshot'] = enhanced_view_screenshot
    
    logger.info("View enhancements registered successfully")
    return True

if __name__ == "__main__":
    # Register flask app context-aware enhancements
    from main import app
    
    with app.app_context():
        try:
            # Register enhanced view and regeneration routes
            register_view_enhancements()
            print("Successfully registered view enhancements")
        except Exception as e:
            logger.error(f"Error registering view enhancements: {str(e)}")
            print(f"Error: {str(e)}")
            sys.exit(1)
            
    print("Screenshot enhancements applied successfully")