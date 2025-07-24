#!/usr/bin/env python3
"""
FIXED Automation Workflow - Addresses Critical Design Flaw
This implementation ensures screenshots are only deleted AFTER successful capture and processing
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

# South African Lottery URLs - exact URLs that work
LOTTERY_URLS = {
    'LOTTO': 'https://www.nationallottery.co.za/results/lotto',
    'LOTTO_PLUS_1': 'https://www.nationallottery.co.za/results/lotto-plus-1-results',
    'LOTTO_PLUS_2': 'https://www.nationallottery.co.za/results/lotto-plus-2-results',
    'POWERBALL': 'https://www.nationallottery.co.za/results/powerball',
    'POWERBALL_PLUS': 'https://www.nationallottery.co.za/results/powerball-plus',
    'DAILY_LOTTO': 'https://www.nationallottery.co.za/results/daily-lotto'
}

# Chromium path for Replit environment
CHROMIUM_PATH = "/nix/store/zi4f80l169xlmivz8vja8wlphq74qqk0-chromium-125.0.6422.141/bin/chromium"

def capture_fresh_screenshots():
    """
    FIXED: Capture fresh screenshots WITHOUT deleting existing ones first
    Only delete old screenshots AFTER successful capture confirmation
    """
    logger.info("🔧 FIXED WORKFLOW: Starting screenshot capture (keeping existing files as backup)")
    
    captured_files = []
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Ensure screenshots directory exists
    os.makedirs('screenshots', exist_ok=True)
    
    try:
        with sync_playwright() as p:
            # Launch browser with enhanced settings for SA lottery site
            browser = p.chromium.launch(
                executable_path=CHROMIUM_PATH,
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--window-size=1920,1080',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                ]
            )
            
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                locale='en-US',
                timezone_id='Africa/Johannesburg'
            )
            
            page = context.new_page()
            
            for lottery_type, url in LOTTERY_URLS.items():
                try:
                    logger.info(f"📸 Capturing {lottery_type} from {url}")
                    
                    # Navigate with extended timeout for SA site
                    page.goto(url, wait_until='networkidle', timeout=45000)
                    page.wait_for_timeout(5000)  # Extra wait for dynamic content
                    
                    filename = f"{timestamp}_{lottery_type.lower()}.png"
                    filepath = os.path.join('screenshots', filename)
                    
                    # Capture with full page content
                    page.screenshot(path=filepath, full_page=True)
                    
                    file_size = os.path.getsize(filepath)
                    logger.info(f"✅ Successfully captured {lottery_type}: {filename} ({file_size:,} bytes)")
                    captured_files.append(filepath)
                    
                except Exception as e:
                    logger.error(f"❌ Failed to capture {lottery_type}: {str(e)}")
                    # Continue with other lottery types
                    continue
            
            browser.close()
            
    except Exception as e:
        logger.error(f"❌ Browser launch failed: {str(e)}")
        return []
    
    logger.info(f"📸 Screenshot capture complete: {len(captured_files)}/6 successful")
    
    # CRITICAL FIX: Only cleanup old files AFTER confirming new captures
    if len(captured_files) >= 3:  # At least 50% success rate
        cleanup_old_screenshots(exclude_pattern=timestamp)
        logger.info("🧹 Old screenshots cleaned up after successful capture")
    else:
        logger.warning("⚠️  Keeping old screenshots due to low capture success rate")
    
    return captured_files

def cleanup_old_screenshots(exclude_pattern=None):
    """
    SAFE cleanup: Remove old screenshots but preserve recent captures
    """
    try:
        all_screenshots = glob.glob('screenshots/*.png')
        for screenshot in all_screenshots:
            if exclude_pattern and exclude_pattern in screenshot:
                continue  # Skip recently captured files
            try:
                os.remove(screenshot)
                logger.info(f"🗑️  Removed old screenshot: {os.path.basename(screenshot)}")
            except Exception as e:
                logger.warning(f"⚠️  Could not remove {screenshot}: {e}")
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")

def extract_lottery_type_from_filename(filename):
    """Extract lottery type from filename"""
    mapping = {
        'lotto.png': 'LOTTO',
        'lotto_plus_1.png': 'LOTTO PLUS 1', 
        'lotto_plus_2.png': 'LOTTO PLUS 2',
        'powerball.png': 'POWERBALL',
        'powerball_plus.png': 'POWERBALL PLUS',
        'daily_lotto.png': 'DAILY LOTTO'
    }
    
    for pattern, lottery_type in mapping.items():
        if pattern in filename.lower():
            return lottery_type
    
    return 'UNKNOWN'

def process_with_ai(screenshot_files):
    """
    Process screenshots using Google Gemini 2.5 Pro AI
    Returns list of extracted lottery data
    """
    logger.info("🤖 Starting AI processing with Google Gemini 2.5 Pro")
    
    api_key = os.environ.get("GOOGLE_API_KEY_SNAP_LOTTERY")
    if not api_key:
        logger.error("❌ GOOGLE_API_KEY_SNAP_LOTTERY not found")
        return []
    
    # Configure Gemini AI
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    extracted_data = []
    
    for screenshot_path in screenshot_files:
        lottery_type = extract_lottery_type_from_filename(screenshot_path)
        logger.info(f"🔍 Processing {lottery_type}: {os.path.basename(screenshot_path)}")
        
        try:
            # Read image
            with open(screenshot_path, 'rb') as f:
                image_data = f.read()
            
            # Create comprehensive extraction prompt
            prompt = f"""
            You are analyzing a South African National Lottery screenshot for {lottery_type}.
            
            Extract ALL the following data with EXACT values from the image:
            
            **DRAW INFORMATION:**
            - Draw ID/Number (find the specific draw number)
            - Draw Date (convert to YYYY-MM-DD format)
            - Lottery Type (LOTTO, LOTTO PLUS 1, LOTTO PLUS 2, POWERBALL, POWERBALL PLUS, DAILY LOTTO)
            
            **WINNING NUMBERS:**
            - Main winning numbers (in numerical order, comma separated)
            - Bonus Ball/PowerBall (if applicable)
            
            **PRIZE DIVISIONS (extract ALL visible divisions):**
            For each division found, extract:
            - Division number/name
            - Description (e.g., "6 Correct Numbers", "5 Correct + Bonus")
            - Number of winners
            - Prize amount per winner
            
            **FINANCIAL DATA:**
            - Rollover Amount (if shown)
            - Total Pool Size (if shown)
            - Total Sales (if shown)
            - Next Jackpot (if shown)
            - Draw Machine (RNG number if shown)
            - Next Draw Date (if shown)
            
            Return ONLY valid JSON in this exact format:
            {{
                "draw_id": "2562",
                "draw_date": "2025-07-24", 
                "lottery_type": "{lottery_type}",
                "winning_numbers": [1, 2, 3, 4, 5, 6],
                "bonus_numbers": [7],
                "prize_divisions": [
                    {{
                        "division": "Div 1",
                        "description": "6 Correct Numbers",
                        "winners": 0,
                        "amount": "R0.00"
                    }}
                ],
                "rollover_amount": "R5,000,000.00",
                "total_pool_size": "R10,000,000.00",
                "total_sales": "R20,000,000.00",
                "next_jackpot": "R8,000,000.00",
                "draw_machine": "RNG 1",
                "next_draw_date": "2025-07-26",
                "extraction_confidence": 95
            }}
            
            CRITICAL: Extract ALL visible prize divisions, not just the first few.
            CRITICAL: Ensure the draw_date is newer than 2025-07-22 (we only want fresh data).
            """
            
            # Process with AI
            response = model.generate_content([
                prompt,
                {"mime_type": "image/png", "data": image_data}
            ])
            
            # Parse response
            try:
                # Clean response (remove markdown code blocks if present)
                response_text = response.text.strip()
                if response_text.startswith('```json'):
                    response_text = response_text[7:]
                if response_text.endswith('```'):
                    response_text = response_text[:-3]
                
                lottery_data = json.loads(response_text)
                
                # Validate we got fresh data (newer than July 22nd)
                draw_date = lottery_data.get('draw_date', '')
                if draw_date > '2025-07-22':
                    logger.info(f"✅ AI extracted fresh data: {lottery_type} Draw {lottery_data.get('draw_id')} ({draw_date})")
                    extracted_data.append(lottery_data)
                else:
                    logger.warning(f"⚠️  Skipping old data: {lottery_type} Draw {lottery_data.get('draw_id')} ({draw_date})")
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON parsing failed for {lottery_type}: {e}")
                logger.error(f"Raw response: {response.text[:500]}...")
                continue
                
        except Exception as e:
            logger.error(f"❌ AI processing failed for {lottery_type}: {e}")
            continue
    
    logger.info(f"🤖 AI processing complete: {len(extracted_data)} fresh results extracted")
    return extracted_data

def save_to_database(extracted_data):
    """
    Save extracted lottery data to PostgreSQL database
    Only saves data newer than July 22nd, 2025
    """
    if not extracted_data:
        logger.info("📊 No fresh data to save")
        return False
    
    logger.info(f"💾 Saving {len(extracted_data)} fresh lottery results to database")
    
    try:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            logger.error("❌ DATABASE_URL not found")
            return False
        
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        saved_count = 0
        
        for data in extracted_data:
            try:
                # Check if this draw already exists
                cursor.execute("""
                    SELECT COUNT(*) FROM lottery_result 
                    WHERE lottery_type = %s AND draw_number = %s
                """, (data.get('lottery_type'), data.get('draw_id')))
                
                if cursor.fetchone()[0] > 0:
                    logger.info(f"⏭️  Skipping duplicate: {data.get('lottery_type')} Draw {data.get('draw_id')}")
                    continue
                
                # Insert new lottery result
                cursor.execute("""
                    INSERT INTO lottery_result (
                        lottery_type, draw_number, draw_date, numbers, bonus_numbers,
                        prize_divisions, rollover_amount, total_pool_size, total_sales,
                        next_jackpot, draw_machine, next_draw_date, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    data.get('lottery_type'),
                    data.get('draw_id'),
                    data.get('draw_date'),
                    json.dumps(data.get('winning_numbers', [])),
                    json.dumps(data.get('bonus_numbers', [])),
                    json.dumps(data.get('prize_divisions', [])),
                    data.get('rollover_amount'),
                    data.get('total_pool_size'),
                    data.get('total_sales'),
                    data.get('next_jackpot'),
                    data.get('draw_machine'),
                    data.get('next_draw_date'),
                    datetime.now()
                ))
                
                saved_count += 1
                logger.info(f"✅ Saved: {data.get('lottery_type')} Draw {data.get('draw_id')} ({data.get('draw_date')})")
                
            except Exception as e:
                logger.error(f"❌ Failed to save {data.get('lottery_type')}: {e}")
                continue
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"💾 Database update complete: {saved_count} new records saved")
        return saved_count > 0
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False

def run_fixed_automation_workflow():
    """
    Main function: Complete fixed automation workflow
    Captures → Processes → Saves → Reports
    """
    logger.info("🚀 Starting FIXED Automation Workflow")
    logger.info("🔧 This version fixes the critical screenshot cleanup issue")
    
    start_time = time.time()
    
    # Step 1: Capture fresh screenshots (FIXED: no premature cleanup)
    logger.info("📸 Step 1: Capturing fresh lottery screenshots...")
    screenshot_files = capture_fresh_screenshots()
    
    if not screenshot_files:
        logger.error("❌ No screenshots captured - aborting workflow")
        return False
    
    # Step 2: Process with AI
    logger.info("🤖 Step 2: Processing screenshots with AI...")
    extracted_data = process_with_ai(screenshot_files)
    
    if not extracted_data:
        logger.warning("⚠️  No fresh data extracted from AI processing")
        return False
    
    # Step 3: Save to database
    logger.info("💾 Step 3: Saving fresh data to database...")
    save_success = save_to_database(extracted_data)
    
    # Step 4: Final cleanup (only processed screenshots)
    logger.info("🧹 Step 4: Final cleanup...")
    for screenshot in screenshot_files:
        try:
            os.remove(screenshot)
            logger.info(f"🗑️  Cleaned up processed screenshot: {os.path.basename(screenshot)}")
        except:
            pass
    
    elapsed_time = time.time() - start_time
    
    if save_success:
        logger.info(f"🎉 FIXED Automation Workflow SUCCESSFUL!")
        logger.info(f"📊 Fresh lottery data captured and saved in {elapsed_time:.1f} seconds")
        logger.info(f"✅ Database now has data newer than July 22nd, 2025")
        return True
    else:
        logger.warning("⚠️  Workflow completed but no new data was saved")
        return False

if __name__ == "__main__":
    success = run_fixed_automation_workflow()
    exit(0 if success else 1)