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

def process_screenshot(screenshot_path, lottery_type):
    """
    Process a screenshot/HTML content to extract lottery data.
    If Anthropic API is available, uses that, otherwise returns a placeholder.
    
    Args:
        screenshot_path (str): Path to the file
        lottery_type (str): Type of lottery (e.g., 'Lotto', 'Powerball')
        
    Returns:
        dict: Extracted lottery data
    """
    # Check if Anthropic client is available
    if not client:
        logger.error("Anthropic client not available. Cannot process without API key.")
        raise Exception("Anthropic API key is required for OCR processing. Please configure the Lotto_scape_ANTHROPIC_KEY environment variable.")
        
    try:
        # Read file and convert to base64
        with open(screenshot_path, "rb") as image_file:
            base64_content = base64.b64encode(image_file.read()).decode("utf-8")
        
        # Create system prompt based on lottery type
        system_prompt = create_system_prompt(lottery_type)
        
        # Determine media type based on file extension
        file_extension = os.path.splitext(screenshot_path)[1].lower()
        if file_extension in ['.html', '.htm']:
            # Process as text
            logger.info(f"Processing HTML content for {lottery_type}")
            
            # Read the content again as text
            with open(screenshot_path, "r", encoding="utf-8", errors="ignore") as html_file:
                html_content = html_file.read()
                
            # Send to Anthropic
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
                                "text": f"Extract the lottery results for {lottery_type} from this HTML content. Return the data in the specified JSON format."
                            },
                            {
                                "type": "text",
                                "text": html_content
                            }
                        ]
                    }
                ]
            )
        else:
            # Process as image
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
            logger.info(f"Content processing completed successfully for {lottery_type}")
            
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
        logger.error(f"Error processing content: {str(e)}")
        raise

def create_system_prompt(lottery_type):
    """
    Create a system prompt for OCR based on lottery type.
    
    Args:
        lottery_type (str): Type of lottery
        
    Returns:
        str: System prompt for OCR
    """
    base_prompt = """
    You are a specialized OCR system designed to extract lottery draw results from screenshots of lottery websites.
    Analyze the provided image and extract the following information:
    
    1. Draw numbers (e.g., Draw 1234)
    2. Draw dates (convert to ISO format YYYY-MM-DD)
    3. The winning numbers drawn
    4. Bonus numbers or PowerBall numbers if applicable
    
    The image will contain lottery results from the South African National Lottery website.
    
    Return the data in this exact JSON format:
    {
        "lottery_type": "The type of lottery",
        "results": [
            {
                "draw_number": "The draw number",
                "draw_date": "YYYY-MM-DD",
                "numbers": [1, 2, 3, 4, 5, 6],
                "bonus_numbers": [7]  # Only if applicable
            },
            // Additional results if present
        ]
    }
    
    Important:
    - Extract ALL results visible in the image, not just the most recent one
    - Convert all numbers to integers, not strings
    - Return draw dates in ISO format (YYYY-MM-DD)
    - If a date format is ambiguous, assume DD-MM-YYYY as the original format
    - For each draw, extract exactly the correct number of main numbers for the lottery type
    """
    
    # Add lottery-specific instructions
    if "lotto" in lottery_type.lower() and "plus" not in lottery_type.lower():
        return base_prompt + """
        For Lotto:
        - Extract exactly 6 main numbers
        - Extract 1 bonus number
        """
    elif "lotto plus" in lottery_type.lower():
        return base_prompt + """
        For Lotto Plus:
        - Extract exactly 6 main numbers
        - Extract 1 bonus number
        """
    elif "powerball" in lottery_type.lower():
        return base_prompt + """
        For PowerBall:
        - Extract exactly 5 main numbers
        - Extract 1 PowerBall number as the bonus_number
        """
    elif "daily lotto" in lottery_type.lower():
        return base_prompt + """
        For Daily Lotto:
        - Extract exactly 5 main numbers
        - There is no bonus number
        """
    else:
        return base_prompt
