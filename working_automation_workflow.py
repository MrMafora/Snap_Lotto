#!/usr/bin/env python3
"""
Working Complete Automation Workflow
Captures screenshots → AI processing → Database save → Cleanup
"""

import os
import json
import glob
import time
import logging
import psycopg2
from datetime import datetime
from playwright.sync_api import sync_playwright
import google.generativeai as genai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def capture_fresh_screenshots():
    """Capture fresh screenshots of all 6 lottery types"""
    logger.info("Step 1: Capturing fresh lottery screenshots...")
    
    # Clear old screenshots first
    old_screenshots = glob.glob('screenshots/*.png')
    for old_file in old_screenshots:
        try:
            os.remove(old_file)
            logger.info(f"Cleaned up old screenshot: {os.path.basename(old_file)}")
        except:
            pass
    
    lottery_urls = {
        'lotto': 'https://www.nationallottery.co.za/results/lotto',
        'lotto_plus_1': 'https://www.nationallottery.co.za/results/lotto-plus-1-results',
        'lotto_plus_2': 'https://www.nationallottery.co.za/results/lotto-plus-2-results',
        'powerball': 'https://www.nationallottery.co.za/results/powerball',
        'powerball_plus': 'https://www.nationallottery.co.za/results/powerball-plus',
        'daily_lotto': 'https://www.nationallottery.co.za/results/daily-lotto'
    }
    
    captured_files = []
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={'width': 1920, 'height': 1080})
            
            for lottery_type, url in lottery_urls.items():
                try:
                    logger.info(f"Capturing {lottery_type} from {url}")
                    page.goto(url, wait_until='networkidle', timeout=30000)
                    page.wait_for_timeout(3000)
                    
                    filename = f"{timestamp}_{lottery_type}.png"
                    filepath = os.path.join('screenshots', filename)
                    page.screenshot(path=filepath, full_page=True)
                    
                    file_size = os.path.getsize(filepath)
                    logger.info(f"✅ Captured {lottery_type}: {filename} ({file_size:,} bytes)")
                    captured_files.append(filepath)
                    
                except Exception as e:
                    logger.error(f"Failed to capture {lottery_type}: {str(e)}")
            
            browser.close()
    except Exception as e:
        logger.error(f"Screenshot capture failed: {str(e)}")
        return []
    
    logger.info(f"Screenshot capture complete: {len(captured_files)}/6 successful")
    return captured_files

def extract_lottery_type(filename):
    """Extract lottery type from filename"""
    filename = filename.lower()
    if 'lotto_plus_1' in filename:
        return 'LOTTO PLUS 1'
    elif 'lotto_plus_2' in filename:
        return 'LOTTO PLUS 2' 
    elif 'lotto' in filename:
        return 'LOTTO'
    elif 'powerball_plus' in filename:
        return 'POWERBALL PLUS'
    elif 'powerball' in filename:
        return 'POWERBALL'
    elif 'daily_lotto' in filename:
        return 'DAILY LOTTO'
    return 'UNKNOWN'

def process_with_ai(captured_files):
    """Process screenshots with Google Gemini AI"""
    logger.info("Step 2: Processing screenshots with Google Gemini AI...")
    
    # Initialize Gemini
    api_key = os.environ.get("GOOGLE_API_KEY_SNAP_LOTTERY")
    if not api_key:
        logger.error("Missing GOOGLE_API_KEY_SNAP_LOTTERY")
        return [], []
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    new_results = []
    processed_files = []
    
    for filepath in captured_files:
        try:
            filename = os.path.basename(filepath)
            lottery_type = extract_lottery_type(filename)
            
            logger.info(f"Processing {lottery_type} with AI: {filename}")
            
            # Read image
            with open(filepath, "rb") as f:
                image_data = f.read()
            
            # AI extraction prompt
            prompt = f"""
            Extract lottery information from this South African {lottery_type} screenshot. 
            Return JSON with this exact format:
            {{
                "lottery_type": "{lottery_type}",
                "draw_number": 2560,
                "draw_date": "2025-07-22",
                "main_numbers": [1,2,3,4,5,6],
                "bonus_numbers": [7],
                "confidence": 95
            }}
            """
            
            # Call Gemini
            response = model.generate_content([prompt, {"mime_type": "image/png", "data": image_data}])
            
            # Parse JSON response
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith('```'):
                response_text = response_text[3:-3].strip()
            
            data = json.loads(response_text)
            confidence = data.get('confidence', 0)
            
            logger.info(f"AI extracted {lottery_type} - Draw {data.get('draw_number')} "
                      f"({data.get('draw_date')}) with {confidence}% confidence")
            
            # Save to database
            try:
                db_url = os.environ.get("DATABASE_URL")
                conn = psycopg2.connect(db_url)
                cur = conn.cursor()
                
                # Check if already exists
                cur.execute("""
                    SELECT id FROM lottery_results 
                    WHERE lottery_type = %s AND draw_number = %s
                """, (data['lottery_type'], data['draw_number']))
                
                if cur.fetchone():
                    logger.info(f"ℹ️ {lottery_type} result already exists (duplicate)")
                else:
                    # Insert new record
                    cur.execute("""
                        INSERT INTO lottery_results (
                            lottery_type, draw_number, draw_date, main_numbers, 
                            bonus_numbers, created_at
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        data['lottery_type'],
                        data['draw_number'], 
                        data['draw_date'],
                        json.dumps(data['main_numbers']),
                        json.dumps(data.get('bonus_numbers', [])),
                        datetime.now()
                    ))
                    
                    record_id = cur.fetchone()[0]
                    conn.commit()
                    
                    new_results.append({
                        'lottery_type': lottery_type,
                        'draw_number': data.get('draw_number'),
                        'draw_date': data.get('draw_date'),
                        'numbers': data.get('main_numbers'),
                        'confidence': confidence,
                        'record_id': record_id
                    })
                    logger.info(f"✅ NEW {lottery_type} result saved to database (ID: {record_id})")
                
                conn.close()
                processed_files.append(filepath)
                    
            except Exception as db_error:
                logger.error(f"Database save failed for {lottery_type}: {str(db_error)}")
                
        except Exception as e:
            logger.error(f"AI processing failed for {lottery_type}: {str(e)}")
    
    return new_results, processed_files

def cleanup_files():
    """Clean up screenshots after processing"""
    logger.info("Step 3: Cleaning up screenshots...")
    
    cleanup_count = 0
    screenshots = glob.glob('screenshots/*.png')
    
    for screenshot in screenshots:
        try:
            os.remove(screenshot)
            cleanup_count += 1
            logger.info(f"Cleaned up: {os.path.basename(screenshot)}")
        except Exception as e:
            logger.warning(f"Could not remove {screenshot}: {e}")
    
    logger.info(f"Cleanup complete: {cleanup_count} files removed")

def run_complete_workflow():
    """Run complete automated lottery workflow"""
    logger.info("=== STARTING COMPLETE AUTOMATED LOTTERY WORKFLOW ===")
    start_time = datetime.now()
    
    try:
        # Step 1: Capture screenshots
        captured_files = capture_fresh_screenshots()
        if not captured_files:
            return {
                'success': False,
                'message': 'No screenshots captured'
            }
        
        # Step 2: AI processing
        new_results, processed_files = process_with_ai(captured_files)
        
        # Step 3: Cleanup
        cleanup_files()
        
        # Summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info("=== AUTOMATION WORKFLOW COMPLETE ===")
        logger.info(f"Duration: {duration:.1f} seconds")
        logger.info(f"Screenshots captured: {len(captured_files)}")
        logger.info(f"Files processed: {len(processed_files)}")
        logger.info(f"New results found: {len(new_results)}")
        
        if new_results:
            logger.info("🎯 NEW LOTTERY RESULTS DETECTED AND SAVED!")
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
        logger.error(f"Workflow failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'message': f"Workflow failed: {str(e)}"
        }

if __name__ == "__main__":
    result = run_complete_workflow()
    print(f"\n=== FINAL RESULT ===")
    print(f"Success: {result['success']}")
    print(f"Message: {result['message']}")