#!/usr/bin/env python3
"""
Step 3: AI Processing Module for Daily Automation
Uses Google Gemini to extract lottery data from captured screenshots
"""

import os
import glob
import logging
from datetime import datetime
import google.generativeai as genai
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_gemini():
    """Configure Google Gemini API"""
    try:
        api_key = Config.GOOGLE_API_KEY
        if not api_key:
            logger.error("Google API key not found in environment")
            return None
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        logger.info("Gemini API configured successfully")
        return model
    except Exception as e:
        logger.error(f"Failed to setup Gemini: {str(e)}")
        return None

def get_latest_screenshots():
    """Get the most recent screenshot files"""
    try:
        screenshot_dir = os.path.join(os.getcwd(), 'screenshots')
        if not os.path.exists(screenshot_dir):
            logger.warning("Screenshots directory does not exist")
            return []
            
        pattern = os.path.join(screenshot_dir, '*.png')
        screenshot_files = glob.glob(pattern)
        
        if not screenshot_files:
            logger.warning("No screenshot files found")
            return []
            
        # Sort by modification time, newest first
        screenshot_files.sort(key=os.path.getmtime, reverse=True)
        
        # Get today's screenshots only
        today = datetime.now().strftime('%Y%m%d')
        today_screenshots = [f for f in screenshot_files if today in os.path.basename(f)]
        
        logger.info(f"Found {len(today_screenshots)} screenshots from today")
        return today_screenshots
        
    except Exception as e:
        logger.error(f"Error getting screenshot files: {str(e)}")
        return []

def extract_lottery_data_from_image(model, image_path):
    """Extract lottery data from a single image using Gemini"""
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
            
        prompt = """
        Analyze this South African National Lottery screenshot and extract ALL lottery information including:

        SECTION 1 - Basic Results:
        - Lottery type: Lotto, Lotto Plus 1, Lotto Plus 2, Powerball, Powerball Plus, or Daily Lotto
        - Draw date (in YYYY-MM-DD format)
        - Draw number 
        - Main winning numbers (6 numbers for Lotto types, 5 for Powerball types, 5 for Daily Lotto)
        - Bonus ball/Powerball number (if applicable)

        SECTION 2 - Prize Divisions (from "Divisions, Winner and Winnings" box):
        - All prize divisions with number of winners and prize amounts
        - Total prize pool and rollover information

        SECTION 3 - Additional Information (from "More Info" section):
        For Lotto, Lotto Plus 1, Lotto Plus 2, Powerball, Powerball Plus extract:
        - Rollover amount
        - Rollover number  
        - Total pool size
        - Total sales
        - Next jackpot
        - Draw machine
        - Next draw date

        For Daily Lotto extract only:
        - Total pool size
        - Total sales  
        - Draw machine
        - Next draw date

        IMPORTANT: Return ONLY valid JSON in this exact format with no additional text:

        {
            "lottery_type": "Lotto",
            "draw_date": "2025-06-20", 
            "draw_number": "2456",
            "main_numbers": [1, 16, 36, 40, 42, 50],
            "bonus_numbers": [7],
            "prize_divisions": [
                {"division": "Division 1", "winners": 0, "prize_amount": "R0.00"},
                {"division": "Division 2", "winners": 5, "prize_amount": "R15,234.50"}
            ],
            "total_prize_pool": "R25,000,000.00",
            "rollover_amount": "R15,000,000.00",
            "rollover_number": "3",
            "total_pool_size": "R30,000,000.00",
            "total_sales": "R45,000,000.00", 
            "next_jackpot": "R40,000,000.00",
            "draw_machine": "Machine 1",
            "next_draw_date": "2025-06-23",
            "estimated_jackpot": "R40,000,000.00",
            "additional_info": "Special promotion details or other notes"
        }

        For Daily Lotto, omit rollover_amount, rollover_number, next_jackpot fields.
        For Powerball types, the bonus number goes in bonus_numbers array.
        For Daily Lotto, leave bonus_numbers as empty array [].
        If any section has no data, use empty arrays or null values.
        If no valid lottery data is found, return: {"error": "No lottery data found"}
        """
        
        response = model.generate_content([prompt, {"mime_type": "image/png", "data": image_data}])
        raw_response = response.text.strip()
        
        # Log the raw response for debugging
        logger.debug(f"Raw Gemini response: {raw_response[:200]}...")
        
        # Extract JSON from response that might contain extra text
        import re
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if json_match:
            json_text = json_match.group(0)
            logger.debug(f"Extracted JSON: {json_text}")
            return json_text
        else:
            logger.warning(f"No JSON found in response: {raw_response}")
            return '{"error": "No valid JSON in response"}'
        
    except Exception as e:
        logger.error(f"Error processing image {image_path}: {str(e)}")
        return '{"error": "Processing failed"}'

def process_all_screenshots():
    """Process all recent screenshots with AI"""
    logger.info("=== STEP 3: AI PROCESSING STARTED ===")
    
    model = setup_gemini()
    if not model:
        logger.error("Failed to setup Gemini model")
        return False
        
    screenshots = get_latest_screenshots()
    if not screenshots:
        logger.error("No screenshots to process")
        return False
        
    processed_count = 0
    extracted_data = []
    
    # Process all screenshots to ensure we get all lottery types
    for screenshot_path in screenshots:
        logger.info(f"Processing: {os.path.basename(screenshot_path)}")
        
        result = extract_lottery_data_from_image(model, screenshot_path)
        if result:
            try:
                import json
                data = json.loads(result)
                if 'error' not in data and 'lottery_type' in data:
                    # Validate required fields
                    required_fields = ['lottery_type', 'draw_date', 'main_numbers']
                    if all(field in data for field in required_fields):
                        extracted_data.append(data)
                        processed_count += 1
                        numbers_str = ', '.join(map(str, data.get('main_numbers', [])))
                        bonus_str = ', '.join(map(str, data.get('bonus_numbers', [])))
                        logger.info(f"✓ {data['lottery_type']} ({data['draw_date']}): {numbers_str}" + 
                                  (f" + {bonus_str}" if bonus_str else ""))
                    else:
                        logger.warning(f"Missing required fields in {os.path.basename(screenshot_path)}")
                else:
                    logger.warning(f"No valid lottery data in {os.path.basename(screenshot_path)}: {data.get('error', 'Unknown error')}")
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error for {os.path.basename(screenshot_path)}: {str(e)}")
                logger.debug(f"Raw response was: {result}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error processing {os.path.basename(screenshot_path)}: {str(e)}")
                continue
    
    # Store extracted data for step 4
    if extracted_data:
        import json
        data_file = os.path.join(os.getcwd(), 'temp_extracted_data.json')
        with open(data_file, 'w') as f:
            json.dump(extracted_data, f, indent=2)
        logger.info(f"Saved {len(extracted_data)} extracted records to temp file")
    
    success = processed_count > 0
    
    if success:
        logger.info(f"=== STEP 3: AI PROCESSING COMPLETED - {processed_count} records extracted ===")
    else:
        logger.error("=== STEP 3: AI PROCESSING FAILED - No data extracted ===")
        
    return success

def run_ai_process():
    """Run the AI processing step"""
    return process_all_screenshots()

if __name__ == "__main__":
    run_ai_process()