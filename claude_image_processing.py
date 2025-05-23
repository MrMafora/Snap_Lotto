"""
Claude Image Processing for Lottery Screenshots

This module provides routes and functionality to process lottery screenshot images
using Claude 3 Opus AI for image analysis and data extraction.
"""
import os
import logging
import threading
import time
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app, session
from sqlalchemy import func, desc
from werkzeug.utils import secure_filename

from models import db, Screenshot, LotteryResult, APIRequestLog
import process_lottery_images

# Set up logging
logger = logging.getLogger(__name__)

# Create blueprint
image_processing_bp = Blueprint('image_processing', __name__)

# Global variables to track processing status
processing_thread = None
processing_status = {
    "is_running": False,
    "total": 0,
    "processed": 0,
    "success": 0,
    "error": 0,
    "start_time": None,
    "end_time": None,
    "last_results": None
}

def get_processing_stats():
    """
    Get current processing statistics
    
    Returns:
        dict: Processing statistics
    """
    stats = {}
    
    # Check if processing is running
    stats["is_running"] = processing_status["is_running"]
    
    # Calculate progress
    if processing_status["total"] > 0:
        progress = int((processing_status["processed"] / processing_status["total"]) * 100)
        stats["progress"] = progress
    else:
        stats["progress"] = 0
    
    # Last run time
    stats["last_run"] = processing_status.get("end_time", None)
    if stats["last_run"]:
        stats["last_run"] = stats["last_run"].strftime('%Y-%m-%d %H:%M')
    
    # Last results
    stats["last_results"] = processing_status.get("last_results", None)
    
    # Count unprocessed images
    with current_app.app_context():
        unprocessed_count = db.session.query(func.count(Screenshot.id)).filter(
            Screenshot.processed == False
        ).scalar()
        stats["unprocessed"] = unprocessed_count or 0
    
    # Get API usage statistics
    today = datetime.utcnow().date()
    with current_app.app_context():
        # Count API calls made today
        api_calls_today = db.session.query(func.count(APIRequestLog.id)).filter(
            func.date(APIRequestLog.created_at) == today,
            APIRequestLog.service == 'anthropic'
        ).scalar()
        stats["api_calls_today"] = api_calls_today or 0
        
        # Calculate success rate
        if api_calls_today > 0:
            success_calls = db.session.query(func.count(APIRequestLog.id)).filter(
                func.date(APIRequestLog.created_at) == today,
                APIRequestLog.service == 'anthropic',
                APIRequestLog.status == 'success'
            ).scalar() or 0
            stats["api_success_rate"] = round((success_calls / api_calls_today) * 100)
        else:
            stats["api_success_rate"] = 0
    
    return stats

def process_images_thread(app, limit, days, force_reprocess):
    """
    Background thread to process images
    
    Args:
        app: Flask app
        limit (int): Maximum number of images to process
        days (int): Only process images from the last N days
        force_reprocess (bool): Whether to reprocess already processed images
    """
    global processing_status
    
    # Update status
    processing_status["is_running"] = True
    processing_status["start_time"] = datetime.utcnow()
    processing_status["processed"] = 0
    processing_status["success"] = 0
    processing_status["error"] = 0
    
    try:
        # Get unprocessed screenshots
        with app.app_context():
            query = db.session.query(Screenshot)
            
            # Filter by processed status
            if not force_reprocess:
                query = query.filter(Screenshot.processed == False)
                
            # Add date filter if specified
            if days:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                query = query.filter(Screenshot.timestamp >= cutoff_date)
                
            # Order by timestamp (oldest first)
            query = query.order_by(Screenshot.timestamp.asc())
            
            # Add limit if specified
            if limit:
                query = query.limit(limit)
                
            screenshots = query.all()
            
        # Update total count
        processing_status["total"] = len(screenshots)
        
        # Process each screenshot
        with app.app_context():
            for idx, screenshot in enumerate(screenshots):
                logger.info(f"Processing screenshot {idx+1}/{processing_status['total']}: ID {screenshot.id}")
                
                # Check if the screenshot file exists
                if not os.path.exists(screenshot.path):
                    logger.error(f"Screenshot file not found: {screenshot.path}")
                    processing_status["error"] += 1
                    processing_status["processed"] += 1
                    continue
                    
                try:
                    # Process the screenshot with Claude 3 Opus
                    from ocr_processor import process_screenshot
                    result = process_screenshot(
                        screenshot_path=screenshot.path,
                        lottery_type=screenshot.lottery_type
                    )
                    
                    # Check if we got a valid result
                    if not result or "error" in result:
                        logger.error(f"Error processing screenshot {screenshot.id}: {result.get('error', 'Unknown error')}")
                        processing_status["error"] += 1
                        processing_status["processed"] += 1
                        continue
                        
                    # Save results to database
                    from data_aggregator import aggregate_data
                    saved_records = aggregate_data(
                        extracted_data=result,
                        lottery_type=screenshot.lottery_type,
                        source_url=screenshot.url
                    )
                    
                    if saved_records:
                        # Mark screenshot as processed
                        screenshot.processed = True
                        db.session.commit()
                        
                        logger.info(f"Successfully processed screenshot {screenshot.id} and saved {len(saved_records)} records")
                        processing_status["success"] += 1
                    else:
                        logger.warning(f"No records saved for screenshot {screenshot.id}")
                        processing_status["error"] += 1
                        
                    processing_status["processed"] += 1
                    
                    # Add a small delay to avoid rate limiting
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Exception processing screenshot {screenshot.id}: {str(e)}")
                    processing_status["error"] += 1
                    processing_status["processed"] += 1
    
    except Exception as e:
        logger.error(f"Error in processing thread: {str(e)}")
    finally:
        # Update status
        processing_status["is_running"] = False
        processing_status["end_time"] = datetime.utcnow()
        
        # Store last results
        processing_status["last_results"] = {
            "total": processing_status["total"],
            "success": processing_status["success"],
            "error": processing_status["error"]
        }
        
        logger.info(f"Processing complete. Results: "
                    f"{processing_status['success']} successful, "
                    f"{processing_status['error']} failed")

@image_processing_bp.route('/process-images', methods=['GET', 'POST'])
def process_images():
    """
    Route to process lottery images with Claude
    """
    global processing_thread
    
    # Get statistics
    stats = get_processing_stats()
    
    # Get recent processing results
    with current_app.app_context():
        results = db.session.query(LotteryResult).filter(
            LotteryResult.ocr_provider == 'anthropic'
        ).order_by(
            LotteryResult.created_at.desc()
        ).limit(10).all()
    
    # Handle form submission
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'start':
            # Check if already running
            if stats["is_running"]:
                flash('Processing is already running', 'warning')
                return redirect(url_for('image_processing.process_images'))
            
            # Get parameters
            limit = request.form.get('limit', type=int)
            days = request.form.get('days', type=int)
            force_reprocess = request.form.get('force_reprocess') == '1'
            
            # Validate parameters
            if not limit or limit < 1:
                limit = 10
            if limit > 100:
                limit = 100
            if not days or days < 1:
                days = 30
            if days > 365:
                days = 365
            
            # Start processing in background thread
            processing_thread = threading.Thread(
                target=process_images_thread,
                args=(current_app, limit, days, force_reprocess)
            )
            processing_thread.daemon = True
            processing_thread.start()
            
            flash(f'Started processing up to {limit} images from the last {days} days', 'success')
            return redirect(url_for('image_processing.process_images'))
        
        elif action == 'check':
            # Get updated statistics
            stats = get_processing_stats()
            
            if stats["is_running"]:
                flash(f'Processing is running: {stats["progress"]}% complete', 'info')
            else:
                flash('Processing is not currently running', 'info')
            
            return redirect(url_for('image_processing.process_images'))
    
    # Render template
    return render_template('process_images.html', stats=stats, results=results)

def register_image_processing_routes(app):
    """Register image processing routes with the Flask app"""
    app.register_blueprint(image_processing_bp)
    logger.info("Claude image processing routes registered")