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
GOOGLE_API_KEY = None
gemini_client = None

def get_gemini_client():
    """Lazy load the Google Gemini client when actually needed"""
    global GOOGLE_API_KEY, gemini_client
    
    # Return existing client if already initialized
    if gemini_client is not None:
        return gemini_client
    
    # Initialize API key from environment variable
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY_SNAP_LOTTERY")
    
    # Log if key is missing
    if not GOOGLE_API_KEY:
        logger.warning("GOOGLE_API_KEY_SNAP_LOTTERY environment variable not set.")
        return None
    
    # Initialize Google Gemini client if API key is available
    try:
        import google.generativeai as genai
        
        # Configure Gemini
        genai.configure(api_key=GOOGLE_API_KEY)
        gemini_client = genai.GenerativeModel('gemini-2.0-flash-exp')
        logger.info("Google Gemini client initialized successfully")
        return gemini_client
    except ImportError:
        logger.error("Failed to import google.generativeai module. Please check if it's properly installed.")
        return None
    except Exception as e:
        logger.error(f"Error initializing Google Gemini client: {str(e)}")
        return None

def process_screenshot(screenshot_path, lottery_type):
    """
    Process a screenshot to extract lottery data using AI-powered OCR.
    
    Args:
        screenshot_path: Path to the screenshot file or Screenshot object
        lottery_type (str): Type of lottery (e.g., 'lotto', 'powerball', etc.)
        
    Returns:
        dict: Processed lottery data
    """
    
    # Handle both file paths and Screenshot objects
    if hasattr(screenshot_path, 'path'):
        # This is a Screenshot object from the database
        file_path = screenshot_path.path
        logger.info(f"Processing Screenshot object: {file_path}")
    else:
        # This is a direct file path
        file_path = screenshot_path
        logger.info(f"Processing file path: {file_path}")
    
    # Check if file exists
    if not os.path.exists(file_path):
        logger.error(f"Screenshot file not found: {file_path}")
        return None
    
    # Get file extension and size
    file_extension = os.path.splitext(file_path)[1].lower()
    file_size = os.path.getsize(file_path)
    
    logger.info(f"Processing {lottery_type} screenshot: {file_path}")
    logger.info(f"File size: {file_size} bytes, Extension: {file_extension}")
    
    # Encode image as base64
    try:
        with open(file_path, 'rb') as image_file:
            base64_content = base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"Error reading image file: {str(e)}")
        return None
    
    # Create system prompt based on lottery type
    system_prompt = create_system_prompt(lottery_type)
    
    # Use Google Gemini for OCR processing
    client = get_gemini_client()
    if client:
        try:
            logger.info(f"Processing with Google Gemini for {lottery_type}")
            
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
            result = process_with_gemini(base64_content, lottery_type, system_prompt, image_format, screenshot_id=getattr(screenshot_path, 'id', None))
            if result and "results" in result and result["results"]:
                logger.info(f"Google Gemini processing completed successfully for {lottery_type}")
                return result
        except Exception as e:
            logger.error(f"Error in Google Gemini processing: {str(e)}")
    
    # If no AI client is available or processing failed
    if not get_gemini_client():
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

def process_with_gemini(base64_content, lottery_type, system_prompt, image_format='jpeg', screenshot_id=None):
    """
    Process a screenshot using Google Gemini for OCR.
    
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
    import google.generativeai as genai

    start_time = datetime.utcnow()
    request_id = None
    prompt_tokens = None
    completion_tokens = None
    status = 'error'  # Default to error, will change to success if all goes well
    error_message = None
    
    try:
        # Get the lazily loaded client
        client = get_gemini_client()
        if not client:
            error_message = "Cannot process with Google Gemini: No client available"
            logger.error(error_message)
            
            # Log the failed API request
            APIRequestLog.log_request(
                service='google',
                endpoint='generate_content',
                model='gemini-2.0-flash-exp',
                status='error',
                error_message=error_message,
                screenshot_id=screenshot_id,
                lottery_type=lottery_type
            )
            return None
            
        # Process as image using Google Gemini
        logger.info(f"Sending screenshot to Google Gemini for OCR processing: {lottery_type}")
        
        # Prepare image for Gemini
        import io
        from PIL import Image
        
        # Decode base64 image
        image_data = base64.b64decode(base64_content)
        image = Image.open(io.BytesIO(image_data))
        
        # Generate content with Gemini
        response = client.generate_content([
            system_prompt,
            image
        ])
        
        # Get response text
        response_text = response.text
        
        # Record successful API call metrics
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        status = 'success'
        
        # Log the successful API request
        APIRequestLog.log_request(
            service='google',
            endpoint='generate_content',
            model='gemini-2.0-flash-exp',
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            status='success',
            duration_ms=duration_ms,
            request_id=request_id,
            screenshot_id=screenshot_id,
            lottery_type=lottery_type
        )
        
        logger.info(f"Google Gemini response received for {lottery_type}")
        logger.debug(f"Raw response: {response_text}")
        
        # Parse the JSON response
        try:
            parsed_response = json.loads(response_text)
            
            # Validate the response structure
            if not isinstance(parsed_response, dict) or "results" not in parsed_response:
                error_message = f"Invalid response structure from Google Gemini for {lottery_type}"
                logger.error(error_message)
                logger.error(f"Response content: {response_text}")
                
                # Update the API request log with the error
                APIRequestLog.log_request(
                    service='google',
                    endpoint='generate_content.json_parse',
                    model='gemini-2.0-flash-exp',
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
                    "ocr_provider": "google",
                    "ocr_model": "gemini-2.0-flash-exp",
                    "raw_response": response_text,
                    "error": error_message
                }
                
            # Add metadata to the response
            parsed_response["ocr_timestamp"] = datetime.utcnow().isoformat()
            parsed_response["ocr_provider"] = "google"
            parsed_response["ocr_model"] = "gemini-2.0-flash-exp"
            
            return parsed_response
            
        except json.JSONDecodeError as e:
            error_message = f"Failed to parse JSON response from Google Gemini for {lottery_type}: {str(e)}"
            logger.error(error_message)
            logger.error(f"Response content: {response_text}")
            
            # Update the API request log with the error
            APIRequestLog.log_request(
                service='google',
                endpoint='generate_content.json_parse',
                model='gemini-2.0-flash-exp',
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
                "ocr_provider": "google",
                "ocr_model": "gemini-2.0-flash-exp",
                "raw_response": response_text,
                "error": error_message
            }
    
    except Exception as e:
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        error_message = f"Error in Google Gemini processing: {str(e)}"
        logger.error(error_message)
        
        # Log the failed API request
        APIRequestLog.log_request(
            service='google',
            endpoint='generate_content',
            model='gemini-2.0-flash-exp',
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            status='error',
            duration_ms=duration_ms,
            error_message=error_message,
            request_id=request_id,
            screenshot_id=screenshot_id,
            lottery_type=lottery_type
        )
        
        return None

def create_system_prompt(lottery_type):
    """
    Create a system prompt tailored to the specific lottery type.
    """
    base_prompt = """You are an expert OCR system specialized in extracting lottery data from South African National Lottery screenshots.

IMPORTANT: Respond ONLY with valid JSON in the exact format specified below. Do not include any explanatory text, markdown formatting, or code blocks.

Extract the following information and return it as JSON:

{
    "lottery_type": "exact lottery name from image",
    "results": [
        {
            "draw_number": "draw/game number",
            "draw_date": "YYYY-MM-DD format",
            "numbers": [list of main numbers as integers],
            "bonus_numbers": [list of bonus/powerball numbers as integers, empty array if none]
        }
    ]
}

Key requirements:
- Extract ALL visible lottery results from the image
- Use exact lottery names as shown (e.g., "LOTTO", "LOTTO PLUS 1", "PowerBall", "Daily Lotto")
- Convert all numbers to integers
- Use YYYY-MM-DD date format
- For Daily Lotto, bonus_numbers should be an empty array []
- Include draw numbers and dates exactly as shown

Focus on accuracy and completeness. Extract every visible lottery result in the image."""

    return base_prompt