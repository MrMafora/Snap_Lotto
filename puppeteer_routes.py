"""
Puppeteer Routes for the Lottery Application

This module provides Flask routes for Puppeteer-based screenshot capture functionality.
"""

import os
import time
import logging
from flask import Blueprint, jsonify, render_template, flash, redirect, url_for, request, current_app
from flask_login import login_required, current_user
from datetime import datetime

# Import puppeteer service
from puppeteer_service import process_lottery_screenshots, LOTTERY_URLS

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Blueprint
puppeteer_bp = Blueprint('puppeteer', __name__)

@puppeteer_bp.route('/admin/capture-screenshots', methods=['GET'])
@login_required
def capture_screenshots_page():
    """Render the screenshot capture page"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    return render_template('admin/capture_screenshots.html',
                          title='Capture Screenshots',
                          lottery_urls=LOTTERY_URLS,
                          meta_title='Admin - Capture Screenshots | Snap Lotto',
                          meta_description='Capture lottery screenshots using Puppeteer')

@puppeteer_bp.route('/admin/api/capture-screenshots', methods=['POST'])
@login_required
def capture_screenshots_api():
    """API endpoint to capture screenshots using Puppeteer"""
    if not current_user.is_admin:
        return jsonify({'status': 'error', 'message': 'Access denied. Admin privileges required.'}), 403
    
    try:
        # Get list of lottery types to capture from request
        data = request.get_json()
        selected_types = data.get('types', []) if data else []
        
        # If no types specified, capture all
        if not selected_types:
            urls_to_capture = LOTTERY_URLS
            logger.info(f"Capturing all {len(LOTTERY_URLS)} lottery screenshots")
        else:
            # Filter URLs by selected types
            urls_to_capture = [url for url in LOTTERY_URLS if url['type'] in selected_types]
            logger.info(f"Capturing {len(urls_to_capture)} selected lottery screenshots")
        
        if not urls_to_capture:
            return jsonify({'status': 'error', 'message': 'No valid lottery types selected'}), 400
        
        # Start the capture process
        start_time = time.time()
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        
        # Convert list to dictionary format expected by process_lottery_screenshots
        url_dict = {url['type']: url['url'] for url in urls_to_capture}
        results = process_lottery_screenshots(url_dict, screenshot_dir)
        elapsed_time = time.time() - start_time
        
        # Count successes and failures
        successes = sum(1 for result in results.values() if result.get('status') == 'success')
        failures = sum(1 for result in results.values() if result.get('status') != 'success')
        
        # Update database if requested
        update_db = data.get('update_db', True) if data else True
        db_update_result = {'updated': False}
        
        if update_db and successes > 0:
            try:
                from models import db, Screenshot
                
                # Update the database
                updates = 0
                creates = 0
                
                # Map of lottery types to database names
                lottery_type_map = {
                    'lotto_history': 'Lotto',
                    'lotto_plus_1_history': 'Lotto Plus 1',
                    'lotto_plus_2_history': 'Lotto Plus 2',
                    'powerball_history': 'Powerball',
                    'powerball_plus_history': 'Powerball Plus',
                    'daily_lotto_history': 'Daily Lotto',
                    'lotto_results': 'Lotto Results',
                    'lotto_plus_1_results': 'Lotto Plus 1 Results',
                    'lotto_plus_2_results': 'Lotto Plus 2 Results',
                    'powerball_results': 'Powerball Results',
                    'powerball_plus_results': 'Powerball Plus Results',
                    'daily_lotto_results': 'Daily Lotto Results',
                }
                
                for lottery_type, result in results.items():
                    if result.get('status') != 'success':
                        continue
                    
                    db_name = lottery_type_map.get(lottery_type)
                    if not db_name:
                        continue
                    
                    filepath = result.get('path')
                    if not filepath:
                        continue
                    
                    # Look for existing record
                    screenshot = Screenshot.query.filter_by(lottery_type=db_name).first()
                    
                    if not screenshot:
                        # Try partial match
                        for s in Screenshot.query.all():
                            if db_name.lower() in s.lottery_type.lower():
                                screenshot = s
                                break
                    
                    if screenshot:
                        # Update existing record
                        screenshot.path = filepath
                        screenshot.timestamp = datetime.now()
                        updates += 1
                    else:
                        # Create new record
                        url = next((lot['url'] for lot in LOTTERY_URLS if lot['type'] == lottery_type), '')
                        screenshot = Screenshot()
                        screenshot.lottery_type = db_name
                        screenshot.url = url
                        screenshot.path = filepath
                        screenshot.timestamp = datetime.now()
                        db.session.add(screenshot)
                        creates += 1
                
                # Commit changes
                db.session.commit()
                db_update_result = {
                    'updated': True,
                    'updates': updates,
                    'creates': creates
                }
                
                logger.info(f"Database updated with {updates} updates and {creates} new records")
            except Exception as e:
                logger.error(f"Error updating database: {str(e)}")
                db_update_result = {
                    'updated': False,
                    'error': str(e)
                }
        
        # Prepare response
        response = {
            'status': 'success' if successes > 0 else 'error',
            'message': f"Captured {successes} out of {len(urls_to_capture)} screenshots in {elapsed_time:.2f} seconds",
            'results': results,
            'summary': {
                'total': len(urls_to_capture),
                'success': successes,
                'failed': failures,
                'elapsed_time': elapsed_time
            },
            'database_update': db_update_result
        }
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error capturing screenshots: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@puppeteer_bp.route('/admin/sync-screenshots', methods=['GET', 'POST'])
@login_required
def sync_screenshots():
    """Quick synchronization of all screenshots"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            # Start the capture process for all URLs
            start_time = time.time()
            screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
            
            # Convert list to dictionary format expected by process_lottery_screenshots
            url_dict = {url['type']: url['url'] for url in LOTTERY_URLS}
            results = process_lottery_screenshots(url_dict, screenshot_dir)
            elapsed_time = time.time() - start_time
            
            # Count successes and failures
            successes = sum(1 for result in results.values() if result.get('status') == 'success')
            failures = sum(1 for result in results.values() if result.get('status') != 'success')
            
            # Update database
            try:
                from models import db, Screenshot
                
                updates = 0
                creates = 0
                
                # Map of lottery types to database names
                lottery_type_map = {
                    'lotto_history': 'Lotto',
                    'lotto_plus_1_history': 'Lotto Plus 1',
                    'lotto_plus_2_history': 'Lotto Plus 2',
                    'powerball_history': 'Powerball',
                    'powerball_plus_history': 'Powerball Plus',
                    'daily_lotto_history': 'Daily Lotto',
                    'lotto_results': 'Lotto Results',
                    'lotto_plus_1_results': 'Lotto Plus 1 Results',
                    'lotto_plus_2_results': 'Lotto Plus 2 Results',
                    'powerball_results': 'Powerball Results',
                    'powerball_plus_results': 'Powerball Plus Results',
                    'daily_lotto_results': 'Daily Lotto Results',
                }
                
                for lottery_type, result in results.items():
                    if result.get('status') != 'success':
                        continue
                    
                    db_name = lottery_type_map.get(lottery_type)
                    if not db_name:
                        continue
                    
                    filepath = result.get('path')
                    if not filepath:
                        continue
                    
                    # Look for existing record
                    screenshot = Screenshot.query.filter_by(lottery_type=db_name).first()
                    
                    if not screenshot:
                        # Try partial match
                        for s in Screenshot.query.all():
                            if db_name.lower() in s.lottery_type.lower():
                                screenshot = s
                                break
                    
                    if screenshot:
                        # Update existing record
                        screenshot.path = filepath
                        screenshot.timestamp = datetime.now()
                        updates += 1
                    else:
                        # Create new record
                        url = next((lot['url'] for lot in LOTTERY_URLS if lot['type'] == lottery_type), '')
                        screenshot = Screenshot()
                        screenshot.lottery_type = db_name
                        screenshot.url = url
                        screenshot.path = filepath
                        screenshot.timestamp = datetime.now()
                        db.session.add(screenshot)
                        creates += 1
                
                # Commit changes
                db.session.commit()
                
                logger.info(f"Database updated with {updates} updates and {creates} new records")
                flash(f"Synced {successes} screenshots and updated database with {updates} updates and {creates} new records", 'success')
            except Exception as e:
                logger.error(f"Error updating database: {str(e)}")
                flash(f"Error updating database: {str(e)}", 'danger')
            
            return redirect(url_for('admin'))
        except Exception as e:
            flash(f"Error syncing screenshots: {str(e)}", 'danger')
            logger.error(f"Error syncing screenshots: {str(e)}")
            return redirect(url_for('admin'))
    
    # GET request - just show the button page
    return render_template('admin/sync_screenshots.html',
                          title='Sync Screenshots',
                          meta_title='Admin - Sync Screenshots | Snap Lotto',
                          meta_description='Sync all lottery screenshots with one click')

def register_puppeteer_routes(app):
    """Register all puppeteer routes with the app"""
    app.register_blueprint(puppeteer_bp)
    logger.info("Puppeteer routes registered successfully")