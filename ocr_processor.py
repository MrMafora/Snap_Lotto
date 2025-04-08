import os
import logging
import base64
import json
import sys
from datetime import datetime
import re
import importlib.util
from html_parser import parse_lottery_html

logger = logging.getLogger(__name__)

# Check if Anthropic library is installed
anthropic_installed = importlib.util.find_spec("anthropic") is not None

# Check if BeautifulSoup is installed
bs4_installed = importlib.util.find_spec("bs4") is not None

# Initialize with custom environment variable name
ANTHROPIC_API_KEY = os.environ.get("Lotto_scape_ANTHROPIC_KEY")
if not ANTHROPIC_API_KEY:
    logger.error("Lotto_scape_ANTHROPIC_KEY environment variable not set.")

# Initialize Anthropic client (if library is installed)
client = None
if anthropic_installed:
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=ANTHROPIC_API_KEY)
    except Exception as e:
        logger.error(f"Error initializing Anthropic client: {str(e)}")

# Import the HTML parser status check
html_parser = None
if bs4_installed:
    try:
        # Already imported parse_lottery_html at the top
        html_parser = True
    except ImportError:
        logger.warning("html_parser module not found, will use AI-only processing")

def process_screenshot(screenshot_path, lottery_type):
    """
    Process a screenshot to extract lottery data using AI-powered OCR.
    
    Args:
        screenshot_path (str): Path to the PNG screenshot file
        lottery_type (str): Type of lottery (e.g., 'Lotto', 'Powerball')
        
    Returns:
        dict: Extracted lottery data
    """
    results = {
        "ai_processed": None
    }
    
    # Check file type
    file_extension = os.path.splitext(screenshot_path)[1].lower()
    is_image = file_extension in ['.png', '.jpg', '.jpeg']
    
    # Verify we have a valid screenshot file
    if not is_image:
        logger.error(f"Invalid file type: {file_extension}. Expected a PNG/JPEG screenshot.")
        return {
            "lottery_type": lottery_type,
            "results": [
                {
                    "draw_number": "Unknown",
                    "draw_date": datetime.now().strftime("%Y-%m-%d"),
                    "numbers": [0, 0, 0, 0, 0, 0] if "powerball" not in lottery_type.lower() and "daily lotto" not in lottery_type.lower() else [0, 0, 0, 0, 0],
                    "bonus_numbers": [] if "daily lotto" in lottery_type.lower() else [0]
                }
            ],
            "ocr_timestamp": datetime.utcnow().isoformat()
        }
    
    # Process with AI-based OCR if client is available
    if client:
        try:
            results["ai_processed"] = process_with_ai(screenshot_path, lottery_type)
            logger.info(f"AI processing completed for {lottery_type}")
        except Exception as e:
            logger.error(f"Error in AI processing: {str(e)}")
    else:
        logger.error("Anthropic client not available. Cannot process without API key.")
    
    # Return the AI-processed result, or a default if it failed
    if results["ai_processed"] and "results" in results["ai_processed"] and results["ai_processed"]["results"]:
        logger.info(f"Content processing completed successfully for {lottery_type}")
        return results["ai_processed"]
    else:
        # Return default structure with empty data
        default_result = {
            "lottery_type": lottery_type,
            "results": [
                {
                    "draw_number": "Unknown",
                    "draw_date": datetime.now().strftime("%Y-%m-%d"),
                    "numbers": [0, 0, 0, 0, 0, 0] if "powerball" not in lottery_type.lower() and "daily lotto" not in lottery_type.lower() else [0, 0, 0, 0, 0],
                    "bonus_numbers": [] if "daily lotto" in lottery_type.lower() else [0]
                }
            ],
            "ocr_timestamp": datetime.utcnow().isoformat()
        }
        logger.info(f"Content processing completed successfully for {lottery_type}")
        return default_result

def process_with_ai(screenshot_path, lottery_type):
    """
    Process a screenshot using Anthropic's Claude AI for OCR.
    
    Args:
        screenshot_path (str): Path to the PNG screenshot file
        lottery_type (str): Type of lottery
        
    Returns:
        dict: The processed result
    """
    try:
        # Create system prompt based on lottery type
        system_prompt = create_system_prompt(lottery_type)
        
        # Read the screenshot file and convert to base64
        with open(screenshot_path, "rb") as image_file:
            base64_content = base64.b64encode(image_file.read()).decode("utf-8")
            
        # Process as image using Anthropic Claude
        logger.info(f"Sending screenshot to Anthropic Claude for OCR processing: {lottery_type}")
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022", # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
            max_tokens=1500,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Extract the lottery results from this {lottery_type} screenshot. Return the data in the specified JSON format."
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_content
                            }
                        }
                    ]
                }
            ]
        )
        
        # Extract and parse the JSON response
        response_text = response.content[0].text
        # Find the JSON part in the response
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        
        if json_match:
            result_json = json_match.group(1)
        else:
            # If no json code block, try to find JSON within the text
            json_pattern = r'\{[\s\S]*"lottery_type"[\s\S]*"results"[\s\S]*\}'
            json_match = re.search(json_pattern, response_text, re.DOTALL)
            if json_match:
                result_json = json_match.group(0)
            else:
                # If still no JSON found, try to parse the whole response
                result_json = response_text
        
        # Parse the response
        try:
            result = json.loads(result_json)
            
            # Add lottery type to result if not present
            if 'lottery_type' not in result:
                result['lottery_type'] = lottery_type
            
            # Add source information
            result['ocr_timestamp'] = datetime.utcnow().isoformat()
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {str(e)}")
            logger.error(f"Response content: {response_text}")
            raise Exception(f"Could not parse JSON response from Claude: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error in AI processing: {str(e)}")
        raise

def combine_results(results, lottery_type):
    """
    Combine results from different processing methods, taking the best data from each.
    
    Args:
        results (dict): Dictionary with different processing results
        lottery_type (str): Type of lottery
        
    Returns:
        dict: Combined result
    """
    # Initialize with a default structure
    combined = {
        "lottery_type": lottery_type,
        "results": [
            {
                "draw_number": "Unknown",
                "draw_date": datetime.now().strftime("%Y-%m-%d"),
                "numbers": [0, 0, 0, 0, 0, 0] if "powerball" not in lottery_type.lower() and "daily lotto" not in lottery_type.lower() else [0, 0, 0, 0, 0],
                "bonus_numbers": [] if "daily lotto" in lottery_type.lower() else [0]
            }
        ],
        "ocr_timestamp": datetime.utcnow().isoformat()
    }
    
    # If we have HTML-processed results, start with those
    if results["html_processed"] and "results" in results["html_processed"] and results["html_processed"]["results"]:
        combined = results["html_processed"]
        combined["ocr_timestamp"] = datetime.utcnow().isoformat()
        
        # If numbers are all zeros or not found, we'll try to improve that from AI results
        html_numbers = combined["results"][0]["numbers"]
        html_bonus = combined["results"][0].get("bonus_numbers", [])
        
        if all(n == 0 for n in html_numbers) and results["ai_processed"] and "results" in results["ai_processed"] and results["ai_processed"]["results"]:
            ai_numbers = results["ai_processed"]["results"][0]["numbers"]
            if not all(n == 0 for n in ai_numbers):
                combined["results"][0]["numbers"] = ai_numbers
            
            # Also get bonus numbers from AI if needed
            if "bonus_numbers" in results["ai_processed"]["results"][0]:
                ai_bonus = results["ai_processed"]["results"][0]["bonus_numbers"]
                if all(n == 0 for n in html_bonus) and not all(n == 0 for n in ai_bonus):
                    combined["results"][0]["bonus_numbers"] = ai_bonus
    
    # If no HTML results or they're incomplete, use AI results
    elif results["ai_processed"] and "results" in results["ai_processed"] and results["ai_processed"]["results"]:
        combined = results["ai_processed"]
    
    # Ensure lottery_type is set correctly
    combined["lottery_type"] = lottery_type
    
    return combined

def create_system_prompt(lottery_type):
    """
    Create a system prompt for OCR based on lottery type.
    
    Args:
        lottery_type (str): Type of lottery
        
    Returns:
        str: System prompt for OCR
    """
    base_prompt = """
    You are a specialized OCR extraction system designed to extract lottery draw results from screenshots of South African lottery websites.
    
    Your PRIMARY task is to accurately extract these FOUR key pieces of information:
    1. Game Type (e.g., Lotto, Lotto Plus 1, Powerball)
    2. Draw ID (e.g., Draw 2530) - This is the unique identifier for the draw
    3. Game Date (convert to ISO format YYYY-MM-DD)
    4. Winning Numbers - The main lottery numbers drawn
    
    Secondary information to extract if available:
    - Bonus numbers or PowerBall numbers
    
    The screenshots come from the South African National Lottery website (nationallottery.co.za).
    
    Pay special attention to:
    - Lottery ball numbers (often in circles)
    - Draw IDs that appear near dates
    - Game dates formatted in various ways
    - Clear headings indicating the lottery type
    
    For the South African lottery website:
    - Look for tables with lottery results
    - Lottery balls are typically displayed as numbers in colored circles
    - Draw dates usually follow a day/month/year format like "05/04/2025"
    - Draw IDs usually appear as "Draw XXXX" where XXXX is a number
    
    Return the data in this exact JSON format:
    {
        "lottery_type": "Game Type",
        "results": [
            {
                "draw_number": "Draw ID as a string",
                "draw_date": "YYYY-MM-DD",
                "numbers": [1, 2, 3, 4, 5, 6],
                "bonus_numbers": [7]  # Only if applicable
            }
        ]
    }
    
    Important:
    - Focus on extracting the MOST RECENT result only
    - THE FOUR KEY FIELDS (Game Type, Draw ID, Game Date, Winning Numbers) are ABSOLUTELY CRITICAL and should be your top priority
    - Convert all numbers to integers, not strings
    - Return draw dates in ISO format (YYYY-MM-DD) 
    - If a date format is ambiguous, assume DD-MM-YYYY as the original format
    - For each draw, extract exactly the correct number of main numbers for the lottery type
    - If you can't find specific data, do NOT make it up - use placeholders like "Unknown" for text fields or 0 for numbers
    - If you find multiple sets of numbers (balls), focus on the first/most recent set
    """
    
    # Add lottery-specific instructions
    if "lotto" in lottery_type.lower() and "plus" not in lottery_type.lower():
        return base_prompt + """
        For Lotto:
        - Extract exactly 6 main numbers
        - Extract 1 bonus number
        - Main numbers are typically in the range of 1-52
        - Look for lottery balls in the screenshot - they are usually displayed as numbers in colored circles
        - If you can't find exactly 6 main numbers, do not invent them - use zeros as placeholders [0,0,0,0,0,0]
        - Pay attention to tables or sections containing "Draw 2530" or similar recent draw numbers
        """
    elif "lotto plus" in lottery_type.lower():
        return base_prompt + """
        For Lotto Plus:
        - Extract exactly 6 main numbers
        - Extract 1 bonus number
        - Main numbers are typically in the range of 1-52
        - Look for lottery balls in the screenshot - they are usually displayed as numbers in colored circles
        - If you can't find exactly 6 main numbers, do not invent them - use zeros as placeholders [0,0,0,0,0,0]
        """
    elif "powerball" in lottery_type.lower():
        return base_prompt + """
        For PowerBall:
        - Extract exactly 5 main numbers
        - Extract 1 PowerBall number as the bonus_number
        - Main numbers are typically in the range of 1-50
        - PowerBall is typically in the range of 1-20
        - Look for lottery balls in the screenshot - main numbers and PowerBall will be in different colored circles
        - If you can't find exactly 5 main numbers, do not invent them - use zeros as placeholders [0,0,0,0,0]
        """
    elif "daily lotto" in lottery_type.lower():
        return base_prompt + """
        For Daily Lotto:
        - Extract exactly 5 main numbers
        - There is no bonus number
        - Main numbers are typically in the range of 1-36
        - Look for lottery balls in the screenshot - they are usually displayed as numbers in colored circles
        - If you can't find exactly 5 main numbers, do not invent them - use zeros as placeholders [0,0,0,0,0]
        """
    else:
        return base_prompt
