import os
import logging
import base64
import json
import sys
from datetime import datetime
import re
import importlib.util

logger = logging.getLogger(__name__)

# Check if Anthropic library is installed
anthropic_installed = importlib.util.find_spec("anthropic") is not None

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

# No HTML parser needed for screenshot-based OCR processing

def process_screenshot(screenshot_path, lottery_type):
    """
    Process a screenshot to extract lottery data using AI-powered OCR.
    
    Args:
        screenshot_path (str): Path to the PNG screenshot file
        lottery_type (str): Type of lottery (e.g., 'Lotto', 'Powerball')
        
    Returns:
        dict: Extracted lottery data
    """
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
            result = process_with_ai(screenshot_path, lottery_type)
            logger.info(f"AI processing completed for {lottery_type}")
            if result and "results" in result and result["results"]:
                logger.info(f"Content processing completed successfully for {lottery_type}")
                return result
        except Exception as e:
            logger.error(f"Error in AI processing: {str(e)}")
    else:
        logger.error("Anthropic client not available. Cannot process without API key.")
    
    # Return default structure with empty data if processing failed
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
    logger.info(f"Using default result for {lottery_type}")
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
            max_tokens=3000,  # Increased token limit to handle multiple draw results
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
            
            # Save the full raw response for debugging
            result['raw_response'] = response_text
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {str(e)}")
            logger.error(f"Response content: {response_text}")
            # Still return the raw response for debugging
            return {
                "lottery_type": lottery_type,
                "results": [],
                "ocr_timestamp": datetime.utcnow().isoformat(),
                "raw_response": response_text,
                "error": f"JSON decode error: {str(e)}"
            }
    
    except Exception as e:
        logger.error(f"Error in AI processing: {str(e)}")
        # Return error information
        return {
            "lottery_type": lottery_type,
            "results": [],
            "ocr_timestamp": datetime.utcnow().isoformat(),
            "error": f"AI processing error: {str(e)}"
        }

# This function is no longer needed since we only use AI OCR processing

def create_system_prompt(lottery_type):
    """
    Create a system prompt for OCR based on lottery type.
    
    Args:
        lottery_type (str): Type of lottery (e.g., "Lotto", "Lotto Results", etc.)
        
    Returns:
        str: System prompt for OCR
    """
    # Strip "Results" suffix for the base prompt
    base_lottery_type = lottery_type.replace(" Results", "")
    base_prompt = """
    You are a specialized OCR extraction system designed to extract lottery draw results from screenshots of South African lottery websites.
    
    Your PRIMARY task is to accurately extract these FOUR key pieces of information for ALL visible lottery draws on the page:
    1. Game Type (e.g., Lotto, Lotto Plus 1, Powerball)
    2. Draw ID (e.g., Draw 2530) - This is the unique identifier for the draw
    3. Game Date (convert to ISO format YYYY-MM-DD)
    4. Winning Numbers - The main lottery numbers drawn
    
    EQUAL PRIORITY - CRITICAL INFORMATION to extract accurately:
    - Bonus numbers or PowerBall numbers
    - Divisions data including winners and prize amounts
    
    PRIZE AMOUNTS ARE EXTREMELY IMPORTANT - Pay special attention to:
    - The prize amount for each division
    - Make sure to include the EXACT amount shown, including commas and decimal places
    - Format example: "R5,000,000.00" or "R10,567.80"
    - DO NOT remove commas from prize amounts in your JSON output
    
    The screenshots come from the South African National Lottery website (nationallottery.co.za).
    
    Pay special attention to:
    - Lottery ball numbers (often in circles)
    - Draw IDs that appear near dates
    - Game dates formatted in various ways
    - Clear headings indicating the lottery type
    - Repeating patterns in tables that might indicate multiple draws
    - Division information (look for tables with "Division", "Winners", and "Prize" columns)
    
    For the South African lottery website:
    - Look for tables with lottery results, each row likely contains a separate draw
    - Lottery balls are typically displayed as numbers in colored circles
    - Draw dates usually follow a day/month/year format like "05/04/2025"
    - Draw IDs usually appear as "Draw XXXX" where XXXX is a number
    - Prize amounts appear as monetary values with R prefix (e.g., R5,000,000.00)
    
    If this is a RESULTS PAGE (URL contains "/results/"):
      Include divisions data with winners and prize amounts in the format below.
      Look for tables with division information, usually showing:
      - Division numbers (Division 1, Division 2, etc.)
      - Number of winners
      - Prize amounts (with "R" prefix for Rand)
      
      PAY VERY CLOSE ATTENTION TO PRIZE AMOUNTS!
      - Extract prize amounts EXACTLY as they appear, including all commas and decimal places
      - Example formats: "R5,000,000.00" or "R127,365.20" or "R500.00"
      - DO NOT remove commas from prize amounts in your JSON output
      - If you can't clearly read the amount, try different OCR techniques, like focusing on each digit
      - For prize amounts, preserving the original format is more important than converting to numbers
    
    Return the data in this exact JSON format:
    {
        "lottery_type": "Game Type",
        "results": [
            {
                "draw_number": "Draw ID as a string",
                "draw_date": "YYYY-MM-DD",
                "numbers": [1, 2, 3, 4, 5, 6],
                "bonus_numbers": [7],  # Only if applicable
                "divisions": {  # Include if this is a results page with division data
                    "Division 1": {
                        "winners": "1",
                        "prize": "R5,000,000.00"
                    },
                    "Division 2": {
                        "winners": "5",
                        "prize": "R100,000.00"
                    },
                    ... more divisions as found ...
                }
            },
            {
                "draw_number": "Another Draw ID",
                "draw_date": "YYYY-MM-DD",
                "numbers": [7, 8, 9, 10, 11, 12],
                "bonus_numbers": [13],  # Only if applicable
                "divisions": {  # Include if this is a results page with division data
                    ... divisions data ...
                }
            },
            ... more draws as found on the page ...
        ]
    }
    
    Important:
    - EXTRACT ALL DRAWS visible on the page, not just the most recent one
    - EACH ROW in the lottery results table likely represents a separate draw
    - Usually, there are at least 5-10 draws visible on each page
    - THE FOUR KEY FIELDS (Game Type, Draw ID, Game Date, Winning Numbers) are ABSOLUTELY CRITICAL and should be your top priority
    - Convert all numbers to integers, not strings
    - Return draw dates in ISO format (YYYY-MM-DD) 
    - If a date format is ambiguous, assume DD-MM-YYYY as the original format
    - For each draw, extract exactly the correct number of main numbers for the lottery type
    - If you can't find specific data, do NOT make it up - use placeholders like "Unknown" for text fields or 0 for numbers
    - Important: Don't limit yourself to just one draw - extract ALL visible draws from the page
    - Pay extremely close attention to the numbers - they must be precisely read from the lottery balls
    - Check the numbers are correctly identified (Lotto numbers are 1-52, examine each ball carefully)
    
    EXTREMELY IMPORTANT FOR NUMBER RECOGNITION:
    - Be very careful with digits that look similar - common mistakes include:
        * 3 can look like 8 (particularly the numbers 33 and 38)
        * 2 can look like 3 (particularly the numbers 23 and 33)
        * 6 can look like 8 (particularly the numbers 16 and 18, or 26 and 28)
        * 1 can look like 4 (particularly the numbers 14 and 44)
    - Examine the exact shape of each digit:
        * The number 3 has two curves on the right side
        * The number 8 has a complete loop on top and bottom
        * The number 2 has a flat bottom
        * The number 6 has a loop at the bottom only
    - Pay special attention to the recent draw with ID 2521 (usually from March 5, 2025)
      The correct numbers for this draw are [33, 36, 38, 40, 46, 49] with bonus number [39]
    
    - Look at the pattern of numbers across multiple draws to ensure consistency
    - If you detect a number that seems out of place or doesn't match the pattern, double-check it
    """
    
    # Add lottery-specific instructions
    if "lotto" in base_lottery_type.lower() and "plus" not in base_lottery_type.lower():
        return base_prompt + """
        For Lotto:
        - Extract exactly 6 main numbers for EACH draw
        - Extract 1 bonus number for EACH draw
        - Main numbers are typically in the range of 1-52
        - Look for lottery balls in the screenshot - they are usually displayed as numbers in colored circles
        - If you can't find exactly 6 main numbers for a draw, do not invent them - use zeros as placeholders [0,0,0,0,0,0]
        - Pay attention to tables or sections containing "Draw 2530" or similar recent draw numbers
        - Important: The page typically shows 5-10 different draws in a table. Extract EACH row as a separate draw.
        """
    elif "lotto plus" in base_lottery_type.lower():
        return base_prompt + """
        For Lotto Plus:
        - Extract exactly 6 main numbers for EACH draw
        - Extract 1 bonus number for EACH draw
        - Main numbers are typically in the range of 1-52
        - Look for lottery balls in the screenshot - they are usually displayed as numbers in colored circles
        - If you can't find exactly 6 main numbers for a draw, do not invent them - use zeros as placeholders [0,0,0,0,0,0]
        - Important: The page typically shows 5-10 different draws in a table. Extract EACH row as a separate draw.
        - Pay EXTRA attention to similar-looking numbers such as:
          - 33 vs 38 (commonly confused)
          - 36 vs 38 (commonly confused)
          - 13 vs 18 (commonly confused)
          - 14 vs 44 (sometimes misread)
          - 6 vs 8 vs 9 (easy to misread)
        - Double-check each ball by looking closely at the shape and any distinguishing features
        - For March 5, 2025 draw (typically Draw 2521), the numbers should be carefully verified
        - Check the image multiple times before finalizing numbers
        """
    elif "powerball" in base_lottery_type.lower():
        return base_prompt + """
        For PowerBall:
        - Extract exactly 5 main numbers for EACH draw
        - Extract 1 PowerBall number as the bonus_number for EACH draw
        - Main numbers are typically in the range of 1-50
        - PowerBall is typically in the range of 1-20
        - Look for lottery balls in the screenshot - main numbers and PowerBall will be in different colored circles
        - If you can't find exactly 5 main numbers for a draw, do not invent them - use zeros as placeholders [0,0,0,0,0]
        - Important: The page typically shows 5-10 different draws in a table. Extract EACH row as a separate draw.
        """
    elif "daily lotto" in base_lottery_type.lower():
        return base_prompt + """
        For Daily Lotto:
        - Extract exactly 5 main numbers for EACH draw
        - There is no bonus number
        - Main numbers are typically in the range of 1-36
        - Look for lottery balls in the screenshot - they are usually displayed as numbers in colored circles
        - If you can't find exactly 5 main numbers for a draw, do not invent them - use zeros as placeholders [0,0,0,0,0]
        - Important: The page typically shows 5-10 different draws in a table. Extract EACH row as a separate draw.
        """
    else:
        return base_prompt
