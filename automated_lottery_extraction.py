#!/usr/bin/env python
"""
Automated Lottery Data Extraction System

This module provides a complete system to:
1. Capture screenshots of lottery results websites daily at 2 AM SAST
2. Send screenshots to Claude's vision API for data extraction
3. Parse and validate extracted data
4. Create a review interface for human verification
5. Import verified data into the database

It uses the APScheduler to run on a schedule and is configurable through
environment variables or the config.py file.
"""

import os
import sys
import json
import base64
import logging
from datetime import datetime, timedelta
import pytz
import requests
import traceback
import time
from io import BytesIO
from typing import Dict, List, Union, Any, Optional, Tuple

import anthropic
from anthropic import Anthropic
# We removed the PIL import since we're not using images anymore
from bs4 import BeautifulSoup
from flask import Blueprint, Flask, request, render_template, redirect, url_for, flash, jsonify, current_app, abort
from flask_login import current_user, login_required
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from models import db, LotteryResult, Screenshot, ImportHistory, ImportedRecord, PendingExtraction
from data_aggregator import normalize_lottery_type
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/automated_extraction.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Create blueprint for automated extraction
automated_extraction_bp = Blueprint('automated_extraction', __name__)

# Initialize the Anthropic client
anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
anthropic_client = Anthropic(api_key=anthropic_api_key)
MODEL = "claude-3-sonnet-20240229"  # Using Claude 3 Sonnet model

# South African timezone
SA_TIMEZONE = pytz.timezone('Africa/Johannesburg')

# Screenshot directory
SCREENSHOT_DIR = Config.SCREENSHOT_DIR

# URLs for lottery results
LOTTERY_URLS = Config.RESULTS_URLS

class LotteryScreenshotManager:
    """Manages the process of capturing lottery screenshots and storing them."""
    
    @staticmethod
    def capture_lottery_screenshots() -> List[Dict[str, Any]]:
        """
        Capture lottery results data using requests instead of screenshots.
        
        Returns:
            List[Dict[str, Any]]: List of dictionaries with lottery data information
        """
        screenshots = []
        
        # Use requests and BeautifulSoup instead of Playwright
        import requests
        from bs4 import BeautifulSoup
        
        # Headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            for url_info in LOTTERY_URLS:
                url = url_info['url']
                lottery_type = url_info['lottery_type']
                
                try:
                    logger.info(f"Capturing HTML content for {lottery_type} from {url}")
                    response = requests.get(url, headers=headers, timeout=30)
                    
                    if response.status_code != 200:
                        logger.error(f"Failed to retrieve page for {lottery_type}. Status code: {response.status_code}")
                        continue
                    
                    html_content = response.text
                    
                    # Parse HTML with BeautifulSoup
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Extract the main content area
                    main_content = soup.find('main') or soup.find('div', class_='content') or soup
                    simplified_content = main_content.get_text(separator='\n', strip=True)
                    
                    # Save both HTML and text to file system for backup
                    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
                    timestamp = datetime.now(SA_TIMEZONE).strftime("%Y%m%d_%H%M%S")
                    html_filename = f"{lottery_type.replace(' ', '_').lower()}_{timestamp}.html"
                    html_path = os.path.join(SCREENSHOT_DIR, html_filename)
                    
                    with open(html_path, "w", encoding='utf-8') as f:
                        f.write(html_content)
                    
                    # Also save a text version for easier review
                    text_filename = f"{lottery_type.replace(' ', '_').lower()}_{timestamp}.txt"
                    text_path = os.path.join(SCREENSHOT_DIR, text_filename)
                    
                    with open(text_path, "w", encoding='utf-8') as f:
                        f.write(simplified_content)
                    
                    # Create "screenshot" record in database 
                    # We're reusing the Screenshot model but storing HTML content instead
                    screenshot = Screenshot(
                        url=url,
                        lottery_type=lottery_type,
                        timestamp=datetime.now(SA_TIMEZONE),
                        path=html_path,
                        zoomed_path=text_path,  # Store text content path in zoomed_path
                        processed=False
                    )
                    db.session.add(screenshot)
                    db.session.commit()
                    
                    # For Claude processing we'll need base64 encoded content
                    html_base64 = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
                    
                    screenshots.append({
                        "id": screenshot.id,
                        "lottery_type": lottery_type,
                        "url": url,
                        "path": html_path,
                        "zoomed_path": text_path,
                        "data": html_base64,
                        "html_content": html_content,
                        "text_content": simplified_content
                    })
                    
                    logger.info(f"Successfully captured and saved content for {lottery_type}")
                    
                except Exception as e:
                    logger.error(f"Error capturing content for {lottery_type}: {e}")
                    logger.error(traceback.format_exc())
                    
                    # Try to use most recent existing data as fallback
                    try:
                        existing_screenshot = Screenshot.query.filter_by(
                            lottery_type=lottery_type,
                            processed=True
                        ).order_by(Screenshot.timestamp.desc()).first()
                        
                        if existing_screenshot and os.path.exists(existing_screenshot.path):
                            logger.info(f"Using existing data as fallback for {lottery_type}")
                            
                            # Check if this is HTML or image
                            if existing_screenshot.path.endswith('.html'):
                                with open(existing_screenshot.path, "r", encoding='utf-8') as f:
                                    html_content = f.read()
                                html_base64 = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
                                
                                # Also get the text content if available
                                text_content = ""
                                if existing_screenshot.zoomed_path and os.path.exists(existing_screenshot.zoomed_path):
                                    with open(existing_screenshot.zoomed_path, "r", encoding='utf-8') as f:
                                        text_content = f.read()
                                
                                screenshots.append({
                                    "id": existing_screenshot.id,
                                    "lottery_type": lottery_type,
                                    "url": url,
                                    "path": existing_screenshot.path,
                                    "zoomed_path": existing_screenshot.zoomed_path,
                                    "data": html_base64,
                                    "html_content": html_content,
                                    "text_content": text_content,
                                    "is_fallback": True
                                })
                            else:
                                # If it's an image, read as binary
                                with open(existing_screenshot.path, "rb") as f:
                                    screenshot_data = f.read()
                                    
                                screenshots.append({
                                    "id": existing_screenshot.id,
                                    "lottery_type": lottery_type,
                                    "url": url,
                                    "path": existing_screenshot.path,
                                    "zoomed_path": existing_screenshot.zoomed_path,
                                    "data": base64.b64encode(screenshot_data).decode('utf-8'),
                                    "is_fallback": True
                                })
                        else:
                            logger.error(f"No fallback data available for {lottery_type}")
                            
                    except Exception as fallback_error:
                        logger.error(f"Error using fallback data for {lottery_type}: {fallback_error}")
        
        except Exception as e:
            logger.error(f"Error in capture_lottery_screenshots: {e}")
            logger.error(traceback.format_exc())
        
        return screenshots

class LotteryDataExtractor:
    """Handles extracting data from screenshots using Claude's vision capabilities."""
    
    @staticmethod
    def extract_data_from_screenshot(screenshot: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract lottery data from HTML content using Claude API.
        
        Args:
            screenshot (Dict[str, Any]): Content information including HTML data and lottery type
            
        Returns:
            Dict[str, Any]: Extracted lottery data
        """
        lottery_type = screenshot["lottery_type"]
        screenshot_id = screenshot["id"]
        
        try:
            # We'll use the base64 data that was already prepared
            base64_content = screenshot["data"]
            
            # Check if we have additional text content
            has_text_content = "text_content" in screenshot and screenshot["text_content"]
            text_content = screenshot.get("text_content", "")
            
            # Define the prompt for Claude
            system_prompt = """
            You are a lottery data extraction expert. Your task is to extract structured lottery data from South African lottery results HTML/text.
            
            Follow these precise guidelines:
            1. Extract the exact lottery type, draw number, draw date, winning numbers, and bonus ball/powerball.
            2. For division details, extract winners and prize amounts for each division.
            3. Format all data as a JSON object with specific fields.
            4. Maintain proper data types (numbers as integers, dates as ISO format strings).
            5. Be extremely precise with numbers - they must be exactly as shown.
            6. For draw dates, ensure they are in ISO format YYYY-MM-DD.
            
            Return ONLY a valid JSON object with the following structure:
            {
                "lottery_type": "exact name of lottery type",
                "draw_number": "draw number as string",
                "draw_date": "draw date in ISO format YYYY-MM-DD",
                "winning_numbers": [array of integers],
                "bonus_numbers": [array of integers],
                "divisions": {
                    "Division 1": {"winners": "number of winners as string", "prize": "prize amount as string with R prefix"},
                    "Division 2": {"winners": "...", "prize": "..."},
                    ...
                }
            }
            """
            
            user_prompt = f"""
            This is South African {lottery_type} results data. Please extract the following information:
            
            1. Draw Number
            2. Draw Date
            3. Winning Numbers
            4. Bonus Ball/Powerball (if applicable)
            5. Division details (winners and prize amounts)
            
            Return only a valid, properly formatted JSON object according to the specified structure.
            """
            
            # Prepare the content for Claude
            content = [{"type": "text", "text": user_prompt}]
            
            # If we have text content, add it
            if has_text_content:
                content.append({
                    "type": "text", 
                    "text": f"Extracted text content:\n\n{text_content}"
                })
            
            # Make the API call to Claude
            response = anthropic_client.messages.create(
                model=MODEL,
                max_tokens=2000,
                temperature=0.0,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": content
                    }
                ]
            )
            
            # Parse the response to extract JSON
            response_text = response.content[0].text
            
            # Extract JSON from the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                try:
                    extracted_data = json.loads(json_text)
                    
                    # Add metadata
                    extracted_data["screenshot_id"] = screenshot_id
                    extracted_data["extraction_timestamp"] = datetime.utcnow().isoformat()
                    extracted_data["ocr_provider"] = "anthropic"
                    extracted_data["ocr_model"] = MODEL
                    
                    # Normalize lottery type
                    if "lottery_type" in extracted_data:
                        extracted_data["lottery_type"] = normalize_lottery_type(extracted_data["lottery_type"])
                    
                    logger.info(f"Successfully extracted data for {lottery_type} draw #{extracted_data.get('draw_number', 'unknown')}")
                    return extracted_data
                
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON from Claude response: {e}")
                    logger.error(f"Invalid JSON text: {json_text}")
                    return {"error": "Failed to parse JSON from response", "response_text": response_text}
            
            else:
                logger.error(f"No JSON found in Claude response: {response_text}")
                return {"error": "No JSON found in response", "response_text": response_text}
        
        except Exception as e:
            logger.error(f"Error extracting data for {lottery_type}: {e}")
            logger.error(traceback.format_exc())
            return {"error": str(e)}

class PendingDataManager:
    """Manages the pending extraction data before final approval."""
    
    @staticmethod
    def save_pending_extraction(extracted_data: Dict[str, Any]) -> int:
        """
        Save extracted data as a pending extraction for review.
        
        Args:
            extracted_data (Dict[str, Any]): Extracted lottery data
            
        Returns:
            int: ID of the created pending extraction
        """
        try:
            # Extract main fields
            lottery_type = extracted_data.get("lottery_type", "Unknown")
            draw_number = extracted_data.get("draw_number", "Unknown")
            
            # Create PendingExtraction record
            pending = PendingExtraction(
                lottery_type=lottery_type,
                draw_number=draw_number,
                extraction_date=datetime.utcnow(),
                screenshot_id=extracted_data.get("screenshot_id"),
                raw_data=json.dumps(extracted_data),
                reviewed=False
            )
            db.session.add(pending)
            db.session.commit()
            
            logger.info(f"Saved pending extraction for {lottery_type} draw #{draw_number} with ID {pending.id}")
            return pending.id
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving pending extraction: {e}")
            logger.error(traceback.format_exc())
            return None

    @staticmethod
    def get_pending_extractions() -> List[Dict[str, Any]]:
        """
        Get all pending extractions that need review.
        
        Returns:
            List[Dict[str, Any]]: List of pending extractions
        """
        try:
            pending_records = PendingExtraction.query.filter_by(reviewed=False).order_by(
                PendingExtraction.lottery_type,
                PendingExtraction.extraction_date.desc()
            ).all()
            
            pending_list = []
            for record in pending_records:
                try:
                    # Parse the raw data
                    raw_data = json.loads(record.raw_data)
                    
                    # Create a simplified record for the UI
                    pending_item = {
                        "id": record.id,
                        "lottery_type": record.lottery_type,
                        "draw_number": record.draw_number,
                        "extraction_date": record.extraction_date.isoformat(),
                        "data": {
                            "winning_numbers": raw_data.get("winning_numbers", []),
                            "bonus_numbers": raw_data.get("bonus_numbers", []),
                            "draw_date": raw_data.get("draw_date", ""),
                            "divisions": raw_data.get("divisions", {})
                        }
                    }
                    
                    # Check if we have the screenshot
                    if record.screenshot_id:
                        screenshot = Screenshot.query.get(record.screenshot_id)
                        if screenshot and screenshot.filename and os.path.exists(screenshot.filename):
                            pending_item["screenshot_filename"] = screenshot.filename
                    
                    pending_list.append(pending_item)
                
                except Exception as e:
                    logger.error(f"Error processing pending extraction {record.id}: {e}")
            
            return pending_list
        
        except Exception as e:
            logger.error(f"Error getting pending extractions: {e}")
            return []

    @staticmethod
    def approve_extraction(extraction_id: int, user_edits: Optional[Dict[str, Any]] = None) -> bool:
        """
        Approve and import a pending extraction to the database.
        
        Args:
            extraction_id (int): ID of the pending extraction
            user_edits (Optional[Dict[str, Any]]): Any edits made by the user
            
        Returns:
            bool: Success status
        """
        try:
            # Get the pending extraction
            pending = PendingExtraction.query.get(extraction_id)
            if not pending:
                logger.error(f"Pending extraction {extraction_id} not found")
                return False
            
            # Parse the raw data
            data = json.loads(pending.raw_data)
            
            # Apply any user edits
            if user_edits:
                for key, value in user_edits.items():
                    if key in data:
                        data[key] = value
            
            # Check if we already have this draw
            existing = LotteryResult.query.filter_by(
                lottery_type=data["lottery_type"],
                draw_number=data["draw_number"]
            ).first()
            
            # Create JSON strings for database
            numbers_json = json.dumps(data.get("winning_numbers", []))
            bonus_numbers_json = json.dumps(data.get("bonus_numbers", []))
            divisions_json = json.dumps(data.get("divisions", {}))
            
            # Create import history
            import_history = ImportHistory(
                import_date=datetime.utcnow(),
                import_type="automated-extraction",
                file_name=f"extraction_{extraction_id}",
                records_added=0,
                records_updated=0,
                total_processed=1,
                errors=0
            )
            db.session.add(import_history)
            db.session.commit()
            
            # Get draw date
            try:
                if data.get("draw_date"):
                    draw_date = datetime.fromisoformat(data["draw_date"])
                else:
                    draw_date = datetime.utcnow()
            except:
                draw_date = datetime.utcnow()
            
            if existing:
                # Update existing record
                existing.draw_date = draw_date
                existing.numbers = numbers_json
                existing.bonus_numbers = bonus_numbers_json
                existing.divisions = divisions_json
                existing.screenshot_id = pending.screenshot_id
                existing.source_url = data.get("source_url", "automated-extraction")
                existing.ocr_provider = data.get("ocr_provider", "anthropic")
                existing.ocr_model = data.get("ocr_model", MODEL)
                existing.ocr_timestamp = data.get("extraction_timestamp", datetime.utcnow().isoformat())
                
                db.session.commit()
                
                # Create imported record
                imported_record = ImportedRecord(
                    import_id=import_history.id,
                    lottery_type=data["lottery_type"],
                    draw_number=data["draw_number"],
                    draw_date=draw_date,
                    is_new=False,
                    lottery_result_id=existing.id
                )
                db.session.add(imported_record)
                
                # Update import history
                import_history.records_updated = 1
                
                logger.info(f"Updated existing {data['lottery_type']} draw #{data['draw_number']}")
            
            else:
                # Create new record
                lottery_result = LotteryResult(
                    lottery_type=data["lottery_type"],
                    draw_number=data["draw_number"],
                    draw_date=draw_date,
                    numbers=numbers_json,
                    bonus_numbers=bonus_numbers_json,
                    divisions=divisions_json,
                    screenshot_id=pending.screenshot_id,
                    source_url=data.get("source_url", "automated-extraction"),
                    ocr_provider=data.get("ocr_provider", "anthropic"),
                    ocr_model=data.get("ocr_model", MODEL),
                    ocr_timestamp=data.get("extraction_timestamp", datetime.utcnow().isoformat())
                )
                db.session.add(lottery_result)
                db.session.commit()
                
                # Create imported record
                imported_record = ImportedRecord(
                    import_id=import_history.id,
                    lottery_type=data["lottery_type"],
                    draw_number=data["draw_number"],
                    draw_date=draw_date,
                    is_new=True,
                    lottery_result_id=lottery_result.id
                )
                db.session.add(imported_record)
                
                # Update import history
                import_history.records_added = 1
                
                logger.info(f"Created new {data['lottery_type']} draw #{data['draw_number']}")
            
            # Mark the pending extraction as reviewed
            pending.reviewed = True
            pending.review_date = datetime.utcnow()
            
            db.session.commit()
            
            return True
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error approving extraction {extraction_id}: {e}")
            logger.error(traceback.format_exc())
            return False

    @staticmethod
    def reject_extraction(extraction_id: int, reason: str = None) -> bool:
        """
        Reject a pending extraction.
        
        Args:
            extraction_id (int): ID of the pending extraction
            reason (str, optional): Reason for rejection
            
        Returns:
            bool: Success status
        """
        try:
            # Get the pending extraction
            pending = PendingExtraction.query.get(extraction_id)
            if not pending:
                logger.error(f"Pending extraction {extraction_id} not found")
                return False
            
            # Mark as reviewed and add rejection reason
            pending.reviewed = True
            pending.review_date = datetime.utcnow()
            pending.rejection_reason = reason
            
            db.session.commit()
            
            logger.info(f"Rejected extraction {extraction_id}: {reason}")
            return True
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error rejecting extraction {extraction_id}: {e}")
            return False

def run_extraction_process():
    """Run the complete extraction process from screenshots to pending data."""
    try:
        logger.info("Starting automated lottery extraction process")
        
        # Step 1: Capture screenshots
        screenshots = LotteryScreenshotManager.capture_lottery_screenshots()
        
        if not screenshots:
            logger.warning("No screenshots captured, aborting process")
            return
        
        logger.info(f"Captured {len(screenshots)} screenshots")
        
        # Step 2: Extract data from each screenshot
        for screenshot in screenshots:
            try:
                logger.info(f"Processing {screenshot['lottery_type']} screenshot")
                
                # Extract data using Claude vision
                extracted_data = LotteryDataExtractor.extract_data_from_screenshot(screenshot)
                
                if not extracted_data or "error" in extracted_data:
                    logger.error(f"Failed to extract data from {screenshot['lottery_type']} screenshot")
                    continue
                
                # Step 3: Save as pending extraction
                pending_id = PendingDataManager.save_pending_extraction(extracted_data)
                
                if pending_id:
                    logger.info(f"Successfully processed {screenshot['lottery_type']} screenshot, pending ID: {pending_id}")
                    
                    # Update screenshot as processed
                    screenshot_record = Screenshot.query.get(screenshot["id"])
                    if screenshot_record:
                        screenshot_record.processed = True
                        db.session.commit()
                
                # Sleep to avoid rate limits
                time.sleep(2)
            
            except Exception as e:
                logger.error(f"Error processing screenshot for {screenshot['lottery_type']}: {e}")
                logger.error(traceback.format_exc())
        
        logger.info("Completed automated lottery extraction process")
    
    except Exception as e:
        logger.error(f"Error in extraction process: {e}")
        logger.error(traceback.format_exc())

# Setup the scheduler
scheduler = BackgroundScheduler()

# Configure the job to run at 2 AM South Africa Standard Time (UTC+2)
def schedule_extraction_job():
    """Schedule the extraction job to run at 2 AM SAST."""
    # Remove existing job if any
    scheduler.remove_all_jobs()
    
    # Add the job to run at 2 AM SAST
    trigger = CronTrigger(hour=2, minute=0, timezone=SA_TIMEZONE)
    scheduler.add_job(run_extraction_process, trigger=trigger, id="lottery_extraction")
    
    # Also add a job to run daily model updates if needed
    # This ensures we're always using the latest available model
    update_trigger = CronTrigger(hour=1, minute=0, timezone=SA_TIMEZONE)
    scheduler.add_job(update_model_configuration, trigger=update_trigger, id="model_update")
    
    logger.info("Scheduled extraction job to run at 2:00 AM SAST")

def update_model_configuration():
    """Update the model configuration to use the latest Claude model."""
    global MODEL
    
    try:
        # For future updates, we could query Anthropic API for latest model
        # For now, we just use the static latest model
        MODEL = "claude-3-sonnet-20240229"  # Using Claude 3 Sonnet model
        logger.info(f"Updated model configuration to use {MODEL}")
    
    except Exception as e:
        logger.error(f"Error updating model configuration: {e}")

# Routes for the web interface
@automated_extraction_bp.route('/pending_extractions')
def pending_extractions():
    """Display pending extractions for review."""
    # Ensure user is logged in
    if not hasattr(current_user, 'is_authenticated') or not current_user.is_authenticated:
        # Import Flask modules here to avoid circular import
        from flask import flash, redirect, url_for
        flash('You must be logged in to access this page.', 'warning')
        return redirect(url_for('login', next=request.url))
    
    # Ensure user is admin
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
        # Import Flask modules here to avoid circular import
        from flask import flash, redirect, url_for
        flash('You must be an admin to access this page.', 'danger')
        return redirect(url_for('index'))
    
    pending_list = PendingDataManager.get_pending_extractions()
    return render_template('pending_extractions.html', pending_extractions=pending_list)

@automated_extraction_bp.route('/extraction_details/<int:extraction_id>')
@login_required
def extraction_details(extraction_id):
    """Display details of a specific extraction."""
    try:
        pending = PendingExtraction.query.get_or_404(extraction_id)
        data = json.loads(pending.raw_data)
        
        # Get screenshot if available
        screenshot_filename = None
        if pending.screenshot_id:
            screenshot = Screenshot.query.get(pending.screenshot_id)
            if screenshot and screenshot.filename and os.path.exists(screenshot.filename):
                screenshot_filename = screenshot.filename
        
        return render_template('extraction_details.html', 
                              extraction=pending, 
                              data=data, 
                              screenshot_filename=screenshot_filename)
    
    except Exception as e:
        logger.error(f"Error displaying extraction details for {extraction_id}: {e}")
        flash(f"Error displaying extraction details: {str(e)}", "error")
        return redirect(url_for('automated_extraction.pending_extractions'))

@automated_extraction_bp.route('/approve_extraction/<int:extraction_id>', methods=['POST'])
@login_required
def approve_extraction(extraction_id):
    """Approve a pending extraction."""
    try:
        # Get user edits if any
        user_edits = {}
        if request.form.get('edited_data'):
            user_edits = json.loads(request.form.get('edited_data'))
        
        success = PendingDataManager.approve_extraction(extraction_id, user_edits)
        
        if success:
            flash(f"Extraction #{extraction_id} approved and imported successfully", "success")
        else:
            flash(f"Failed to approve extraction #{extraction_id}", "error")
        
        return redirect(url_for('automated_extraction.pending_extractions'))
    
    except Exception as e:
        logger.error(f"Error approving extraction {extraction_id}: {e}")
        flash(f"Error approving extraction: {str(e)}", "error")
        return redirect(url_for('automated_extraction.pending_extractions'))

@automated_extraction_bp.route('/reject_extraction/<int:extraction_id>', methods=['POST'])
@login_required
def reject_extraction(extraction_id):
    """Reject a pending extraction."""
    try:
        reason = request.form.get('rejection_reason', 'No reason provided')
        success = PendingDataManager.reject_extraction(extraction_id, reason)
        
        if success:
            flash(f"Extraction #{extraction_id} rejected", "info")
        else:
            flash(f"Failed to reject extraction #{extraction_id}", "error")
        
        return redirect(url_for('automated_extraction.pending_extractions'))
    
    except Exception as e:
        logger.error(f"Error rejecting extraction {extraction_id}: {e}")
        flash(f"Error rejecting extraction: {str(e)}", "error")
        return redirect(url_for('automated_extraction.pending_extractions'))

@automated_extraction_bp.route('/run_extraction_now')
@login_required
def run_extraction_now():
    """Run the extraction process immediately."""
    try:
        # Run in a separate thread to avoid blocking
        import threading
        thread = threading.Thread(target=run_extraction_process)
        thread.start()
        
        flash("Extraction process started. Check pending extractions in a few minutes.", "info")
        return redirect(url_for('automated_extraction.pending_extractions'))
    
    except Exception as e:
        logger.error(f"Error starting extraction process: {e}")
        flash(f"Error starting extraction process: {str(e)}", "error")
        return redirect(url_for('automated_extraction.pending_extractions'))

# API endpoints
@automated_extraction_bp.route('/api/pending_extractions')
@login_required
def api_pending_extractions():
    """API endpoint to get pending extractions."""
    pending_list = PendingDataManager.get_pending_extractions()
    return jsonify({"pending_extractions": pending_list})

@automated_extraction_bp.route('/api/approve_extraction/<int:extraction_id>', methods=['POST'])
@login_required
def api_approve_extraction(extraction_id):
    """API endpoint to approve an extraction."""
    try:
        data = request.get_json()
        user_edits = data.get('user_edits', {})
        
        success = PendingDataManager.approve_extraction(extraction_id, user_edits)
        
        if success:
            return jsonify({"status": "success", "message": f"Extraction #{extraction_id} approved"})
        else:
            return jsonify({"status": "error", "message": f"Failed to approve extraction #{extraction_id}"}), 400
    
    except Exception as e:
        logger.error(f"Error in API approve_extraction: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@automated_extraction_bp.route('/api/reject_extraction/<int:extraction_id>', methods=['POST'])
@login_required
def api_reject_extraction(extraction_id):
    """API endpoint to reject an extraction."""
    try:
        data = request.get_json()
        reason = data.get('reason', 'No reason provided')
        
        success = PendingDataManager.reject_extraction(extraction_id, reason)
        
        if success:
            return jsonify({"status": "success", "message": f"Extraction #{extraction_id} rejected"})
        else:
            return jsonify({"status": "error", "message": f"Failed to reject extraction #{extraction_id}"}), 400
    
    except Exception as e:
        logger.error(f"Error in API reject_extraction: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@automated_extraction_bp.route('/api/run_extraction_now', methods=['POST'])
@login_required
def api_run_extraction_now():
    """API endpoint to run extraction process."""
    try:
        # Run in a separate thread
        import threading
        thread = threading.Thread(target=run_extraction_process)
        thread.start()
        
        return jsonify({"status": "success", "message": "Extraction process started"})
    
    except Exception as e:
        logger.error(f"Error in API run_extraction_now: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def register_extraction_routes(app):
    """Register extraction routes with the app."""
    app.register_blueprint(automated_extraction_bp, url_prefix='/admin/extraction')
    
    # Start the scheduler when the app starts
    if not scheduler.running:
        scheduler.start()
        schedule_extraction_job()
        
        # Register shutdown function
        import atexit
        atexit.register(lambda: scheduler.shutdown())

# Run this module directly to test the extraction process
if __name__ == '__main__':
    from main import app
    
    # If argument is "schedule", just set up the schedule
    if len(sys.argv) > 1 and sys.argv[1] == "schedule":
        with app.app_context():
            if not scheduler.running:
                scheduler.start()
                schedule_extraction_job()
                
                print("Scheduled extraction job. Press Ctrl+C to exit.")
                
                try:
                    # Keep the script running
                    while True:
                        time.sleep(60)
                except KeyboardInterrupt:
                    print("Shutting down scheduler...")
                    scheduler.shutdown()
    
    # Otherwise, run the extraction process immediately
    else:
        with app.app_context():
            run_extraction_process()