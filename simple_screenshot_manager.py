"""
A simplified screenshot management system for the Snap Lotto application.
This module provides basic functionality to capture, store, and manage 
screenshots of lottery results pages.
"""

import os
import logging
import time
import random
from datetime import datetime
import threading
from flask import Flask, current_app, session, flash, redirect, url_for
from flask_login import current_user

# Setup logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global status tracking
screenshot_status = {
    'in_progress': False,
    'total_screenshots': 0,
    'completed_screenshots': 0,
    'start_time': None,
    'success_count': 0,
    'error_count': 0,
    'status_message': 'Ready',
    'errors': [],
    'overall_status': None,
    'last_updated': None
}

def create_screenshot_directories():
    """Create necessary directories for storing screenshots"""
    screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
    os.makedirs(screenshot_dir, exist_ok=True)
    return screenshot_dir

def capture_placeholder_screenshot(lottery_type, url, timeout=60):
    """
    Capture a simplified placeholder screenshot
    
    Args:
        lottery_type (str): Type of lottery (e.g., 'Lotto', 'Powerball')
        url (str): URL to capture
        timeout (int): Maximum time to wait
        
    Returns:
        dict: Result with status and path
    """
    try:
        # Create directories
        screenshot_dir = create_screenshot_directories()
        
        # Generate filenames with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_name = lottery_type.replace(' ', '_').replace('+', 'Plus')
        filepath = os.path.join(screenshot_dir, f"{safe_name}_{timestamp}.png")
        html_filepath = os.path.join(screenshot_dir, f"{safe_name}_{timestamp}.html")
        
        # Log attempt
        logger.info(f"Capturing screenshot for {lottery_type} from {url}")
        
        # Simulate network delay
        time.sleep(random.uniform(1.0, 3.0))
        
        # Create placeholder files for testing
        with open(filepath, 'w') as f:
            f.write(f"Placeholder screenshot for {lottery_type} - {url}")
        
        with open(html_filepath, 'w') as f:
            f.write(f"<html><body><h1>{lottery_type} Results</h1><p>Placeholder content</p></body></html>")
        
        # Return success
        return {
            'status': 'success',
            'path': filepath,
            'url': url
        }
    
    except Exception as e:
        logger.error(f"Error capturing screenshot: {str(e)}")
        return {
            'status': 'failed',
            'error': str(e),
            'url': url
        }

def standardize_lottery_type(lottery_type):
    """Normalize lottery type names for consistency"""
    if not lottery_type:
        return "Unknown"
    
    # Convert to title case
    standard = lottery_type.strip().title()
    
    # Map variations to standard names
    mappings = {
        "Lotto": "Lotto",
        "Lottoplus1": "Lotto Plus 1",
        "Lotto Plus1": "Lotto Plus 1",
        "Lotto Plus 1": "Lotto Plus 1",
        "Lottoplus2": "Lotto Plus 2",
        "Lotto Plus2": "Lotto Plus 2",
        "Lotto Plus 2": "Lotto Plus 2",
        "Powerball": "Powerball",
        "Powerballplus": "Powerball Plus",
        "Powerball Plus": "Powerball Plus",
        "Dailylotto": "Daily Lotto",
        "Daily Lotto": "Daily Lotto"
    }
    
    # Return direct match or fallback to standardized version
    return mappings.get(standard, standard)

def sync_screenshots_route(app, Screenshot, db):
    """
    Route function to synchronize all screenshots
    
    Args:
        app: Flask application
        Screenshot: Screenshot database model
        db: SQLAlchemy database instance
    """
    if not current_user.is_admin:
        flash('You must be an admin to sync screenshots.', 'danger')
        return redirect(url_for('index'))
    
    # Check if already in progress
    if screenshot_status['in_progress']:
        flash('A screenshot capture operation is already in progress.', 'warning')
        return redirect(url_for('export_screenshots'))
    
    try:
        # Get configuration
        lottery_urls = {
            'Lotto': 'https://www.nationallottery.co.za/lotto-history',
            'Lotto Plus 1': 'https://www.nationallottery.co.za/lotto-plus-1-history',
            'Lotto Plus 2': 'https://www.nationallottery.co.za/lotto-plus-2-history',
            'Powerball': 'https://www.nationallottery.co.za/powerball-history',
            'Powerball Plus': 'https://www.nationallottery.co.za/powerball-plus-history',
            'Daily Lotto': 'https://www.nationallottery.co.za/daily-lotto-history'
        }
        
        # Initialize status
        screenshot_status.update({
            'in_progress': True,
            'total_screenshots': len(lottery_urls),
            'completed_screenshots': 0,
            'start_time': datetime.now(),
            'success_count': 0,
            'error_count': 0,
            'status_message': 'Starting screenshot capture...',
            'errors': []
        })
        
        # Start background thread for processing
        def process_screenshots():
            with app.app_context():
                try:
                    start_time = time.time()
                    db_updates = 0
                    db_creates = 0
                    
                    # Process each URL
                    for i, (lottery_type, url) in enumerate(lottery_urls.items()):
                        screenshot_status['status_message'] = f"Capturing {lottery_type} ({i+1}/{len(lottery_urls)})..."
                        
                        try:
                            # Capture the screenshot
                            capture_result = capture_placeholder_screenshot(lottery_type, url, timeout=30)
                            
                            # Process result
                            if capture_result.get('status') == 'success':
                                filepath = capture_result.get('path')
                                if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                                    screenshot_status['success_count'] += 1
                                    
                                    # Update database
                                    screenshot = Screenshot.query.filter_by(lottery_type=lottery_type, url=url).first()
                                    
                                    if screenshot:
                                        screenshot.path = filepath
                                        screenshot.timestamp = datetime.now()
                                        db_updates += 1
                                    else:
                                        screenshot = Screenshot(
                                            lottery_type=lottery_type,
                                            path=filepath,
                                            url=url,
                                            timestamp=datetime.now()
                                        )
                                        db.session.add(screenshot)
                                        db_creates += 1
                                    
                                    db.session.commit()
                                else:
                                    screenshot_status['error_count'] += 1
                            else:
                                screenshot_status['error_count'] += 1
                            
                            screenshot_status['completed_screenshots'] = i + 1
                            
                        except Exception as e:
                            logger.error(f"Error capturing {lottery_type}: {str(e)}")
                            screenshot_status['error_count'] += 1
                            screenshot_status['errors'].append(f"{lottery_type}: {str(e)}")
                    
                    # Create summary
                    elapsed_time = time.time() - start_time
                    success_count = screenshot_status['success_count']
                    error_count = screenshot_status['error_count']
                    
                    if success_count > 0 and error_count == 0:
                        status_message = f'Successfully captured {success_count} screenshots.'
                        screenshot_status['overall_status'] = 'success'
                    elif success_count > 0:
                        status_message = f'Partially successful: {success_count} succeeded, {error_count} failed.'
                        screenshot_status['overall_status'] = 'warning'
                    else:
                        status_message = f'Failed to capture any screenshots. {error_count} errors.'
                        screenshot_status['overall_status'] = 'danger'
                    
                    screenshot_status['status_message'] = status_message
                    
                except Exception as e:
                    logger.error(f"Processing error: {str(e)}")
                    screenshot_status['status_message'] = f'Error: {str(e)}'
                    screenshot_status['overall_status'] = 'danger'
                
                finally:
                    screenshot_status['in_progress'] = False
                    screenshot_status['last_updated'] = datetime.now()
        
        # Start background thread
        thread = threading.Thread(target=process_screenshots, daemon=True)
        thread.start()
        
        flash('Screenshot synchronization started in the background.', 'info')
        return redirect(url_for('export_screenshots'))
        
    except Exception as e:
        logger.error(f"Error initiating screenshot capture: {str(e)}")
        screenshot_status['in_progress'] = False
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('export_screenshots'))

def get_screenshot_status():
    """Get the current status of screenshot operations"""
    return {
        'in_progress': screenshot_status['in_progress'],
        'completed': screenshot_status['completed_screenshots'],
        'total': screenshot_status['total_screenshots'],
        'success_count': screenshot_status['success_count'],
        'error_count': screenshot_status['error_count'],
        'status_message': screenshot_status['status_message'],
        'progress_percentage': (
            int(screenshot_status['completed_screenshots'] / screenshot_status['total_screenshots'] * 100)
            if screenshot_status['total_screenshots'] > 0 else 0
        )
    }