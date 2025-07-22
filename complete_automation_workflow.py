#!/usr/bin/env python3
"""
Complete Automated Lottery Workflow System
Captures fresh screenshots, processes with AI, updates database, and cleans up files automatically
"""

import logging
import sys
import os
import time
import shutil
import glob
from datetime import datetime
from playwright.sync_api import sync_playwright

# Add current directory to path
sys.path.append('.')

def setup_logging():
    """Configure logging for automation workflow"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('automation_workflow.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def capture_fresh_screenshots(logger):
    """Capture fresh screenshots of all lottery types"""
    logger.info("Step 1: Starting fresh screenshot capture...")
    
    # STEP 1: Clean up old screenshots FIRST
    logger.info("Cleaning up old screenshots before capture...")
    screenshots_dir = 'screenshots'
    if os.path.exists(screenshots_dir):
        old_files = glob.glob(os.path.join(screenshots_dir, '*.png'))
        for old_file in old_files:
            try:
                os.remove(old_file)
                logger.info(f"Removed old screenshot: {os.path.basename(old_file)}")
            except Exception as e:
                logger.warning(f"Could not remove {old_file}: {e}")
        logger.info(f"Cleanup complete: {len(old_files)} old screenshots removed")
    
    # Lottery URLs and types
    lottery_urls = {
        'LOTTO': 'https://www.nationallottery.co.za/results/lotto',
        'LOTTO PLUS 1': 'https://www.nationallottery.co.za/results/lotto-plus-1-results',
        'LOTTO PLUS 2': 'https://www.nationallottery.co.za/results/lotto-plus-2-results',
        'POWERBALL': 'https://www.nationallottery.co.za/results/powerball',
        'POWERBALL PLUS': 'https://www.nationallottery.co.za/results/powerball-plus',
        'DAILY LOTTO': 'https://www.nationallottery.co.za/results/daily-lotto'
    }
    
    # Create screenshots directory
    os.makedirs('screenshots', exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    captured_files = []
    
    try:
        with sync_playwright() as p:
            # Use existing Chromium in Replit
            browser_path = "/nix/store/zi4f80l169xlmivz8vja8wlphq74qqk0-chromium-125.0.6422.141/bin/chromium"
            
            browser = p.chromium.launch(
                executable_path=browser_path,
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            
            for lottery_type, url in lottery_urls.items():
                try:
                    logger.info(f"Capturing {lottery_type} from {url}")
                    
                    # Navigate and wait for load
                    page.goto(url, wait_until='networkidle', timeout=30000)
                    page.wait_for_timeout(3000)  # Additional wait for dynamic content
                    
                    # Generate filename
                    safe_name = lottery_type.lower().replace(' ', '_').replace('+', '_plus')
                    filename = f"{timestamp}_{safe_name}.png"
                    filepath = os.path.join('screenshots', filename)
                    
                    # Take screenshot
                    page.screenshot(path=filepath, full_page=True)
                    
                    file_size = os.path.getsize(filepath)
                    logger.info(f"✅ Captured {lottery_type}: {filename} ({file_size:,} bytes)")
                    captured_files.append((lottery_type, filepath))
                    
                except Exception as e:
                    logger.error(f"Failed to capture {lottery_type}: {str(e)}")
            
            browser.close()
            
    except Exception as e:
        logger.error(f"Screenshot capture system failed: {str(e)}")
        return []
    
    logger.info(f"Screenshot capture complete: {len(captured_files)}/6 successful")
    return captured_files

def process_with_ai(captured_files, logger):
    """Process screenshots with Google Gemini AI"""
    logger.info("Step 2: Starting AI processing with Google Gemini 2.5 Pro...")
    
    from app import app
    from ai_lottery_processor import CompleteLotteryProcessor
    
    new_results = []
    processed_files = []
    
    with app.app_context():
        processor = CompleteLotteryProcessor()
        
        for lottery_type, filepath in captured_files:
            try:
                logger.info(f"Processing {lottery_type} with AI: {os.path.basename(filepath)}")
                
                result = processor.process_single_image(filepath, lottery_type)
                
                if result and result.get('success'):
                    data = result.get('data', {})
                    confidence = data.get('confidence', 0)
                    
                    logger.info(f"AI extracted {lottery_type} - Draw {data.get('draw_number')} "
                              f"({data.get('draw_date')}) with {confidence}% confidence")
                    
                    # Try to save to database
                    try:
                        success = processor.save_to_database(data)
                        if success:
                            new_results.append({
                                'lottery_type': lottery_type,
                                'draw_number': data.get('draw_number'),
                                'draw_date': data.get('draw_date'),
                                'numbers': data.get('main_numbers'),
                                'confidence': confidence,
                                'filepath': filepath
                            })
                            logger.info(f"✅ NEW {lottery_type} result saved to database")
                        else:
                            logger.info(f"ℹ️ {lottery_type} result already exists (duplicate)")
                            
                        processed_files.append(filepath)
                        
                    except Exception as db_error:
                        logger.error(f"Database save failed for {lottery_type}: {str(db_error)}")
                        
                else:
                    logger.warning(f"No data extracted from {lottery_type}. Result: {result}")
                    
            except Exception as e:
                logger.error(f"AI processing failed for {lottery_type}: {str(e)}")
    
    return new_results, processed_files

def cleanup_old_files(processed_files, new_results, logger):
    """Clean up screenshots after successful AI processing"""
    logger.info("Step 3: Starting cleanup of processed screenshots...")
    
    # Always clean up processed files after AI extraction is complete
    cleanup_count = 0
    
    try:
        screenshot_dir = 'screenshots'
        
        # Remove all screenshots since we've extracted the data
        if os.path.exists(screenshot_dir):
            all_screenshots = glob.glob(os.path.join(screenshot_dir, '*.png'))
            
            for screenshot_file in all_screenshots:
                try:
                    os.remove(screenshot_file)
                    cleanup_count += 1
                    logger.info(f"Cleaned up: {os.path.basename(screenshot_file)}")
                except Exception as e:
                    logger.warning(f"Could not remove {screenshot_file}: {e}")
        
        # Clean up any temporary upload files
        upload_dir = 'uploads'
        if os.path.exists(upload_dir):
            old_uploads = glob.glob(os.path.join(upload_dir, '*.png'))
            old_uploads.extend(glob.glob(os.path.join(upload_dir, '*.jpg')))
            old_uploads.extend(glob.glob(os.path.join(upload_dir, '*.jpeg')))
            
            for upload_file in old_uploads:
                try:
                    # Only remove files older than 1 hour
                    file_age = time.time() - os.path.getmtime(upload_file)
                    if file_age > 3600:  # 1 hour
                        os.remove(upload_file)
                        cleanup_count += 1
                        logger.info(f"Cleaned up old upload: {os.path.basename(upload_file)}")
                except Exception as e:
                    logger.warning(f"Could not remove upload {upload_file}: {e}")
        
        # Clean up old log files (keep only last 5)
        log_files = glob.glob('automation_workflow*.log')
        if len(log_files) > 5:
            log_files.sort(key=os.path.getmtime, reverse=True)
            for old_log in log_files[5:]:
                try:
                    os.remove(old_log)
                    cleanup_count += 1
                    logger.info(f"Cleaned up old log: {os.path.basename(old_log)}")
                except Exception as e:
                    logger.warning(f"Failed to remove {old_log}: {str(e)}")
        
        logger.info(f"Cleanup complete: {cleanup_count} files removed")
        
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")

def run_complete_automation():
    """Run the complete automated lottery workflow with cleanup"""
    logger = setup_logging()
    
    logger.info("=== STARTING COMPLETE AUTOMATED LOTTERY WORKFLOW ===")
    start_time = datetime.now()
    
    try:
        # Step 1: Capture fresh screenshots
        logger.info("Step 1: Capturing fresh lottery screenshots...")
        captured_files = capture_fresh_screenshots(logger)
        
        if not captured_files:
            return {
                'success': False,
                'error': 'No screenshots captured',
                'message': 'Screenshot capture failed'
            }
        
        # Step 2: Process with AI and save to database
        logger.info("Step 2: Processing screenshots with Google Gemini AI...")
        new_results, processed_files = process_with_ai(captured_files, logger)
        
        # Step 3: Clean up old files after successful processing
        if new_results:
            logger.info("Step 3: Cleaning up old files after successful extraction...")
            cleanup_old_files(processed_files, new_results, logger)
        
        # Step 4: Summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("=== AUTOMATION WORKFLOW COMPLETE ===")
        logger.info(f"Duration: {duration:.1f} seconds")
        logger.info(f"Screenshots captured: {len(captured_files)}")
        logger.info(f"Files processed: {len(processed_files)}")
        logger.info(f"New results found: {len(new_results)}")
        
        if new_results:
            logger.info("🎯 NEW LOTTERY RESULTS DETECTED, SAVED, AND CLEANED UP!")
            for result in new_results:
                logger.info(f"   - {result['lottery_type']} Draw {result['draw_number']} "
                          f"({result['draw_date']}) - {result['confidence']}% confidence")
        else:
            logger.info("ℹ️ No new lottery results found (all current)")
            
        return {
            'success': True,
            'duration': duration,
            'screenshots_captured': len(captured_files),
            'files_processed': len(processed_files),
            'new_results': len(new_results),
            'results': new_results,
            'message': f"Captured {len(captured_files)} screenshots, found {len(new_results)} new results"
        }
        
    except Exception as e:
        logger.error(f"Automation workflow failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'message': f"Workflow failed: {str(e)}"
        }

if __name__ == "__main__":
    result = run_complete_automation()
    print(f"\n=== FINAL RESULT ===")
    print(f"Success: {result['success']}")
    print(f"Message: {result['message']}")
    
    if result['success']:
        sys.exit(0)
    else:
        sys.exit(1)