#!/usr/bin/env python3
"""
Improved Automated Lottery Workflow System
Safer approach that preserves data during network issues
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

def test_network_connectivity():
    """Test if SA National Lottery website is accessible"""
    try:
        import requests
        response = requests.get('https://www.nationallottery.co.za', timeout=10)
        return response.status_code == 200
    except:
        return False

def capture_fresh_screenshots_safe(logger):
    """Safely capture fresh screenshots with fallback strategy"""
    logger.info("Step 1: Starting safe screenshot capture...")
    
    screenshots_dir = 'screenshots'
    os.makedirs(screenshots_dir, exist_ok=True)
    
    # Check existing screenshots first
    existing_files = glob.glob(os.path.join(screenshots_dir, '*.png'))
    logger.info(f"Found {len(existing_files)} existing screenshots")
    
    # Test network connectivity before attempting capture
    if not test_network_connectivity():
        logger.warning("Network connectivity issue detected - using existing screenshots if available")
        if existing_files:
            logger.info(f"Using {len(existing_files)} existing screenshots due to network issues")
            return [(f"EXISTING_{i}", f) for i, f in enumerate(existing_files)]
        else:
            logger.error("No existing screenshots and network unavailable")
            return []
    
    # Lottery URLs and types
    lottery_urls = {
        'LOTTO': 'https://www.nationallottery.co.za/results/lotto',
        'LOTTO PLUS 1': 'https://www.nationallottery.co.za/results/lotto-plus-1-results',
        'LOTTO PLUS 2': 'https://www.nationallottery.co.za/results/lotto-plus-2-results',
        'POWERBALL': 'https://www.nationallottery.co.za/results/powerball',
        'POWERBALL PLUS': 'https://www.nationallottery.co.za/results/powerball-plus',
        'DAILY LOTTO': 'https://www.nationallottery.co.za/results/daily-lotto'
    }
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    captured_files = []
    temp_files = []  # Track temporary files for cleanup on failure
    
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
                    
                    # Navigate with shorter timeout for faster failure detection
                    page.goto(url, wait_until='networkidle', timeout=15000)
                    page.wait_for_timeout(2000)  # Shorter wait
                    
                    # Generate filename
                    safe_name = lottery_type.lower().replace(' ', '_').replace('+', '_plus')
                    filename = f"{timestamp}_{safe_name}.png"
                    filepath = os.path.join(screenshots_dir, filename)
                    
                    # Take screenshot
                    page.screenshot(path=filepath, full_page=True)
                    
                    file_size = os.path.getsize(filepath)
                    logger.info(f"✅ Captured {lottery_type}: {filename} ({file_size:,} bytes)")
                    captured_files.append((lottery_type, filepath))
                    temp_files.append(filepath)
                    
                except Exception as e:
                    logger.error(f"Failed to capture {lottery_type}: {str(e)}")
            
            browser.close()
            
    except Exception as e:
        logger.error(f"Screenshot capture system failed: {str(e)}")
        # Clean up partial captures on failure
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
        
        # Fall back to existing screenshots if available
        if existing_files:
            logger.info(f"Falling back to {len(existing_files)} existing screenshots")
            return [(f"EXISTING_{i}", f) for i, f in enumerate(existing_files)]
        return []
    
    # Only clean up old screenshots if we successfully captured new ones
    if captured_files and len(captured_files) >= 3:  # At least half successful
        logger.info("Successfully captured new screenshots - cleaning up old ones")
        for old_file in existing_files:
            try:
                os.remove(old_file)
                logger.info(f"Removed old screenshot: {os.path.basename(old_file)}")
            except Exception as e:
                logger.warning(f"Could not remove old file {old_file}: {e}")
    
    logger.info(f"Screenshot capture complete: {len(captured_files)}/6 successful")
    return captured_files

def process_with_ai_safe(captured_files, logger):
    """Safely process screenshots with Google Gemini AI"""
    logger.info("Step 2: Starting AI processing with Google Gemini 2.5 Pro...")
    
    if not captured_files:
        logger.error("No screenshots available for AI processing")
        return [], []
    
    from app import app
    from ai_lottery_processor import CompleteLotteryProcessor
    
    new_results = []
    processed_files = []
    
    try:
        with app.app_context():
            processor = CompleteLotteryProcessor()
            
            for lottery_type, filepath in captured_files:
                try:
                    logger.info(f"Processing {lottery_type} with AI: {os.path.basename(filepath)}")
                    
                    # Process the screenshot
                    results = processor.process_screenshot(filepath, lottery_type)
                    
                    if results and results.get('success'):
                        new_results.extend(results.get('new_records', []))
                        processed_files.append(filepath)
                        logger.info(f"✅ Successfully processed {lottery_type}")
                    else:
                        logger.warning(f"AI processing failed for {lottery_type}")
                        
                except Exception as e:
                    logger.error(f"Error processing {lottery_type}: {str(e)}")
            
    except Exception as e:
        logger.error(f"AI processing system failed: {str(e)}")
    
    logger.info(f"AI processing complete: {len(processed_files)} files processed, {len(new_results)} new results")
    return new_results, processed_files

def run_improved_automation():
    """Run the improved automated lottery workflow"""
    logger = setup_logging()
    
    logger.info("=== STARTING IMPROVED AUTOMATED LOTTERY WORKFLOW ===")
    start_time = datetime.now()
    
    try:
        # Step 1: Safely capture screenshots (or use existing ones)
        logger.info("Step 1: Safely capturing lottery screenshots...")
        captured_files = capture_fresh_screenshots_safe(logger)
        
        if not captured_files:
            return {
                'success': False,
                'error': 'No screenshots available for processing',
                'message': 'No screenshots captured and no existing screenshots found'
            }
        
        # Step 2: Process with AI and save to database
        logger.info("Step 2: Processing screenshots with Google Gemini AI...")
        new_results, processed_files = process_with_ai_safe(captured_files, logger)
        
        # Step 3: Summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("=== IMPROVED AUTOMATION WORKFLOW COMPLETE ===")
        logger.info(f"Duration: {duration:.1f} seconds")
        logger.info(f"Screenshots available: {len(captured_files)}")
        logger.info(f"Files processed: {len(processed_files)}")
        logger.info(f"New results found: {len(new_results)}")
        
        if new_results:
            logger.info("🎯 NEW LOTTERY RESULTS DETECTED AND SAVED!")
            for result in new_results:
                logger.info(f"   - {result.get('lottery_type', 'Unknown')} Draw {result.get('draw_number', 'N/A')} "
                          f"({result.get('draw_date', 'N/A')})")
        else:
            logger.info("ℹ️ No new lottery results found (all current)")
            
        return {
            'success': True,
            'duration': duration,
            'screenshots_available': len(captured_files),
            'files_processed': len(processed_files),
            'new_results': len(new_results),
            'results': new_results,
            'message': f"Processed {len(captured_files)} screenshots, found {len(new_results)} new results"
        }
        
    except Exception as e:
        logger.error(f"Improved automation workflow failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'message': f"Workflow failed: {str(e)}"
        }

if __name__ == "__main__":
    result = run_improved_automation()
    print(f"Workflow result: {result}")