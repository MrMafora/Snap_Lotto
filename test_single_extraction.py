#!/usr/bin/env python3
"""
Test Google Gemini 2.5 Pro extraction on a single lottery screenshot
"""

import os
import sys
import json
import base64
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def encode_image(image_path):
    """Encode image to base64 for Gemini API"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"Error encoding image {image_path}: {str(e)}")
        return None

def extract_lottery_data_from_image(image_path):
    """Extract lottery data from image using Google Gemini 2.5 Pro"""
    try:
        import google.generativeai as genai
        
        # Configure Google Gemini
        api_key = os.environ.get('GOOGLE_API_KEY_SNAP_LOTTERY')
        if not api_key:
            logger.error("GOOGLE_API_KEY_SNAP_LOTTERY not found in environment")
            return None
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Encode image
        image_b64 = encode_image(image_path)
        if not image_b64:
            return None
        
        # Create comprehensive prompt for lottery extraction
        prompt = """
You are a highly accurate lottery data extraction system. Extract lottery information from this screenshot with 100% precision.

CRITICAL REQUIREMENTS:
1. Extract EXACT numbers as they appear in the image
2. Return valid JSON format only
3. Use exact lottery type names from the image
4. Extract complete prize division information if visible

Expected JSON structure:
{
    "lottery_type": "exact name from image (LOTTO, LOTTO PLUS 1, LOTTO PLUS 2, PowerBall, PowerBall Plus, Daily Lotto)",
    "draw_number": "exact draw number as string",
    "draw_date": "YYYY-MM-DD format",
    "main_numbers": [array of integers],
    "bonus_numbers": [array of integers, empty if none],
    "divisions": [
        {
            "division": "DIV 1",
            "description": "description text",
            "winners": number or 0,
            "winnings": "amount as string"
        }
    ],
    "rollover_amount": "amount string or null",
    "rollover_number": "number or null",
    "total_pool_size": "amount string or null",
    "total_sales": "amount string or null",
    "next_jackpot": "amount string or null",
    "draw_machine": "machine name or null",
    "next_draw_date": "YYYY-MM-DD or null"
}

Extract the data NOW:
"""
        
        # Send to Google Gemini
        response = model.generate_content([
            prompt,
            {
                "mime_type": "image/png",
                "data": image_b64
            }
        ])
        
        if not response or not response.text:
            logger.error("No response from Google Gemini")
            return None
        
        # Parse JSON response
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        extracted_data = json.loads(response_text)
        
        logger.info(f"Successfully extracted data for {extracted_data.get('lottery_type')} Draw {extracted_data.get('draw_number')}")
        return extracted_data
        
    except Exception as e:
        logger.error(f"Error extracting from {image_path}: {str(e)}")
        return None

def test_lottery_extraction():
    """Test Google Gemini extraction on lottery screenshots"""
    logger.info("=== TESTING GOOGLE GEMINI 2.5 PRO LOTTERY EXTRACTION ===")
    
    # Test with LOTTO screenshot first
    lotto_image = "screenshots/20250606_171929_lotto.png"
    
    if not os.path.exists(lotto_image):
        logger.error(f"Test image not found: {lotto_image}")
        return
    
    logger.info(f"Processing: {lotto_image}")
    result = extract_lottery_data_from_image(lotto_image)
    
    if result:
        logger.info("=== EXTRACTION SUCCESSFUL ===")
        logger.info(f"Lottery Type: {result.get('lottery_type')}")
        logger.info(f"Draw Number: {result.get('draw_number')}")
        logger.info(f"Draw Date: {result.get('draw_date')}")
        logger.info(f"Main Numbers: {result.get('main_numbers')}")
        logger.info(f"Bonus Numbers: {result.get('bonus_numbers')}")
        
        # Check for expected values from the LOTTO image
        expected_numbers = [10, 15, 24, 28, 35, 49]  # From visual inspection of the image
        expected_bonus = [26]
        
        actual_numbers = result.get('main_numbers', [])
        actual_bonus = result.get('bonus_numbers', [])
        
        numbers_match = sorted(actual_numbers) == sorted(expected_numbers)
        bonus_match = sorted(actual_bonus) == sorted(expected_bonus)
        
        logger.info(f"Accuracy Check:")
        logger.info(f"  Expected Numbers: {expected_numbers}")
        logger.info(f"  Extracted Numbers: {actual_numbers}")
        logger.info(f"  Numbers Match: {numbers_match}")
        logger.info(f"  Expected Bonus: {expected_bonus}")
        logger.info(f"  Extracted Bonus: {actual_bonus}")
        logger.info(f"  Bonus Match: {bonus_match}")
        
        if numbers_match and bonus_match:
            logger.info("✓ PERFECT EXTRACTION ACCURACY")
        else:
            logger.warning("✗ EXTRACTION MISMATCH DETECTED")
            
        return result
    else:
        logger.error("❌ EXTRACTION FAILED")
        return None

def process_all_screenshots():
    """Process all 6 lottery screenshots"""
    logger.info("=== PROCESSING ALL LOTTERY SCREENSHOTS ===")
    
    screenshots = [
        "20250606_171929_lotto.png",
        "20250606_171942_lotto_plus_1_results.png", 
        "20250606_171954_lotto_plus_2_results.png",
        "20250606_172007_powerball.png",
        "20250606_172018_powerball_plus.png",
        "20250606_172030_daily_lotto.png"
    ]
    
    results = {}
    success_count = 0
    
    for screenshot in screenshots:
        image_path = f"screenshots/{screenshot}"
        
        if not os.path.exists(image_path):
            logger.warning(f"Screenshot not found: {image_path}")
            continue
            
        logger.info(f"Processing: {screenshot}")
        result = extract_lottery_data_from_image(image_path)
        
        if result:
            success_count += 1
            lottery_type = result.get('lottery_type', 'Unknown')
            results[lottery_type] = result
            
            logger.info(f"✓ {lottery_type}: {result.get('main_numbers')} + {result.get('bonus_numbers')}")
        else:
            logger.error(f"✗ Failed to process {screenshot}")
    
    logger.info(f"Processing complete: {success_count}/{len(screenshots)} successful extractions")
    
    # Display summary
    logger.info("=== EXTRACTION SUMMARY ===")
    for lottery_type, data in results.items():
        logger.info(f"{lottery_type} Draw {data.get('draw_number')}: {data.get('main_numbers')} + {data.get('bonus_numbers')}")
    
    return results

def main():
    """Main function"""
    logger.info("Starting Google Gemini 2.5 Pro lottery extraction test...")
    
    # First test single extraction
    single_result = test_lottery_extraction()
    
    if single_result:
        # If single test successful, process all screenshots
        all_results = process_all_screenshots()
        
        logger.info(f"Google Gemini 2.5 Pro extraction completed: {len(all_results)} lottery types processed")
    else:
        logger.error("Single extraction test failed")
    
    logger.info("Google Gemini lottery extraction test finished")

if __name__ == "__main__":
    main()