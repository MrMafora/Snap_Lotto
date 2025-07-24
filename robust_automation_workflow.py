#!/usr/bin/env python3
"""
Robust Automation Workflow - Based on Working screenshot_capture.py
Fixes the timeout issues by using proper wait conditions and anti-detection measures
"""

import os
import json
import glob
import time
import logging
import psycopg2
from datetime import datetime
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# South African Lottery URLs - confirmed working
LOTTERY_URLS = {
    'LOTTO': 'https://www.nationallottery.co.za/results/lotto',
    'LOTTO PLUS 1': 'https://www.nationallottery.co.za/results/lotto-plus-1-results',
    'LOTTO PLUS 2': 'https://www.nationallottery.co.za/results/lotto-plus-2-results',
    'POWERBALL': 'https://www.nationallottery.co.za/results/powerball',
    'POWERBALL PLUS': 'https://www.nationallottery.co.za/results/powerball-plus',
    'DAILY LOTTO': 'https://www.nationallottery.co.za/results/daily-lotto'
}

# Chromium path for Replit environment
CHROMIUM_PATH = "/nix/store/zi4f80l169xlmivz8vja8wlphq74qqk0-chromium-125.0.6422.141/bin/chromium"

def capture_screenshots_robust():
    """
    Robust screenshot capture based on working screenshot_capture.py approach
    Uses domcontentloaded instead of networkidle to avoid timeout issues
    """
    logger.info("🔧 Starting ROBUST screenshot capture (based on working approach)")
    
    captured_files = []
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Ensure screenshots directory exists
    os.makedirs('screenshots', exist_ok=True)
    
    try:
        with sync_playwright() as p:
            # Launch browser with anti-detection measures (from working code)
            browser = p.chromium.launch(
                executable_path=CHROMIUM_PATH,
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--window-size=1920,1080',
                    '--disable-blink-features=AutomationControlled',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
                    '--accept-lang=en-US,en;q=0.9',
                    '--disable-accelerated-2d-canvas',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--force-color-profile=srgb'
                ]
            )
            
            # Create context with enhanced settings (from working code)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='Africa/Johannesburg',
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
            )
            
            # Create page from context
            page = context.new_page()
            
            # Add stealth scripts before navigation (from working code)
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
                window.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'permissions', {
                    get: () => ({ query: () => Promise.resolve({ state: 'granted' }) })
                });
            """)
            
            for lottery_type, url in LOTTERY_URLS.items():
                try:
                    logger.info(f"📸 Capturing {lottery_type} from {url}")
                    
                    # CRITICAL FIX: Use domcontentloaded instead of networkidle
                    # This is what was working in screenshot_capture.py
                    try:
                        response = page.goto(url, wait_until='domcontentloaded', timeout=60000)
                        if response and response.status >= 400:
                            logger.warning(f"HTTP {response.status} response for {lottery_type}")
                    except Exception as nav_error:
                        logger.warning(f"Navigation issue for {lottery_type}: {nav_error}")
                        # Continue anyway - page might still be usable
                    
                    # Wait for content to load (from working code)
                    page.wait_for_timeout(3000)
                    
                    # Scroll to ensure full content loads (from working code)
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(1000)
                    page.evaluate("window.scrollTo(0, 0)")
                    
                    # Generate filename
                    safe_lottery_type = lottery_type.lower().replace(' ', '_').replace('+', '_plus')
                    filename = f"{timestamp}_{safe_lottery_type}.png"
                    filepath = os.path.join('screenshots', filename)
                    
                    # Take screenshot with full page
                    logger.info(f"📸 Taking screenshot: {filename}")
                    page.screenshot(path=filepath, full_page=True)
                    
                    # Get file size and verify
                    file_size = os.path.getsize(filepath)
                    logger.info(f"✅ Successfully captured {lottery_type}: {filename} ({file_size:,} bytes)")
                    
                    captured_files.append((lottery_type, filepath))
                    
                except Exception as e:
                    logger.error(f"❌ Failed to capture {lottery_type}: {str(e)}")
                    # Continue with other lottery types
                    continue
            
            browser.close()
            
    except Exception as e:
        logger.error(f"❌ Browser launch failed: {str(e)}")
        return []
    
    logger.info(f"📸 Robust screenshot capture complete: {len(captured_files)}/6 successful")
    
    # Only cleanup old files if we got at least half the captures
    if len(captured_files) >= 3:
        cleanup_old_screenshots(exclude_pattern=timestamp)
        logger.info("🧹 Old screenshots cleaned up after successful capture")
    
    return captured_files

def cleanup_old_screenshots(exclude_pattern=None):
    """Remove old screenshots but preserve recent captures"""
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

def process_with_ai_robust(captured_files):
    """
    Process screenshots with Google Gemini 2.5 Pro
    Focus on extracting fresh data (newer than July 22nd, 2025)
    """
    logger.info("🤖 Starting AI processing with Google Gemini 2.5 Pro")
    
    api_key = os.environ.get("GOOGLE_API_KEY_SNAP_LOTTERY")
    if not api_key:
        logger.error("❌ GOOGLE_API_KEY_SNAP_LOTTERY not found")
        return []
    
    # Import and configure Gemini
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-pro')
    except Exception as e:
        logger.error(f"❌ Failed to initialize Gemini: {e}")
        return []
    
    extracted_data = []
    
    for lottery_type, filepath in captured_files:
        try:
            logger.info(f"🔍 Processing {lottery_type}: {os.path.basename(filepath)}")
            
            # Read image
            with open(filepath, 'rb') as f:
                image_data = f.read()
            
            # Create comprehensive extraction prompt
            prompt = f"""
            You are analyzing a South African National Lottery screenshot for {lottery_type}.
            
            Extract ALL the following data with EXACT values from the image:
            
            **DRAW INFORMATION:**
            - Draw ID/Number (find the specific draw number)
            - Draw Date (convert to YYYY-MM-DD format)
            - Lottery Type ({lottery_type})
            
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
            - Next Jackpot (if shown)
            - Rollover Amount (if shown)
            - Total Sales (if shown)
            
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
                "next_jackpot": "R8,000,000.00",
                "rollover_amount": "R5,000,000.00",
                "total_sales": "R20,000,000.00",
                "extraction_confidence": 95
            }}
            
            CRITICAL: Only return data if the draw_date is newer than 2025-07-22 (we only want fresh data).
            CRITICAL: Extract ALL visible prize divisions, not just the first few.
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
                confidence = lottery_data.get('extraction_confidence', 0)
                
                if draw_date > '2025-07-22':
                    logger.info(f"✅ AI extracted fresh data: {lottery_type} Draw {lottery_data.get('draw_id')} ({draw_date}) - {confidence}% confidence")
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

def save_to_database_robust(extracted_data):
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
                # Check if this draw already exists in lottery_results table
                cursor.execute("""
                    SELECT COUNT(*) FROM lottery_results 
                    WHERE lottery_type = %s AND draw_number = %s
                """, (data.get('lottery_type'), data.get('draw_id')))
                
                if cursor.fetchone()[0] > 0:
                    logger.info(f"⏭️  Skipping duplicate: {data.get('lottery_type')} Draw {data.get('draw_id')}")
                    continue
                
                # Insert new lottery result into correct table with correct column names
                cursor.execute("""
                    INSERT INTO lottery_results (
                        lottery_type, draw_number, draw_date, main_numbers, bonus_numbers,
                        prize_divisions, next_jackpot, rollover_amount, total_sales,
                        created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    data.get('lottery_type'),
                    data.get('draw_id'),
                    data.get('draw_date'),
                    json.dumps(data.get('winning_numbers', [])),
                    json.dumps(data.get('bonus_numbers', [])),
                    json.dumps(data.get('prize_divisions', [])),
                    data.get('next_jackpot'),
                    data.get('rollover_amount'),
                    data.get('total_sales'),
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

def run_robust_automation_workflow():
    """
    Main function: Robust automation workflow that actually works
    Based on the working screenshot_capture.py approach
    """
    logger.info("🚀 Starting ROBUST Automation Workflow")
    logger.info("🔧 Using working screenshot approach (domcontentloaded + stealth)")
    
    start_time = time.time()
    
    # Step 1: Capture screenshots with robust approach
    logger.info("📸 Step 1: Capturing screenshots with robust approach...")
    captured_files = capture_screenshots_robust()
    
    if not captured_files:
        logger.error("❌ No screenshots captured - aborting workflow")
        return False
    
    # Step 2: Process with AI
    logger.info("🤖 Step 2: Processing screenshots with AI...")
    extracted_data = process_with_ai_robust(captured_files)
    
    if not extracted_data:
        logger.warning("⚠️  No fresh data extracted from AI processing")
        return False
    
    # Step 3: Save to database
    logger.info("💾 Step 3: Saving fresh data to database...")
    save_success = save_to_database_robust(extracted_data)
    
    # Step 4: Final cleanup (only processed screenshots)
    logger.info("🧹 Step 4: Final cleanup...")
    for lottery_type, screenshot_path in captured_files:
        try:
            os.remove(screenshot_path)
            logger.info(f"🗑️  Cleaned up processed screenshot: {os.path.basename(screenshot_path)}")
        except:
            pass
    
    elapsed_time = time.time() - start_time
    
    if save_success:
        logger.info(f"🎉 ROBUST Automation Workflow SUCCESSFUL!")
        logger.info(f"📊 Fresh lottery data captured and saved in {elapsed_time:.1f} seconds")
        logger.info(f"✅ Database now has data newer than July 22nd, 2025")
        return True
    else:
        logger.warning("⚠️  Workflow completed but no new data was saved")
        return False

if __name__ == "__main__":
    success = run_robust_automation_workflow()
    exit(0 if success else 1)