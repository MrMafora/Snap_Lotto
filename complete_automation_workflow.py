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
    logger.info("Starting fresh screenshot capture...")
    
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
    logger.info("Starting AI processing...")
    
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
                
                if result and 'extracted_data' in result:
                    data = result['extracted_data']
                    confidence = result.get('confidence', 0)
                    
                    logger.info(f"AI extracted {lottery_type} - Draw {data.get('draw_number')} "
                              f"({data.get('draw_date')}) with {confidence}% confidence")
                    
                    # Try to save to database
                    try:
                        success = processor.save_to_database(data, lottery_type)
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
                    logger.warning(f"No data extracted from {lottery_type}")
                    
            except Exception as e:
                logger.error(f"AI processing failed for {lottery_type}: {str(e)}")
    
    return new_results, processed_files

def cleanup_old_files(processed_files, new_results, logger):
    """Clean up old screenshots and files after successful processing"""
    logger.info("Starting cleanup of old files...")
    
    # Only clean up if we have new results
    if not new_results:
        logger.info("No new results found - skipping cleanup")
        return
    
    cleanup_count = 0
    
    try:
        # Clean up old screenshots (keep only today's newest ones)
        screenshot_dir = 'screenshots'
        today = datetime.now().strftime('%Y%m%d')
        
        # Get all screenshot files
        all_screenshots = glob.glob(os.path.join(screenshot_dir, '*.png'))
        
        # Group by lottery type and keep only the newest for each type
        lottery_types = ['lotto', 'lotto_plus_1', 'lotto_plus_2', 'powerball', 'powerball_plus', 'daily_lotto']
        
        for lottery_type in lottery_types:
            # Find all files for this lottery type
            type_files = [f for f in all_screenshots if lottery_type in os.path.basename(f)]
            
            if len(type_files) > 1:
                # Sort by modification time, keep newest
                type_files.sort(key=os.path.getmtime, reverse=True)
                
                # Delete older files (keep only the most recent)
                for old_file in type_files[1:]:
                    try:
                        os.remove(old_file)
                        cleanup_count += 1
                        logger.info(f"Cleaned up old screenshot: {os.path.basename(old_file)}")
                    except Exception as e:
                        logger.warning(f"Failed to remove {old_file}: {str(e)}")
        
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