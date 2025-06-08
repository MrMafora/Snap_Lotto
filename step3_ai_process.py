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
        Extract lottery results from this South African lottery screenshot. Look for:
        1. Draw date (format YYYY-MM-DD)
        2. Draw number
        3. Lottery type (Lotto, Lotto Plus 1, Lotto Plus 2, Powerball, Powerball Plus, Daily Lotto)
        4. Winning numbers (main numbers and bonus ball if applicable)
        
        Return data in this exact JSON format:
        {
            "lottery_type": "exact type name",
            "draw_date": "YYYY-MM-DD",
            "draw_number": "number",
            "main_numbers": [1, 2, 3, 4, 5, 6],
            "bonus_numbers": [7]
        }
        
        If no lottery data is found, return: {"error": "No lottery data found"}
        """
        
        response = model.generate_content([prompt, {"mime_type": "image/png", "data": image_data}])
        return response.text.strip()
        
    except Exception as e:
        logger.error(f"Error processing image {image_path}: {str(e)}")
        return None

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
    
    for screenshot_path in screenshots[:6]:  # Process up to 6 most recent
        logger.info(f"Processing: {os.path.basename(screenshot_path)}")
        
        result = extract_lottery_data_from_image(model, screenshot_path)
        if result:
            try:
                import json
                data = json.loads(result)
                if 'error' not in data:
                    extracted_data.append(data)
                    processed_count += 1
                    logger.info(f"Extracted: {data.get('lottery_type', 'Unknown')} - {data.get('draw_date', 'No date')}")
                else:
                    logger.warning(f"No data in {os.path.basename(screenshot_path)}")
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON response for {os.path.basename(screenshot_path)}")
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