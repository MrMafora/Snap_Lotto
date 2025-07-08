#!/usr/bin/env python3
"""
Capture fresh screenshots and extract authentic lottery data using Gemini 2.5 Pro
"""

import os
import logging
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from google import genai
from google.genai import types
import json
from models import db, LotteryResult
from main import app
from cache_manager import cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def capture_lottery_screenshot(lottery_type, url):
    """Capture a single lottery screenshot"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        try:
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state('networkidle', timeout=30000)
            await asyncio.sleep(2)  # Extra wait for dynamic content
            
            # Take screenshot
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{lottery_type.lower().replace(' ', '_')}.png"
            filepath = os.path.join('screenshots', filename)
            
            await page.screenshot(path=filepath, full_page=False)
            logger.info(f"Captured {lottery_type}: {filename}")
            
            await browser.close()
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to capture {lottery_type}: {e}")
            await browser.close()
            return None

def extract_with_gemini(image_path, lottery_type):
    """Extract lottery data using Gemini 2.5 Pro"""
    
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        logger.error("GEMINI_API_KEY not found")
        return None
    
    client = genai.Client(api_key=api_key)
    
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    # Tailored prompts for each lottery type
    if lottery_type == 'DAILY LOTTO':
        prompt = """Extract the Daily Lotto results from this South African lottery screenshot.
        
        Return a JSON object with:
        - draw_number: The draw number (4 digits)
        - draw_date: The draw date in YYYY-MM-DD format
        - main_numbers: Array of 5 winning numbers
        - divisions: Array of 4 prize divisions with division number, winners count, and prize amount
        
        Example format:
        {
            "draw_number": 4524,
            "draw_date": "2025-07-08",
            "main_numbers": [1, 2, 3, 4, 5],
            "divisions": [
                {"division": 1, "winners": 0, "prize": "R100,000"},
                {"division": 2, "winners": 10, "prize": "R1,500"},
                {"division": 3, "winners": 100, "prize": "R200"},
                {"division": 4, "winners": 1000, "prize": "R20"}
            ]
        }"""
    elif 'POWERBALL' in lottery_type:
        prompt = f"""Extract the {lottery_type} results from this South African lottery screenshot.
        
        Return a JSON object with:
        - draw_number: The draw number (4 digits)
        - draw_date: The draw date in YYYY-MM-DD format
        - main_numbers: Array of 5 main winning numbers
        - powerball: The single powerball number
        - divisions: Array of 9 prize divisions
        
        Example format:
        {{
            "draw_number": 1631,
            "draw_date": "2025-07-08",
            "main_numbers": [1, 2, 3, 4, 5],
            "powerball": 10,
            "divisions": [
                {{"division": 1, "winners": 0, "prize": "R50,000,000"}},
                ... (9 divisions total)
            ]
        }}"""
    else:  # LOTTO types
        prompt = f"""Extract the {lottery_type} results from this South African lottery screenshot.
        
        Return a JSON object with:
        - draw_number: The draw number (4 digits)
        - draw_date: The draw date in YYYY-MM-DD format
        - main_numbers: Array of 6 main winning numbers
        - bonus_number: The single bonus ball number
        - divisions: Array of 8 prize divisions
        
        Example format:
        {{
            "draw_number": 2556,
            "draw_date": "2025-07-05",
            "main_numbers": [1, 2, 3, 4, 5, 6],
            "bonus_number": 7,
            "divisions": [
                {{"division": 1, "winners": 0, "prize": "R10,000,000"}},
                ... (8 divisions total)
            ]
        }}"""
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
                prompt
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        if response and response.text:
            result = json.loads(response.text)
            logger.info(f"Extracted {lottery_type}: Draw {result.get('draw_number')}")
            return result
            
    except Exception as e:
        logger.error(f"Gemini extraction failed for {lottery_type}: {e}")
    
    return None

def save_to_database(lottery_type, data):
    """Save extracted data to database"""
    
    with app.app_context():
        try:
            # Prepare data
            main_numbers = data['main_numbers']
            bonus_numbers = []
            if 'powerball' in data:
                bonus_numbers = [data['powerball']]
            elif 'bonus_number' in data:
                bonus_numbers = [data['bonus_number']]
            
            # Check if exists
            existing = db.session.query(LotteryResult).filter_by(
                lottery_type=lottery_type,
                draw_number=data['draw_number']
            ).first()
            
            if existing:
                # Update
                existing.draw_date = datetime.strptime(data['draw_date'], '%Y-%m-%d').date()
                existing.main_numbers = main_numbers
                existing.bonus_numbers = bonus_numbers
                existing.divisions = json.dumps(data.get('divisions', []))
                logger.info(f"Updated {lottery_type} draw {data['draw_number']}")
            else:
                # Create new
                new_result = LotteryResult(
                    lottery_type=lottery_type,
                    draw_number=data['draw_number'],
                    draw_date=datetime.strptime(data['draw_date'], '%Y-%m-%d').date(),
                    main_numbers=main_numbers,
                    bonus_numbers=bonus_numbers,
                    divisions=json.dumps(data.get('divisions', []))
                )
                db.session.add(new_result)
                logger.info(f"Added {lottery_type} draw {data['draw_number']}")
            
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Database save failed: {e}")
            db.session.rollback()
            return False

async def main():
    """Main function to capture and extract lottery data"""
    
    # Define lotteries to process
    lotteries = [
        ('LOTTO PLUS 2', 'https://www.nationallottery.co.za/results/lotto-plus-2-results'),
        ('POWERBALL', 'https://www.nationallottery.co.za/results/powerball'),
        ('POWERBALL PLUS', 'https://www.nationallottery.co.za/results/powerball-plus'),
        ('DAILY LOTTO', 'https://www.nationallottery.co.za/results/daily-lotto')
    ]
    
    success_count = 0
    
    for lottery_type, url in lotteries:
        logger.info(f"\nProcessing {lottery_type}...")
        
        # Capture screenshot
        screenshot_path = await capture_lottery_screenshot(lottery_type, url)
        if not screenshot_path:
            continue
        
        # Extract data
        data = extract_with_gemini(screenshot_path, lottery_type)
        if not data:
            continue
        
        # Save to database
        if save_to_database(lottery_type, data):
            success_count += 1
    
    # Clear cache
    cache.clear()
    logger.info(f"\nCompleted: {success_count}/{len(lotteries)} successful")
    logger.info("Cache cleared - fresh data will load")

if __name__ == "__main__":
    logger.info("=== CAPTURE AND EXTRACT AUTHENTIC DATA ===")
    asyncio.run(main())