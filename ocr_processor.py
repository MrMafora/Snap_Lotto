import os
import logging
import base64
import json
import sys
from datetime import datetime
import re
import importlib.util

logger = logging.getLogger(__name__)

# Initialize variables - actual client will be created on first use
ANTHROPIC_API_KEY = None
anthropic_client = None

def get_anthropic_client():
    """Lazy load the Anthropic client when actually needed"""
    global ANTHROPIC_API_KEY, anthropic_client
    
    # Return existing client if already initialized
    if anthropic_client is not None:
        return anthropic_client
    
    # Initialize API key from environment variable
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
    
    # Log if key is missing
    if not ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY environment variable not set.")
        return None
    
    # Initialize Anthropic client if ANTHROPIC_API_KEY is available
    try:
        import anthropic
        from anthropic import Anthropic
        
        # Initialize client
        anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
        logger.info("Anthropic client initialized successfully")
        return anthropic_client
    except ImportError:
        logger.error("Failed to import anthropic module. Please check if it's properly installed.")
        return None
    except Exception as e:
        logger.error(f"Error initializing Anthropic client: {str(e)}")
        return None

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
            "ocr_timestamp": datetime.utcnow().isoformat(),
            "ocr_provider": "unknown",
            "ocr_model": "unknown",
            "error": f"Invalid file type: {file_extension}. Expected a PNG/JPEG screenshot."
        }
    
    # Read the screenshot file and convert to base64
    try:
        with open(screenshot_path, "rb") as image_file:
            base64_content = base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        logger.error(f"Error reading image file: {str(e)}")
        return {
            "lottery_type": lottery_type,
            "results": [],
            "ocr_timestamp": datetime.utcnow().isoformat(),
            "ocr_provider": "unknown",
            "ocr_model": "unknown",
            "error": f"Error reading image file: {str(e)}"
        }
    
    # Create system prompt based on lottery type
    system_prompt = create_system_prompt(lottery_type)
    
    # Use Anthropic Claude for OCR processing
    # Lazy load the client only when needed
    client = get_anthropic_client()
    if client:
        try:
            logger.info(f"Processing with Anthropic Claude for {lottery_type}")
            
            # Determine the image format from file extension
            image_format = 'jpeg'  # Default to JPEG
            if file_extension == '.png':
                image_format = 'png'
            elif file_extension in ['.jpg', '.jpeg']:
                image_format = 'jpeg'
            elif file_extension == '.webp':
                image_format = 'webp'
            
            logger.info(f"Detected image format: {image_format}")
            
            # Process with appropriate image format
            # Pass the screenshot ID if available for tracking in API logs
            result = process_with_anthropic(base64_content, lottery_type, system_prompt, image_format, screenshot_id=getattr(screenshot_path, 'id', None))
            if result and "results" in result and result["results"]:
                logger.info(f"Anthropic processing completed successfully for {lottery_type}")
                return result
        except Exception as e:
            logger.error(f"Error in Anthropic processing: {str(e)}")
    
    # If no AI client is available or processing failed
    if not get_anthropic_client():
        logger.error("No AI client available. Cannot process without API key.")
    
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
        "ocr_timestamp": datetime.utcnow().isoformat(),
        "ocr_provider": "unknown",
        "ocr_model": "unknown"
    }
    logger.info(f"Using default result for {lottery_type}")
    return default_result

def process_with_anthropic(base64_content, lottery_type, system_prompt, image_format='jpeg', screenshot_id=None):
    """
    Process a screenshot using Anthropic's Claude AI for OCR.
    
    Args:
        base64_content (str): Base64-encoded image data
        lottery_type (str): Type of lottery
        system_prompt (str): System prompt for AI
        image_format (str): Format of the image (jpeg, png, etc.)
        screenshot_id (int, optional): ID of the screenshot being processed
        
    Returns:
        dict: The processed result
    """
    # Import only when needed to avoid circular imports
    from models import APIRequestLog

    start_time = datetime.utcnow()
    request_id = None
    prompt_tokens = None
    completion_tokens = None
    status = 'error'  # Default to error, will change to success if all goes well
    error_message = None
    
    try:
        # Get the lazily loaded client
        client = get_anthropic_client()
        if not client:
            error_message = "Cannot process with Anthropic: No client available"
            logger.error(error_message)
            
            # Log the failed API request
            APIRequestLog.log_request(
                service='anthropic',
                endpoint='messages.create',
                model='claude-3-5-sonnet-20241022',
                status='error',
                error_message=error_message,
                screenshot_id=screenshot_id,
                lottery_type=lottery_type
            )
            return None
            
        # Set media type based on image format
        media_type = f"image/{image_format.lower()}"
        logger.info(f"Using media type: {media_type} for image processing")
        
        # Process as image using Anthropic Claude
        logger.info(f"Sending screenshot to Anthropic Claude for OCR processing: {lottery_type}")
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022", # Latest Claude model
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
                                "media_type": media_type,
                                "data": base64_content
                            }
                        }
                    ]
                }
            ]
        )
        
        # Calculate duration
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Get metrics from the response
        if hasattr(response, 'usage'):
            prompt_tokens = getattr(response.usage, 'input_tokens', None)
            completion_tokens = getattr(response.usage, 'output_tokens', None)
        
        # Get request ID if available
        if hasattr(response, 'id'):
            request_id = response.id
        
        # Get the text content from the response
        response_text = response.content[0].text
        
        # Keep this for logging/debugging purposes
        logger.info(f"Received response from Claude 3 Sonnet for {lottery_type}")
        
        # The response should be directly parsable as JSON now
        result_json = response_text
        
        # Change status to success since we got a response
        status = 'success'
        
        # Log the successful API request
        APIRequestLog.log_request(
            service='anthropic',
            endpoint='messages.create',
            model='claude-3-5-sonnet-20241022',
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            status=status,
            duration_ms=duration_ms,
            request_id=request_id,
            screenshot_id=screenshot_id,
            lottery_type=lottery_type
        )
        
        # Parse the response
        try:
            result = json.loads(result_json)
            
            # Add lottery type to result if not present
            if 'lottery_type' not in result:
                result['lottery_type'] = lottery_type
            
            # Add source information
            result['ocr_timestamp'] = datetime.utcnow().isoformat()
            
            # Add OCR provider information
            result['ocr_provider'] = "anthropic"
            result['ocr_model'] = "claude-3-5-sonnet-20241022"
            
            # Save the full raw response for debugging
            result['raw_response'] = response_text
            
            return result
            
        except json.JSONDecodeError as e:
            error_message = f"Error parsing JSON response: {str(e)}"
            logger.error(error_message)
            logger.error(f"Response content: {response_text}")
            
            # Update the API request log with the error
            APIRequestLog.log_request(
                service='anthropic',
                endpoint='messages.create.json_parse',
                model='claude-3-5-sonnet-20241022',
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                status='error',
                duration_ms=duration_ms,
                error_message=error_message,
                request_id=request_id,
                screenshot_id=screenshot_id,
                lottery_type=lottery_type
            )
            
            # Still return the raw response for debugging
            return {
                "lottery_type": lottery_type,
                "results": [],
                "ocr_timestamp": datetime.utcnow().isoformat(),
                "ocr_provider": "anthropic",
                "ocr_model": "claude-3-5-sonnet-20241022",
                "raw_response": response_text,
                "error": error_message
            }
    
    except Exception as e:
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        error_message = f"Error in Anthropic processing: {str(e)}"
        logger.error(error_message)
        
        # Log the failed API request
        APIRequestLog.log_request(
            service='anthropic',
            endpoint='messages.create',
            model='claude-3-5-sonnet-20241022',
            status='error',
            duration_ms=duration_ms,
            error_message=error_message,
            screenshot_id=screenshot_id,
            lottery_type=lottery_type
        )
        
        # Return error information
        return {
            "lottery_type": lottery_type,
            "results": [],
            "ocr_timestamp": datetime.utcnow().isoformat(),
            "ocr_provider": "anthropic",
            "ocr_model": "claude-3-5-sonnet-20241022",
            "error": error_message
        }

def create_system_prompt(lottery_type):
    """
    Create appropriate system prompt based on lottery type
    
    Args:
        lottery_type (str): Type of lottery
        
    Returns:
        str: System prompt for AI
    """
    # Base prompt with South African lottery context
    base_prompt = """
    You are a South African lottery data extraction specialist. Your task is to extract lottery results and related data from screenshots of the National Lottery website. 
    
    Important notes:
    - South African lottery formats include Lotto (6 numbers + 1 bonus), Lotto Plus 1 (6 numbers + 1 bonus), Lotto Plus 2 (6 numbers + 1 bonus), Powerball (5 numbers + 1 bonus), Powerball Plus (5 numbers + 1 bonus), and Daily Lotto (5 numbers, no bonus).
    - For history pages: Extract EACH DRAW shown in the image, not just the most recent one. There can be multiple draws shown on a single page.
    - Draw numbers are sometimes shown as "Draw 1234" or "DRAW 1234" - extract only the number portion.
    - Dates are in DD-MM-YYYY or DD/MM/YYYY format as typical in South Africa.
    - 'Division' refers to prize categories. Division data includes the division number, match criteria, number of winners, and prize amount.
    - Prize amounts are in South African Rand (R) format with commas, like "R5,000,000.00".
    
    Be very precise about:
    1. Extracting ALL draws visible in the image
    2. Correct lottery numbers, including bonus numbers
    3. Draw dates in YYYY-MM-DD format
    4. Prize divisions, winners and amounts where available
    
    For any unclear or partially visible information, use "Unknown" or omit the field rather than guessing.

    Return the data in this structured JSON format:
    {
        "lottery_type": "The type of lottery (e.g., Lotto, Powerball)",
        "results": [
            {
                "draw_number": "Draw ID number",
                "draw_date": "Draw date in YYYY-MM-DD format",
                "numbers": [array of main winning numbers as integers],
                "bonus_numbers": [array of bonus numbers as integers, empty for Daily Lotto],
                "divisions": {
                    "Division 1": {
                        "match": "Description of match (e.g., '6 Correct Numbers')",
                        "winners": "Number of winners",
                        "prize": "Prize amount in R format"
                    },
                    "Division 2": {...},
                    ... and so on for all visible divisions
                }
            },
            ... additional draws if multiple are shown
        ]
    }
    """
    
    # Add lottery-specific details
    if "lotto" in lottery_type.lower() and "plus" not in lottery_type.lower() and "daily" not in lottery_type.lower():
        base_prompt += """
        For Lotto:
        - Extract 6 main numbers and 1 bonus number
        - Division 1 = six correct numbers
        - Division 2 = five correct numbers + bonus number
        - Division 3 = five correct numbers
        - Division 4 = four correct numbers + bonus number
        - Division 5 = four correct numbers
        - Division 6 = three correct numbers + bonus number
        - Division 7 = three correct numbers
        - Division 8 = two correct numbers + bonus number
        """
    elif "lotto plus 1" in lottery_type.lower():
        base_prompt += """
        For Lotto Plus 1:
        - Extract 6 main numbers and 1 bonus number
        - Same division structure as Lotto
        """
    elif "lotto plus 2" in lottery_type.lower():
        base_prompt += """
        For Lotto Plus 2:
        - Extract 6 main numbers and 1 bonus number
        - Same division structure as Lotto
        """
    elif "powerball" in lottery_type.lower() and "plus" not in lottery_type.lower():
        base_prompt += """
        For Powerball:
        - Extract 5 main numbers and 1 Powerball number (treat as the bonus number)
        - Division 1 = five correct numbers + Powerball
        - Division 2 = five correct numbers
        - Division 3 = four correct numbers + Powerball
        - Division 4 = four correct numbers
        - Division 5 = three correct numbers + Powerball
        - Division 6 = three correct numbers
        - Division 7 = two correct numbers + Powerball
        - Division 8 = one correct number + Powerball
        - Division 9 = zero correct numbers + Powerball
        """
    elif "powerball plus" in lottery_type.lower():
        base_prompt += """
        For Powerball Plus:
        - Extract 5 main numbers and 1 Powerball number (treat as the bonus number)
        - Same division structure as Powerball
        """
    elif "daily lotto" in lottery_type.lower():
        base_prompt += """
        For Daily Lotto:
        - Extract 5 main numbers (no bonus number)
        - Division 1 = five correct numbers
        - Division 2 = four correct numbers
        - Division 3 = three correct numbers
        - Division 4 = two correct numbers
        """
    
    # If this is a results page (contains prize division info)
    if "results" in lottery_type.lower():
        base_prompt += """
        Special Instructions for Results Pages:
        - This is a results page which usually shows detailed prize division information
        - Pay special attention to extracting division data including match criteria, winners, and prize amounts
        - The page may show multiple divisions (Division 1 through Division 8/9)
        - Division descriptions often show the matching criteria (e.g., "FIVE CORRECT NUMBERS + BONUS BALL")
        - Carefully extract both the number of winners and the prize amount for each division
        - Prize amounts include the currency symbol R (South African Rand), e.g., "R5,000,000.00"
        """
        
    return base_prompt

def extract_divisions_from_text(text, lottery_type):
    """
    Extract division information from OCR text.
    
    Args:
        text (str): OCR extracted text
        lottery_type (str): Type of lottery
        
    Returns:
        dict: Dictionary of divisions
    """
    divisions = {}
    
    # Define regex patterns for different formats
    patterns = [
        # Pattern 1: Division X - XXX Winners - Prize: RXXX
        r'(?:Division|DIV)[.\s]*(\d+)[.\s]*[-:]*[.\s]*(.*?)[.\s]*[-:]*[.\s]*(\d+)[.\s]*(?:Winner|Winners)[.\s]*[-:]*[.\s]*(?:Prize|PRIZE)?[.\s]*[-:]*[.\s]*(R[\d,.]+)',
        # Pattern 2: Division X: XXX Winners - RXXX each
        r'(?:Division|DIV)[.\s]*(\d+)[.\s]*[-:]*[.\s]*(\d+)[.\s]*(?:Winner|Winners)[.\s]*[-:]*[.\s]*(R[\d,.]+)[.\s]*(?:each|per person)?',
        # Pattern 3: X CORRECT NUMBERS - XXX Winners - RXXX
        r'((?:\w+\s+){2,4}NUMBERS(?:\s+\+\s+BONUS(?:\s+BALL)?)?)[.\s]*[-:]*[.\s]*(\d+)[.\s]*(?:Winner|Winners)[.\s]*[-:]*[.\s]*(R[\d,.]+)',
        # Pattern 4: Div X (description) - XXX - RXXX
        r'(?:Div|DIV)[.\s]*(\d+)[.\s]*\((.*?)\)[.\s]*[-:]*[.\s]*(\d+)[.\s]*[-:]*[.\s]*(R[\d,.]+)'
    ]
    
    # Try each pattern
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            if len(match.groups()) == 4:  # Pattern 1 or 4
                div_num, match_desc, winners, prize = match.groups()
                divisions[f"Division {div_num}"] = {
                    "match": match_desc.strip() if match_desc else "",
                    "winners": winners.strip(),
                    "prize": prize.strip()
                }
            elif len(match.groups()) == 3:  # Pattern 2 or 3
                if match.groups()[0].isdigit():  # Pattern 2
                    div_num, winners, prize = match.groups()
                    divisions[f"Division {div_num}"] = {
                        "match": "",
                        "winners": winners.strip(),
                        "prize": prize.strip()
                    }
                else:  # Pattern 3
                    match_desc, winners, prize = match.groups()
                    # Try to determine division number from match description
                    div_num = determine_division_number(match_desc, lottery_type)
                    divisions[f"Division {div_num}"] = {
                        "match": match_desc.strip(),
                        "winners": winners.strip(),
                        "prize": prize.strip()
                    }
    
    return divisions

def determine_division_number(match_description, lottery_type):
    """
    Determine division number from match description.
    
    Args:
        match_description (str): Description of the match (e.g., 'SIX CORRECT NUMBERS')
        lottery_type (str): Type of lottery
        
    Returns:
        str: Division number as string
    """
    match_desc = match_description.lower()
    
    if "daily lotto" in lottery_type.lower():
        if "five" in match_desc or "5" in match_desc:
            return "1"
        elif "four" in match_desc or "4" in match_desc:
            return "2"
        elif "three" in match_desc or "3" in match_desc:
            return "3"
        elif "two" in match_desc or "2" in match_desc:
            return "4"
    elif "powerball" in lottery_type.lower():
        if "five" in match_desc or "5" in match_desc:
            if "powerball" in match_desc or "bonus" in match_desc:
                return "1"
            else:
                return "2"
        elif "four" in match_desc or "4" in match_desc:
            if "powerball" in match_desc or "bonus" in match_desc:
                return "3"
            else:
                return "4"
        elif "three" in match_desc or "3" in match_desc:
            if "powerball" in match_desc or "bonus" in match_desc:
                return "5"
            else:
                return "6"
        elif "two" in match_desc or "2" in match_desc:
            if "powerball" in match_desc or "bonus" in match_desc:
                return "7"
            else:
                return "0"  # Not a valid division for powerball
        elif "one" in match_desc or "1" in match_desc:
            if "powerball" in match_desc or "bonus" in match_desc:
                return "8"
        elif "zero" in match_desc or "0" in match_desc:
            if "powerball" in match_desc or "bonus" in match_desc:
                return "9"
    else:  # Lotto, Lotto Plus 1, Lotto Plus 2
        if "six" in match_desc or "6" in match_desc:
            return "1"
        elif "five" in match_desc or "5" in match_desc:
            if "bonus" in match_desc:
                return "2"
            else:
                return "3"
        elif "four" in match_desc or "4" in match_desc:
            if "bonus" in match_desc:
                return "4"
            else:
                return "5"
        elif "three" in match_desc or "3" in match_desc:
            if "bonus" in match_desc:
                return "6"
            else:
                return "7"
        elif "two" in match_desc or "2" in match_desc:
            if "bonus" in match_desc:
                return "8"
    
    # Default to X if we can't determine
    return "X"

if __name__ == "__main__":
    # Simple command-line interface for testing
    if len(sys.argv) < 3:
        print("Usage: python ocr_processor.py <screenshot_path> <lottery_type>")
        sys.exit(1)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Process the screenshot
    screenshot_path = sys.argv[1]
    lottery_type = sys.argv[2]
    
    result = process_screenshot(screenshot_path, lottery_type)
    print(json.dumps(result, indent=2))