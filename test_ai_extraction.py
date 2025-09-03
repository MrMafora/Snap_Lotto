#!/usr/bin/env python3
"""
Test Google Gemini AI extraction on captured lottery screenshots
"""

import os
import logging
from pathlib import Path
from google import genai
from google.genai import types
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_gemini_extraction():
    """Test Gemini extraction on a real captured screenshot"""
    
    # Initialize Gemini client
    api_key = os.environ.get("GOOGLE_API_KEY_SNAP_LOTTERY")
    if not api_key:
        logger.error("❌ GOOGLE_API_KEY_SNAP_LOTTERY not found in environment")
        return False
    
    client = genai.Client(api_key=api_key)
    
    # Find the latest screenshot
    screenshots_dir = Path("screenshots")
    screenshot_files = list(screenshots_dir.glob("*.png"))
    
    if not screenshot_files:
        logger.error("❌ No screenshot files found")
        return False
    
    # Use the test_capture.png which has real lottery data
    test_file = screenshots_dir / "test_capture.png"
    if test_file.exists():
        latest_screenshot = test_file
        logger.info(f"📸 Testing with working screenshot: {latest_screenshot.name}")
    else:
        # Fallback to most recent file
        latest_screenshot = max(screenshot_files, key=lambda x: x.stat().st_mtime)
        logger.info(f"📸 Testing with: {latest_screenshot.name}")
    
    # Determine lottery type from filename
    filename = latest_screenshot.name
    if "lotto_plus_1" in filename:
        lottery_type = "LOTTO PLUS 1"
    elif "lotto_plus_2" in filename:
        lottery_type = "LOTTO PLUS 2"
    elif "powerball_plus" in filename:
        lottery_type = "POWERBALL PLUS"
    elif "powerball" in filename:
        lottery_type = "POWERBALL"
    elif "daily_lotto" in filename:
        lottery_type = "DAILY LOTTO"
    elif "lotto" in filename:
        lottery_type = "LOTTO"
    else:
        lottery_type = "UNKNOWN"
    
    logger.info(f"🎯 Detected lottery type: {lottery_type}")
    
    # Prepare extraction prompt
    prompt = f"""
    You are analyzing a South African National Lottery website screenshot.
    I can see lottery numbers displayed on the page. Please extract ALL visible lottery information in JSON format:

    {{
        "lottery_type": "determine the lottery type from context",
        "draw_number": "extract the draw number if visible",
        "draw_date": "extract any date information (YYYY-MM-DD format)",
        "main_numbers": [extract ANY lottery numbers you can see displayed on the page],
        "bonus_numbers": [extract any bonus/powerball numbers],
        "jackpot_amount": "extract any jackpot amounts (R84 MILLION, etc.)",
        "next_draw_date": "extract next draw date if visible",
        "visible_numbers": [list ALL individual numbers you can see anywhere on the page],
        "confidence": "your confidence percentage in the extraction"
    }}

    Look carefully for:
    - Individual lottery numbers (like 03, 22, 51, etc.)
    - Draw dates (like "LAST DRAWN: 19 JUL 2025")
    - Jackpot amounts (like "R84 MILLION")
    - Any lottery game names visible
    
    Extract everything you can see, even if it's promotional content.
    """
    
    try:
        # Read screenshot
        with open(latest_screenshot, "rb") as f:
            image_bytes = f.read()
            
        # Analyze with Gemini 2.5 Pro
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/png",
                ),
                prompt
            ],
        )
        
        if response.text:
            logger.info(f"🤖 Gemini AI Response Length: {len(response.text)} characters")
            logger.info("📋 Extracted Data:")
            print("=" * 50)
            print(response.text)
            print("=" * 50)
            
            # Try to parse as JSON
            try:
                extracted_data = json.loads(response.text)
                logger.info("✅ Successfully parsed as JSON")
                return extracted_data
            except json.JSONDecodeError:
                logger.warning("⚠️ Response is not valid JSON but content received")
                return response.text
        else:
            logger.error("❌ Empty response from Gemini")
            return False
            
    except Exception as e:
        logger.error(f"❌ Gemini extraction failed: {e}")
        return False

if __name__ == "__main__":
    print("🧠 Testing Google Gemini AI Extraction")
    print("=" * 50)
    
    result = test_gemini_extraction()
    
    if result:
        print("✅ AI extraction test completed successfully")
    else:
        print("❌ AI extraction test failed")