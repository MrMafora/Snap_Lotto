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
    Process a screenshot/HTML content to extract lottery data.
    Uses both AI-based approach and direct HTML parsing, then combines the results.
    
    Args:
        screenshot_path (str): Path to the file
        lottery_type (str): Type of lottery (e.g., 'Lotto', 'Powerball')
        
    Returns:
        dict: Extracted lottery data
    """
    results = {
        "ai_processed": None,
        "html_processed": None
    }
    
    # Check file type
    file_extension = os.path.splitext(screenshot_path)[1].lower()
    is_html = file_extension in ['.html', '.htm']
    is_image = file_extension in ['.png', '.jpg', '.jpeg']
    
    # Process HTML content if available
    if is_html:
        # Read the HTML content
        try:
            with open(screenshot_path, "r", encoding="utf-8", errors="ignore") as html_file:
                html_content = html_file.read()
                
            # Try HTML parser first (if available)
            if bs4_installed and parse_lottery_html:
                try:
                    results["html_processed"] = parse_lottery_html(html_content, lottery_type)
                    logger.info(f"HTML parsing completed for {lottery_type}")
                except Exception as e:
                    logger.error(f"Error in HTML parsing: {str(e)}")
        except Exception as e:
            logger.error(f"Error reading HTML file: {str(e)}")
    
    # Find paired HTML file for image files
    elif is_image:
        # Look for a corresponding HTML file (same timestamp, same URL)
        try:
            base_name = os.path.basename(screenshot_path)
            dir_name = os.path.dirname(screenshot_path)
            
            # Extract timestamp and URL from filename
            parts = base_name.split('_', 1)
            if len(parts) == 2:
                timestamp = parts[0]
                url_part = os.path.splitext(parts[1])[0]
                
                # Look for matching HTML file
                html_file_pattern = f"{timestamp}_{url_part}.html"
                html_path = os.path.join(dir_name, html_file_pattern)
                
                if os.path.exists(html_path):
                    logger.info(f"Found paired HTML file for image: {html_path}")
                    with open(html_path, "r", encoding="utf-8", errors="ignore") as html_file:
                        html_content = html_file.read()
                    
                    # Try HTML parser with this content
                    if bs4_installed and parse_lottery_html:
                        try:
                            results["html_processed"] = parse_lottery_html(html_content, lottery_type)
                            logger.info(f"HTML parsing from paired file completed for {lottery_type}")
                        except Exception as e:
                            logger.error(f"Error in HTML parsing from paired file: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing paired HTML file: {str(e)}")
    
    # Try AI-based approach if client is available
    if client:
        try:
            results["ai_processed"] = process_with_ai(screenshot_path, lottery_type)
            logger.info(f"AI processing completed for {lottery_type}")
        except Exception as e:
            logger.error(f"Error in AI processing: {str(e)}")
    else:
        logger.error("Anthropic client not available. Cannot process without API key.")
    
    # Combine results, giving preference to the HTML parser for accurate numbers
    final_result = combine_results(results, lottery_type)
    logger.info(f"Content processing completed successfully for {lottery_type}")
    return final_result

def process_with_ai(screenshot_path, lottery_type):
    """
    Process content using the Anthropic AI.
    
    Args:
        screenshot_path (str): Path to the file (HTML file)
        lottery_type (str): Type of lottery
        
    Returns:
        dict: The processed result
    """
    try:
        # Create system prompt based on lottery type
        system_prompt = create_system_prompt(lottery_type)
        
        # Determine file type based on extension
        file_extension = os.path.splitext(screenshot_path)[1].lower()
        
        # Process HTML content (optimized approach)
        if file_extension in ['.html', '.htm']:
            logger.info(f"Processing HTML content for {lottery_type}")
            
            # Read the content as text
            with open(screenshot_path, "r", encoding="utf-8", errors="ignore") as html_file:
                html_content = html_file.read()
            
            # Use a simplified approach to extract just the essential content
            # to prevent exceeding token limits
            simplified_content = html_content
            
            # If HTML is too large, extract just the main section
            if len(html_content) > 100000:
                logger.info("HTML content is very large, attempting to extract main section")
                # Look for main content sections in the HTML
                main_patterns = [
                    r'<main[^>]*>(.*?)</main>',
                    r'<div[^>]*main[^>]*>(.*?)</div>',
                    r'<div[^>]*content[^>]*>(.*?)</div>',
                    r'<div[^>]*results[^>]*>(.*?)</div>',
                    r'<table[^>]*>(.*?)</table>'
                ]
                
                for pattern in main_patterns:
                    matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
                    if matches:
                        # Take the largest match
                        simplified_content = max(matches, key=len)
                        logger.info(f"Extracted main content section ({len(simplified_content)} chars)")
                        break
            
            # Send to Anthropic
            logger.info(f"Sending HTML content to Anthropic Claude for processing: {lottery_type}")
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
                                "text": simplified_content
                            }
                        ]
                    }
                ]
            )
        # Handle image files (rare case now that we're storing HTML)
        else:
            # Read file and convert to base64
            with open(screenshot_path, "rb") as image_file:
                base64_content = base64.b64encode(image_file.read()).decode("utf-8")
                
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
    You are a specialized data extraction system designed to extract lottery draw results from HTML content of South African lottery websites.
    
    Your PRIMARY task is to accurately extract these FOUR key pieces of information:
    1. Game Type (e.g., Lotto, Lotto Plus 1, Powerball)
    2. Draw ID (e.g., Draw 2530) - This is the unique identifier for the draw
    3. Game Date (convert to ISO format YYYY-MM-DD)
    4. Winning Numbers - The main lottery numbers drawn
    
    Secondary information to extract if available:
    - Bonus numbers or PowerBall numbers
    
    The HTML content will come from the South African National Lottery website (nationallottery.co.za).
    
    Pay special attention to:
    - Tables containing lottery results
    - Elements with class names containing "ball", "number", "result", etc.
    - Draw IDs that appear near dates
    - Game dates formatted in various ways
    
    For the South African lottery website:
    - Look for HTML tables with lottery results
    - Winning numbers are often in elements with class names like "lotto-ball", "number-ball", etc.
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
        - The HTML content should contain elements with lottery balls, possibly with class names like "lotto-ball" or similar
        - If you can't find exactly 6 main numbers, do not invent them - use zeros as placeholders [0,0,0,0,0,0]
        - Look for tables or sections containing "Draw 2530" or similar recent draw numbers
        """
    elif "lotto plus" in lottery_type.lower():
        return base_prompt + """
        For Lotto Plus:
        - Extract exactly 6 main numbers
        - Extract 1 bonus number
        - Main numbers are typically in the range of 1-52
        - The HTML content should contain elements with lottery balls, possibly with class names like "lotto-ball" or similar
        - If you can't find exactly 6 main numbers, do not invent them - use zeros as placeholders [0,0,0,0,0,0]
        """
    elif "powerball" in lottery_type.lower():
        return base_prompt + """
        For PowerBall:
        - Extract exactly 5 main numbers
        - Extract 1 PowerBall number as the bonus_number
        - Main numbers are typically in the range of 1-50
        - PowerBall is typically in the range of 1-20
        - The HTML content should contain elements with lottery balls, possibly with class names like "powerball-ball" or similar
        - If you can't find exactly 5 main numbers, do not invent them - use zeros as placeholders [0,0,0,0,0]
        """
    elif "daily lotto" in lottery_type.lower():
        return base_prompt + """
        For Daily Lotto:
        - Extract exactly 5 main numbers
        - There is no bonus number
        - Main numbers are typically in the range of 1-36
        - The HTML content should contain elements with lottery balls, possibly with class names like "daily-lotto-ball" or similar
        - If you can't find exactly 5 main numbers, do not invent them - use zeros as placeholders [0,0,0,0,0]
        """
    else:
        return base_prompt
